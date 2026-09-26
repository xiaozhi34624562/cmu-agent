# WattBot Challenge 2025：KohakuRAG 论文与代码精读

## 结论先行

KohakuRAG 的价值不只在“层级索引”。它把三个经常被分开优化的问题做成了一个闭环：

1. 用 Document → Section → Paragraph → Sentence 树保留结构和引用 provenance；
2. 用 LLM 多查询规划和跨查询共识扩大检索覆盖率；
3. 用 retry、结构化输出和 abstention-aware ensemble 控制拒答、引用和随机性。

论文最值得借鉴的工程结论是：在这个引用敏感、数值容差极严的任务上，Prompt 顺序和失败重试的收益远大于再叠加一个 BM25 通道。也就是说，RAG 的瓶颈并不总在 Retriever；Context layout、输出协议和不确定性处理可能是更大的质量杠杆。

## 本地资料

- 论文：[KohakuRAG.pdf](papers/KohakuRAG.pdf)
- 代码：[KohakuRAG](code/KohakuRAG/)
- 来源与版本：[source-manifest.md](resources/source-manifest.md)

## 比赛背景与网址

WattBot 2025 要求系统基于 32 份 AI 能源与环境影响相关的论文、技术报告和幻灯片回答问题。语料约 500K tokens，训练集 41 个有标注问题，测试集 282 个问题；问题涉及功耗、水耗、碳排放和性能指标。

主要入口：

- [Kaggle 比赛主页](https://www.kaggle.com/competitions/WattBot2025)
- [Leaderboard](https://www.kaggle.com/competitions/WattBot2025/leaderboard)
- [Discussion：选手交流与解题思路](https://www.kaggle.com/competitions/WattBot2025/discussion)
- [Code / Notebooks](https://www.kaggle.com/competitions/WattBot2025/code)
- [论文 arXiv 页面](https://arxiv.org/abs/2603.07612)
- [作者代码仓库](https://github.com/KohakuBlueleaf/KohakuRAG)

时间上需要区分：比赛发生在 2025 年，38 页的完整论文于 2026 年 3 月公开。KohakuRAG 以队名 `Kohaku-Lab` 获得 Public 和 Private Leaderboard 双第一，Private 最终分数为 0.861。

## 评分协议为什么决定了系统设计

系统输出可抽象为 `(answer, references, abstain)`：

| 指标 | 权重 | 含义 |
|---|---:|---|
| Value Score | 75% | 数值答案需落在 ±0.1% 相对误差内；类别答案归一化后精确匹配 |
| Reference Score | 15% | 预测引用集合与真值集合的 Jaccard 相似度 |
| Hallucination Score | 10% | 证据不足时正确拒答，而不是猜测 |

```text
Final = 0.75 × Value + 0.15 × Reference + 0.10 × Hallucination
```

这意味着：

- 只生成“语义上差不多”的答案没有分；
- 数值正确但引用错，仍然损失 15%；
- 对所有困难问题都拒答，会损失主要的 Value 分；
- 为提高 recall 无限制扩大上下文，反而可能造成错值、错引用和错误拒答。

KohakuRAG 的层级检索、retry 和投票分别对应这三个矛盾。

## 系统总览

```text
PDF / Markdown / Text
          │
          ▼
Document → Section → Paragraph → Sentence (+ Image nodes)
          │ bottom-up embedding propagation
          ▼
SQLite + sqlite-vec / optional BM25
          │
Question → LLM Query Planner → n related queries
          │                         │
          └──────── dense retrieval per query ────────┘
                              │
                  dedup + cross-query reranking
                              │
                   hierarchical context expansion
                              │
             context-before-question structured prompt
                              │
       blank? → increase top-k and retry → valid candidate
                              │
                 multi-run / cross-model ensemble
                              │
                answer + value + exact references
```

## 1. 层级文档索引

### 四级树与节点标识

每份文档解析为：

```text
document
└── section
    └── paragraph
        └── sentence
```

节点 ID 类似 `doc:sec_i:p_j:s_k`，并保留 source document ID 和位置信息。图表作为特殊 paragraph node；可以存 VLM caption，也可以使用 Jina v4 直接做 image embedding。

固定长度 chunk 的问题是：

- 句子可能从定义与条件中被切开；
- 表格标题、脚注和数字可能不在同一 chunk；
- chunk ID 很难自然映射到原文结构和引用；
- 召回小 chunk 后缺少足够上下文，召回大 chunk 又引入噪声。

KohakuRAG 的关键不是只检索父节点，而是“细粒度命中 + 按树扩展上下文”。Sentence 提供精准定位，Paragraph/Section 提供解释范围，document ID 提供引用 provenance。

### Bottom-up embedding propagation

Sentence 叶节点直接编码：

```text
e_sentence = Encoder(sentence_text)
```

父节点使用子节点 embedding 的 token-length weighted average：

```text
e_parent = Σ token_count(child) × e_child / Σ token_count(child)
```

好处：父节点向量不需要再次把整段文本送入模型，可从子节点增量构建；不同层级向量落在同一空间中。风险是平均会抹平少数但关键的数字或否定句，并不等价于对完整父文本重新编码。对于“某表格脚注中的例外条件”，应仍以 sentence/paragraph 叶层召回为主。

论文建立出的索引规模为：32 documents、639 sections、944 paragraphs、24,565 sentences 和 280 images，其中 275 张图可提取内容。

## 2. 多查询检索与跨查询重排

Planner 把问题扩展为多种检索表达：

- 替换术语和同义词；
- 展开缩写；
- 拆解 compound question；
- 加入文档中可能出现的上下文关键词。

每个 planned query 独立取 Top-k。对于候选节点 `v`，系统计算：

- `frequency(v)`：多少个 query 都检索到该节点；
- `score(v)`：多个 query 的相似度累计；
- `combined(v)`：归一化 frequency 与 score 的加权组合。

这个方法可视为轻量的 query ensemble。相比 Cross-Encoder，它不需要额外大模型逐 pair 重排；相比简单 RRF，它保留原始相似度强度。

消融结果说明不能只看共现频率：Frequency-only 在 k=4 时只有 0.396，而不重排为 0.808；Combined 在不同 k 上最稳定。原因是多个同质改写可能把一个泛化但不精确的段落反复召回，频率并不自动等于相关性。

Planner query 数量从 2 增至 6，k=4 从 0.562 提升到 0.787。生产环境应设置 query diversity 检查，避免六个几乎相同的 query 浪费检索预算。

## 3. Hierarchical context expansion

命中 sentence 后加入 parent paragraph 和局部 siblings；命中 paragraph 后可加入 parent section。代码支持：

- `parent_depth` / `child_depth`；
- node ID dedup；
- tree-overlap dedup；
- 最终 `top_k_final` 截断。

这里存在一个容易忽略的 token amplification：Top-k 是检索节点数，不是最终 prompt snippet 数。每个节点扩展父子上下文后，实际 token 数可能成倍增长。因此生产系统要同时控制：

```text
retrieval_top_k
expanded_node_count
unique_document_count
final_token_budget
```

## 4. Prompt 顺序、结构化输出与 Retry

### Context 放在 Question 前面

论文把标准的 `Question → Context` 改为 `Context → Question`：

| k | 标准 Q→C | 重排 C→Q |
|---:|---:|---:|
| 4 | 0.418 | **0.752** |
| 8 | 0.485 | **0.783** |
| 16 | 0.704 | **0.811** |

k=4 相对提升 80%。作者用 lost-in-the-middle、attention sink 和 recency bias 解释。工程上更重要的含义是：问题与严格输出要求靠近生成位置，模型更容易遵守格式并聚焦最后的任务指令。

这项收益很大，也提示实验可能同时改变了指令布局，而不只是“上下文顺序”。迁移时应在自己的模型、context length 和 system/user message 结构上重新做 A/B test。

### 结构化答案

模型输出包括：

- natural language `answer`；
- 评测使用的 `answer_value`；
- `ref_id`；
- `explanation`；
- 证据不足时的 `is_blank`。

仓库 prompt 对单位处理要求非常严格：解释中必须说明单位如何使用或转换，但 `answer_value` 只能输出值本身。这是把“推理过程”和“评测字段”分离的正确做法。

### Retry as iterative deepening

如果模型输出 `is_blank`，系统增加 top-k 并重新检索/生成，直到有答案或达到 retry 上限。

| Max retries | k=4 | k=8 | k=16 |
|---:|---:|---:|---:|
| 0 | 0.488 | 0.836 | 0.837 |
| 1 | 0.720 | 0.843 | 0.846 |
| 2 | **0.827** | **0.854** | **0.871** |

低 k 时相对提升 69%。本质上是按难度分配算力：简单问题用小上下文，只有拒答的问题才支付更高检索和生成成本。

风险是模型的 `is_blank` 并非校准后的置信度。模型也可能在错误证据上自信作答，此时 retry 不会触发。生产环境还应增加 citation entailment、数值一致性和 answer confidence gate。

## 5. Multimodal retrieval

KohakuRAG 提供两条路线：

1. Caption-based：Qwen-VL 生成 image caption，把 caption 作为 paragraph text 检索；
2. Vision-enabled：Jina v4 直接编码图片，并把检索到的图传给支持视觉输入的 LLM。

在 k=16 上：

| Embedding | Score |
|---|---:|
| Jina v3 text-only | 0.824 |
| Jina v3 + captions | 0.824 |
| Jina v4 + native images | **0.890** |

Direct image embedding 比 text-only 高 6.6 个百分点。Caption 是有损中间表示，尤其会漏掉图中坐标轴、图例、单位和趋势；但 direct vision 的存储、推理和 API 成本更高。对金融年报可采用 router：普通正文走 text，检测到 chart/table/scan 时才走视觉通道。

## 6. Ensemble 与拒答感知投票

单次生成有随机性，系统支持五种 aggregation：

| 模式 | 策略 |
|---|---|
| Independent | answer 与 references 分别投票 |
| AnswerPriority | 先选答案，再从该答案对应 runs 中选引用 |
| RefPriority | 先选引用，再选匹配答案 |
| Union | 选答案后合并所有匹配 run 的引用 |
| Intersection | 选答案后只保留共同引用 |

`ignore_blank=true` 的逻辑是：只要存在非 blank 答案，就先过滤 blank 再投票；只有全 blank 时才拒答。n=9 时由 0.882 提升至 0.894，收益 1.2pp。AnswerPriority 平均排名最好，因为引用是从最终答案对应的 runs 中选，不容易出现“答案 A + 支持答案 B 的引用”。

性能随 ensemble size 近似对数增长，约 9–11 次后边际收益明显下降。每次 run 都包含检索和生成，成本近似线性增长；线上系统应改为 confidence-triggered ensemble，而不是所有请求固定跑 9 次。

## 关键实验与错误分析

论文分析 2,583 个预测，75.2% 完全正确。错误中的分布为：

| 错误类型 | 占错误比例 | 工程含义 |
|---|---:|---|
| 不必要拒答 | 26.8% | evidence 找到了但模型仍 blank；retry/blank filtering 有效 |
| 引用不匹配 | 23.6% | 答案对但引用错，需 evidence-constrained citation |
| 值选择错误 | 22.2% | 上下文存在多个看似合理的数字 |
| 舍入/计算错误 | 13.3% | ±0.1% 容差下必须做程序化计算 |
| 类型错误 | 12.2% | 数值与类别、字符串格式不一致 |
| 单位转换错误 | 1.6% | 正确证据被检索后，模型大多能处理单位 |

最重要的结论：Reference mismatch 与 Value selection 合计接近一半错误。继续增加召回可能只会给模型更多相似数字；下一步应做 evidence selection 和 constrained extraction，而不是无上限扩大 context。

## Leaderboard 稳定性

- KohakuRAG：Public 0.902 (#1) → Private 0.861 (#1)；
- 单次 Gemini-3-pro + images：0.901 → 0.839，下降 6.2%；
- GPT-oss-120B 7-run ensemble：0.862 → 0.857，只下降 0.5%；
- 最终 Top-5 mixed ensemble：Private 0.861。

这表明 ensemble 的主要价值不是推高 Public 峰值，而是降低 partition shift 和单次采样方差。论文还指出 Public #21/#20 最终成为 Private #2/#3，提醒不能只围绕 Public Leaderboard 调参。

## 代码导读

| 目录/文件 | 作用 |
|---|---|
| `src/kohakurag/types.py` | Document/Section/Paragraph/Node 等核心类型 |
| `src/kohakurag/parsers.py` | Markdown/Text → 层级 payload |
| `src/kohakurag/pdf_utils.py` | PDF 文本、页和图片抽取 |
| `src/kohakurag/indexer.py` | 节点构建与 embedding |
| `src/kohakurag/datastore.py` | In-memory 与 KohakuVault/sqlite-vec store、BM25、上下文扩展 |
| `src/kohakurag/pipeline.py` | planner、retrieval、dedup、rerank、snippet assembly |
| `scripts/wattbot_answer.py` | 比赛 Query Planner、prompt、retry、structured output |
| `scripts/wattbot_aggregate.py` | 五种 ensemble voting 与 blank handling |
| `scripts/wattbot_validate.py` | 官方三项加权评分 |
| `workflows/sweeps/` | embedding、top-k、rerank、LLM、ensemble 消融 |
| `configs/` | KohakuEngine 的可版本化 Python 配置 |

推荐阅读顺序：

```text
docs/architecture.md
  → src/kohakurag/types.py
  → src/kohakurag/indexer.py
  → src/kohakurag/datastore.py
  → src/kohakurag/pipeline.py
  → scripts/wattbot_answer.py
  → scripts/wattbot_aggregate.py
```

仓库比论文更接近一个可复用框架：支持 async I/O、并发限制、API retry、SQLite 单文件部署、Jina v4、BM25、sweep 和 mock chat model。但“production-ready”应谨慎理解：外部 API、模型下载、规则式 PDF 解析、引用约束和成本治理仍需业务侧补齐。

## 论文与代码的一致性/差异

- 论文的层级节点、planner、三种 rerank、prompt reorder、retry 和五种 ensemble 在代码中都有对应实现。
- 论文默认实验写 Jina v3 768-dim；仓库 README 部分位置写 1024-dim，`docs/wattbot.md` 又写 768。实际复现必须以具体 config 和模型输出维度为准。
- `pyproject.toml` 声明 Apache-2.0，但当前 commit 没有 `LICENSE` 文件；使用或分发前应向作者确认并补齐许可证文本。
- 测试包含外部 API 和大模型集成项，不能把“仓库有 tests”理解成离线、零成本即可完整验证。

## Senior AI Engineer 视角：迁移与改造

### 值得直接迁移

1. 层级 node ID 和 provenance；
2. 细粒度命中、父级上下文扩展；
3. query planning 与跨查询 dedup/rerank；
4. context-before-question 的实验设计；
5. `is_blank`、retry 和结构化输出；
6. answer-aware citation aggregation；
7. 将 retrieval、answer、citation、abstention 分开评测。

### 需要重做

1. **PDF parser**：规则式 section detection 对双栏、扫描件、跨页表格和异常 heading 不稳；金融场景应引入 layout model 与 table structure recognition。
2. **Parent embedding**：加权平均可作为快速 baseline，但关键父节点建议额外 full-text embedding 或 late chunking。
3. **Citation constraint**：让模型自由输出 `ref_id` 仍会错引；应从实际 evidence IDs 中 constrained select，并加 entailment 检查。
4. **数值推理**：精确容差任务应用 Python/SQL/DSL 执行计算，LLM 负责生成公式和解释。
5. **成本控制**：固定多次 ensemble 改为基于熵、run disagreement、evidence coverage 的动态升级。
6. **增量索引**：单文件 SQLite 很适合小规模可移植部署；大规模、多租户、高并发场景需要分片、版本化和增量更新策略。

## 面向金融 PDF RAG 的推荐组合

```text
Layout-aware PDF parser
    ├─ text hierarchy: document/section/table/paragraph/sentence
    └─ page image hierarchy: page/figure/chart/table crop
                         │
            text dense + BM25 + image embedding
                         │
              multi-query / entity-period routing
                         │
       cross-query fusion + strong final reranker
                         │
        hierarchical evidence expansion with token budget
                         │
          executable calculation + constrained citation
                         │
      confidence gate → retry / visual path / ensemble
```

KohakuRAG 最适合作为“引用型、结构化文档 RAG 的系统骨架”。它不是最终答案，但比只替换 embedding model 更接近真正可运营的方案。

## 复现建议

先用 2 份文档和 mock/small LLM 验证：解析 → index → retrieve → context expansion。再逐步加入 Jina v4、planner、retry 和 ensemble。不要一开始运行完整 sweep；论文的最佳方案涉及大模型 API、多次推理和图像 embedding，成本会线性累积。


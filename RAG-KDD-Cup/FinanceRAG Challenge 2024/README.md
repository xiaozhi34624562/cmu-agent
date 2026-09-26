# FinanceRAG Challenge 2024：Multi-Reranker 论文与代码精读

## 结论先行

Multi-Reranker 的核心不是“把多个向量检索器做融合”，而是把检索任务改造成两级 Cross-Encoder 筛选：第一级用较轻的 Jina reranker 对全量 query-document pair 打分，保留 Top 200；第二级按数据子集切换更合适的 reranker，输出 Top 10。它再配合金融查询关键词扩展、MultiHiertt 表格抽取，以及论文中描述但仓库尚未开源的长上下文答案融合。

这一方案的比赛价值很高，但不能直接照搬到生产环境。对全语料做 Cross-Encoder 是高精度、低可扩展性的竞赛打法；生产系统应在它前面补充 BM25/Dense ANN 召回，并把 Multi-Reranker 保留为后续精排层。

## 本地资料

- 论文：[Multi-Reranker.pdf](papers/Multi-Reranker.pdf)
- 代码：[FinanceRAG](code/FinanceRAG/)
- 来源与版本：[source-manifest.md](resources/source-manifest.md)

## 比赛背景与网址

FinanceRAG 是 ACM ICAIF 2024 相关的金融 RAG Challenge。语料来自 10-K、收益报告、财务表格等，覆盖术语检索、事实性问答、表格数值推理和多轮问答。比赛把 RAG 拆成两个任务：

1. Task 1：对每个问题从语料中返回最相关的 Top 10 corpus，主要指标是 nDCG@10。
2. Task 2：根据检索出的证据生成精确答案，重点考察长上下文、数值和表格推理。

主要入口：

- [Kaggle 比赛主页](https://www.kaggle.com/competitions/icaif-24-finance-rag-challenge)
- [Leaderboard](https://www.kaggle.com/competitions/icaif-24-finance-rag-challenge/leaderboard)
- [Discussion：选手交流与解题思路](https://www.kaggle.com/competitions/icaif-24-finance-rag-challenge/discussion)
- [Code / Notebooks](https://www.kaggle.com/competitions/icaif-24-finance-rag-challenge/code)
- [论文 arXiv 页面](https://arxiv.org/abs/2411.16732)
- [作者代码仓库](https://github.com/cv-lee/FinanceRAG)

论文报告最终获得第二名，并给出 Task 1 Public Leaderboard nDCG@10 = 0.63996。需要注意，公开榜成绩不等同于最终 Private Leaderboard 泛化能力；论文只有 4 页，也没有报告完整的置信区间、逐数据集结果和所有工程参数。

## 任务与数据集

| 子集 | 文档类型 | 主要能力 |
|---|---|---|
| FinDER | 10-K 与披露文件 | 金融术语、缩写、专业表达 |
| FinQABench | 10-K | 事实性与幻觉检测 |
| FinanceBench | 10-K | 真实世界直接问答 |
| TATQA | 财务报告文本与表格 | 算术、比较、逻辑推理 |
| FinQA | 收益报告文本与表格 | 多步数值推理 |
| ConvFinQA | 收益报告 | 对话式、多轮金融推理 |
| MultiHiertt | 年报层级表格与正文 | 跨表格、跨章节的复杂推理 |

nDCG@10 同时奖励“找到了相关文档”和“把它放在更靠前的位置”。简化表示为：

```text
DCG@10  = Σ relevance_i / log2(i + 1)
nDCG@10 = DCG@10 / ideal_DCG@10
```

因此，只提高 Top 200 召回但不改善 Top 10 顺序不会带来足够收益；这正是第二级 reranker 的作用。

## 论文方法：三阶段系统

```text
Query / Corpus
      │
      ├─ Query keyword expansion (GPT-4o-mini)
      └─ MultiHiertt table-only corpus refinement
                    │
                    ▼
      Jina reranker over full candidate set
                    │ Top 200
                    ▼
       Dataset-specific second reranker
                    │ Top 10 / Top 20
                    ▼
       LLM generation and long-context fusion
```

### 1. Pre-retrieval：查询扩展和语料重写

原始问题常包含缩写、隐含语义和多步意图。作者用 GPT-4o-mini 实验了：

- paraphrase；
- keyword extraction；
- hypothetical document；
- 原始 query 与扩展 query 拼接。

消融实验的关键结果：

| Query / Corpus 组合 | nDCG@10 |
|---|---:|
| 原始 query + 原始 corpus | 0.48949 |
| 原始 + paraphrase | 0.51228 |
| 原始 + keyword | 0.54090 |
| 原始 + hypothetical document | 0.43707 |
| 原始 + keyword + MultiHiertt table-only | **0.58102** |
| 原始 + corpus summary | 0.45589 |

工程解释：

- keyword expansion 保留了原始问题，同时补充可匹配的金融实体和术语，信息损失较小。
- hypothetical document 在这个任务上可能把问题改写成“看起来像答案”的文本，引入与真实财务披露不一致的词汇和事实噪声。
- corpus summary 对需要精确数值的问题危险：摘要器倾向于保留主题结论，却删除年份、单位、表头和脚注。
- table-only 对 MultiHiertt 有效，因为相关事实高度集中在表格；但不能无条件应用到其他子集，否则会丢失定义、时间范围和计算口径。

仓库中的 `pre_retrieval.py` 实际做法是把原始 query 和 LLM 生成内容拼接，并仅对 MultiHiertt 调用 `_extract_table_from_corpus()`。仓库还附带 `queries_prep.jsonl`，让 query expansion 在不重复调用 API 时保持可复现。

### 2. Retrieval：两级 Cross-Encoder

第一级统一使用：

```text
jinaai/jina-reranker-v2-base-multilingual
全语料候选 → Top 200
```

第二级根据子集选择：

| 子集 | 第二级模型 |
|---|---|
| FinDER | `BAAI/bge-reranker-v2-m3` |
| FinQABench | `jinaai/jina-reranker-v2-base-multilingual` |
| FinanceBench | `jinaai/jina-reranker-v2-base-multilingual` |
| TATQA | `BAAI/bge-reranker-v2-m3` |
| FinQA | `Alibaba-NLP/gte-multilingual-reranker-base` |
| ConvFinQA | `BAAI/bge-reranker-v2-m3` |
| MultiHiertt | `jinaai/jina-reranker-v2-base-multilingual` |

Cross-Encoder 联合编码 `(query, document)`，能直接建模术语、数字和上下文关系，通常比单独编码后做 cosine similarity 更准。代价是每个 query-document pair 都需要一次模型前向计算。

仓库的 `prepare_dataset.py` 为每个 query 建立对全 corpus 的候选集合，`run.sh` 再进行第一级全量 rerank。这说明它本质上不是“ANN 召回 + rerank”，而是“全量 rerank + 再 rerank”。复杂度接近 `O(|Q| × |D| × CrossEncoderCost)`，只适合比赛规模或离线批处理。

### 3. Generation：32K 上下文管理

论文中的生成策略为：

```text
若 Query + Top 20 corpus <= 32K tokens：
    一次生成答案
否则：
    Top 1-10 生成 R1
    Top 11-20 生成 R2
    再融合 R1 与 R2
```

设计动机不是模型“装不下”，而是长上下文中间位置的信息利用率下降。对于金融问答，这个风险尤其明显，因为答案可能只是表格中的一个数字。

但这里存在两个技术问题：

1. 按排名机械分成两半可能把同一计算链所需证据拆开。
2. 答案级 fusion 无法恢复第一次生成时已经遗漏的证据，也可能把两个口径不同的数字错误合并。

生产化时更合理的做法是按文档、年份、表格或 evidence group 分组，并让第二阶段对“证据 + 中间计算”做可验证聚合。

## 代码导读

| 文件 | 作用 |
|---|---|
| `prepare_dataset.py` | 通过 Kaggle CLI 下载并重排七个子集的数据结构 |
| `pre_retrieval.py` | LLM query expansion、MultiHiertt 表格抽取、prepared corpus 生成 |
| `prompt.json` | 不同子集的 query expansion prompt |
| `rerank.py` | CrossEncoder 加载、Top-K rerank 和结果保存 |
| `financerag/rerank/cross_encoder.py` | 生成 query-document pair 并批量打分 |
| `run.sh` | 安装依赖、下载数据、两级 rerank、生成最终 CSV |
| `financerag/tasks/` | 七个子集的加载和统一任务接口 |

推荐阅读顺序：

```text
run.sh
  → prepare_dataset.py
  → pre_retrieval.py
  → rerank.py
  → financerag/rerank/cross_encoder.py
  → financerag/tasks/BaseTask.py
```

### 论文与代码的差距

这是复现时最重要的一点：

- 仓库 README 明确将 Task 2 划掉；
- `run.sh` 只生成 `results/final.csv` 的检索结果；
- 论文中的 Top 20、32K split、R1/R2 fusion 没有实现；
- `financerag/generate/openai.py` 只是通用封装，不构成完整比赛生成流水线。

所以该仓库可以复现论文的检索主干，但不能宣称完整复现端到端第二名方案。

## Senior AI Engineer 视角：为什么有效，哪里不稳

### 有效之处

1. **把误差分解到阶段。** Query、corpus、reranker、generation 分开做消融，比只看最终答案更容易定位收益。
2. **按数据分布选 reranker。** 表格推理、术语检索和直接事实问答的最佳交叉编码器并不相同。
3. **拒绝过早摘要。** 金融 RAG 的数值、单位、年份、表头和脚注都可能是答案条件。
4. **先优化排序指标。** nDCG@10 给检索阶段提供稳定、可自动化的离线反馈。

### 风险与限制

1. **全量 Cross-Encoder 不可扩展。** 百万级 chunk 下延迟和 GPU 成本不可接受。
2. **数据集级模型路由依赖已知标签。** 生产 query 通常没有 FinQA/TATQA 这样的子集 ID，需要训练 router 或统一 reranker。
3. **使用标注选择最佳 reranker 有过拟合风险。** 应按 company、fiscal year、document 划分验证集，避免近重复文档泄漏。
4. **Query expansion 是外部 API 依赖。** 需要缓存、版本化 prompt，并测量每种扩展的增量收益和成本。
5. **论文证据有限。** 只有 4 页，缺少端到端 Task 2 数值、逐子集指标、延迟、成本和显著性分析。

## 如何迁移到生产级金融 RAG

推荐架构：

```text
Query normalization / entity + period extraction
                  │
      BM25 + Dense ANN parallel recall
                  │  Top 100-300
           RRF / calibrated fusion
                  │
       one strong cross-encoder reranker
                  │  Top 20-50
       evidence grouping by filing/table/year
                  │
       calculation-aware answer generator
                  │
    citation, unit and period consistency checks
```

落地时优先补充：

- 查询路由：公司、报表类型、报告期、指标和单位；
- 表格结构：保留 row/column header、footnote 和 page coordinates；
- 双通道召回：BM25 处理 ticker、缩写和精确指标名，Dense 处理语义改写；
- Reranker 校准：按 query type 建立分桶评测，而不是盲目串联多个大模型；
- 数值验证：答案必须能回溯到单元格或可执行计算式；
- 指标拆分：Recall@K、nDCG@K、数值准确率、引用 precision/recall、延迟和每 query 成本。

如果语料很小、答案价值极高、允许离线批处理，这篇论文的“直接全量 rerank”可以作为质量上限；如果语料持续增长，它应该是评测 oracle，而不是线上主架构。

## 复现建议

仓库要求 Python 3.10+、CUDA 12.2+、Kaggle credentials 和 OpenAI API key。完整 `run.sh` 会安装 FlashAttention、下载比赛数据并执行大量 Cross-Encoder 计算，作者建议 A100/Colab Pro+。

建议分阶段复现：

1. 先只跑一个小子集和少量 queries，验证数据格式；
2. 对比 original query 与 prepared query；
3. 固定第一级 Top 200，再更换第二级模型；
4. 记录每个阶段的 nDCG@10、GPU 时间和显存；
5. 最后自行实现 Task 2，并明确其不是仓库原始代码。


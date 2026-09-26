# EReL@MIR 2025 多模态文档检索：官方前三名代码与方案精读

## 结论先行

EReL@MIR 2025 的三个获奖方案给出了三条清晰的技术路线：

- iLearn：训练五个 GME-Qwen2-VL LoRA 专家，再用 DINOv2 visual anchor 和 rank fusion 冲击最高分；
- LLMHunter：不训练模型，通过 GME、ColQwen2、多路召回、传统局部特征验证和 Qwen2.5-VL-72B 重排，在第一名 0.1 分以内；
- GPU is all you need：完全 zero-shot，只用 ColQwen2 late interaction 和 FAISS，结构最简单，但与前两名有明显差距。

最重要的行业结论是：多模态文档 RAG 不能把 PDF 一律 OCR 成纯文本。页面截图、局部图像、OCR 文本和 layout chunk 是互补的检索视图；性能领先的系统采用同一多模态 backbone，但针对“文档内页面检索”和“开放域视觉知识检索”设计不同路线。

## 本地资料

- 官方 Overview：[EReL-Multimodal-Document-Retrieval-Challenge-Overview.pdf](papers/EReL-Multimodal-Document-Retrieval-Challenge-Overview.pdf)
- 第一名技术报告：[1st-iLearn-Technical-Report.pdf](papers/1st-iLearn-Technical-Report.pdf)
- 第一名代码：[01-iLearn-MDR](code/01-iLearn-MDR/)
- 第二名代码：[02-LLMHunter-MMDocRetrievalChallenge](code/02-LLMHunter-MMDocRetrievalChallenge/)
- 第三名代码：[03-GPU-is-all-you-need-MultiModal_InformationRetrieval](code/03-GPU-is-all-you-need-MultiModal_InformationRetrieval/)
- 来源、commit 与许可：[source-manifest.md](resources/source-manifest.md)

## 比赛背景与网址

EReL@MIR 是 The Web Conference 2025 同期 workshop。Track 1 “Multimodal Document Retrieval Challenge” 是多模态 RAG 的检索前端评测，要求一个统一系统处理两种差异很大的任务。

主要入口：

- [Kaggle 比赛主页](https://www.kaggle.com/competitions/multimodal-document-retrieval-challenge)
- [Leaderboard](https://www.kaggle.com/competitions/multimodal-document-retrieval-challenge/leaderboard)
- [Kaggle Discussion：选手交流与解题思路](https://www.kaggle.com/competitions/multimodal-document-retrieval-challenge/discussion)
- [Kaggle Code / Notebooks](https://www.kaggle.com/competitions/multimodal-document-retrieval-challenge/code)
- [官方 Challenge 页面](https://erel-mir.github.io/challenge/mdr-track1/)
- [官方 Winners 与代码](https://erel-mir.github.io/challenge/results/)
- [官方 Overview 论文](https://arxiv.org/abs/2606.04240)

官方 workshop 的 Discussion 页面目前仍是 TBA，因此实际方案资料以 Kaggle Discussion、官方 Winners、Overview 论文和三个 GitHub 仓库为主。

## 排名口径：必须先讲清楚

| Award rank | Team | Combined score | Submissions |
|---:|---|---:|---:|
| 1 | iLearn | 65.69 | 120 |
| 2 | LLMHunter | 65.59 | 59 |
| — | GoAhead | 60.73 | 62 |
| 3 | GPU is all you need | 57.30 | 14 |

`GoAhead` 在原始 leaderboard 上排第三，但没有按要求提交可验证代码，主办方无法复核，因此不具备获奖资格；官方第三名顺延为 `GPU is all you need`。本目录严格按官方 Winners 页面下载 1st/2nd/3rd 获奖代码。

如果后续文章写“Leaderboard raw #3”，应指 GoAhead；写“official 3rd-place winner”，应指 GPU is all you need。二者不能混用。

## 两个任务与评分

### Task 1：MMDocIR

给定文本问题和指定长文档，从该文档的所有 PDF 页面中找到相关页。

- 313 份文档；
- 平均 65.1 页；
- 覆盖 academic paper、financial report、government/legal document、guidebook、brochure、news 等十类文档；
- 检索空间限制在当前文档内部；
- 目标是 page-level retrieval，不是直接生成答案。

### Task 2：M2KR

根据 image 或 image+text query，从开放域 Wikipedia 风格的 passage/screenshot corpus 中找相关内容。来源包含 WIT、KVQA、OVEN、OK-VQA、Infoseek、Encyclopedic-VQA 等知识密集型视觉任务。

### 评分

每个任务计算：

```text
TaskScore = mean(Recall@1, Recall@3, Recall@5)
FinalScore = mean(MMDocIR TaskScore, M2KR TaskScore)
```

当一个 query 有多个相关项时，需要在 Top-k 中覆盖全部相关项才能取得 100% recall。这比单 positive 的 hit rate 更强调 multi-positive coverage。

官方记录：455 entrants、41 active participants、22 teams、586 submissions。第一、第二名只差 0.10 分。

## 为什么这不是“一个模型统一解决一切”

比赛要求 unified model，但三个获奖队都采用了：

```text
shared Qwen2-VL-family embedding backbone
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
MMDocIR: text → page       M2KR: image(+text) → passage
within-document routing    open-domain visual routing
```

统一的是表示 backbone，不是检索流程。MMDocIR 需要读懂页面 layout、表格和文本；M2KR 需要视觉实体识别、世界知识和近重复图像匹配。把两种任务强行塞进同一条无差别 pipeline，反而损失性能。

## 第一名 iLearn：Fine-tuned expert ensemble + Visual Anchor

### 系统结构

```text
GME-Qwen2-VL-7B
  ├─ LoRA expert 1
  ├─ LoRA expert 2
  ├─ LoRA expert 3
  ├─ LoRA expert 4
  └─ LoRA expert 5
          │ rank averaging / fusion
          ▼
    GME ensemble ranking
          │
M2KR query image → DINOv2 vs page sub-images
          │ similarity > task-specific threshold
          ▼
    force-promote visual anchor candidate to rank 1
```

### 1. k×[EOS] pooling

普通 GME 使用一个 EOS token 的最后层 hidden state 作为整体 embedding。iLearn 追加 `k=5~10` 个 EOS，平均这些 token 的 hidden states：

```text
embedding = mean(last_hidden_state[:, -k:, :])
```

技术报告称 Top-k recall 提升 2–3 points，几乎不增加主干前向成本。仓库代码可看到 5-token 和 7-token mean pooling 变体。

合理解释是：单 EOS 是一个高方差的信息瓶颈；多个尾部 token 给 Transformer 多个可聚合位置。但它并非通用结论，效果依赖模型训练方式、padding、chat template 和 EOS 的 attention mask，迁移到其他 VLM 时需要重新验证。

### 2. 五个 LoRA 专家

五个 GME retriever 使用不同训练样本和超参数进行 LoRA fine-tuning，多 positive contrastive objective 让每个 query 可以拉近多个正确项。仓库 `run.sh` 展示了不同 learning rate 和 epoch 组合，例如 `2e-5/1 epoch`、`5e-5/1 epoch`、`1e-5/1-2 epochs`，LoRA rank 64、alpha 16、dropout 0.05。

最终不是平均 embedding，而是对五个 ranked list 做平均名次融合。这样避免不同 expert 的 raw similarity scale 不可比。

### 3. Visual Anchor Point

M2KR 中很多 query image 会在候选 Wikipedia screenshot 的局部区域近似重复。iLearn：

1. 把候选页面分割成 sub-images；
2. 用 DINOv2 编码 query image 和所有 sub-images；
3. 计算最大 cosine similarity；
4. 若超过子任务阈值，直接把该候选提升到 rank 1。

这相当于一个高 precision shortcut：语义模型不知道图中人物是谁时，实例级视觉匹配仍能找到包含同一图片的页面。

风险也非常明显：它利用了 benchmark 中近重复视觉资产。真实金融场景中，同一张图可能被复制到多个研报，或者只改了一个年份和坐标轴；Visual Anchor 应作为候选增强信号，不能直接等同于语义正确。

### 代码与复现性

关键文件：

| 文件 | 作用 |
|---|---|
| `run.sh` | 五专家训练、推理、rank merge 和 visual result merge |
| `fine-tune/ft.py` / `zhengliu/train.py` | LoRA + multi-positive contrastive training |
| `*/gme_inference.py` | 多 EOS pooling 的 GME wrapper |
| `cv_test/dinov24test.py` | DINOv2 visual anchor similarity |
| `merge_rank.py` | 五个系统的平均 rank fusion |
| `merge_result.py` | 用 visual similarity 调整最终结果 |
| `report.pdf` | 第一名技术报告 |

完整系统 README 报告使用 8×A100 40 GB。仓库包含代码但没有完整 LoRA checkpoints，脚本还有作者机器的绝对路径和 `to/your_path` placeholder，不能一键复现榜单分数。

## 第二名 LLMHunter：Training-free multi-route + 72B VLM reranker

### 总体思路

LLMHunter 不更新任何模型参数，把效果提升集中在：

- 多粒度、多模态召回；
- 不同路线的候选合并；
- 传统视觉几何验证；
- 大型 VLM 对候选做最终 yes/no relevance judgment。

官方榜 65.59；仓库自报 65.5 with rerank、64.0 without rerank。也就是说 Qwen-VL rerank 提供最后约 1.5 points，而总计约 12 points 的提升主要来自多路召回与重排组合，不是某一个单模型替换。

### M2KR 路线

```text
Route A: GME image(+text) query → passage text
Route B: GME query image → layout/page/subfigure image
          │
          ├─ SIFT / ORB + RANSAC homography verification
          ▼
      merge candidate pool
          │
Qwen2.5-VL-72B-AWQ binary relevance reranker
```

SIFT/ORB 检查局部 keypoint matching 和 homography inlier ratio，适合验证近重复图像；GME 负责语义相关性；72B VLM 负责最后的跨模态相关性判断。三者分别解决 instance match、semantic recall 和 contextual relevance。

### MMDocIR 路线

```text
Route A: ColQwen2 text → page image late interaction
Route B: GME text → layout/page image
Route C: GME text → OCR text chunks
          │
          ▼
   fusion + query-adaptive instructions
          │
          ▼
     Qwen2.5-VL reranking
```

ColQwen2 的 late interaction 保留多 token/page patch 向量，通过 MaxSim 让 query token 分别匹配页面的不同区域，比把整页压成一个向量更适合表格和复杂 layout。

### 为什么它特别值得学习

第一名靠训练五专家达到 65.69，第二名零训练达到 65.59，差距只有 0.10。这说明在多模态检索中，route design、候选覆盖和强 reranker 可以抵消大量 fine-tuning 收益。

不过“training-free”不等于“低成本”：Qwen2.5-VL-72B-AWQ、GME-7B 和 ColQwen2-7B 仍要求高显存和较长推理时间。它降低的是训练成本和数据依赖，不一定降低线上延迟。

### 代码导读

| 文件 | 作用 |
|---|---|
| `m2kr_1_gme_instruct_*` | GME image/text route |
| `m2kr_2_gme_*subfig*` | layout/subfigure 视觉路线 |
| `utils/image_similarity.py` | ORB、SIFT、RANSAC 几何验证 |
| `mmdocir_1_colqwen.py` | ColQwen2 page late interaction |
| `mmdocir_2_gme_layout_*` | GME layout image embedding/retrieval |
| `mmdocir_3_gme_text_*` | OCR text embedding/retrieval |
| `*ContentJudger/qwen25vl_judger.py` | Qwen2.5-VL relevance judgment |
| `submission_best.py` | 合并最终 Top 5 submission |

仓库还给出只用 GME 的 unified solution，榜单约 61.7，可作为更可落地的成本基线。

## 第三名 GPU is all you need：Zero-shot ColQwen2

第三名完全不训练、不 rerank、不 ensemble，用同一个 ColQwen2 backbone 服务两个任务。

### MMDocIR

每页构建两份 multi-vector representation：

- page screenshot image embedding；
- 官方 VLM-generated page text embedding。

二者沿 token dimension 拼接，再与 text query 做 late-interaction MaxSim，输出 Top 5 pages。这里的“融合”保留 token-level 向量，不是把 image/text 各压成一个 dense vector 后求平均。

### M2KR

1. 从 Wikipedia 页面 screenshot 中裁剪或从网页抓取 candidate images；
2. 用 ColQwen2 得到 multi-vector output；
3. 去除 special token 区域后做 mean pooling，得到单向量；
4. 用 `faiss.IndexFlatL2` 精确搜索；
5. 把 image neighbor 映射回 source article。

这条路线简单、透明，是很好的 zero-shot baseline。它的局限包括：

- mean pooling 丢失 late interaction 的细粒度优势；
- `IndexFlatL2` 是精确 brute-force，语料扩大后需要 IVF/HNSW/PQ；
- live Wikipedia scraping 会随网页变化，降低时间可复现性；
- 没有 reranker，Top 5 容易被视觉相似但语义错误的图片占据。

### 代码导读

| 文件 | 作用 |
|---|---|
| `Task1_MMDocIR/src/task1_ColQwen2.py` | 页面 image/text embedding、late interaction、Top 5 |
| `Task1_MMDocIR/misc/retrieval_workflow.png` | Task 1 流程图 |
| `Task2_M2KR/src/scrape.py` | Wikipedia image scraping |
| `Task2_M2KR/src/extract_images.py` | screenshot 图像区域提取 |
| `Task2_M2KR/src/model.py` | ColQwen2 与 mean pooling |
| `Task2_M2KR/src/main.py` | FAISS IndexFlatL2 构建与查询 |

README 报告使用多张 A100 或 L40S、约 48 GB VRAM。数据和模型需要单独下载。

## 三队横向比较

| 维度 | iLearn | LLMHunter | GPU is all you need |
|---|---|---|---|
| Official rank | 1 | 2 | 3 |
| Score | 65.69 | 65.59 | 57.30 |
| Backbone | GME-Qwen2-VL-7B | GME + ColQwen2 | ColQwen2 |
| Fine-tuning | 5 个 LoRA experts | 无 | 无 |
| Multi-route | 中等 | 最强 | 简单两任务分支 |
| Reranker | rank ensemble + visual promotion | Qwen2.5-VL-72B | 无 |
| 传统视觉 | DINOv2 visual anchor | SIFT/ORB/RANSAC | screenshot crop/scrape |
| Late interaction | 非主线 | MMDocIR ColQwen2 | MMDocIR 主线 |
| 推理成本 | 很高，5 experts | 很高，72B reranker | 相对最低 |
| 复现门槛 | 训练数据、5 LoRA、8×A100 | 多模型与 72B 显存 | 模型/数据和多 GPU |
| 核心价值 | 训练与 ensemble 上限 | 无训练系统设计上限 | 简洁 zero-shot baseline |

## Senior AI Engineer 视角：真正可迁移的原则

### 1. Page image 是一等公民

PDF 的语义不仅在 OCR text：

- 表格的行列关系；
- 图表的轴、图例和空间邻近；
- 页面标题与图注；
- 字体、颜色和版式层级；
- 扫描件中 OCR 丢失的细节。

因此应同时保留 `page_image`, `layout_blocks`, `ocr_text`, `table_structure` 四种视图，而不是解析完文本就丢弃页面图。

### 2. 共享 backbone，按 query/task 路由

推荐 router：

| Query 类型 | 主路线 |
|---|---|
| 公司、年份、指标、精确术语 | BM25 + text dense |
| “图中/下图/趋势/柱状图” | page image + chart crop |
| 扫描公告 | OCR + page image |
| 表格数值 | table structure + page late interaction |
| 图片寻找出处 | visual anchor / image-to-image |

这与获奖队的共同模式一致：backbone 可以共享，候选生成和重排不必统一。

### 3. Late interaction 与 dense embedding 分层使用

- Dense single-vector：便宜，适合全库 first-stage ANN；
- ColQwen/ColPali multi-vector：精细但存储和 MaxSim 计算昂贵，适合文档内页面检索或 Top-N rerank；
- VLM generative reranker：最贵，适合最后几十个候选。

生产架构不应对百万页面直接跑 72B reranker。

### 4. 传统视觉仍有价值

DINO、SIFT、ORB 不是过时组件。它们对近重复图片、logo、人物、局部图表和 screenshot reuse 提供高 precision 信号，而且比让 VLM“理解一切”更可解释。

但必须区分：

```text
visual identity match ≠ semantic answer relevance
```

金融图表可能模板完全相同、年份和数字不同；应把 visual match 用于召回增强，再由 OCR/表格数值和时间条件验证。

### 5. 比赛指标隐藏了线上问题

该挑战只评检索 recall，没有评：

- 最终答案正确性；
- 引用是否支持回答；
- 数值和单位；
- 延迟、GPU 内存和成本；
- 页面版本漂移；
- OCR 错误和敏感文档安全。

把方案迁移到 RAG 时，必须补充 generation/citation evaluation，不能把 Recall@5 直接当作端到端质量。

## 推荐的金融多模态 RAG 架构

```text
PDF ingestion
  ├─ native text + coordinates
  ├─ table structure + cell lineage
  ├─ page screenshot
  └─ figure/chart crops
          │
          ▼
query router / entity-period-unit parser
          │
  ┌───────┼───────────────┐
  ▼       ▼               ▼
BM25   text dense      image dense ANN
  │       │               │
  └──── candidate union / RRF ────┘
                  │
        page-level late interaction
                  │
      VLM or cross-encoder reranker
                  │
    evidence group + exact value extraction
                  │
       grounded answer with page/cell citation
```

从三队中组合时，我会选择：第三名的简单 ColQwen2 baseline 建立可测下限，第二名的 multi-route 和 VLM reranking 提升精度，再只在数据量和收益证明充分时引入第一名的 LoRA experts。这样的实验路径能清楚知道每一层增加了多少质量、成本和复杂度。

## 复现顺序

1. 先跑第三名 MMDocIR 的少量页面，理解 multi-vector MaxSim；
2. 加入 image/text page fusion；
3. 复现第二名的 GME text/layout routes，先不启用 72B reranker；
4. 测量 fusion 前后 Recall@1/3/5；
5. 在小候选集上加入 Qwen-VL reranker；
6. 最后评估第一名的 k×EOS、单 LoRA expert、五 expert ensemble 和 visual anchor；
7. 每一步记录 GPU-hours、index size、query latency 和 score delta。

不要从第一名完整 8×A100 流程开始。对于学习和工程迁移，第二名与第三名更容易建立可解释的基线；第一名适合研究性能上限。


# RAG 竞赛论文、代码与工程分析仓库

本仓库按“论文、官方代码、来源核验、中文工程分析”组织 FinanceRAG、WattBot、EReL@MIR 和 Meta CRAG/CRAG-MM 资料。根 README 是全仓库导航；各项目和论文 README 承担方法、实验、代码映射、复现边界及金融 RAG 迁移的详细分析。

## 目录

- [仓库资产快照](#仓库资产快照)
- [快速导航](#快速导航)
- [完整资料索引](#完整资料索引)
- [代码与复现状态](#代码与复现状态)
- [主题学习路线](#主题学习路线)
- [仓库约定与已知缺口](#仓库约定与已知缺口)
- [设计与实施文档](#设计与实施文档)

## 仓库资产快照

| 资产 | 当前用户主工作区 | 根 Git 可移植归档 | 统计口径 |
|---|---:|---:|---|
| 比赛或年度专题 | 5 | 5 | FinanceRAG、WattBot、EReL、CRAG 2024、CRAG-MM 2025 |
| PDF 文件 | 15 | 14 | 主工作区排除 `.git/`、`.worktrees/`；Git 口径使用被追踪文件 |
| 独立 PDF 内容 | 14 | 14 | 按 SHA-256 去重 |
| `papers/` 归档 PDF | 14 | 14 | 项目维护的稳定论文入口 |
| 来源清单 | 13 | 13 | 三个既有项目加十个 CRAG 单元 |
| 本地官方代码仓库 | 7 | 0 | 嵌套仓库保留各自 `.git`，被根 `.gitignore` 排除 |
| Meta CRAG 研究单元 | 10 | 10 | CRAG 2024 八篇、CRAG-MM 2025 两篇 |

当前用户主工作区实际包含 15 个 PDF 文件、14 份独立 PDF 内容、14 个 `papers/` 稳定归档 PDF、13 份来源清单和 7 个本地官方代码仓库。EReL 第一名技术报告保留了两个内容相同的文件：[上游代码仓库原件](./EReL%40MIR%202025/code/01-iLearn-MDR/report.pdf)与 [`papers/` 稳定归档副本](./EReL%40MIR%202025/papers/1st-iLearn-Technical-Report.pdf)，两者 SHA-256 均为 `06c4b8ca4751dd502b9e49132570242ea101e0cf562dece329ac78274428474c`。

根 Git 的可移植归档只包含 14 个 PDF 和 13 份来源清单，不包含 7 个被忽略的嵌套代码仓库。因此，新 checkout 或隔离 worktree 默认只有 14 个 PDF、没有上游代码 clone；“15 个 PDF、7 个本地官方代码仓库”描述的是当前用户主工作区物理状态，不是根 Git 的自包含资产承诺。

## 快速导航

| 专题 | 独立论文内容 | 当前本地官方仓库 | 技术分析 | 论文入口 | 代码入口 | 来源 |
|---|---:|---:|---|---|---|---|
| FinanceRAG Challenge 2024 | 1 | 1 | [项目分析](./FinanceRAG%20Challenge%202024/README.md) | [Multi-Reranker](./FinanceRAG%20Challenge%202024/papers/Multi-Reranker.pdf) | [FinanceRAG](./FinanceRAG%20Challenge%202024/code/FinanceRAG/) | [manifest](./FinanceRAG%20Challenge%202024/resources/source-manifest.md) |
| WattBot Challenge 2025 | 1 | 1 | [项目分析](./WattBot%20Challenge%202025/README.md) | [KohakuRAG](./WattBot%20Challenge%202025/papers/KohakuRAG.pdf) | [KohakuRAG](./WattBot%20Challenge%202025/code/KohakuRAG/) | [manifest](./WattBot%20Challenge%202025/resources/source-manifest.md) |
| EReL@MIR 2025 | 2 | 3 | [项目分析](./EReL%40MIR%202025/README.md) | [挑战综述](./EReL%40MIR%202025/papers/EReL-Multimodal-Document-Retrieval-Challenge-Overview.pdf) · [第一名报告](./EReL%40MIR%202025/papers/1st-iLearn-Technical-Report.pdf) | [三支获奖团队](./EReL%40MIR%202025/code/) | [manifest](./EReL%40MIR%202025/resources/source-manifest.md) |
| Meta KDD Cup CRAG 2024 | 8 | 1 | [年度导航](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/README.md) | [八篇论文目录](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/) | [代码状态见各单元](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/) | [八份 manifest](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/) |
| Meta KDD Cup CRAG-MM 2025 | 2 | 1 | [年度导航](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/README.md) | [两篇论文目录](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/) | [代码状态见各单元](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/) | [两份 manifest](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/) |

Meta CRAG 跨年度的主题比较、方法矩阵和推荐顺序见 [Meta KDD Cup CRAG 总导航](./Meta%20KDD%20Cup%20CRAG/README.md)。

## 完整资料索引

### FinanceRAG Challenge 2024

- [中文技术分析](./FinanceRAG%20Challenge%202024/README.md)
- [Multi-Reranker 论文 PDF](./FinanceRAG%20Challenge%202024/papers/Multi-Reranker.pdf)
- [FinanceRAG 官方代码](./FinanceRAG%20Challenge%202024/code/FinanceRAG/)
- [来源清单](./FinanceRAG%20Challenge%202024/resources/source-manifest.md)

核心内容是金融语料的查询扩展、两阶段 cross-encoder reranking 和长上下文生成。代码包含检索与重排主线，但论文中的完整 Task 2 生成流程尚未全部发布。

### WattBot Challenge 2025

- [中文技术分析](./WattBot%20Challenge%202025/README.md)
- [KohakuRAG 论文 PDF](./WattBot%20Challenge%202025/papers/KohakuRAG.pdf)
- [KohakuRAG 官方代码](./WattBot%20Challenge%202025/code/KohakuRAG/)
- [来源清单](./WattBot%20Challenge%202025/resources/source-manifest.md)

核心内容是层级文档索引、多查询检索、上下文扩展、引用、多模态图像索引与拒答感知 ensemble。完整运行依赖外部模型、API 和比赛数据。

### EReL@MIR 2025

| 资料 | 本地入口 | 说明 |
|---|---|---|
| 中文技术分析 | [三支获奖团队方案比较](./EReL%40MIR%202025/README.md) | 比较 retrieval、reranking、视觉特征、融合、成本与复现性 |
| 挑战综述 | [Overview PDF](./EReL%40MIR%202025/papers/EReL-Multimodal-Document-Retrieval-Challenge-Overview.pdf) | 官方挑战综述与最终获奖口径 |
| 第一名技术报告归档 | [Visual Anchor Point PDF](./EReL%40MIR%202025/papers/1st-iLearn-Technical-Report.pdf) | 根 Git 追踪的稳定副本 |
| 第一名原始报告 | [上游 `report.pdf`](./EReL%40MIR%202025/code/01-iLearn-MDR/report.pdf) | 与归档副本 SHA-256 相同，仅存在于当前本地 clone |
| 第一名 iLearn | [MDR 官方代码](./EReL%40MIR%202025/code/01-iLearn-MDR/) | LoRA 专家、Visual Anchor；commit `ccda92d` |
| 第二名 LLMHunter | [MMDocRetrievalChallenge 官方代码](./EReL%40MIR%202025/code/02-LLMHunter-MMDocRetrievalChallenge/) | 多路检索与 VLM reranker；commit `4a6080a` |
| 第三名 GPU is all you need | [MultiModal_InformationRetrieval 官方代码](./EReL%40MIR%202025/code/03-GPU-is-all-you-need-MultiModal_InformationRetrieval/) | zero-shot ColQwen2 等路线；commit `e9010f2` |
| 来源清单 | [source manifest](./EReL%40MIR%202025/resources/source-manifest.md) | 排名区别、论文、代码 commit、许可证和数据链接 |

EReL 原始榜单第三名因未提交必需代码而不具备获奖资格；本仓库按官方获奖页面归档最终获奖前三名。

### Meta KDD Cup CRAG 2024

| 论文 | 技术分析 | PDF | 代码 | 来源 | 名次口径 | 复现状态 |
|---|---|---|---|---|---|---|
| Winning Solution For Meta KDD Cup'24 | [分析](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/01-Winning-Solution/README.md) | [PDF](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/01-Winning-Solution/papers/Winning-Solution-For-Meta-KDD-Cup-24.pdf) | [官方仓库状态](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/01-Winning-Solution/code/README.md) | [manifest](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/01-Winning-Solution/resources/source-manifest.md) | 三任务第一 | 官方 GitLab 上游 503；论文可审计 |
| Revisiting the Solution of Meta KDD Cup 2024: CRAG | [分析](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/02-Revisiting-CRAG/README.md) | [PDF](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/02-Revisiting-CRAG/papers/Revisiting-the-Solution-of-Meta-KDD-Cup-2024-CRAG.pdf) | [官方代码](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/02-Revisiting-CRAG/code/CRAG-in-KDD-Cup2024/) | [manifest](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/02-Revisiting-CRAG/resources/source-manifest.md) | 作者报告 Task 2/3 第二 | 本地 clone `df3fea4`；缺模型和完整数据 |
| A Simple yet Effective RAG Framework | [分析](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/03-Simple-Effective-RAG/README.md) | [PDF](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/03-Simple-Effective-RAG/papers/A-Simple-yet-Effective-RAG-Framework-for-Meta-KDD-Cup-2024.pdf) | [代码状态](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/03-Simple-Effective-RAG/code/README.md) | [manifest](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/03-Simple-Effective-RAG/resources/source-manifest.md) | Task 1 三个类别第一 | 未发现作者代码 |
| Knowledge Graph Integration and Self-Verification | [分析](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/04-KG-Self-Verification/README.md) | [PDF](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/04-KG-Self-Verification/papers/Knowledge-Graph-Integration-and-Self-Verification.pdf) | [代码状态](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/04-KG-Self-Verification/code/README.md) | [manifest](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/04-KG-Self-Verification/resources/source-manifest.md) | Task 3 条件简单题头部结果 | 未发现作者代码 |
| Honest AI | [分析](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/05-Honest-AI/README.md) | [PDF](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/05-Honest-AI/papers/Honest-AI.pdf) | [代码状态](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/05-Honest-AI/code/README.md) | [manifest](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/05-Honest-AI/resources/source-manifest.md) | Task 2 false-premise 类别第一 | 未发现作者代码或 adapter |
| TCAF | [分析](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/06-TCAF/README.md) | [PDF](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/06-TCAF/papers/5_TCAF_a_Multi_Agent_Approach_.pdf) | [代码状态](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/06-TCAF/code/README.md) | [manifest](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/06-TCAF/resources/source-manifest.md) | Task 1 multi-hop 类别第一 | 未发现作者代码或完整 prompts |
| A Hybrid RAG System | [分析](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/07-Hybrid-RAG/README.md) | [PDF](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/07-Hybrid-RAG/papers/A-Hybrid-RAG-System.pdf) | [官方仓库状态](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/07-Hybrid-RAG/code/README.md) | [manifest](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/07-Hybrid-RAG/resources/source-manifest.md) | Task 1 第三；Task 2 五类第一 | 官方 GitLab 上游 503；论文可审计 |
| MARAGS | [分析](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/08-MARAGS/README.md) | [PDF](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/08-MARAGS/papers/MARAGS.pdf) | [代码状态](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/08-MARAGS/code/README.md) | [manifest](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/08-MARAGS/resources/source-manifest.md) | 论文与官方 spotlight 名次存在冲突 | 未发现作者代码或 adapters |

### Meta KDD Cup CRAG-MM 2025

| 论文 | 技术分析 | PDF | 代码 | 来源 | 名次口径 | 复现状态 |
|---|---|---|---|---|---|---|
| Winning Meta KDD Cup'25 Task 2 | [分析](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/09-Winning-Task-2/README.md) | [PDF](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/09-Winning-Task-2/papers/18_Winning_Meta_KDD_Cup_25_Tas.pdf) | [官方代码](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/09-Winning-Task-2/code/crag-mm/) | [manifest](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/09-Winning-Task-2/resources/source-manifest.md) | Task 2 human evaluation 第一，0.233 | 本地 clone `2728d3a`；需 HF 模型/数据、搜索 API 和 GPU |
| DB3 Team's Solution For Meta KDD Cup'25 | [分析](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/10-DB3-Solution/README.md) | [PDF](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/10-DB3-Solution/papers/DB3-Team-Solution-For-Meta-KDD-Cup-25.pdf) | [官方仓库状态](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/10-DB3-Solution/code/README.md) | [manifest](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/10-DB3-Solution/resources/source-manifest.md) | Task 1/2 第二、Task 3 第一、ego-centric 大奖 | 官方 GitLab 上游 503；论文可审计 |

## 代码与复现状态

### 已克隆到当前主工作区的官方仓库

| 项目 | 本地仓库 | 固定提交 | 静态状态 | 完整运行仍需 |
|---|---|---|---|---|
| FinanceRAG | [FinanceRAG](./FinanceRAG%20Challenge%202024/code/FinanceRAG/) | `a4fc6e9` | Git 完整性与 Python 语法通过 | Kaggle 数据、OpenAI API、模型与 GPU |
| WattBot | [KohakuRAG](./WattBot%20Challenge%202025/code/KohakuRAG/) | `f3d27c8` | Git 完整性与 Python 语法通过 | 比赛数据、模型下载、生成 API |
| EReL 第一名 | [MDR](./EReL%40MIR%202025/code/01-iLearn-MDR/) | `ccda92d` | Git 完整性与 Python 语法通过 | LoRA checkpoints、完整数据、GPU |
| EReL 第二名 | [MMDocRetrievalChallenge](./EReL%40MIR%202025/code/02-LLMHunter-MMDocRetrievalChallenge/) | `4a6080a` | Git 完整性与 Python 语法通过 | 大模型、数据路径、GPU |
| EReL 第三名 | [MultiModal_InformationRetrieval](./EReL%40MIR%202025/code/03-GPU-is-all-you-need-MultiModal_InformationRetrieval/) | `e9010f2` | Git 完整性与 Python 语法通过 | 数据、模型、GPU、可能漂移的网页图片 |
| CRAG 2024 APEX | [CRAG-in-KDD-Cup2024](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/02-Revisiting-CRAG/code/CRAG-in-KDD-Cup2024/) | `df3fea4` | Git 完整性与 Python 语法通过 | CRAG 数据、mock API、模型与 GPU |
| CRAG-MM 2025 NVIDIA | [crag-mm](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/09-Winning-Task-2/code/crag-mm/) | `2728d3a` | Git 完整性与 Python 语法通过 | gated VLM、HF 数据、搜索 API、GPU |

这些目录是独立的上游 Git 仓库，不由根 Git 携带。表中的“静态通过”只表示仓库完整性和源码语法可检查，不表示依赖齐全、端到端运行成功或榜单结果已复现。

### 其他代码发布状态

| 论文 | 状态 | 处理方式 |
|---|---|---|
| 2024 db3 Winning Solution | 官方仓库已发布，上游核验时 HTTP 503 | 保留官方 URL 和失败原因，不使用第三方镜像 |
| 2024 Hybrid RAG | 官方仓库已发布，上游核验时 HTTP 503 | 保留官方 URL 和失败原因，不使用第三方镜像 |
| 2025 db3 Solution | 官方仓库已发布，上游核验时 HTTP 503 | 保留官方 URL 和失败原因，不使用第三方镜像 |
| Simple RAG | 未发现作者代码 | 以 `code/README.md` 记录检索范围 |
| KG Self-Verification | 未发现作者代码 | 不用第三方 GraphRAG 冒充论文实现 |
| Honest AI | 未发现作者代码或 adapter | 只按论文记录训练配置和缺口 |
| TCAF | 未发现作者代码或完整 prompts | 只归档官方论文与来源证据 |
| MARAGS | 未发现作者代码或 adapters | 保留方法与名次冲突说明 |

## 主题学习路线

1. **检索与重排：** [FinanceRAG](./FinanceRAG%20Challenge%202024/README.md) → [Simple RAG](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/03-Simple-Effective-RAG/README.md) → [APEX](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/02-Revisiting-CRAG/README.md)。
2. **层级文档与引用：** [KohakuRAG](./WattBot%20Challenge%202025/README.md) → [EReL 多模态文档检索](./EReL%40MIR%202025/README.md)。
3. **金融表格与结构化计算：** [FinanceRAG](./FinanceRAG%20Challenge%202024/README.md) → [Hybrid RAG](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/07-Hybrid-RAG/README.md) → [2024 db3](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/01-Winning-Solution/README.md)。
4. **验证与拒答：** [KG Self-Verification](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/04-KG-Self-Verification/README.md) → [Honest AI](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/05-Honest-AI/README.md) → [MARAGS](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/08-MARAGS/README.md)。
5. **Agent 与复杂推理：** [TCAF](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/06-TCAF/README.md) → [Hybrid RAG](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/07-Hybrid-RAG/README.md) → [2025 db3](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/10-DB3-Solution/README.md)。
6. **多模态检索：** [EReL 获奖方案比较](./EReL%40MIR%202025/README.md) → [NVIDIA Task 2](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/09-Winning-Task-2/README.md)。
7. **多轮视觉 RAG：** [CRAG-MM 年度导航](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/README.md) → [2025 db3](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/10-DB3-Solution/README.md)。
8. **生产评估与复现：** [2024 APEX](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/02-Revisiting-CRAG/README.md) → [Honest AI](./Meta%20KDD%20Cup%20CRAG/CRAG%202024/05-Honest-AI/README.md) → [NVIDIA Task 2](./Meta%20KDD%20Cup%20CRAG/CRAG-MM%202025/09-Winning-Task-2/README.md)，重点比较 accuracy、hallucination、missing、风险加权 score、延迟与成本。

## 仓库约定与已知缺口

- 每个项目或论文单元使用 `README.md` 保存中文技术分析，`papers/` 保存稳定论文归档，`code/` 保存官方仓库或代码状态说明，`resources/source-manifest.md` 保存来源、commit、许可证和复现缺口。
- 只有论文、作者、团队或官方比赛资料明确关联的仓库才称为“官方代码”；第三方复现不会混入。
- 上游 clone 保留自己的 `.git`，并由根 `.gitignore` 精确排除；这样可以保留上游历史，但新 checkout 不会自动获得这些仓库。
- PDF 物理文件数按权威主工作区统计；独立内容数按 SHA-256 去重。EReL 第一名报告的两个副本是唯一重复组。
- 不下载多 GB 模型权重、需接受条款或凭据的完整数据集，也不保存 API 密钥；manifest 提供外部依赖和下载入口。
- 2026-08-12 核验时，三个 AIcrowd GitLab 官方仓库返回 HTTP 503。它们属于“官方代码已发布但当前不可访问”，不同于“作者未发布代码”。
- PDF 可读、Git 完整性通过和 Python 语法通过都属于静态审计；未运行 GPU/API-heavy 官方评测的项目不会声称端到端或榜单复现。

## 设计与实施文档

- [Kaggle RAG 研究归档实施计划](./docs/superpowers/plans/2026-08-11-kaggle-rag-research-archive.md)
- [Meta CRAG 研究归档设计](./docs/superpowers/specs/2026-08-12-meta-crag-research-archive-design.md)
- [Meta CRAG 研究归档实施计划](./docs/superpowers/plans/2026-08-12-meta-crag-research-archive.md)
- [根 README 全仓库导航重构设计](./docs/superpowers/specs/2026-08-12-root-readme-navigation-redesign.md)
- [根 README 全仓库导航重构实施计划](./docs/superpowers/plans/2026-08-12-root-readme-navigation-redesign.md)

# Meta KDD Cup CRAG 学习档案

本目录把 2024 文本 CRAG 与 2025 多模态/多轮 CRAG-MM 的十篇代表性 workshop 技术报告整理为可核验研究单元。这里严格区分比赛、workshop 论文、主会论文、任务总名次和类别名次；未运行官方 GPU/API 评测的材料不会声称“复现榜单”。

- [CRAG 2024：八篇方案](./CRAG%202024/README.md)
- [CRAG-MM 2025：两篇获奖方案](./CRAG-MM%202025/README.md)

## 两届比赛如何演进

| 维度 | CRAG 2024 | CRAG-MM 2025 |
|---|---|---|
| 输入 | 文本问题 | 图片 + 文本，多轮上下文 |
| 信息源 | 网页、mock KG API | image-indexed KG、网页、多轮历史 |
| 核心错误 | 动态事实、长尾实体、错误前提、网页噪声 | 视觉目标错认、实体漂移、OCR、跨模态证据不一致 |
| 可靠性机制 | routing、verification、abstention、adapter/agent | grounding、multitask VLM、judge calibration、DPO/GRPO |
| 工程瓶颈 | 30 秒内检索/生成与幻觉平衡 | 更严格多模态推理、模型/检索延迟与人工评测 gap |

## 方法与复现矩阵

| 论文 | Retrieval / routing | Reliability | Agent / tuning | 本地论文 | 官方代码 |
|---|---|---|---|---|---|
| [2024 db3](./CRAG%202024/01-Winning-Solution/README.md) | 多粒度网页 + 公共数据 + KG API | prompt + 拒答微调 | LoRA | 有 | GitLab 暂不可达 |
| [APEX](./CRAG%202024/02-Revisiting-CRAG/README.md) | 领域/动态双路由 | 时间/实体约束 | zero-shot + few-shot/CoT | 有 | GitHub clone |
| [Simple RAG](./CRAG%202024/03-Simple-Effective-RAG/README.md) | retrieve-rank + augmentation | 指标选型 | CoT/ReAct 对比 | 有 | 无 |
| [KG Self-V](./CRAG%202024/04-KG-Self-Verification/README.md) | KG 优先、网页 fallback | evidence gate | LLM verifier | 有 | 无 |
| [Honest AI](./CRAG%202024/05-Honest-AI/README.md) | domain hybrid | selective prediction | QLoRA | 有 | 无 |
| [TCAF](./CRAG%202024/06-TCAF/README.md) | rewriting + constraints | false-premise detector | 三 agent flow | 有 | 无 |
| [Hybrid RAG](./CRAG%202024/07-Hybrid-RAG/README.md) | 文本/表格/KG | attribute/refusal | extractor + calculator | 有 | GitLab 暂不可达 |
| [MARAGS](./CRAG%202024/08-MARAGS/README.md) | cross-encoder | hittable relabel | 多 LoRA adapter | 有 | 无 |
| [NVIDIA Task 2](./CRAG-MM%202025/09-Winning-Task-2/README.md) | VLM query/rerank | RAGAS + threshold | multitask fine-tuning | 有 | GitHub clone |
| [db3 2025](./CRAG-MM%202025/10-DB3-Solution/README.md) | grounding + task-specific retrieval | refusal reward | SFT/DPO/GRPO | 有 | GitLab 暂不可达 |

## 四条学习主线

1. **完整获胜系统**：2024 db3 → APEX → 2025 db3，理解数据源路由、API/KG 和多模态检索如何组合。
2. **验证与拒答**：KG Self-Verification → Honest AI → NVIDIA Task 2，理解 evidence gating、selective prediction 和 judge calibration。
3. **复杂推理与模块化**：Simple RAG → Hybrid RAG → MARAGS → TCAF，比较 prompt、计算器、adapter 与 agent 的收益/成本。
4. **金融迁移**：把 query time、主体/期间/单位校验、point-in-time 数据、结构化计算和错误高惩罚作为基础设施，而不是只换 embedding。

## 阅读本档案的约定

每篇目录包含 `README.md`、`papers/`、`code/`、`resources/source-manifest.md`。`code/README.md` 表示作者未发布或上游暂不可访问；不会用第三方实现冒充官方代码。嵌套 clone 保留上游 `.git`，commit 与 license 写入 manifest。

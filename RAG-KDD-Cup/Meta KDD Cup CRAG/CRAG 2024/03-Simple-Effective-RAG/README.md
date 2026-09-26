# A Simple yet Effective RAG Framework

## 1. 一段结论

这篇 Task 1 报告以端到端 score 比较 RAG 组件，证明高级方法在 30 秒限制和错误负分下未必更好。团队获三个问题类别第一，而非 Task 1 总冠军。

[论文](./papers/A-Simple-yet-Effective-RAG-Framework-for-Meta-KDD-Cup-2024.pdf) · [代码状态](./code/README.md) · [来源清单](./resources/source-manifest.md)

## 2. 论文身份与比赛背景

本文是 2024 KDD Cup CRAG Workshop 的 Task 1 技术报告。`simple_w_condition`、`set`、`aggregation` 类别结果与出版类型均按 OpenReview/论文记录。

## 3. 任务与评分目标

给定网页证据后限时生成短答案；错误负分、拒答零分要求同时控制 coverage、hallucination 与 latency，不能只看局部 accuracy。

## 4. 问题诊断与基线弱点

直接 RAG 受 HTML 噪声和粗 chunk 影响；复杂 query augmentation 或 agent loop 又会放大幻觉和超时。局部指标改善可能损害最终 score。

## 5. 端到端架构与数据流

解析网页并切分，经 recall-then-rank/BGE 排序后，由 4-bit GPTQ Llama3-70B 生成；实验分支比较 direct、CoT、ReAct、Self-RAG、HyDE、Step-Back 和 query rewriting/fusion。

## 6. 核心机制

主线是清洗切分、retrieve-then-rank 与 CoT 短答案生成。昂贵 reranker 只处理有限候选，额外推理策略只有在端到端实验中证明收益才启用。

## 7. 实验、消融与报告分数

HyDE 让 set/false-premise accuracy 各升约 0.03；Step-Back 把 `simple_w_condition` 从 0.34 提至 0.43，但 hallucination 从 0.13 升至 0.17。ReAct multi-hop 达 0.21，却因超时和错误使总分比 CoT 低 0.1；原始 prompt 比 CoT 低 0.11。

## 8. 评分机制下为何有效

CoT 先归纳证据再输出短答案，retrieve-then-rank 控制昂贵排序成本。以真实时间预算下的 CRAG score 选组件，可避免 accuracy 提升却增加 Incorrect=-1 的反优化。

## 9. 代码地图

作者没有发布官方仓库，无法建立文件级代码地图。论文只能映射出 HTML 处理、检索/重排、query augmentation 和生成四个逻辑阶段；代码状态文件记录了检索范围。

## 10. 复现条件与缺失产物

需要 CRAG Task 1 数据、HTML/chunk 参数、BGE、Llama3-70B GPTQ、完整 prompts 和限时环境。chunk 参数、prompt 全文、随机种子与部署细节未公开。

## 11. 工程限制、延迟成本与故障传播

工程判断：每次 rewrite、agent loop 或反思都会增加延迟和新幻觉；上游 query 改写偏离会污染检索与生成。论文无代码，实验主要来自单一比赛分布，迁移前需重新校准。

## 12. 对金融 RAG 的迁移

工程判断：按事实、比较、聚合、多跳和错误前提分别测 accuracy/hallucination/latency。财务聚合走受控计算工具，最终答案短且带单位与来源；HyDE/Step-Back 仅在类别级验证后启用并设超时回退。

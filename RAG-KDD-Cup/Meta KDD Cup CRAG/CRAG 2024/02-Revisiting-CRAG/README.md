# Revisiting the Solution of Meta KDD Cup 2024: CRAG

## 1. 一段结论

APEX 用“领域 × 信息动态性”双路由贯穿 retrieval、augmentation、generation，证明统一 RAG pipeline 面对异构问题时会系统性失效，路由应成为一等架构组件。

[论文](./papers/Revisiting-the-Solution-of-Meta-KDD-Cup-2024-CRAG.pdf) · [官方代码](./code/CRAG-in-KDD-Cup2024/) · [来源清单](./resources/source-manifest.md)

## 2. 论文身份与比赛背景

本文是 APEX 团队的 2024 KDD Cup CRAG Workshop 技术报告，覆盖三项任务并重点讨论 Task 2/3。OpenReview 记录作者报告的 Task 2/3 第二名，本档案不把它改写成本地复现结论。

## 3. 任务与评分目标

系统需在网页、KG/API 和拒答之间选择路径，并在错误负分、拒答零分下提高期望得分。Task 3 还有约 50 个噪声网页与严格延迟预算，排序质量与成本必须共同优化。

## 4. 问题诊断与基线弱点

统一 RAG 忽略领域、动态性、实体别名和 query time，可能把错误实体传给 API、把过期网页当实时事实，或在缺证时继续生成。

## 5. 端到端架构与数据流

Router 用 Llama-3-8B 做领域分类并结合动态性选路。Web Retriever 解析 HTML、chunk、pre-rank、BGE-M3 rerank；API Extractor 抽取实体与时间后调用领域 mock KG；Llama-3-70B-Instruct 用领域 few-shot/CoT 生成并对数值后处理。

## 6. 核心机制

关键是双路由、网页 pre-rank + rerank、API 前实体/时间约束，以及按领域配置的 few-shot/CoT。动态且无实时 API 的问题倾向拒答。

## 7. 实验、消融与报告分数

公开集 LLM-only 与 direct RAG 为 -7.29%/-6.78%，Task 2/3 pipeline 为 31.22%/31.66%。Task 3 去掉 pre-rank，延迟从 5.96 秒升至 68.17 秒且分数下降；Task 2 去掉 entity match 或 time extraction，31.22% 降至 21.44%/18.45%。

## 8. 评分机制下为何有效

pre-rank 同时减少噪声错误和超时；实体/时间约束减少 API 的精确错误；动态性路由允许高风险时拒答。Few-shot/CoT 消融也表明裸 accuracy 上升不代表风险调整后 score 上升。

## 9. 代码地图

`main.py` 是入口，`models/router/router.py` 负责路由，`models/retrieve/` 负责检索，`models/mock_api/` 封装领域 API，`prompts/templates.py` 保存提示，`evaluation.py` 对接评估，架构图在 `image/`。

## 10. 复现条件与缺失产物

仓库固定于 `df3fea49e365520124453de85b70063a634c4b4d`，无独立 LICENSE。需要 CRAG 数据、mock API、Llama/BGE/reranker 权重和 GPU；本地只完成 Git 与语法静态检查。

## 11. 工程限制、延迟成本与故障传播

工程判断：router、实体链接和 API schema 构成级联依赖；8B 路由和 70B 生成增加延迟，prompt 规则会随 schema 漂移。生产系统需记录 `route_reason`、解析置信度和拒答原因，并缓存实体解析与稳定事实。

## 12. 对金融 RAG 的迁移

工程判断：实时行情、历史财报、公告事件、研报观点和公司关系分别路由到 API、point-in-time DB、文档索引与图关系。实体匹配输出证券代码和有效期，主体或时点不确定时先澄清或拒答。

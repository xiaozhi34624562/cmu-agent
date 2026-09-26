# A Hybrid RAG System with Comprehensive Enhancement on Complex Reasoning

## 1. 一段结论

ElectricSheep 把复杂推理前移到证据结构化层：分别处理网页文本、表格、属性、三元组、数值计算和错误前提，再交给受约束生成器。

[论文](./papers/A-Hybrid-RAG-System.pdf) · [代码状态](./code/README.md) · [来源清单](./resources/source-manifest.md)

## 2. 论文身份与比赛背景

本文是 2024 KDD Cup CRAG Workshop 技术报告，同时发布于 arXiv。论文报告 Task 1 第三及 Task 2 七类中的五类第一；名次来源见 manifest。

## 3. 任务与评分目标

覆盖三项任务及静态、慢变、实时、金融等领域。在错误负分和时限下，系统既要保留表格/数值结构，又要识别不可答与错误前提。

## 4. 问题诊断与基线弱点

复杂推理常因 HTML 清洗丢表格结构、实体关系不显式、数字未进入计算器而失败。扩大上下文不能替代新鲜数据源，也会增加幻觉。

## 5. 端到端架构与数据流

HTML parsing 保留表格，经 chunk refinement 后由 attribute predictor 判断问题属性；LLM/KG Extractor 生成文本、表格、三元组和模型知识四类参考，数值题进入 calculator，最后按受约束 reasoning prompt 输出。

## 6. 核心机制

证据按类型组织而非拼接相似 chunk；attribute predictor 控制策略/拒答；calculator 处理数值；false-premise 使用专门 prompt。结构化中间表示减轻生成器负担。

## 7. 实验、消融与报告分数

本地 Task 1 从 baseline 增至 15.8%，最终私榜 21.8%；私榜对比列出 db3 28.4%、md_dh 24.0%、ElectricSheep 21.8%。KG 和 hallucination control 是关键增量；static/slow-changing 较强，real-time/finance 较弱。

## 8. 评分机制下为何有效

结构化证据与计算器减少生成错误，attribute predictor 在高风险题拒答，从而降低 Incorrect=-1。实时/金融弱项说明推理增强无法弥补数据时点错误。

## 9. 代码地图

论文给出作者 GitLab 仓库，但核验时返回 HTTP 503，无法建立本地文件级映射。逻辑模块包括 HTML/table 处理、属性预测、LLM/KG 抽取、calculator、reasoning 与 corner-case handling。

## 10. 复现条件与缺失产物

需要 CRAG 数据、网页/表格清洗、属性预测器、KG API、LLM extractor、计算器与 prompts。官方仓库当前不可达，模型权重和数据未打包，无法验证实现完整性。

## 11. 工程限制、延迟成本与故障传播

工程判断：模块多、调用扇出和延迟高；LLM extractor 可能生成伪三元组，上游属性误判会送错处理路径。生产化需为每种中间表示定义 schema、provenance、置信度和超时回退，禁止模型知识与外部证据无标识混合。

## 12. 对金融 RAG 的迁移

工程判断：保留表格结构、单位、报告期与合并口径；数值计算使用可测试函数；三元组只从有 provenance 的披露抽取。attribute predictor 路由到财务计算、事件关系、实时行情或拒答，并把动态性作为核心特征。

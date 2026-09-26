# TCAF: Thought-Chain-Agent-Flow

## 1. 一段结论

TCAF 将错误前提检测、证据推理和最终表述分给 Detector、Thought、Answer 三类串行 agent。创新点是上下文职责分离，而不只是“多 agent”标签。

[论文](./papers/5_TCAF_a_Multi_Agent_Approach_.pdf) · [代码状态](./code/README.md) · [来源清单](./resources/source-manifest.md)

## 2. 论文身份与比赛背景

本文是 2024 KDD Cup CRAG Workshop 技术报告，官方 PDF 已从 OpenReview 下载并校验。论文报告 Task 1 multi-hop 类别第一；这是类别结果，不是 Task 1 总冠军。

## 3. 任务与评分目标

方案覆盖三项任务，重点处理多跳和错误前提。在 Incorrect=-1、Missing=0 下，Detector 需要及时阻止错误前提，推理链则必须在限时内组合可引用证据。

## 4. 问题诊断与基线弱点

最终生成器直接读取大量网页时容易 lost in context；多跳事实未先组合会导致漏答，错误前提又会让后续推理建立在不存在的关系上。

## 5. 端到端架构与数据流

预处理清洗网页，Retrieval 结合 query rewriting 与 reference constraint；conditional false-premise detection 只在必要路径触发。Detector 检查假设，Thought Agent 汇总证据，Answer Agent 消费压缩事实输出答案。

## 6. 核心机制

职责分离让 evidence synthesis 与 answer formatting 解耦，reference constraint 限制答案空间，条件检测避免所有请求都承担额外调用成本。

## 7. 实验、消融与报告分数

论文/OpenReview 报告 Task 1 multi-hop 类别第一，并称 Task 2/3 位居前列。由于本地未运行比赛环境，这些均保留为来源支持的作者/比赛表述，不生成额外复现数字。

## 8. 评分机制下为何有效

Detector 可将错误前提从 Incorrect=-1 转为拒答或纠正，Thought Agent 降低无关证据对答案的干扰。收益取决于上游摘要忠实度；若摘要编造，职责分离也会放大错误。

## 9. 代码地图

作者未发布官方仓库、完整 prompts 或模型配置，无法建立文件级映射。论文只支持 Pre-processing、Retrieval、Detector、Thought、Answer 五个逻辑模块。

## 10. 复现条件与缺失产物

需要 CRAG 数据、网页清洗、query rewriting、reference constraint、三类 agent prompts 与外部 LLM。论文 PDF 可审计，但代码、配置、运行日志和成本参数缺失。

## 11. 工程限制、延迟成本与故障传播

工程判断：串行 agent 增加调用、延迟与成本；Thought Agent 遗漏或编造后，Answer Agent 因看不到原文更难纠正。生产系统应传递带 citation 的 claim 列表，设置调用预算、超时回退和 agent-level traces。

## 12. 对金融 RAG 的迁移

工程判断：Detector 检查主体/期间/口径，Thought Agent 改成证据计划器，输出指标、依赖文档与公式；Answer Agent 只消费校验 claims。保存可审计证据图和计算步骤，不保存不受约束的自由思维链。

# Knowledge Graph Integration and Self-Verification

## 1. 一段结论

系统在 KG 命中时使用结构化事实，网页路径则先判断证据是否足够，只有通过 gate 才生成答案。关键贡献是把 evidence sufficiency 独立于答案表述。

[论文](./papers/Knowledge-Graph-Integration-and-Self-Verification.pdf) · [代码状态](./code/README.md) · [来源清单](./resources/source-manifest.md)

## 2. 论文身份与比赛背景

本文是 2024 KDD Cup CRAG Workshop 技术报告，研究 KG 集成与网页证据自验证。论文报告 Task 3 `simple_with_conditions` 类别头部结果，不将其表述为任务总冠军。

## 3. 任务与评分目标

系统覆盖网页与 mock KG，目标是在 `Perfect=1 / Acceptable=0.5 / Missing=0 / Incorrect=-1` 下减少无证据作答：结构化证据提高准确率，自验证门在缺证时拒答。

## 4. 问题诊断与基线弱点

语义相似不等于证据蕴含答案；KG 也可能因实体或参数错配返回“精确但错误”的事实。基线缺少独立可答性判断。

## 5. 端到端架构与数据流

系统做领域识别与实体规范化，调用 KG API 并转成自然语言证据；网页路径由 all-MiniLM-L6-v2 检索 top-15 snippets，LLM 判断证据是否充分，不足则拒答，充分才生成。

## 6. 核心机制

KG 优先消费高质量结构化结果，网页 fallback 则采用两阶段 verifier/generator。可答性与表述解耦，避免生成器一边判断证据一边被迫回答。

## 7. 实验、消融与报告分数

Task 2 公开集消融中，KG 使 accuracy 提升约 17%、overall score 提升约 22%；self-verification 主要降低 hallucination。阶段二 Task 1/2/3 为 0.174/0.228/0.210，错误率为 0.189/0.177/0.155；Task 3 条件简单题报告 42.2%。

## 8. 评分机制下为何有效

gate 判断 `P(correct|evidence)` 是否足以覆盖错误成本；证据不足转为 Missing=0，避免 Incorrect=-1。论文未给概率校准，仅用 LLM 文本判断，因此 verifier 与 generator 仍可能同源偏差。

## 9. 代码地图

作者未发布官方仓库，无法从逻辑模块映射到文件入口。代码状态文件记录了 OpenReview、论文与作者页面检索；第三方 GraphRAG 或 self-verification 项目未被冒充为论文实现。

## 10. 复现条件与缺失产物

需要 CRAG 网页/KG 数据、实体规范化规则、all-MiniLM-L6-v2、LLaMA 3、完整验证/生成 prompts。官方代码、prompt package、权重和配置均未发布。

## 11. 工程限制、延迟成本与故障传播

工程判断：KG 不天然解决实时性，实体错配会产生精确错误；同源 LLM verifier 对日期、单位和隐含矛盾未必可靠。两次 LLM 调用增加延迟，生产系统需确定性校验、freshness、跨源一致性和结构化阈值。

## 12. 对金融 RAG 的迁移

工程判断：将 KG 替换为证券主数据、财务指标库和关系图；先验证代码、报告期、币种与合并口径。网页片段做 entailment 与时点检查，证据不能支持金额或比较基准时返回带原因的拒答。

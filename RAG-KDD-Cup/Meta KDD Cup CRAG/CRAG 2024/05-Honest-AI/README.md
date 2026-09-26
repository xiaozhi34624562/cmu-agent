# Honest AI

## 1. 一段结论

Honest AI 把拒答从 prompt 技巧变成监督目标：重标训练答案并用 QLoRA 让 7B 模型学习何时说 `I don't know`，再以 domain hybrid 恢复部分覆盖。

[论文](./papers/Honest-AI.pdf) · [代码状态](./code/README.md) · [来源清单](./resources/source-manifest.md)

## 2. 论文身份与比赛背景

本文是 2024 KDD Cup CRAG Workshop 技术报告，同时发布于 arXiv。论文报告 Task 2 false-premise 类别第一；这是类别结果，不是 Task 2 总冠军。

## 3. 任务与评分目标

目标是在错误负分条件下做 selective prediction：可答样本提供覆盖，证据或能力不足时拒答，通过阈值平衡 accuracy、hallucination 与 missing。

## 4. 问题诊断与基线弱点

朴素 RAG 会把相似但错误的日期、数字和实体交给生成器；普通微调又把所有 gold 当成必须回答目标，导致不可答样本编造。cosine similarity 不能判断真实性。

## 5. 端到端架构与数据流

先按类别重标 target，用 4-bit Llama-2-7B-chat 做 QLoRA；混合路径用 Llama-3-8B RAG 处理较可靠的 movie 域，Sentence-BERT 剪枝，RAG 无有效答案时回退到拒答模型。

## 6. 核心机制

QLoRA 配置为 `r=64`、alpha 16、dropout 0.1、batch 8、学习率 2e-4、weight decay 0.001、5 epochs。标签变换让模型学习哪些类别不值得冒险，路由再控制回答覆盖。

## 7. 实验、消融与报告分数

微调模型在 323 条在线样本得 0.096；300 条离线混合实验中，阈值 0.75 将 0.073 提至 0.086，accuracy 增 0.026、hallucination 也增 0.013。结果说明阈值是 coverage-risk 决策变量。

## 8. 评分机制下为何有效

重标把拒答写入监督目标，使模型不再对所有 gold 强制作答；domain hybrid 恢复部分覆盖。系统以减少 Incorrect=-1 换取部分 Missing=0，并由阈值寻找正期望收益。

## 9. 代码地图

作者未公开代码、adapter 或标签变换脚本，无法建立文件级映射。代码状态文件记录 OpenReview、arXiv 和作者公开检索结果。

## 10. 复现条件与缺失产物

需要 Llama-2-7B-chat、4-bit QLoRA、CRAG 数据、标签规则、RAG 路由和外部搜索/KG 环境。论文给出主要超参，但缺完整标签脚本、adapter、数据切分、prompt 和随机种子。

## 11. 工程限制、延迟成本与故障传播

工程判断：按 question type 粗重标可能学到类别捷径，分布变化后过度拒答；router 错误会直接改变 coverage。RAG 路径还会引入外部调用延迟和冲突证据，需逐样本校准与失败原因监控。

## 12. 对金融 RAG 的迁移

工程判断：为金额、日期、主体和预测问题建立 risk tiers；高风险题只在结构化源与原文一致时回答。训练集加入口径冲突、跨期混用、同名公司和未来泄漏，线上同时监控 coverage、错误成本与 calibration curve。

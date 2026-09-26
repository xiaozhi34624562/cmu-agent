# DB3 Team's Solution For Meta KDD Cup' 25

## 1. 一段结论

db3 为三个 CRAG-MM 任务分别设计 retrieval，同时以 SFT、DPO、GRPO 和 ensemble 控制回答/拒答。核心洞见是视觉 grounding 与风险偏好必须共同优化。

[论文](./papers/DB3-Team-Solution-For-Meta-KDD-Cup-25.pdf) · [代码状态](./code/README.md) · [来源清单](./resources/source-manifest.md)

## 2. 论文身份与比赛背景

本文是 2025 KDD Cup CRAG-MM Workshop 技术报告，同时发布于 arXiv。论文与 PKU 报道支持 Task 1/2 第二、Task 3 第一及 ego-centric queries 大奖。

## 3. 任务与评分目标

Task 1 面向 image-indexed KG，Task 2 加 web，Task 3 处理多轮视觉对话。系统需要在视觉实体识别、证据检索与拒答之间平衡，并区分不同任务和评价口径。

## 4. 问题诊断与基线弱点

图片相似不等于同一实体；OCR 或 grounding 错误会让后续文本检索失去意义。纯 SFT 也难调节回答意愿，本地 judge/ensemble 容易过拟合或超时。

## 5. 端到端架构与数据流

Task 1 用 CLIP 召回，Grounding DINO 定位第一视角目标，VLM 重排 query/index image；Task 2 加实体识别、web query rewriting 和文本检索；Task 3 合并历史轮次维持实体状态。答案模型再经 SFT/DPO/GRPO 和 checkpoint/domain ensemble。

## 6. 核心机制

task-specific retrieval 解决不同模态误差；训练标签根据内部知识与 RAG 证据是否充分决定回答或拒答；偏好/RL 与 ensemble 调节风险偏好。

## 7. 实验、消融与报告分数

论文观察 DPO 更保守，missing 约 70%–90%；GRPO 更主动，missing 约 60%–80%，Task 1 两者最终约 5%。论文报告 Task 1/2 第二、Task 3 第一及大奖；本地未复现这些结果。

## 8. 评分机制下为何有效

接近比赛的正确正奖、拒答零、错误负奖使训练直接优化风险。DPO/GRPO 提供不同 coverage-risk 点，ensemble 再选择更稳答案，但收益必须扣除延迟和 judge 偏差。

## 9. 代码地图

论文给出作者 GitLab 仓库，但核验时返回 HTTP 503，无法建立文件级映射。逻辑模块包括 CLIP/Grounding DINO/VLM 重排、web/multi-turn retrieval、SFT/DPO/GRPO 与 checkpoint/domain ensemble。

## 10. 复现条件与缺失产物

需要 CRAG-MM 数据、CLIP、Grounding DINO、Llama Vision、judge、训练框架与大规模 GPU。官方源码当前不可达，commit/license 无法固定，权重和比赛环境未打包。

## 11. 工程限制、延迟成本与故障传播

工程判断：视觉 grounding、OCR、domain routing 任一错误都会级联；多 checkpoint ensemble 昂贵且可能超时，本地 judge 偏差会污染策略。线上应蒸馏模型、保留跨证据校验并记录多轮实体状态。

## 12. 对金融 RAG 的迁移

工程判断：图表、票据和公告截图先做 region grounding 与主体/期间识别，再回原始披露检索；OCR 文本不能直接当事实。奖励对错误金额、错公司和未来信息给予更高负收益，ensemble 仅用于离线研究。

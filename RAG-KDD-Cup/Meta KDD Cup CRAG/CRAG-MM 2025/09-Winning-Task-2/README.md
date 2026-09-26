# Winning Meta KDD Cup'25 Task 2

## 1. 一段结论

Team NVIDIA 将 query writing、reranking、grounded answering 和拒答蒸馏进单一 VLM，优势来自 26.5k 合成 datamix 与贴近人工判断的 proxy metric，而非堆叠模型。

[论文](./papers/18_Winning_Meta_KDD_Cup_25_Tas.pdf) · [官方代码](./code/crag-mm/) · [来源清单](./resources/source-manifest.md)

## 2. 论文身份与比赛背景

本文是 2025 KDD Cup CRAG-MM Workshop 技术报告，官方 PDF 已从 OpenReview 下载并校验。OpenReview 报告 Team NVIDIA 在 Task 2 最终人工评测第一，分数 0.233；自动与人工评测不混写。

## 3. 任务与评分目标

Task 2 输入图片与文本并加入网页多源证据，要求完成视觉理解、query 生成、重排、grounded answer 和拒答。最终以人工评价为关键口径，离线 proxy 必须与人评相关。

## 4. 问题诊断与基线弱点

多模型流水线部署复杂，自动 judge 可能与最终人工评价错位；视觉实体、网页证据和回答意愿任一失配都会降低结果。全局拒答阈值也可能掩盖领域差异。

## 5. 端到端架构与数据流

约 2.5k 原始样本经 Llama-4-Maverick 合成 query-writing、reranking、answering 数据，再由 GPT-4o judge 筛选为 26.5k datamix。Llama-3.2-11B-Vision-Instruct 通过任务指令切换角色，答案后处理使用拒答概率阈值。

## 6. 核心机制

单一多任务 VLM 减少服务数量；RAGAS judge 作为模型选择 proxy；阈值调节 coverage/hallucination。官方 HF 数据与模型在 manifest 中链接，但大权重未下载。

## 7. 实验、消融与报告分数

论文报告 RAGAS proxy 与人工判断相关性超过 0.92，最终 human-eval 为 0.233 并获 Task 2 第一。相关性是总体统计，不代表每个领域或错误类型都校准。

## 8. 评分机制下为何有效

与人评相关的 proxy 减少“自动榜优化、人工榜失效”；拒答概率阈值把错误风险转成可调决策。效果依赖 synthetic/judge bias 是否受控。

## 9. 代码地图

`agents/submission_agent_task_two.py` 是 agent；`data_gen.py`、`agents/data_gen_agent.py`、`synthetic/query_writing.py` 构造数据；`train.py` 训练；`local_evaluation.py` 评估；image/web loader 处理外部证据；Dockerfile/aicrowd.json 对应提交环境。

## 10. 复现条件与缺失产物

仓库固定于 `2728d3a21b474afee1ad88f21941c80479c678b7`，Apache-2.0。运行需 gated VLM、搜索 API、比赛图片/网页、HF 数据/模型和 GPU；本地只完成静态审计。

## 11. 工程限制、延迟成本与故障传播

工程判断：多任务梯度可能冲突，教师和 judge 偏好会固化到学生；query 错误会污染检索、重排和答案。单模型降低服务开销但不消除 VLM 推理成本，阈值应按领域、实体流行度和证据质量分层。

## 12. 对金融 RAG 的迁移

工程判断：把多任务改为图表识别、查询生成、证据重排、财务问答与拒答，用分析师标注 judge 校准。合成数据保持 point-in-time，单独评估金额、日期、主体、单位和引用完整性。

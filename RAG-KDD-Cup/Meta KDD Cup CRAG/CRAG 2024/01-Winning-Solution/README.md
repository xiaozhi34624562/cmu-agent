# Winning Solution For Meta KDD Cup' 24

## 1. 一段结论

db3 把 CRAG 视为受负分约束的动态数据系统：Task 1 组合网页与公共结构化数据，Task 2/3 规整 KG API，再用拒答微调控制生成风险。论文报告三个任务均第一，核心价值是检索、结构化查询、数据工程和拒答的联合优化。

[论文](./papers/Winning-Solution-For-Meta-KDD-Cup-24.pdf) · [代码状态](./code/README.md) · [来源清单](./resources/source-manifest.md)

## 2. 论文身份与比赛背景

本文是 db3 团队的 2024 KDD Cup CRAG Workshop 技术报告，覆盖 Task 1、2、3。论文、OpenReview 与北京大学团队报道共同支持三任务第一；它不是 KDD 主会论文，作者与名次口径见来源清单。

## 3. 任务与评分目标

Task 1 处理网页检索摘要，Task 2 加入 mock KG API，Task 3 面对更多噪声网页与 API。系统面向 `Perfect=1 / Acceptable=0.5 / Missing=0 / Incorrect=-1`：证据不足时拒答优于高风险猜测，同时不能靠全面拒答获得正分。

## 4. 问题诊断与基线弱点

错误来自三层：网页事实未被抽出；动态或领域数据不适合只靠网页；生成器拿到证据后仍可能扩写。统一 top-k RAG 无法同时解决新鲜度、结构化调用和负分风险。

## 5. 端到端架构与数据流

Task 1 用 BeautifulSoup 清洗 HTML，构造 coarse/fine、parent/child 多粒度 chunk，经 reranker 后与公共数据路径汇合，再由 Llama-3-8B-Instruct 生成。Task 2/3 先做领域与实体解析，生成受控 API，执行结果转回自然语言证据后进入拒答感知生成器。

## 6. 核心机制

多粒度检索兼顾定位与上下文；稳定领域走公共数据，动态问题保留 query time；短答案、错误前提指令和去幻觉微调控制输出；受限 schema 将自由代码生成收缩成可校验的 text-to-API。

## 7. 实验、消融与报告分数

论文报告 Task 1、2、3 分数分别为 28.4%、42.7%、47.8%，并给出领域/类型评估，但没有完整端到端消融表。这些数字是来源支持的比赛结果，不是本地复现结果。

## 8. 评分机制下为何有效

多源路由提高可答题覆盖，短答案和拒答微调降低错误成本，规整 API 减少工具格式错误。三者共同优化期望收益。工程判断：壁垒来自数据路由、KG schema 和训练标签组成的闭环，而非单独替换 embedding。

## 9. 代码地图

作者仓库地址已确认，但 AIcrowd GitLab 核验时返回 HTTP 503，无法建立文件级映射。论文对应的逻辑模块包括 HTML 清洗/切分、BCEmbedding 重排、公共数据、KG API 规整执行、Llama 生成与 LoRA 拒答训练；具体入口不能在仓库恢复前猜测。

## 10. 复现条件与缺失产物

需要 CRAG 数据/API、公共领域数据、BCEmbedding/reranker、Llama 3、vLLM 与 LoRA 资源。模型权重、完整数据和当前不可访问的仓库未打包；未运行 GPU 训练或榜单评测。

## 11. 工程限制、延迟成本与故障传播

工程判断：领域规则和公共数据维护成本高；路由、实体/时间解析或 API schema 错误会级联为“格式正确但事实错误”的答案。生产化需要 schema versioning、证据 lineage、超时回退、确定性校验和拒答原因可观测性。

## 12. 对金融 RAG 的迁移

工程判断：公告/研报走文档检索，行情/财务指标走 point-in-time SQL/API；生成前统一为带来源、日期、单位的 evidence object。训练样本覆盖证据不足、主体歧义、口径冲突和错误前提，并让错误金额或日期的成本高于拒答。

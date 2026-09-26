# Meta KDD Cup 2024 CRAG

## 比赛背景

CRAG 用 4,409 组 QA、五个领域、八种问题类型检验动态与长尾事实。Task 1 给约 5 个网页，Task 2 增加 mock KG API，Task 3 扩展到约 50 个噪声网页与 API。自动评测通常按正确 `+1`、拒答 `0`、错误 `-1` 计分；部分材料还区分 Perfect 与 Acceptable。它迫使系统同时优化 answer coverage 与 hallucination risk。

- [AIcrowd 比赛页](https://www.aicrowd.com/challenges/meta-comprehensive-rag-benchmark-kdd-cup-2024)
- [官方 workshop 日程与方案展示](https://kddcup24.github.io/pages/schedule.html)
- [OpenReview 11 篇 workshop submissions](https://openreview.net/submissions?venue=KDD.org%2F2024%2FWorkshop%2FKDD_Cup_CRAG)
- [获奖公告](https://discourse.aicrowd.com/t/meta-crag-challenge-2024-winners-announcement/10786)

## 八篇论文导航

| # | 方法主线 | 比赛口径 | 代码状态 |
|---|---|---|---|
| [01 db3 Winning Solution](./01-Winning-Solution/README.md) | 双通路检索、KG/API、拒答微调 | 三任务第一 | 官方 GitLab 当前 503 |
| [02 APEX Revisiting CRAG](./02-Revisiting-CRAG/README.md) | 领域/动态路由、实体与时间抽取 | 论文称 Task 2/3 第二 | [GitHub clone](./02-Revisiting-CRAG/code/CRAG-in-KDD-Cup2024/) |
| [03 Simple Effective RAG](./03-Simple-Effective-RAG/README.md) | 检索/重排、CoT、query augmentation | Task 1 三个类别第一 | 未发布 |
| [04 KG + Self-Verification](./04-KG-Self-Verification/README.md) | KG 结构化证据、可答性 gate | Task 3 条件简单题头部 | 未发布 |
| [05 Honest AI](./05-Honest-AI/README.md) | QLoRA 拒答学习、hybrid routing | Task 2 false-premise 第一 | 未发布 |
| [06 TCAF](./06-TCAF/README.md) | Detector/Thought/Answer agent flow | Task 1 multi-hop 第一 | 未发布；PDF 已归档 |
| [07 Hybrid RAG](./07-Hybrid-RAG/README.md) | 文本/表格/KG/计算器综合推理 | Task 1 第三；Task 2 五类第一 | 官方 GitLab 当前 503 |
| [08 MARAGS](./08-MARAGS/README.md) | 多 LoRA adapter、hittable relabel | 名次来源有冲突 | 未发布 |

## 推荐学习顺序

先读 01 理解完整获胜系统，再读 02 学路由与消融；03 说明复杂技术为何不一定适合限时系统；04、05 建立 verification/abstention；最后读 08 与 06 看 adapter/agent 分工，07 作为文本、表格、KG 和数值推理的综合案例。

## Senior Engineer 复现检查

1. 固定 query time、数据快照、模型、prompt、router 与 evaluator 版本。
2. 分层记录 retrieval hit、entity/time parsing、API execution、evidence sufficiency 与 final answer。
3. 同时报 accuracy、hallucination、missing、score 与 p95 latency。
4. 任何名次/分数先看 [各论文 source manifest](./01-Winning-Solution/resources/source-manifest.md)，不要把类别冠军写成任务总冠军。

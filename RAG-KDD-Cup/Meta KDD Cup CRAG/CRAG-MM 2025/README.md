# Meta KDD Cup 2025 CRAG-MM

## 从文本 RAG 到多模态、多轮

CRAG-MM 面向视觉问答与可穿戴设备：Task 1 从 image-indexed KG 回答单轮问题，Task 2 再加入网页多源证据，Task 3 处理 2–6 轮视觉对话。系统不仅要“搜到文本”，还要完成视觉 grounding、实体链接、OCR、query rewriting、跨模态重排和拒答，并满足严格时限。

- [官方 benchmark/challenge 页面](https://kddcup25.github.io/index.html)
- [AIcrowd 比赛页](https://www.aicrowd.com/challenges/meta-crag-mm-challenge-2025)
- [OpenReview 16 篇 workshop submissions](https://openreview.net/submissions?venue=KDD.org%2F2025%2FWorkshop%2FCRAG-MM_KDD_Cup)
- [AIcrowd 获奖公告](https://discourse.aicrowd.com/t/meta-crag-challenge-2025-winners-announcement/17308)

## 两篇获奖方案

| 论文 | 核心方法 | 名次口径 | 可复现性 |
|---|---|---|---|
| [Winning Task 2 - Team NVIDIA](./09-Winning-Task-2/README.md) | 单一多任务 VLM；26.5k 合成 datamix；RAGAS judge；拒答阈值 | Task 2 human-eval 第一，0.233 | [PDF](./09-Winning-Task-2/papers/18_Winning_Meta_KDD_Cup_25_Tas.pdf)；[GitHub clone](./09-Winning-Task-2/code/crag-mm/)；HF 数据/模型外链 |
| [DB3 Team Solution](./10-DB3-Solution/README.md) | task-specific retrieval；Grounding DINO/图像重排；SFT/DPO/GRPO；checkpoint ensemble | Task 1/2 第二、Task 3 第一、ego-centric 大奖 | PDF 已归档；官方 GitLab 当前 503 |

## 对比要点

NVIDIA 将多个子任务蒸馏到一个 VLM，并用贴近人工判断的 proxy metric 选模型，架构更集中；db3 把 retrieval 按任务/模态拆开，训练侧用偏好学习和 RL 控制回答意愿，架构更模块化。前者风险是 synthetic/judge bias，后者风险是组件级联、ensemble 延迟和离线过拟合。

## 金融多模态启示

财报截图、图表和票据必须先定位目标区域与主体/期间，再回到原始披露检索；视觉相似不能作为事实相同的充分条件。多轮问题要维护 entity/time state。拒答阈值要按金额、主体、时效和证据质量分层，并用人工标注的高风险错误集校准。

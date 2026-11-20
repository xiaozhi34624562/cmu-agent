# Search 2: Tree Search

- 课程：CMU 11-768；官方条目标识 CMU-13a。
- 官网日期：2026-11-17；讲者：JY Koh；稳定本地目录 `21.TreeSearch`。
- 官网题目：**Search 2: Tree Search**；PDF 封面：**Search and Planning**。
- 材料同步日期：2026-11-20（Asia/Shanghai）。
- [官方课表](https://www.cmu-agents.com/#/schedule) · [本轮原始课表](../../syllabus-snapshots/2026-11-20/cmu/schedule.json) · [完整课表](../COURSE_SCHEDULE.md)。

## 主讲义与讲解状态

- [Search and Planning · 100 页](2026-11-17-jy-koh.pdf)；原文件名和原始字节保留。
- Source: https://www.cmu-agents.com/slides/2026-11-17-jy-koh.pdf
- SHA-256：`ae36ec248377b87ceee1ff34be11f8a20d31b705f4acf70994cec6127a2bc5e6`。完整取得时间、页数与版本见 [MATERIALS.json](MATERIALS.json)。
- [完整中文讲解](notes.zh-CN.md)沿主讲义五段问题链展开，结合 6 项指定阅读和 20 项官方参考的相关正文，并标注论文实验范围。复读和来源核查范围见课程 [REVIEW.json](../REVIEW.json)。
- [教学算例](examples/search_primitives.py) · [运行输出](examples/RESULTS.json)。固定输入验证 24 点算式、PUCT 一步选择与回传、行程硬约束和关键路径算术。

## 指定 Readings

| 原文完整标题 | 本地全文 | 实际版本 / 页数 | 来源方式 | 官方入口 |
|---|---|---|---|---|
| Tree of Thoughts: Deliberate Problem Solving with Large Language Models | [PDF](readings/Tree_of_Thoughts_Deliberate_Problem_Solving_with_Large_Language_Models.pdf) | 2305.10601v2 / 14 | 本轮下载 | https://arxiv.org/abs/2305.10601 |
| Stream of Search (SoS): Learning to Search in Language | [PDF](readings/Stream_of_Search_SoS_Learning_to_Search_in_Language.pdf) | 2404.03683v1 / 16 | 本轮下载 | https://arxiv.org/abs/2404.03683 |
| Tree Search for Language Model Agents | [PDF](readings/Tree_Search_for_Language_Model_Agents.pdf) | 2407.01476v4 / 25 | 复用旧归档 | https://arxiv.org/abs/2407.01476 |
| Is Your LLM Secretly a World Model of the Internet? Model-Based Planning for Web Agents | [PDF](readings/Is_Your_LLM_Secretly_a_World_Model_of_the_Internet_Model-Based_Planning_for_Web_Agents.pdf) | 2411.06559v2 / 22 | 本轮下载 | https://arxiv.org/abs/2411.06559 |
| Recursive Language Models | [PDF](readings/Recursive_Language_Models.pdf) | 2512.24601v3 / 43 | 复用旧归档 | https://arxiv.org/abs/2512.24601 |
| Multi-Agent Computer Use | [PDF](readings/Multi-Agent_Computer_Use.pdf) | 2606.01533v1 / 42 | 复用旧归档 | https://arxiv.org/abs/2606.01533 |

## 官方 References

| 原文完整标题 | 本地全文 | 实际版本 / 页数 | 来源方式 | 官方入口 |
|---|---|---|---|---|
| Thinking Fast and Slow with Deep Learning and Tree Search | [PDF](references/Thinking_Fast_and_Slow_with_Deep_Learning_and_Tree_Search.pdf) | 1705.08439v4 / 19 | 本轮下载 | https://arxiv.org/abs/1705.08439 |
| Mastering the Game of Go without Human Knowledge | [PDF](references/Mastering_the_Game_of_Go_without_Human_Knowledge.pdf) | Author accepted manuscript, UCL Discovery 10045895; 42-page unformatted edition / 42 | 本轮下载 | https://www.nature.com/articles/nature24270 |
| A General Reinforcement Learning Algorithm That Masters Chess, Shogi, and Go through Self-Play | [PDF](references/A_General_Reinforcement_Learning_Algorithm_That_Masters_Chess_Shogi_and_Go_through_Self-Play.pdf) | Author accepted manuscript, UCL Discovery 10069050; 32-page accepted edition / 32 | 本轮下载 | https://doi.org/10.1126/science.aar6404 |
| ReST-MCTS*: LLM Self-Training via Process Reward Guided Tree Search | [PDF](references/ReST-MCTS_LLM_Self-Training_via_Process_Reward_Guided_Tree_Search.pdf) | 2406.03816v3 / 38 | 本轮下载 | https://arxiv.org/abs/2406.03816 |
| Graph of Thoughts: Solving Elaborate Problems with Large Language Models | [PDF](references/Graph_of_Thoughts_Solving_Elaborate_Problems_with_Large_Language_Models.pdf) | 2308.09687v4 / 63 | 本轮下载 | https://arxiv.org/abs/2308.09687 |
| Beyond A*: Better Planning with Transformers via Search Dynamics Bootstrapping | [PDF](references/Beyond_A_Better_Planning_with_Transformers_via_Search_Dynamics_Bootstrapping.pdf) | 2402.14083v2 / 21 | 本轮下载 | https://arxiv.org/abs/2402.14083 |
| DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning | [PDF](references/DeepSeek-R1_Incentivizing_Reasoning_Capability_in_LLMs_via_Reinforcement_Learning.pdf) | 2501.12948v1 / 22 | 本轮下载 | https://arxiv.org/html/2501.12948v1#S4.SS2 |
| Language Agent Tree Search Unifies Reasoning, Acting, and Planning in Language Models | [PDF](references/Language_Agent_Tree_Search_Unifies_Reasoning_Acting_and_Planning_in_Language_Models.pdf) | 2310.04406v3 / 23 | 本轮下载 | https://arxiv.org/abs/2310.04406 |
| DeepSeek-Prover-V1.5: Harnessing Proof Assistant Feedback for Reinforcement Learning and Monte-Carlo Tree Search | [PDF](references/DeepSeek-Prover-V1.5_Harnessing_Proof_Assistant_Feedback_for_Reinforcement_Learning_and_Monte-Carlo_Tree_Search.pdf) | 2408.08152v1 / 28 | 本轮下载 | https://arxiv.org/abs/2408.08152 |
| Mastering Atari, Go, Chess and Shogi by Planning with a Learned Model | [PDF](references/Mastering_Atari_Go_Chess_and_Shogi_by_Planning_with_a_Learned_Model.pdf) | 1911.08265v2 / 21 | 本轮下载 | https://www.nature.com/articles/s41586-020-03051-4 |
| Reasoning with Language Model is Planning with World Model | [PDF](references/Reasoning_with_Language_Model_is_Planning_with_World_Model.pdf) | EMNLP 2023 proceedings, pages 8154-8173 / 20 | 本轮下载 | https://aclanthology.org/2023.emnlp-main.507/ |
| CWM: An Open-Weights LLM for Research on Code Generation with World Models | [PDF](references/CWM_An_Open-Weights_LLM_for_Research_on_Code_Generation_with_World_Models.pdf) | 2510.02387v1 / 58 | 本轮下载 | https://arxiv.org/abs/2510.02387 |
| WorldCoder, a Model-Based LLM Agent: Building World Models by Writing Code and Interacting with the Environment | [PDF](references/WorldCoder_a_Model-Based_LLM_Agent_Building_World_Models_by_Writing_Code_and_Interacting_with_the_Environment.pdf) | 2402.12275v3 / 65 | 本轮下载 | https://arxiv.org/abs/2402.12275 |
| Generating Code World Models with Large Language Models Guided by Monte Carlo Tree Search | [PDF](references/Generating_Code_World_Models_with_Large_Language_Models_Guided_by_Monte_Carlo_Tree_Search.pdf) | 2405.15383v2 / 40 | 复用旧归档 | https://arxiv.org/abs/2405.15383 |
| Recursive Agent Optimization | [PDF](references/Recursive_Agent_Optimization.pdf) | 2605.06639v1 / 27 | 复用旧归档 | https://arxiv.org/abs/2605.06639 |
| ADaPT: As-Needed Decomposition and Planning with Language Models | [PDF](references/ADaPT_As-Needed_Decomposition_and_Planning_with_Language_Models.pdf) | Findings of NAACL 2024, pages 4226-4252 / 27 | 本轮下载 | https://aclanthology.org/2024.findings-naacl.264/ |
| HuggingGPT: Solving AI Tasks with ChatGPT and its Friends in Hugging Face | [PDF](references/HuggingGPT_Solving_AI_Tasks_with_ChatGPT_and_its_Friends_in_Hugging_Face.pdf) | NeurIPS 2023 proceedings / 27 | 本轮下载 | https://proceedings.neurips.cc/paper_files/paper/2023/hash/77c33e6a367922d003ff102ffb92b658-Abstract-Conference.html |
| An LLM Compiler for Parallel Function Calling | [PDF](references/An_LLM_Compiler_for_Parallel_Function_Calling.pdf) | PMLR 235, ICML 2024 proceedings, pages 24370-24391 / 22 | 本轮下载 | https://proceedings.mlr.press/v235/kim24y.html |
| Effective Strategies for Asynchronous Software Engineering Agents | [PDF](references/Effective_Strategies_for_Asynchronous_Software_Engineering_Agents.pdf) | 2603.21489v2 / 22 | 复用旧归档 | https://arxiv.org/abs/2603.21489 |
| Discriminative World Models for Web Agents | [PDF](references/Discriminative_World_Models_for_Web_Agents.pdf) | 2609.02885v1 / 16 | 本轮下载 | https://arxiv.org/abs/2609.02885 |

## 讲义内嵌链接的核对入口

- [Recursive Agent Optimization v2，Tables 1–3、§4](https://arxiv.org/html/2605.06639v2) 对应讲义 pp.61–64、93。归档 PDF 保留 v1，讲解中的表格数字按 v2 作者原文核对。
- [ToT 的 24 点评价解析代码](https://raw.githubusercontent.com/princeton-nlp/tree-of-thought-llm/master/src/tot/tasks/game24.py) 对应讲义 pp.83–84，核对末行匹配与评分权重。[GoT 的排序评分代码](https://raw.githubusercontent.com/spcl/graph-of-thoughts/main/examples/sorting/utils.py) 对应 p.86，核对 0 至 9 的计数差与相邻逆序。代码入口为作者仓库分支，讲解按讲义展示与本次读取的内容核对。
- [Recurrent World Models Facilitate Policy Evolution](https://papers.neurips.cc/paper_files/paper/2018/hash/2de5d16682c3c35007e4e92982f1a2ba-Abstract.html) 与 [DoomRNN 作者演示](https://worldmodels.github.io/doomrnn/) 对应讲义 p.45，用于历史背景。

## 获取、版本与验证边界

- 共 26 项阅读/参考正文均已保存；6 项复用既有归档，20 项本轮下载。逐项原路径、原文件名、实际版本、页数、取得/复用时间和 SHA-256 见 [REFERENCES.json](REFERENCES.json)。复用不冒充新下载，也不声称是当前最新版本。
- 官网简称与实际论文题名分别保留。未固定版本的 arXiv 链接按实际保存版本标识；来源替代及失败尝试保留在逐项记录。
- 归档时核验文件头、页数、首面题名与版本，讲解复核时另查正文中的机制、公式和相关结果。实验执行限于本课教学算例。
- AlphaGo Zero/AlphaZero 取得 UCL 作者接受稿；MuZero 取得 arXiv 版本。它们对应官网论文，但不冒称与出版排版逐字节相同。
- DeepSeek-R1 特按官方 `v1#S4.SS2` 取回 22 页原版；没有用既有 86 页 v2 替代。

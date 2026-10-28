# CMU 11-768：AI Agents 中文学习资料

以原讲义为主线，阅读材料补机制与实验，一手参考补背景和实现。各课讲解区分来源结论、教学推导与工程建议。

| 课次 | 原讲义与来源 | 中文讲解 |
|---|---|---|
| 1 | [1. Course Overview: What Is an Agent?](1.WhatIsAnAgent/SOURCES.md) | [课程讲解](1.WhatIsAnAgent/notes.zh-CN.md) |
| 2 | [2. Agent Capabilities 1: Tool Use](2.ToolUse/SOURCES.md) | [课程讲解](2.ToolUse/lecture-02-tool-use-complete-notes.zh-CN.md) |
| 3 | [3. Agent Capabilities 2: Context Management for Long-Context Agents](3.LongContext/SOURCES.md) | [课程讲解](3.LongContext/long_context_lecture03_integrated_notes.md) |
| 4 | [4. Agent Capabilities 3: Skills and Memory](4.SkillsAndMemory/SOURCES.md) | [课程讲解](4.SkillsAndMemory/Skills_and_Memory_Integrated_Notes.md) |
| 5 | [5. Agent Capabilities 4: Planning, Task Decomposition, and Multi-Agent Coordination](5.PlanningAndCoordination/SOURCES.md) | [课程讲解](5.PlanningAndCoordination/lecture05_planning_coordination_integrated_notes.md) |
| 6 | [6. Domains 1: Coding Agents](6.CodingAgents/SOURCES.md) | [课程讲解](6.CodingAgents/coding_agent_lecture06_integrated_notes.md) |
| 7 | [7. Computer Use Agents](7.ComputerUseAgents/SOURCES.md) | [课程讲解](7.ComputerUseAgents/lecture-07-computer-use-agents-notes.md) |
| 8 | [8. Training 1: Supervised Fine-Tuning (SFT)](8.SupervisedFineTuning/SOURCES.md) | [课程讲解](8.SupervisedFineTuning/SFT_Lecture08_Integrated_Notes.md) |
| 9 | [9. Training 2: Reinforcement Learning Basics](9.TrainingRLBasics/SOURCES.md) | [课程讲解](9.TrainingRLBasics/rl_lecture09_integrated_notes.md) |
| 10 | [10. Domains 3: Deep Research Agents](10.DeepResearchAgents/SOURCES.md) | [课程讲解](10.DeepResearchAgents/Deep_Research_Lecture10_Integrated_Notes.md) |
| 11 | [11. Training 3: Advanced RL Algorithms](11.AdvancedRLAlgorithms/SOURCES.md) | [课程讲解](11.AdvancedRLAlgorithms/lecture-11-advanced-rl-integrated.md) |
| 12 | [12. Training 4: RL Systems](12.TrainingRLSystems/SOURCES.md) | [课程讲解](12.TrainingRLSystems/notes.zh-CN.md) |
| 13 | [13. Safety 1: Agent Safety](13.AgentSafety/SOURCES.md) | [课程讲解](13.AgentSafety/lecture-13-agent-safety-study-guide.md) |
| 14 | [14. Frameworks 1: OpenHands](14.OpenHands/SOURCES.md) | [课程讲解](14.OpenHands/Lecture14_OpenHands_Integrated_Notes.md) |
| 15 | [15. Frameworks 2: Orchestration and Monitoring](15.OrchestrationAndMonitoring/SOURCES.md) | [课程讲解](15.OrchestrationAndMonitoring/lecture-15-orchestration-and-monitoring-complete-guide.md) |
| 16 | [16. Agents and the Future of Work](16.AgentsAndTheFutureOfWork/SOURCES.md) | [课程讲解](16.AgentsAndTheFutureOfWork/notes.zh-CN.md) |

第 10 课还保留[通用设计](10.DeepResearchAgents/Deep_Research_Agent_General_Design.md)、[来源核对](10.DeepResearchAgents/Deep_Research_Agent_Design_Source_Checks.md)与[金融 Agent 三篇论文研究](10.DeepResearchAgents/Finance_Agent_Research_2026_Three_Papers.md)。这些是专题补充，不是新增课次。

第 16 课对应官网 **2026-10-27** 的 Zora Wang 嘉宾课，讲义封面为 *AI Agents for Human Work*，保留原文件名；16 是本地资料目录序号。官网 10 月 22 日的 *Safety 2: Observability and Monitoring* 仍未提供材料，没有据此虚构一份讲义。最新同步范围和待获取事项见[来源总入口](SOURCES.md)。

## 作业资料

| 作业 | 原始说明与代码 | 本地归档状态 |
|---|---|---|
| 1 · Agent Harness | [官方 README](assignment/assignment-1/README.md) · [作业说明](assignment/assignment-1/ASSIGNMENT.md) | 保留既有归档 |
| 2 · 数据可视化 Agent 评测 | [官方 README](assignment/assignment-2/README.md) · [作业说明](assignment/assignment-2/ASSIGNMENT.md) | 保留既有归档 |
| 3 · 强化学习训练 | [来源和阅读入口](assignment/assignment-3/SOURCES.md) · [官方作业说明](assignment/assignment-3/ASSIGNMENT.md) | 2026-10-28 收录固定提交 `88d1b1f` 的 59 个原始文件；包含待实现函数，未进行训练 |

## 阅读与维护

先读中文讲解的导读与资料映射，再按实际 PDF 页序回读原讲义；自测先自行作答，再对照答案。性能数字应连同基线、数据、模型、预算与局限阅读。

逐篇内容复核、修订与复读记录见 [REVIEW.json](REVIEW.json)，自动检查结果见 [VERIFICATION.json](VERIFICATION.json)。记录绑定文件 SHA-256，仅说明相应版本与核查范围，不代替模型实验复现。

新增公开材料后，同步维护本课 SOURCES.md、讲解、REFERENCES.json 与本页；原文件名和原始二进制内容保留。后续检查可运行 `python3 tools/verify_course_notes.py`（在仓库根目录执行）。

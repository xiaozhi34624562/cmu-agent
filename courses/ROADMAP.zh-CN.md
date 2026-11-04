# 四门课程学习 Roadmap：按步骤打开每一讲

**从第 01 步开始，按表格向下学。** 左侧“步骤”是你的学习顺序；课程后的数字是本地目录号，MIT 使用官网 Week。原始 Lecture 编号以打开的讲义为准。括号里的日期是官方授课日期，不是你的自学截止日期。

第一段路线：[Stanford 01 中文讲解](329z/1.IntroductionWhatAreAgenticSystems/notes.zh-CN.md) → [Stanford 02 中文讲解](329z/2.LLMsForBuilders/notes.zh-CN.md) → [CMU 01 中文讲解](11-768/1.WhatIsAnAgent/notes.zh-CN.md)。随后继续阶段 0 的后三讲，再进入阶段 1 的编码作业。

这份安排面向你的 Java 后端、银行报送、Flink/Paimon/StarRocks 与基金公司 LLM 开发背景：先建立可测量的 Agent，再深入数据/评测、生产可靠性、自动优化、推理服务与模型训练。目标是能够独立负责生产 AI 系统的 Senior AI Engineer。

## 怎么用这张表

1. **一行对应一讲或一份作业。** 先沿“主讲义”确定本讲的问题，再配合“中文讲解”逐段学习；“全部资料”包含指定 readings、references、嘉宾和其他学习材料，按讲义主线穿插阅读。四门课的所有内容均保留。
2. **遇到作业行就做作业。** 按正式原题完成必做要求，不等四门课全部看完才开始；同一时间只推进一项主要编码作业。
3. **遇到“回访”只补本行明确的章节/目标。** 本讲所有部分、指定阅读与相应练习完成后，才标记整讲完成；不是把同一讲重新从头看一遍。
4. **遇到“待讲义/待题目”保留待回访状态，继续下一条前置已满足的任务。** 材料状态于 2026-11-04 核对官网并同步新增正文；历史版本与获取限制保留在来源索引。未来课次的学习重点是规划，发布后按正文修订。

你当前的掌握程度和每周投入时间尚未测量，所以这里给出明确顺序和验收，不编造完成日期或已学进度。

## 总导航

| 学习阶段 | 对应步骤 | 这一段的主要行动 |
|---|---|---|
| [阶段 0：先把 Agent、模型与系统的关系讲清楚](#p0) | 01–06 | 逐讲学习并完成本阶段验收 |
| [阶段 1：从会用 Agent 到亲手写出完整循环](#p1) | 07–20 | Harvard HW1 · Mads-Lens → Stanford HW1 · Agentic Harness |
| [阶段 2：扩展到协作、Coding、Computer Use 和 Deep Research](#p2) | 21–34 | CMU HW1 · Harness → Harvard HW2 · Mads-Loop |
| [阶段 3：建立可信的数据与评测](#p3) | 35–44 | CMU HW2 · Eval → Stanford HW2 · Evaluate an Agent |
| [阶段 4：让系统能恢复、受约束，并适合真实用户](#p4) | 45–53 | 逐讲学习并完成本阶段验收 |
| [阶段 5：在可靠评测之上优化搜索、上下文和 Harness](#p5) | 54–67 | Harvard HW3 · Mads-Opt → MIT Context Evolution · 计划作业 → MIT Harness Evolution · 计划作业 |
| [阶段 6：补齐推理服务与全栈性能能力](#p6) | 68–80 | Harvard HW4 · Mads-Serve → Harvard HW5 · Mads-Stack |
| [阶段 7：学习 SFT、RL 和模型演化](#p7) | 81–90 | CMU HW3 · Training → MIT Model Evolution · 计划作业 |
| [阶段 8：学习环境演化与前沿，并完成项目](#p8) | 91–95 | MIT Task Evolution · 计划作业 |

[项目与非编码任务](#projects) · [待定嘉宾与历史占位](#pending) · [作业怎么做](#homework-method) · [完整日历反查学习步骤](SYLLABUS-COVERAGE.zh-CN.md)

<a id="p0"></a>

## 阶段 0：先把 Agent、模型与系统的关系讲清楚

用你已有的 LLM 开发经验建立共同语言，同时补上模型计算直觉；这一步结束后就进入编码。

| 步骤 | 具体课次 / 作业 | 直接打开 | 本次学习或实现目标 |
|---|---|---|---|
| <a id="step-01"></a>01 | Stanford 01 · Introduction：Agentic Systems | [中文讲解](329z/1.IntroductionWhatAreAgenticSystems/notes.zh-CN.md) · [主讲义](329z/1.IntroductionWhatAreAgenticSystems/slides/lecture01.pdf) · [全部资料](329z/1.IntroductionWhatAreAgenticSystems/SOURCES.md) | 区分模型、工作流与 Agent，明确谁维护状态、谁决定下一步。 |
| <a id="step-02"></a>02 | Stanford 02 · LLMs for Builders | [中文讲解](329z/2.LLMsForBuilders/notes.zh-CN.md) · [主讲义](329z/2.LLMsForBuilders/slides/lecture02.pdf) · [全部资料](329z/2.LLMsForBuilders/SOURCES.md) | 把 token、生成、采样、工具输出与模型能力边界接起来。 |
| <a id="step-03"></a>03 | CMU 01 · What Is an Agent? | [中文讲解](11-768/1.WhatIsAnAgent/notes.zh-CN.md) · [主讲义](11-768/1.WhatIsAnAgent/lecture-01-agents.pdf) · [全部资料](11-768/1.WhatIsAnAgent/SOURCES.md) | 用 ReAct、Toolformer 和最小 coding agent 对照执行、工具训练与评测。 |
| <a id="step-04"></a>04 | Harvard 01 · Course Overview | [中文讲解](2680/1.CourseOverviewAndLogistics/notes.zh-CN.md) · [主讲义](2680/1.CourseOverviewAndLogistics/1_intro.pdf) · [全部资料](2680/1.CourseOverviewAndLogistics/SOURCES.md) | 建立 Agent—模型—硬件的层次图，区分任务正确性、可靠性和系统成本。 |
| <a id="step-05"></a>05 | Harvard 10 · Intro to LLMs（后续 [第 68 步](#step-68)） | [中文讲解](2680/10.EfficientLLMServingBasicsI.IntroToLLMs/notes.zh-CN.md) · [主讲义](2680/10.EfficientLLMServingBasicsI.IntroToLLMs/9_llm_serving_basics_1.pdf) · [全部资料](2680/10.EfficientLLMServingBasicsI.IntroToLLMs/SOURCES.md) | **本次读 §0–6**：token、Transformer、attention 和 KV 的语义；§7–17 在阶段 6 完成。 |
| <a id="step-06"></a>06 | MIT W01 · Course Introduction | [中文讲解](MAS.S62/1.CourseIntroduction/notes.zh-CN.md) · [主讲义](<MAS.S62/1.CourseIntroduction/slides/lec1 - intro.pdf>) · [全部资料](MAS.S62/1.CourseIntroduction/SOURCES.md) | 完整读导论，区分 Context/Harness/Model/Environment 四种优化对象与反馈。 |

**本阶段验收：** 画出一次 LLM 请求和一个 Agent 循环的数据流；用小练习检查 Python、张量、条件概率与梯度的基础。

**项目节点：** 确定投研证据助手的一个小任务：例如少量公司公告的变化摘要与引用核查。先写用户、输入、成功条件与简单基线。

<a id="p1"></a>

## 阶段 1：从会用 Agent 到亲手写出完整循环

先用 Harvard HW1 观察现成 Agent，再按组件逐讲学习，最后完成不依赖框架的 Stanford HW1。

| 步骤 | 具体课次 / 作业 | 直接打开 | 本次学习或实现目标 |
|---|---|---|---|
| <a id="step-07"></a>07 | Harvard 02 · How Claude Code Works | [中文讲解](2680/2.AgentsUseI.HowClaudeCodeWorks/lecture_02_agent_use_integrated_notes.md) · [主讲义](2680/2.AgentsUseI.HowClaudeCodeWorks/2_agent_use_1.pdf) · [工程补充](2680/2.AgentsUseI.HowClaudeCodeWorks/coding_agent_integrated_guide.md) · [全部资料](2680/2.AgentsUseI.HowClaudeCodeWorks/SOURCES.md) | 解释 Claude Code 的工具、上下文与执行循环；工程补充也在本行链接中。 |
| <a id="step-08"></a>08 | **Harvard HW1 · Mads-Lens** | [原题](2680/site/assignments/assignment1.html) · [作业入口](2680/assignment/assignment-1/SOURCES.md) | 学完上面的 Claude Code 一讲就开始：完成原题的观测界面、轨迹与回放要求；保留一次失败轨迹。 |
| <a id="step-09"></a>09 | Harvard 21 · Student Sharing I：HW1 复盘 | [全部资料](2680/21.StudentSharingI/SOURCES.md) · **待讲义/分享材料** | 在 HW1 后复盘轨迹、交互与失败。官方分享材料待取得；个人复盘不算完成官方分享。 |
| <a id="step-10"></a>10 | Stanford 03 · RAG | [中文讲解](329z/3.RetrievalAugmentedGenerationRAG/notes.zh-CN.md) · [主讲义](329z/3.RetrievalAugmentedGenerationRAG/slides/lecture03.pdf) · [全部资料](329z/3.RetrievalAugmentedGenerationRAG/SOURCES.md) | 把检索、证据组织与生成分开，理解 RAG 为什么仍会出错。 |
| <a id="step-11"></a>11 | Stanford 04 · Tool Use & Function Calling | [中文讲解](329z/4.ToolUseFunctionCalling/notes.zh-CN.md) · [主讲义](329z/4.ToolUseFunctionCalling/slides/lecture04.pdf) · [全部资料](329z/4.ToolUseFunctionCalling/SOURCES.md) | 设计工具 schema、执行结果与错误契约，区分模型生成调用和真实执行。 |
| <a id="step-12"></a>12 | CMU 02 · Tool Use | [中文讲解](11-768/2.ToolUse/lecture-02-tool-use-complete-notes.zh-CN.md) · [主讲义](11-768/2.ToolUse/lecture-02-tool-use.pdf) · [全部资料](11-768/2.ToolUse/SOURCES.md) | 深化工具学习、接口与评测；对照 Stanford 工具课解释机制差异。 |
| <a id="step-13"></a>13 | Harvard 04 · Context Management & Tool Design | [中文讲解](2680/4.AgentsDesignI.ContextManagementAndToolDesign/lecture-04_context_and_tool_design_integrated.md) · [主讲义](2680/4.AgentsDesignI.ContextManagementAndToolDesign/4_agent_design_1.pdf) · [全部资料](2680/4.AgentsDesignI.ContextManagementAndToolDesign/SOURCES.md) | 把上下文预算、工具反馈和任务结构落实为 harness 设计。 |
| <a id="step-14"></a>14 | CMU 03 · Long Context | [中文讲解](11-768/3.LongContext/long_context_lecture03_integrated_notes.md) · [主讲义](11-768/3.LongContext/lecture-03-long-context.pdf) · [全部资料](11-768/3.LongContext/SOURCES.md) | 解释长上下文能力、成本与失败；区分窗口容量和有效信息利用。 |
| <a id="step-15"></a>15 | CMU 04 · Skills & Memory | [中文讲解](11-768/4.SkillsAndMemory/Skills_and_Memory_Integrated_Notes.md) · [主讲义](11-768/4.SkillsAndMemory/lecture-04-memory-and-skills.pdf) · [全部资料](11-768/4.SkillsAndMemory/SOURCES.md) | 区分技能、检索记忆、工作上下文和更新策略。 |
| <a id="step-16"></a>16 | Stanford 05 · Frameworks & Orchestration（后续 [第 46 步](#step-46)） | [讲解定位](329z/5.FrameworksOrchestration/notes.zh-CN.md#1-先拆清楚数据系统和评测共同决定表现) · [主讲义](329z/5.FrameworksOrchestration/slides/lecture05.pdf) · [全部资料](329z/5.FrameworksOrchestration/SOURCES.md) | **本次读 §1–7**：DSPy 抽象、模块与显式状态图；§8–13 留到阶段 4 的故障恢复实践。 |
| <a id="step-17"></a>17 | Stanford 06 · Agent Design Patterns & Scaffolds | [中文讲解](329z/6.AgentDesignPatternsScaffolds/notes.zh-CN.md) · [主讲义](329z/6.AgentDesignPatternsScaffolds/slides/lecture06.pdf) · [全部资料](329z/6.AgentDesignPatternsScaffolds/SOURCES.md) | 把循环、路由、反思等模式落实为可终止、可取消、受预算约束的控制流。 |
| <a id="step-18"></a>18 | Stanford 07 · Agent Memory Architectures | [中文讲解](329z/7.AgentMemoryArchitectures/notes.zh-CN.md) · [主讲义](329z/7.AgentMemoryArchitectures/slides/lecture07.pdf) · [全部资料](329z/7.AgentMemoryArchitectures/SOURCES.md) | 设计记忆写入、读取、修订与删除；说明记忆和流程状态的区别。 |
| <a id="step-19"></a>19 | Harvard 06 · Agent Memory & Reliability | [中文讲解](2680/6.AgentsDesignIII.AgentMemoryAndReliability/lecture06_agent_memory_reliability.md) · [主讲义](2680/6.AgentsDesignIII.AgentMemoryAndReliability/6_agent_design_3.pdf) · [全部资料](2680/6.AgentsDesignIII.AgentMemoryAndReliability/SOURCES.md) | 把失败类型、记忆策略和可靠性实验连起来。 |
| <a id="step-20"></a>20 | **Stanford HW1 · Agentic Harness** | [原题 PDF](329z/assignment/assignment-1/upstream/cs329z_assignment1_harness.pdf) · [starter / 契约](329z/assignment/assignment-1/SOURCES.md) | 完成全部必做题；按原题不用 Agent 框架，实现邮件/RAG 组件、工具循环、压缩、记忆及审批，再完成规定评测与说明。随后做 [10 分钟闭卷验收](#stanford-quizzes)，解释本人实现的设计与取舍。 |

**本阶段验收：** 完成 HW1 的原题要求，能脱离框架解释工具协议、状态、终止、压缩、记忆和人工批准；从第一天保存 trace 与固定小测试集。

**项目节点：** 完成 [Stanford 项目 proposal](#project-stanford)：把投研任务收窄为可交付、可评测的原型。

<a id="p2"></a>

## 阶段 2：扩展到协作、Coding、Computer Use 和 Deep Research

先学分工和任务环境，再完成两份 harness 作业，最后检验同一套设计如何迁移到其他 Agent。

| 步骤 | 具体课次 / 作业 | 直接打开 | 本次学习或实现目标 |
|---|---|---|---|
| <a id="step-21"></a>21 | CMU 05 · Planning & Coordination | [中文讲解](11-768/5.PlanningAndCoordination/lecture05_planning_coordination_integrated_notes.md) · [主讲义](11-768/5.PlanningAndCoordination/lecture-05-planning.pdf) · [全部资料](11-768/5.PlanningAndCoordination/SOURCES.md) | 从任务分解、规划和信息协调出发，判断何时需要多 Agent。 |
| <a id="step-22"></a>22 | Stanford 08 · Multi-Agent Systems | [中文讲解](329z/8.MultiAgentSystems/notes.zh-CN.md) · [主讲义](329z/8.MultiAgentSystems/slides/lecture08.pdf) · [全部资料](329z/8.MultiAgentSystems/SOURCES.md) | 比较 handoff、agent-as-tool 与协作结构，写清共享状态和成本。 |
| <a id="step-23"></a>23 | Harvard 03 · 100x Engineer with Multi-agents | [中文讲解](2680/3.AgentsUseII.100xEngineerWithMultiAgents/Lecture03_MultiAgent_完整学习讲义.md) · [主讲义](2680/3.AgentsUseII.100xEngineerWithMultiAgents/3_agent_use_2.pdf) · [全部资料](2680/3.AgentsUseII.100xEngineerWithMultiAgents/SOURCES.md) | 从使用者角度观察多 Agent 开发工作流和协调开销。 |
| <a id="step-24"></a>24 | Harvard 05 · Multi-agent Architecture & Communication | [中文讲解](2680/5.AgentsDesignII.MultiAgentArchitectureCoordinationAndCommunication/lecture-05_multi-agent-coordination_完整学习笔记.md) · [主讲义](2680/5.AgentsDesignII.MultiAgentArchitectureCoordinationAndCommunication/5_agent_design_2.pdf) · [全部资料](2680/5.AgentsDesignII.MultiAgentArchitectureCoordinationAndCommunication/SOURCES.md) | 从实现者角度设计通信、协调与冲突处理。 |
| <a id="step-25"></a>25 | CMU 18 · Multi-Agent Interaction（10/29） | [完整中文讲解](11-768/18.MultiAgentInteraction/notes.zh-CN.md) · [44 页讲义](11-768/18.MultiAgentInteraction/lecture-18-multi-agent-systems.pdf) · [全部资料](11-768/18.MultiAgentInteraction/SOURCES.md) | 比较角色、开放委派、异步共享进展；继续学习人机交互、模拟器泛化、协作自训练与辩论监督，完成自测和确定性教学小程序。 |
| <a id="step-26"></a>26 | CMU 06 · Coding Agents | [中文讲解](11-768/6.CodingAgents/coding_agent_lecture06_integrated_notes.md) · [主讲义](11-768/6.CodingAgents/lecture-06-coding-agents.pdf) · [全部资料](11-768/6.CodingAgents/SOURCES.md) | 理解代码任务、补丁、测试、环境和失败反馈怎样组成闭环。 |
| <a id="step-27"></a>27 | CMU 14 · OpenHands | [中文讲解](11-768/14.OpenHands/Lecture14_OpenHands_Integrated_Notes.md) · [主讲义](11-768/14.OpenHands/lecture-14-openhands.pdf) · [全部资料](11-768/14.OpenHands/SOURCES.md) | 用 OpenHands 对照 agent SDK、执行环境与可复用 harness 结构。 |
| <a id="step-28"></a>28 | Stanford 10 · Terminal-Bench 嘉宾课（后续 [第 41 步](#step-41)） | [讲解定位](329z/10.GuestLectureTerminalBench/notes.zh-CN.md#1-从写规则到观察结果工程责任如何移动) · [主讲义](329z/10.GuestLectureTerminalBench/slides/lecture10.pdf) · [全部资料](329z/10.GuestLectureTerminalBench/SOURCES.md) | **本次读 §1–5**：任务、尝试、轨迹、harness 与终端环境；评分与统计放到阶段 3。 |
| <a id="step-29"></a>29 | Stanford 16 · SWE-bench 嘉宾课（后续 [第 42 步](#step-42)） | [全部资料](329z/16.GuestLectureSWEBench/SOURCES.md) · **待讲义/分享材料** | 待讲义；本阶段关注软件任务和执行环境，评分协议在阶段 3 回访，具体章节发布后再定。 |
| <a id="step-30"></a>30 | Stanford 18 · Coding & Software Agents | [全部资料](329z/18.CodingSoftwareAgents/SOURCES.md) · **待讲义/分享材料** | 待讲义；将正式 Coding / Software Agents 内容与已实现的 coding harness 对照。 |
| <a id="step-31"></a>31 | **CMU HW1 · Harness** | [原题](11-768/assignment/assignment-1/ASSIGNMENT.md) · [代码与环境](11-768/assignment/assignment-1/README.md) | 在原题的 coding/chess 环境完成 harness；比较动作、观察、上下文与停止条件，保留迁移前后差异。 |
| <a id="step-32"></a>32 | **Harvard HW2 · Mads-Loop** | [原题](2680/site/assignments/assignment2.html) · [starter](2680/assignment/assignment-2/SOURCES.md) | 完成原题的 coding loop；固定模型、任务、配置与 trace，作为后续 HW3–5 的连续基线。 |
| <a id="step-33"></a>33 | CMU 07 · Computer Use Agents | [中文讲解](11-768/7.ComputerUseAgents/lecture-07-computer-use-agents-notes.md) · [主讲义](11-768/7.ComputerUseAgents/lecture-07-computer-use-agents.pdf) · [全部资料](11-768/7.ComputerUseAgents/SOURCES.md) | 将动作/观察扩展到浏览器和桌面，分析界面变化与执行反馈。 |
| <a id="step-34"></a>34 | CMU 10 · Deep Research Agents | [中文讲解](11-768/10.DeepResearchAgents/Deep_Research_Lecture10_Integrated_Notes.md) · [主讲义](11-768/10.DeepResearchAgents/lecture-10-deep-research-agents.pdf) · [设计补充](11-768/10.DeepResearchAgents/Deep_Research_Agent_General_Design.md) · [来源辨析](11-768/10.DeepResearchAgents/Deep_Research_Agent_Design_Source_Checks.md) · [金融研究补充](11-768/10.DeepResearchAgents/Finance_Agent_Research_2026_Three_Papers.md) · [全部资料](11-768/10.DeepResearchAgents/SOURCES.md) | 先完整主讲解，再读设计、来源辨析与金融研究补充；解释研究计划、检索、证据整合和失败边界。 |

**本阶段验收：** 在原题环境完成 CMU HW1 与 Harvard HW2；能解释单 Agent/多 Agent 的比较条件，以及 harness 迁移中需要改变的部分。

**项目节点：** 把跨文档核查或研究计划接入投研原型；只有实验显示需要时才增加多 Agent。

<a id="p3"></a>

## 阶段 3：建立可信的数据与评测

你有数据工程基础，这里把关注点从数据流是否跑通推进到数据、评分和结论是否可信。

| 步骤 | 具体课次 / 作业 | 直接打开 | 本次学习或实现目标 |
|---|---|---|---|
| <a id="step-35"></a>35 | Stanford 11 · What Data Do Agents Need? | [中文讲解](329z/11.WhatDataDoAgentsNeed/notes.zh-CN.md) · [主讲义](329z/11.WhatDataDoAgentsNeed/slides/lecture11.pdf) · [全部资料](329z/11.WhatDataDoAgentsNeed/SOURCES.md) | 区分执行、训练、评测数据，检查来源、拆分、泄漏和合成反馈。 |
| <a id="step-36"></a>36 | Stanford 12 · Data Selection & Quality | [全部资料](329z/12.DataSelectionQuality/SOURCES.md) · **待讲义/分享材料** | 待讲义；正式数据选择与质量课补到这里，已有数据实践可继续。 |
| <a id="step-37"></a>37 | Harvard 07 · Agent Evaluation | [中文讲解](2680/7.AgentDesignIV.AgentEvaluation/Agent_Eval_Lecture07_Integrated_Notes.md) · [主讲义](2680/7.AgentDesignIV.AgentEvaluation/7_agent_design_4.pdf) · [全部资料](2680/7.AgentDesignIV.AgentEvaluation/SOURCES.md) | 定义任务成功、评测单位与协议，检查可靠性指标的含义。 |
| <a id="step-38"></a>38 | **CMU HW2 · Eval** | [原题](11-768/assignment/assignment-2/ASSIGNMENT.md) · [代码与环境](11-768/assignment/assignment-2/README.md) | 完成可视化 Agent 评分与任务/环境要求；用失败案例检验评分器是否测到了原题目标。 |
| <a id="step-39"></a>39 | Stanford 13 · Evaluation & Benchmark Design | [全部资料](329z/13.EvaluationFundamentalsBenchmarkDesign/SOURCES.md) · **待讲义/分享材料** | 待讲义；核对任务采样、benchmark 设计和结果解释。 |
| <a id="step-40"></a>40 | Stanford 15 · LLM-as-Judge & Evaluation Infrastructure | [全部资料](329z/15.LLMAsJudgeEvaluationInfrastructure/SOURCES.md) · **待讲义/分享材料** | 待讲义；重点检查 Judge 校准、误差分析和评测基础设施的实际要求。 |
| <a id="step-41"></a>41 | Stanford 10 · Terminal-Bench 嘉宾课 **（回访）** | [讲解定位](329z/10.GuestLectureTerminalBench/notes.zh-CN.md#6-verifier-的权威来自隔离和有效性不能来自名字) · [主讲义](329z/10.GuestLectureTerminalBench/slides/lecture10.pdf) · [全部资料](329z/10.GuestLectureTerminalBench/SOURCES.md) | **回访 §6–14**：Verifier、作弊测试、重复实验、波动、失败分析和 benchmark 生命周期。 |
| <a id="step-42"></a>42 | Stanford 16 · SWE-bench 嘉宾课 **（回访）** | [全部资料](329z/16.GuestLectureSWEBench/SOURCES.md) · **待讲义/分享材料** | 待讲义；回访评分器、任务分布、污染和可复现条件，不能因看过任务介绍就算完成。 |
| <a id="step-43"></a>43 | Harvard 19 · 企业 Agent 开发与评测嘉宾课 | [全部资料](2680/19.GuestLectureDevelopingAndEvaluatingAgentsInEnterpriseSetting/SOURCES.md) · **待讲义/分享材料** | 待嘉宾材料；把企业任务约束与开发、评测闭环接起来。 |
| <a id="step-44"></a>44 | **Stanford HW2 · Building an Evaluation Task** | [17 页正式原题](329z/assignment/assignment-2/upstream/cs329z_assignment2_evaluation.pdf) · [starter / 版本](329z/assignment/assignment-2/SOURCES.md) | 学习 Harbor、Docker 和三类样例轨迹；构造一个有效任务，验证 oracle 与 verifier，提交五次独立模型尝试、一页报告和三份同伴评审。作业完成后接 [10 分钟闭卷验收](#stanford-quizzes)与 [评测互评](#stanford-peer-reviews)。 |

**本阶段验收：** 评分器有正反例测试；开发集和验收集分开；能把解析、检索、推理、工具和评分错误区分开，并报告成本及结果波动。

**项目节点：** 完成 [MIT W4 proposal](#project-mit-proposal)、[CMU 研究问题与 proposal](#project-cmu) 和 [Harvard proposal](#project-harvard)；准备 [Stanford 论文讲解与评审](#paper-work)。

<a id="p4"></a>

## 阶段 4：让系统能恢复、受约束，并适合真实用户

把你的后端经验落实到 Agent 的副作用、长任务状态、权限和人工介入；安全与基本评测在前面作业中已开始，这里系统深化。

| 步骤 | 具体课次 / 作业 | 直接打开 | 本次学习或实现目标 |
|---|---|---|---|
| <a id="step-45"></a>45 | CMU 15 · Orchestration & Monitoring | [中文讲解](11-768/15.OrchestrationAndMonitoring/lecture-15-orchestration-and-monitoring-complete-guide.md) · [主讲义](11-768/15.OrchestrationAndMonitoring/lecture-15-orchestration-and-monitoring.pdf) · [全部资料](11-768/15.OrchestrationAndMonitoring/SOURCES.md) | 连接工作流、状态持久化、评测、观测和行为监控。 |
| <a id="step-46"></a>46 | Stanford 05 · Frameworks & Orchestration **（回访）** | [讲解定位](329z/5.FrameworksOrchestration/notes.zh-CN.md#8-durable-orchestration让业务流程跨故障继续推进) · [主讲义](329z/5.FrameworksOrchestration/slides/lecture05.pdf) · [全部资料](329z/5.FrameworksOrchestration/SOURCES.md) | **回访 §8–13，并对照 §7**：持久执行、重试/取消/版本升级、harness 成本与框架选型。 |
| <a id="step-47"></a>47 | CMU 17 · Observability & Monitoring（10/22） | [全部资料](11-768/17.ObservabilityAndMonitoring/SOURCES.md) · **待讲义/分享材料** | 待讲义；将正式可观测性课补到已有 trace、指标与告警设计中。 |
| <a id="step-48"></a>48 | CMU 13 · Agent Safety | [中文讲解](11-768/13.AgentSafety/lecture-13-agent-safety-study-guide.md) · [主讲义](11-768/13.AgentSafety/lecture-13-agent-safety.pdf) · [全部资料](11-768/13.AgentSafety/SOURCES.md) | 明确威胁模型、沙箱、最小权限、监控和评测的边界。 |
| <a id="step-49"></a>49 | Harvard 09 · Agent Safety / Self-evolving Harness 讨论（后续 [第 64 步](#step-64)） | [讲解定位](2680/9.AdvancedAgentDesignII.AgentSafetySelfEvolvingHarness/notes.zh-CN.md#1-先定义系统状态与授权而不是先背攻击名称) · [全部资料](2680/9.AdvancedAgentDesignII.AgentSafetySelfEvolvingHarness/SOURCES.md) · **论文讨论，无教师讲义** | **本次读 §0–8、§17、§19–21 的安全部分**；按官方分组阅读安全论文，不等不存在的教师讲义。 |
| <a id="step-50"></a>50 | Stanford 17 · Agent Safety & Guardrails | [全部资料](329z/17.AgentSafetyGuardrails/SOURCES.md) · **待讲义/分享材料** | 待讲义；核对正式 guardrails 课程，与现有权限和工具边界实验对照。 |
| <a id="step-51"></a>51 | CMU 16 · Agents and the Future of Work（10/27） | [中文讲解](11-768/16.AgentsAndTheFutureOfWork/notes.zh-CN.md) · [主讲义](11-768/16.AgentsAndTheFutureOfWork/2026-10-27-zora-wang.pdf) · [全部资料](11-768/16.AgentsAndTheFutureOfWork/SOURCES.md) | 理解自动化与增强的不同评价；用真实工作任务和人类交付要求定义价值。 |
| <a id="step-52"></a>52 | CMU 19 · Human-Agent Interaction（11/10） | [全部资料](11-768/19.HumanAgentInteraction/SOURCES.md) · **待讲义/分享材料** | 待讲义；补人工接管、反馈和 Human-Agent Interaction 的正式内容。 |
| <a id="step-53"></a>53 | Stanford 19 · Proactive Agents | [全部资料](329z/19.ProactiveAgents/SOURCES.md) · **待讲义/分享材料** | 待讲义；核对主动执行的任务触发、授权、打扰与退出边界。 |

**本阶段验收：** 在长期项目实际测试工具写入后崩溃、超时/限流、重启恢复、取消、权限拒绝和回滚；说明哪些情况仍需人工处理。

**项目节点：** 完成 [Stanford midpoint demo/report](#project-stanford)，收集真实使用反馈，区分“技术上执行成功”和“用户愿意采用”。

<a id="p5"></a>

## 阶段 5：在可靠评测之上优化搜索、上下文和 Harness

先做预算与性能归因，再做自动优化；MIT 的 Context/Harness 部分在这里进入，不必等全部 RL 学完。

| 步骤 | 具体课次 / 作业 | 直接打开 | 本次学习或实现目标 |
|---|---|---|---|
| <a id="step-54"></a>54 | Harvard 08 · Agent Cost & Performance | [中文讲解](2680/8.AdvancedAgentDesignI.CostAndPerformance/lecture-08_agent_cost_and_performance.md) · [主讲义](2680/8.AdvancedAgentDesignI.CostAndPerformance/8_agent_design_5.pdf) · [全部资料](2680/8.AdvancedAgentDesignI.CostAndPerformance/SOURCES.md) | 把成功率、时延、token 和每成功任务成本放在同一比较条件下。 |
| <a id="step-55"></a>55 | Stanford 09 · Optimization（后续 [第 85 步](#step-85)） | [讲解定位](329z/9.Optimization/notes.zh-CN.md#1-优化之前先把可改变的对象写清楚) · [主讲义](329z/9.Optimization/slides/lecture09.pdf) · [全部资料](329z/9.Optimization/SOURCES.md) | **本次读 §1–7、§11–15**：示例/提示/程序优化、反馈、候选选择与实验流程；§8–10 在阶段 7 学。 |
| <a id="step-56"></a>56 | CMU 20 · Reranking & Critic Models（11/12） | [全部资料](11-768/20.RerankingAndCriticModels/SOURCES.md) · **待讲义/分享材料** | 待讲义；区分最终评分器和搜索中的 critic，具体算法发布后核实。 |
| <a id="step-57"></a>57 | CMU 21 · Tree Search（11/17） | [全部资料](11-768/21.TreeSearch/SOURCES.md) · **待讲义/分享材料** | 待讲义；在 critic/reranking 后学 Tree Search；比较时显式计入额外推理预算。 |
| <a id="step-58"></a>58 | **Harvard HW3 · Mads-Opt** | [原题](2680/site/assignments/assignment3.html) · [starter](2680/assignment/assignment-3/SOURCES.md) | 在 HW2 基线上完成原题优化；同任务、同预算比较成功率、耗时与成本，说明每项改动的作用。 |
| <a id="step-59"></a>59 | Harvard 22 · Assignment 3 Student Sharing | [全部资料](2680/22.Assignment3StudentSharing/SOURCES.md) · **原件有密码保护，正文待取得** | 在 HW3 后展示基线、改动、失败与取舍；官方分享材料待取得。 |
| <a id="step-60"></a>60 | Harvard 23 · Assignment 3 Feedback | [全部资料](2680/23.Assignment3Feedback/SOURCES.md) · **原件有密码保护，正文待取得** | 在 HW3 后吸收正式反馈；把反馈转成可验证的下一项改动。 |
| <a id="step-61"></a>61 | MIT W02 · Context Evolution 1 | [中文讲解](MAS.S62/2.ContextEvolution1/notes.zh-CN.md) · [主讲义](<MAS.S62/2.ContextEvolution1/slides/lec2 - context.pdf>) · [嘉宾讲义](MAS.S62/2.ContextEvolution1/slides/context_guest.pdf) · [教程](MAS.S62/2.ContextEvolution1/tutorials/Textgrad_tutorial.ipynb) · [全部资料](MAS.S62/2.ContextEvolution1/SOURCES.md) | 学习 Context Evolution 主讲、嘉宾和 TextGrad 教程，辨认优化对象与反馈。 |
| <a id="step-62"></a>62 | MIT W03 · Context Evolution 2 | [中文讲解](MAS.S62/3.ContextEvolution2/notes.zh-CN.md) · [主讲义](<MAS.S62/3.ContextEvolution2/slides/lec3 - llm optimizers.pdf>) · [全部资料](MAS.S62/3.ContextEvolution2/SOURCES.md) | 学习 LLM optimizer 的候选生成、评估和选择，检查开发集与泛化。 |
| <a id="step-63"></a>63 | **MIT Context Evolution · 计划作业** | [已公开 OpenEvolve notebook](MAS.S62/assignment/assignment-1/OpenEvolve_assignment.ipynb) · [题号与计划入口](MAS.S62/assignment/SOURCES.md) | 先完成已公开 notebook 的原题。它正文标 Assignment 3，本地旧入口为 HW1，大纲把 OpenEvolve 列为 Context 候选；正式编号对应关系待核实。 |
| <a id="step-64"></a>64 | Harvard 09 · Agent Safety / Self-evolving Harness 讨论 **（回访）** | [讲解定位](2680/9.AdvancedAgentDesignII.AgentSafetySelfEvolvingHarness/notes.zh-CN.md#9-从安全转向演化先看更新对象与反馈通道) · [全部资料](2680/9.AdvancedAgentDesignII.AgentSafetySelfEvolvingHarness/SOURCES.md) · **论文讨论，无教师讲义** | **回访 §9–16、§18–21**：Reflexion、ADAS/DGM、ACE、Meta-Harness 等；把剩余论文分组和安全演化结论补完整。 |
| <a id="step-65"></a>65 | MIT W05 · Harness Evolution 1 | [中文讲解](MAS.S62/5.HarnessEvolution1/notes.zh-CN.md) · [主讲义](<MAS.S62/5.HarnessEvolution1/slides/lec4 - harness.pdf>) · [嘉宾讲义](MAS.S62/5.HarnessEvolution1/slides/harness_guest.pdf) · [全部资料](MAS.S62/5.HarnessEvolution1/SOURCES.md) | 学习 Harness Evolution 主讲与嘉宾材料，区分改代码、改工具和改执行策略。 |
| <a id="step-66"></a>66 | MIT W06 · Harness Evolution 2 | [中文讲解](MAS.S62/6.HarnessEvolution2/notes.zh-CN.md) · [主讲义](<MAS.S62/6.HarnessEvolution2/slides/lec5 - multi agent.pdf>) · [教程](<MAS.S62/6.HarnessEvolution2/tutorials/harness engineering tutorial.pdf>) · [全部资料](MAS.S62/6.HarnessEvolution2/SOURCES.md) | 学习多 Agent / harness 演化及教程，检查收益来自结构变化还是预算变化。 |
| <a id="step-67"></a>67 | **MIT Harness Evolution · 计划作业** | [计划作业 2](MAS.S62/assignment/assignment-2/SOURCES.md) | **待完整题目。** 大纲候选为 SkillOpt/DGM/Meta-Harness；先用 W5–6 做有基线的小实验，正式作业完成状态保持待核实。 |

**本阶段验收：** 每次优化先写假设、冻结评测和预算，再做基线/消融；能说明反馈如何导致更新，收益在何种任务上失效。

**项目节点：** 完成 [CMU project check-in](#project-cmu)：保留至少一个未支持原假设的结果及其解释。

<a id="p6"></a>

## 阶段 6：补齐推理服务与全栈性能能力

这是针对你 AI infra 短板的重点阶段。沿 Harvard 的连续作业链推进，把 Agent 工作负载与 GPU/服务端测量连起来。

| 步骤 | 具体课次 / 作业 | 直接打开 | 本次学习或实现目标 |
|---|---|---|---|
| <a id="step-68"></a>68 | Harvard 10 · Intro to LLMs **（回访）** | [讲解定位](2680/10.EfficientLLMServingBasicsI.IntroToLLMs/notes.zh-CN.md#7-参数量与-flops把70b拆开) · [主讲义](2680/10.EfficientLLMServingBasicsI.IntroToLLMs/9_llm_serving_basics_1.pdf) · [全部资料](2680/10.EfficientLLMServingBasicsI.IntroToLLMs/SOURCES.md) | **回访 §7–17，并复查 §1、§3、§6**：参数/FLOPs、显存、模型架构、CPU 检查与性能实验。 |
| <a id="step-69"></a>69 | Harvard 11 · Intro to GPUs | [中文讲解](2680/11.EfficientLLMServingBasicsII.IntroToGPUs/notes.zh-CN.md) · [主讲义](2680/11.EfficientLLMServingBasicsII.IntroToGPUs/10_llm_serving_basics_2a.pdf) · [全部资料](2680/11.EfficientLLMServingBasicsII.IntroToGPUs/SOURCES.md) | 理解 GPU 执行、带宽、算力和 kernel；把瓶颈推断转为可验证测量。 |
| <a id="step-70"></a>70 | Harvard 12 · Batching, Paging & Parallelism | [全部资料](2680/12.EfficientLLMServingBasicsIII.BatchingPagingAndParallelism/SOURCES.md) · **待讲义/分享材料** | 待讲义；补 batching、paging 与 parallelism，解释并发请求的资源占用。 |
| <a id="step-71"></a>71 | **Harvard HW4 · Mads-Serve** | [原题](2680/site/assignments/assignment4.html) · [作业讲义](2680/assignment/assignment-4/assignment4.pdf) · [starter](2680/assignment/assignment-4/SOURCES.md) | 完成原题的服务实现与实验，先留下端到端基线。后续课程未有讲义时，按已公开 handout 推进其允许的部分。 |
| <a id="step-72"></a>72 | Harvard 13 · Speculative Decoding | [全部资料](2680/13.EfficientLLMServing.SpeculativeDecoding/SOURCES.md) · **待讲义/分享材料** | 待讲义；理解 speculative decoding 的适用条件，测量端到端收益。 |
| <a id="step-73"></a>73 | Harvard 14 · Scheduling & Prefix Caching | [全部资料](2680/14.EfficientAgenticSystems.SchedulingAndPrefixCaching/SOURCES.md) · **待讲义/分享材料** | 待讲义；连接调度、prefix reuse、等待时间与吞吐。 |
| <a id="step-74"></a>74 | Harvard 16 · KV Cache & Model Architectures | [全部资料](2680/16.EfficientLLMServing.KVCacheOptimizationAndModelArchitectures/SOURCES.md) · **待讲义/分享材料** | 待讲义；分析 KV cache 优化与模型架构对容量和性能的影响。 |
| <a id="step-75"></a>75 | Harvard 15 · Pruning & Quantization | [全部资料](2680/15.EfficientLLMServing.PruningAndQuantization/SOURCES.md) · **待讲义/分享材料** | 待讲义；分析剪枝/量化的质量、内存和真实速度取舍。 |
| <a id="step-76"></a>76 | Harvard 17 · Routing & Load Balancing | [全部资料](2680/17.EfficientAgenticSystem.RoutingAndLoadBalancing/SOURCES.md) · **待讲义/分享材料** | 待讲义；分析 routing、load balancing 与不同请求的服务质量。 |
| <a id="step-77"></a>77 | Harvard 20 · Why Infrastructure Sets the Pace of AI | [全部资料](2680/20.GuestLectureWhyInfrastructureSetsThePaceOfAI/SOURCES.md) · **待讲义/分享材料** | 待嘉宾材料；用前面的测量理解基础设施为什么约束可实现的 AI 产品。 |
| <a id="step-78"></a>78 | Harvard 24 · Engine Optimizations / Agent-engine Co-design 分享 | [全部资料](2680/24.StudentSharingIII.EngineOptimizationsAndAgentEngineCoDesign/SOURCES.md) · **待讲义/分享材料** | 待分享材料；连接 engine 优化和 Agent-engine 协同设计，复盘 HW4 的服务基线。 |
| <a id="step-79"></a>79 | **Harvard HW5 · Mads-Stack** | [计划作业 5](2680/assignment/assignment-5/SOURCES.md) | **待完整题目。** 在 HW2/3/4 的同一任务链上做全栈优化；正式实现与验收要求以发布后的原题为准。 |
| <a id="step-80"></a>80 | Harvard 25 · Student Sharing IV | [全部资料](2680/25.StudentSharingIV/SOURCES.md) · **待讲义/分享材料** | 待分享材料；展示全链路性能证据和未解决的问题，具体主题以正式材料为准。 |

**本阶段验收：** 在同一 Agent 工作负载下拆解排队、模型推理、工具和传输耗时；报告质量、TTFT/TPOT、吞吐、显存与成本，完成已公开原题要求。

**项目节点：** 为 [Harvard 项目](#project-harvard) 完成服务与 Agent 的联合实验；把系统选择写成基于证据的设计取舍。

<a id="p7"></a>

## 阶段 7：学习 SFT、RL 和模型演化

前面已经有可用数据、可信评测和系统测量，现在再改变模型权重，才能分辨数据、算法与系统造成的效果。

| 步骤 | 具体课次 / 作业 | 直接打开 | 本次学习或实现目标 |
|---|---|---|---|
| <a id="step-81"></a>81 | CMU 08 · Supervised Fine-Tuning | [中文讲解](11-768/8.SupervisedFineTuning/SFT_Lecture08_Integrated_Notes.md) · [主讲义](11-768/8.SupervisedFineTuning/lecture-08-sft.pdf) · [全部资料](11-768/8.SupervisedFineTuning/SOURCES.md) | 理解训练样本、token 级 loss、mask、数据组织与 SFT 的能力边界。 |
| <a id="step-82"></a>82 | **补充练习 · SFT 最小验收** | [回到 SFT 讲解](11-768/8.SupervisedFineTuning/SFT_Lecture08_Integrated_Notes.md) | 自建小实验，不冒充官方作业：核对数据/模板/loss mask，跑一次小规模微调或 LoRA，并用保留任务比较训练前后。 |
| <a id="step-83"></a>83 | CMU 09 · RL Basics | [中文讲解](11-768/9.TrainingRLBasics/rl_lecture09_integrated_notes.md) · [主讲义](11-768/9.TrainingRLBasics/lecture-09-rl-basics.pdf) · [全部资料](11-768/9.TrainingRLBasics/SOURCES.md) | 从策略梯度、奖励、优势与 GRPO 建立训练直觉。 |
| <a id="step-84"></a>84 | CMU 11 · Advanced RL Algorithms | [中文讲解](11-768/11.AdvancedRLAlgorithms/lecture-11-advanced-rl-integrated.md) · [主讲义](11-768/11.AdvancedRLAlgorithms/lecture-11-rl-advanced.pdf) · [全部资料](11-768/11.AdvancedRLAlgorithms/SOURCES.md) | 理解进阶 RL 的信用分配、目标、奖励与稳定性条件。 |
| <a id="step-85"></a>85 | Stanford 09 · Optimization **（回访）** | [讲解定位](329z/9.Optimization/notes.zh-CN.md#8-sft让模型更像经过筛选的成功行为) · [主讲义](329z/9.Optimization/slides/lecture09.pdf) · [全部资料](329z/9.Optimization/SOURCES.md) | **回访 §8–10，并对照 §7、§13**：SFT、GRPO、on-policy distillation；解释何时该改权重。 |
| <a id="step-86"></a>86 | CMU 12 · RL Systems | [中文讲解](11-768/12.TrainingRLSystems/notes.zh-CN.md) · [主讲义](11-768/12.TrainingRLSystems/lecture-12-rl-systems.pdf) · [全部资料](11-768/12.TrainingRLSystems/SOURCES.md) | 理解 rollout、训练和版本同步的系统约束，连接前面的 serving 经验。 |
| <a id="step-87"></a>87 | **CMU HW3 · Training** | [原题](11-768/assignment/assignment-3/ASSIGNMENT.md) · [starter 与运行边界](11-768/assignment/assignment-3/SOURCES.md) | 完成轨迹处理、同步 REINFORCE/GRPO、异步 GRPO、TextCraft 和原题必做实验；真实训练结果与离线测试分开记录。 |
| <a id="step-88"></a>88 | MIT W07 · Model Evolution 1 | [中文讲解](MAS.S62/7.ModelEvolution1/notes.zh-CN.md) · [主讲义](<MAS.S62/7.ModelEvolution1/slides/lec6 - training.pdf>) · [嘉宾讲义](MAS.S62/7.ModelEvolution1/slides/model_guest.pdf) · [教程](<MAS.S62/7.ModelEvolution1/tutorials/lec6 - rl in practice.pdf>) · [全部资料](MAS.S62/7.ModelEvolution1/SOURCES.md) | 读 Model Evolution 主讲、嘉宾与 RL 实践教程，比较训练和自蒸馏机制。 |
| <a id="step-89"></a>89 | MIT W09 · Model Evolution 2 | [已有 RL 教程](<MAS.S62/7.ModelEvolution1/tutorials/lec6 - rl in practice.pdf>) · [全部资料](MAS.S62/9.ModelEvolution2/SOURCES.md) · **待本周正文核实** | **W9 正文归属待核实。** 官网链接指向已有 W7 RL 教程；不可把旧教程当成 W9 全部新内容。 |
| <a id="step-90"></a>90 | **MIT Model Evolution · 计划作业** | [计划作业 3](MAS.S62/assignment/assignment-3/SOURCES.md) | **待完整题目。** 以大纲暂定的 test-time training / continual learning 方向预习，正文公开后核对实现要求。 |

**本阶段验收：** 能构造有效训练样本并解释 loss/reward；完成原题必做训练与消融，区分真实训练、离线测试和未运行计划。

**项目节点：** 完成 [MIT W8 midterm](#project-mit-midterm)，将模型变化与上下文/harness 变化做公平比较。

<a id="p8"></a>

## 阶段 8：学习环境演化与前沿，并完成项目

最后改变任务与环境，检验前面学到的优化是否真正迁移；四课项目分别按各自要求验收。

| 步骤 | 具体课次 / 作业 | 直接打开 | 本次学习或实现目标 |
|---|---|---|---|
| <a id="step-91"></a>91 | MIT W10 · Environment Evolution 1 | [全部资料](MAS.S62/10.EnvironmentEvolution1/SOURCES.md) · **待讲义/分享材料** | 待讲义；进入任务/环境生成，核对正式课件的对象、反馈与评价方式。 |
| <a id="step-92"></a>92 | MIT W11 · Environment Evolution 2 | [全部资料](MAS.S62/11.EnvironmentEvolution2/SOURCES.md) · **待讲义/分享材料** | 待讲义；连接 world models、评价/奖励演化和泛化检验。 |
| <a id="step-93"></a>93 | **MIT Task Evolution · 计划作业** | [计划作业 4](MAS.S62/assignment/assignment-4/SOURCES.md) | **待完整题目。** 大纲暂定 PostTrainBench；重点保留任务/评价生成与泛化检验位置，不预填未公开题目。 |
| <a id="step-94"></a>94 | MIT W12 · Future Topics（W12） | [全部资料](MAS.S62/12.FutureTopics/SOURCES.md) · **待讲义/分享材料** | 待讲义；大纲中的科学/多模态前沿按实际发布内容学习，避免仅凭主题预设方法。 |
| <a id="step-95"></a>95 | MIT W14 · Future Topics（W14） | [全部资料](MAS.S62/14.FutureTopics/SOURCES.md) · **待讲义/分享材料** | 待讲义；学习具身与安全演化等前沿内容，明确迁移边界。 |

**本阶段验收：** 以新任务或新环境检验泛化，保留反例和复现条件；交付能运行的系统、实验记录、报告与演示。

**项目节点：** 完成 [四课项目与展示](#projects)，并回访 [尚未定题的嘉宾课](#pending)。

<a id="projects"></a>

## 项目、展示、论文讲解与阅读作业

长期工程项目采用公开资料的投研证据助手，从 5–10 家公司的变化摘要、证据引用与待核查事项起步。四门课可以共用数据与工程底座，但分别按官方项目目标交付；一个 demo 不代表四个项目完成。

| 项目 / 活动 | 在上面哪一阶段做 | 直接入口与交付 |
|---|---|---|
| <a id="project-stanford"></a>Stanford project | 阶段 1 proposal → 阶段 4 midpoint → 阶段 8 final | [项目要求](329z/project/SOURCES.md)：任务/数据/环境、工作原型、评测、报告与演示；官网演示明确为 12/09 15:30–18:30，最终报告日期仍为 Dec 7–11/TBA；均为 Pacific Time。 |
| <a id="project-cmu"></a>CMU mini research project | 阶段 3 问题/proposal → 阶段 5 check-in → 阶段 8 report/poster | [项目要求](11-768/project/SOURCES.md)：研究问题、基线、机制实验与反例；11/05 project hours、12/01 和 12/03 poster 均保留。项目占课程评分 50%；完整 handout 未取得，组队人数存在官方页面冲突。 |
| <a id="project-harvard"></a>Harvard project | 阶段 3 proposal → 阶段 6 性能/产品实验 → 阶段 8 final | [正式要求](2680/project/SOURCES.md)：选择 product/research track；按原题完成比较、消融、反例、成本与可复现报告；12/07 poster/demo 保留。 |
| <a id="project-mit-proposal"></a>MIT W4 · Project Proposal | 阶段 3 结束前 | [W4 活动](MAS.S62/4.ProjectProposalPresentations/SOURCES.md) · [本学期大纲](MAS.S62/site/syllabus/ai4ai-syllabus.pdf)：明确演化对象、研究问题与可信评测，提交相关工作综述和初步基线结果，并做 proposal 展示。 |
| <a id="project-mit-midterm"></a>MIT W8 · Project Midterm | 阶段 7 的模型实验形成基线后 | [W8 活动](MAS.S62/8.ProjectMidtermPresentations/SOURCES.md)：说明已得到的证据、失败与下一步假设。 |
| <a id="project-mit-final"></a>MIT W13 · Project Final | 阶段 8 收束 | [W13 活动](MAS.S62/13.ProjectFinalPresentations/SOURCES.md) · [项目入口](MAS.S62/project/SOURCES.md)：最终研究报告与展示；项目入口中的往届案例仅供参考。 |

<a id="paper-work"></a>

| 非编码学习任务 | 插入位置 | 直接入口与完成方式 |
|---|---|---|
| Stanford Paper Video | 阶段 3 | [正式 handout](329z/site/assignments/paper_video.pdf)：录制 10–15 分钟视频，包含方法、批判分析和实践增量（运行代码、具体例子或小实验）。按 handout 的选题限制选论文；不能只复述论文。 |
| <a id="stanford-quizzes"></a>Stanford 2 次 HW-based quiz | [第 20 步 HW1](#step-20)后一次；[第 44 步 HW2](#step-44)正式完成后一次 | [正式要求](329z/site/logistics.html#coursework)：每次 10 分钟，解释本人作业的设计决策与取舍。正式试题未公开时，独立闭卷自测并保存回答，标记为自学验收，不计作学校 quiz 成绩。 |
| <a id="stanford-peer-reviews"></a>Stanford 同伴评审 | 阶段 3 的论文视频与 HW2 评测；阶段 4 的中期 demo、阶段 8 的最终 demo | [课程概要](329z/site/logistics.html#coursework) 仍统一写每类 2 份；新 [HW2 handout p.15](329z/assignment/assignment-2/upstream/cs329z_assignment2_evaluation.pdf#page=15) 明确要求评审 **3 份任务**，12/02 提交，按该作业具体要求理解。课程 gallery 未取得，替代评审单独标作自学练习。 |
| CMU lecture highlights | 每一讲结束 | [官方大纲](syllabus-snapshots/2026-11-01/cmu/syllabus.json)：记录一个有证据的 takeaway、一个仍不明白的问题；正式课程提交规则以官网为准。 |
| MIT 4 次 reading assignments | 阶段 5 Context 一次、Harness 一次；阶段 7 Model 一次；阶段 8 Task/Environment 一次 | [大纲与计划](MAS.S62/site/syllabus/ai4ai-syllabus.pdf)：每次提交指定论文的主旨总结，并结合本人数据或研究回答 research question probes。配套阅读见对应 lecture 的“全部资料”；四次作业的具体篇目和问题待核实，按主题插入是本路线的个人安排。 |
| Harvard 讨论与学生分享 | 已插在相关 lecture / HW 后 | 第 9 项讨论与第 21–25 项分享/反馈都在主表中，不能因为没有教师 slides 而跳过。 |

<a id="pending"></a>

## 等内容明确后再定位的课程

下面三项有正式课表位置。材料公开后依据实际主题和前置插入阶段 2–8；检查点设在阶段 8 收束前，不将待定主题猜成已学内容。

| 课次 | 直接入口 | 安排 |
|---|---|---|
| <a id="pending-c22"></a>CMU 22 · Guest Lecture（11/19，题目待定） | [全部资料](11-768/22.GuestLecture20261119/SOURCES.md) · **待讲义/分享材料** | 主题/资料核实后决定具体学习位置，完成前保持待回访。 |
| <a id="pending-c23"></a>CMU 23 · Guest Lecture（11/24，题目待定） | [全部资料](11-768/23.GuestLecture20261124/SOURCES.md) · **待讲义/分享材料** | 主题/资料核实后决定具体学习位置，完成前保持待回访。 |
| <a id="pending-s14"></a>Stanford 14 · Fireside Chat with Andrew Ng（11/09） | [全部资料](329z/14.FiresideChatWithAndrewNg/SOURCES.md) · **待讲义/分享材料** | 主题/资料核实后决定具体学习位置，完成前保持待回访。 |
| <a id="legacy-h18"></a>Harvard 18 · Others 历史占位 | [保留资料与状态](2680/18.EfficientAgenticSystems.Others/SOURCES.md) | 已不对应当前正式课表的确定主题；资料保留，有明确内容后再归位，不额外虚构一讲。 |

9 条停课记录仍保留在 [完整日历](SYLLABUS-COVERAGE.zh-CN.md)：CMU 4 条、Harvard 3 条、Stanford 2 条。停课不产生学习任务。主表覆盖所有已定主题的教学/讨论/分享，另表覆盖 3 次待定嘉宾、8 条项目日历与历史占位。

<a id="homework-method"></a>

## 每份作业怎么做

1. 先读本行的**原题、评分/提交要求、接口与测试**，列出必做项；课程中的方法进入实现时再沿 lecture 链接回查。
2. 在独立工作目录实现，保留资料库的官方 starter 原貌。先跑基线，区分环境问题、待实现函数和行为错误。
3. 完成原题全部必做要求，再做一项有明确假设的对照/消融；记录模型、数据、代码版本、配置、结果、失败轨迹、成本与耗时。
4. 最后把已经验证的机制迁移到投研项目。官方 coding/chess/邮件/可视化任务先按原题做；迁移实践另记，不替代官方作业。

14 个正式或计划作业位置全部已插入主表：Harvard 5、Stanford 2、CMU 3、MIT 4。MIT Context 的公开 notebook 编号冲突，以及其余未取得的正式题目，均在相应行标明。补充 SFT 练习是个人能力验收，不计入这 14 项。

涉及 API/GPU 时，先核对原题版本、可用账号、硬件和预算；学校资源不假定可用。离线/mock 检查、真实推理、真实训练分别计进度，公开测试通过不代替原题实验。

## 更新与完成的判断

- 每讲以 lecture slides 决定主线，readings 补机制与证据，references 补背景与实现；讨论课按正式阅读要求组织。每个“全部资料”入口都保留未取得材料的状态。
- 一个阶段可以“可执行部分完成，仍有待回访项”。后续讲义未发布时，继续前置已满足的任务；不把占位、阅读过概要或下载文件记成学会。
- 同 URL 正文修订时保留来源版本，复查受影响的讲解、页码和作业约束；日期变更只调整课表，知识依赖有变化才重排步骤。
- 内容公开后更新当前步骤、材料链接和 [课表覆盖表](SYLLABUS-COVERAGE.zh-CN.md)，不新增一份平行 roadmap。完整官方脉络与来源见 [COURSE_LAYOUT.json](COURSE_LAYOUT.json) 和 [大纲来源](syllabus-snapshots/2026-11-04/README.md)。

学到 Senior 所需的证据包括：能运行、能解释失败、能做设计取舍、能在变化的任务中检验边界，并让他人理解和复现。课程项目提供练习场，真实运行维护和协作继续检验这些能力。

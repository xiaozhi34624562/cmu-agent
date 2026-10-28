# 三门课程中文讲解：学习质量复核（2026-10-28）

本轮完整阅读了 CMU 11-768 的 19 份、Harvard CS2680 的 12 份、MIT MAS.S62 的 6 份中文讲解及配套学习文档，共 37 份。修订 31 份，6 份在完整审核后保留正文；每份修订稿都在最后一次正文改动后全文复读两遍。每篇的来源页段、具体问题、最终校验值和复读范围保存在下表记录中。

## 以什么背景为起点

读者是有 Java 及一般应用开发经验的 LLM Developer。接口、调用链、状态、并发、缓存、异常恢复与测试是已有经验；概率统计、梯度、训练计算图、GPU 执行细节需要在课程使用时讲清。已有业务经验可以帮助举例，但不会把三门课压缩为 RAG、金融投研或报告审核专题。

审核关注的是能否沿文章学会：先说明所解决的问题，再引出必要概念和机制，解释符号与假设，沿一个案例走完过程，最后通过手算、故障判断和迁移题检验理解。长文增加必要的首读路线；细节放在它所解释的问题旁边，而不是只在开头声明“适合开发者”。已有完整、连贯的讲解不为了产生改动而重写。

## 实际改动

| 学习障碍 | 具体修订 | 示例入口 |
|---|---|---|
| 应用调用直接跳到模型训练 | 区分运行时状态与模型参数；从 logits、概率、负对数损失到一次参数更新，再接 SFT、组优势和策略梯度 | [CMU SFT](../../../11-768/8.SupervisedFineTuning/SFT_Lecture08_Integrated_Notes.md)、[CMU 进阶 RL](../../../11-768/11.AdvancedRLAlgorithms/lecture-11-advanced-rl-integrated.md)、[MIT 模型演化](../../../MAS.S62/7.ModelEvolution1/notes.zh-CN.md) |
| 知道缓存、并发的名字，但不清楚模型系统中的约束 | 解释 KV 缓存的对象与失效条件、生成和训练的数据流、显存容量/带宽/算力、版本冲突和恢复语义 | [Harvard 课程导论](../../../2680/1.CourseOverviewAndLogistics/notes.zh-CN.md)、[Harvard GPU 基础](../../../2680/11.EfficientLLMServingBasicsII.IntroToGPUs/notes.zh-CN.md)、[CMU RL 系统](../../../11-768/12.TrainingRLSystems/notes.zh-CN.md)、[MIT Harness 演化](../../../MAS.S62/6.HarnessEvolution2/notes.zh-CN.md) |
| 公式与指标只给结论 | 补等差求和、条件概率、Precision/Recall/F1、宏平均、κ、p 值、置信范围的定义、分母、算例与限制 | [Harvard 评测](../../../2680/7.AgentDesignIV.AgentEvaluation/Agent_Eval_Lecture07_Integrated_Notes.md)、[Harvard 记忆与可靠性](../../../2680/6.AgentsDesignIII.AgentMemoryAndReliability/lecture06_agent_memory_reliability.md) |
| 方法名单没有连接到决策过程 | 用通用 API 修复、分页、错误传播、版本更新等案例解释何时用哪种机制；增补需要给出理由的自测和参考答案 | [CMU 规划与协调](../../../11-768/5.PlanningAndCoordination/lecture05_planning_coordination_integrated_notes.md)、[Harvard 成本与性能](../../../2680/8.AdvancedAgentDesignI.CostAndPerformance/lecture-08_agent_cost_and_performance.md)、[MIT 上下文演化](../../../MAS.S62/2.ContextEvolution1/notes.zh-CN.md) |
| 论文成绩被理解为一般保证 | 明确比较基线、总预算、独立性、样本单位和评分覆盖；把内部不一致与未复现部分写清 | [CMU 工作场景 Agent](../../../11-768/16.AgentsAndTheFutureOfWork/notes.zh-CN.md)、[Harvard 安全与自演化讨论课](../../../2680/9.AdvancedAgentDesignII.AgentSafetySelfEvolvingHarness/notes.zh-CN.md) |

来源回查保留了几项对学习很重要的区别：MIT 模型演化中 TTRL 同一归档内的摘要增益和图中数值不一致；SDFT 的公式与训练描述存在需要核对的差异；CMU RL 系统中的 8.31 倍是特定基线下单 GPU 梯度计算阶段的比较；Context Pruning 的金额归零指标并不证明全部类别与票据对应正确；Harvard GPU 课明确 Ragged Paged Attention 的 73% MFU 使用按矩阵利用率调整后的算力分母，以及 Mirage 理论等价保证与当前候选检查实现的差别。原始 PDF 未改写，讲解解释这些差异，不能从缺失证据补成确定结论。

## 逐篇记录

“修订后复读两遍”指最后正文版本，记录绑定 SHA-256；“保留正文”指本轮完整阅读后没有发现需要修改的实质问题，不借用过去审核替代本轮阅读。CMU 第 10 课的来源说明是配套文档，不冒充另一份完整课堂讲义。Harvard 第 9 课是按官方四组阅读组织的讨论课，没有教师讲义 PDF。

| 课程 | 学习文档 | 本轮结果 | 详细记录 |
|---|---|---|---|
| 11-768 | [Lecture 1｜What Is an Agent：从预测 token 到能够执行、验证和停止的系统](../../../11-768/1.WhatIsAnAgent/notes.zh-CN.md) | 修订后全文复读两遍 | [记录](primary_cmu_1_5/1-overview.json) |
| 11-768 | [Lecture 02：语言模型的工具使用——从 token 预测到可靠行动](../../../11-768/2.ToolUse/lecture-02-tool-use-complete-notes.zh-CN.md) | 修订后全文复读两遍 | [记录](primary_cmu_1_5/2-tool-use.json) |
| 11-768 | [Long Context：从模型的历史访问，到 Agent 的持续工作](../../../11-768/3.LongContext/long_context_lecture03_integrated_notes.md) | 完整审核，保留正文 | [记录](primary_cmu_1_5/3-long-context.json) |
| 11-768 | [Skills 与 Memory：从有限上下文到可验证的经验复用](../../../11-768/4.SkillsAndMemory/Skills_and_Memory_Integrated_Notes.md) | 完整审核，保留正文 | [记录](primary_cmu_1_5/4-skills-memory.json) |
| 11-768 | [Lecture 05｜Planning 与 Coordination：从任务分解到可靠的长任务执行](../../../11-768/5.PlanningAndCoordination/lecture05_planning_coordination_integrated_notes.md) | 修订后全文复读两遍 | [记录](primary_cmu_1_5/5-planning.json) |
| 11-768 | [Coding Agent：从代码生成到可靠的软件工程智能体](../../../11-768/6.CodingAgents/coding_agent_lecture06_integrated_notes.md) | 修订后全文复读两遍 | [记录](cmu_6_11/6-coding.json) |
| 11-768 | [Computer Use Agents：从闭环决策到可靠工程系统](../../../11-768/7.ComputerUseAgents/lecture-07-computer-use-agents-notes.md) | 修订后全文复读两遍 | [记录](cmu_6_11/7-computer-use.json) |
| 11-768 | [Lecture 08｜SFT：从监督目标到可靠 Agent 的完整讲义](../../../11-768/8.SupervisedFineTuning/SFT_Lecture08_Integrated_Notes.md) | 修订后全文复读两遍 | [记录](cmu_6_11/8-sft.json) |
| 11-768 | [面向 LLM 工程师的强化学习](../../../11-768/9.TrainingRLBasics/rl_lecture09_integrated_notes.md) | 修订后全文复读两遍 | [记录](cmu_6_11/9-rl-basics.json) |
| 11-768 | [Deep Research Agent 通用设计：一手来源核查](../../../11-768/10.DeepResearchAgents/Deep_Research_Agent_Design_Source_Checks.md) | 完整审核，保留正文 | [记录](cmu_6_11/10-design-source-checks.json) |
| 11-768 | [Deep Research Agent 通用设计：围绕问题、论断、证据与缺口组织研究](../../../11-768/10.DeepResearchAgents/Deep_Research_Agent_General_Design.md) | 修订后全文复读两遍 | [记录](cmu_6_11/10-general-design.json) |
| 11-768 | [Deep Research：让 AI 带着问题查资料，带着证据作判断](../../../11-768/10.DeepResearchAgents/Deep_Research_Lecture10_Integrated_Notes.md) | 修订后全文复读两遍 | [记录](primary_cmu_10/10-main.json) |
| 11-768 | [2026 年金融 Agent 研究：FutureX-Pro、MBABench 与 AURA-4B](../../../11-768/10.DeepResearchAgents/Finance_Agent_Research_2026_Three_Papers.md) | 修订后全文复读两遍 | [记录](cmu_6_11/10-finance-three-papers.json) |
| 11-768 | [Lecture 11：面向 LLM Agent 的进阶强化学习](../../../11-768/11.AdvancedRLAlgorithms/lecture-11-advanced-rl-integrated.md) | 修订后全文复读两遍 | [记录](primary_cmu_11/11-advanced-rl.json) |
| 11-768 | [Lecture 12｜RL Systems：把 Agent 轨迹变成一致、可扩展的策略更新](../../../11-768/12.TrainingRLSystems/notes.zh-CN.md) | 修订后全文复读两遍 | [记录](cmu_late_mit/11-768-12.json) |
| 11-768 | [Agent Safety：从威胁模型到可验证的执行控制](../../../11-768/13.AgentSafety/lecture-13-agent-safety-study-guide.md) | 完整审核，保留正文 | [记录](cmu_late_mit/11-768-13.json) |
| 11-768 | [Lecture 14 · OpenHands：从模型能力到可靠交付的 Agent 系统](../../../11-768/14.OpenHands/Lecture14_OpenHands_Integrated_Notes.md) | 完整审核，保留正文 | [记录](cmu_late_mit/11-768-14.json) |
| 11-768 | [Lecture 15：Orchestration and Monitoring](../../../11-768/15.OrchestrationAndMonitoring/lecture-15-orchestration-and-monitoring-complete-guide.md) | 完整审核，保留正文 | [记录](cmu_late_mit/11-768-15.json) |
| 11-768 | [AI Agents for Human Work：从基准能力到真实工作与人机协作](../../../11-768/16.AgentsAndTheFutureOfWork/notes.zh-CN.md) | 修订后全文复读两遍 | [记录](cmu_late_mit/11-768-16.json) |
| 2680 | [第 1 课｜Course overview and logistics：为什么 Agent 优化必须从成功任务出发](../../../2680/1.CourseOverviewAndLogistics/notes.zh-CN.md) | 修订后全文复读两遍 | [记录](harvard_full/01-overview.json) |
| 2680 | [Coding Agent：从运行机制到可靠工程系统](../../../2680/2.AgentsUseI.HowClaudeCodeWorks/coding_agent_integrated_guide.md) | 修订后全文复读两遍 | [记录](harvard_full/02-coding-guide.json) |
| 2680 | [Lecture 02｜Agent Use：从模型调用到可验证的工作系统](../../../2680/2.AgentsUseI.HowClaudeCodeWorks/lecture_02_agent_use_integrated_notes.md) | 修订后全文复读两遍 | [记录](harvard_full/02-lecture-main.json) |
| 2680 | [Lecture 03 · Multi-agent：从独立 Agent 到可靠协作系统](../../../2680/3.AgentsUseII.100xEngineerWithMultiAgents/Lecture03_MultiAgent_%E5%AE%8C%E6%95%B4%E5%AD%A6%E4%B9%A0%E8%AE%B2%E4%B9%89.md) | 修订后全文复读两遍 | [记录](harvard_full/03-multi-agent.json) |
| 2680 | [Lecture 04：Context Management 与 Tool Design](../../../2680/4.AgentsDesignI.ContextManagementAndToolDesign/lecture-04_context_and_tool_design_integrated.md) | 修订后全文复读两遍 | [记录](harvard_full/04-context-tools.json) |
| 2680 | [Lecture 05：多智能体协调——从对话、任务分解到可验证的共同决策](../../../2680/5.AgentsDesignII.MultiAgentArchitectureCoordinationAndCommunication/lecture-05_multi-agent-coordination_%E5%AE%8C%E6%95%B4%E5%AD%A6%E4%B9%A0%E7%AC%94%E8%AE%B0.md) | 修订后全文复读两遍 | [记录](harvard_full/05-coordination.json) |
| 2680 | [Lecture 06：Agent Memory 与 Reliability](../../../2680/6.AgentsDesignIII.AgentMemoryAndReliability/lecture06_agent_memory_reliability.md) | 修订后全文复读两遍 | [记录](harvard_full/06-memory-reliability.json) |
| 2680 | [Agent Eval：从任务成功到可信交付](../../../2680/7.AgentDesignIV.AgentEvaluation/Agent_Eval_Lecture07_Integrated_Notes.md) | 修订后全文复读两遍 | [记录](harvard_full/07-evaluation.json) |
| 2680 | [Agent Cost and Performance：从计算浪费到预算内的可靠交付](../../../2680/8.AdvancedAgentDesignI.CostAndPerformance/lecture-08_agent_cost_and_performance.md) | 修订后全文复读两遍 | [记录](harvard_full/08-cost-performance.json) |
| 2680 | [第 9 课：Agent 安全与自演化 Harness——把改进能力放进可约束的闭环](../../../2680/9.AdvancedAgentDesignII.AgentSafetySelfEvolvingHarness/notes.zh-CN.md) | 修订后全文复读两遍 | [记录](harvard_full/09-safety-evolution.json) |
| 2680 | [第 10 课：LLM 服务基础 I——从一个请求到模型的计算、状态与成本](../../../2680/10.EfficientLLMServingBasicsI.IntroToLLMs/notes.zh-CN.md) | 修订后全文复读两遍 | [记录](harvard_full/10-llm-basics.json) |
| 2680 | [第 11 课：LLM 服务基础 II——从 GPU 的吞吐机器到可验证的性能优化](../../../2680/11.EfficientLLMServingBasicsII.IntroToGPUs/notes.zh-CN.md) | 修订后全文复读两遍 | [记录](harvard_full/11-gpus.json) |
| MAS.S62 | [Week 1｜Course introduction：怎样把“自演化 AI”变成可检验的工程问题](../../../MAS.S62/1.CourseIntroduction/notes.zh-CN.md) | 修订后全文复读两遍 | [记录](primary_mit_1_3/1-intro.json) |
| MAS.S62 | [Week 2｜Context evolution 1：从提示优化到可持续的上下文学习](../../../MAS.S62/2.ContextEvolution1/notes.zh-CN.md) | 修订后全文复读两遍 | [记录](primary_mit_1_3/2-context.json) |
| MAS.S62 | [Week 3：Context evolution 2——让 LLM 成为可验证的优化器](../../../MAS.S62/3.ContextEvolution2/notes.zh-CN.md) | 修订后全文复读两遍 | [记录](primary_mit_1_3/3-optimizer.json) |
| MAS.S62 | [Week 5｜Harness evolution 1：从可管理的记忆到可验证的系统演化](../../../MAS.S62/5.HarnessEvolution1/notes.zh-CN.md) | 修订后全文复读两遍 | [记录](cmu_late_mit/MAS.S62-5.json) |
| MAS.S62 | [Week 6｜Harness evolution 2：从 Agent Loop 到可验证的多 Agent 演化](../../../MAS.S62/6.HarnessEvolution2/notes.zh-CN.md) | 修订后全文复读两遍 | [记录](primary_mit_6/6-harness.json) |
| MAS.S62 | [Week 7：Model evolution 1——从奖励学习到自蒸馏与持续适应](../../../MAS.S62/7.ModelEvolution1/notes.zh-CN.md) | 修订后全文复读两遍 | [记录](primary_mit_7/7-model.json) |

## 验证范围与剩余限制

- 原始资料对照已推送的同步版本检查，原始讲义、论文、网页正文与上游代码快照保持不变；见 [原始内容完整性记录](ORIGINAL_INTEGRITY.json)。新增源文件链接和补充资料校验值写入对应来源索引。
- 来源映射、讲解覆盖、本地链接、显式 PDF 页码、补充资料校验值，以及记录与最终讲解的一致性均执行实际检查。最终结果见 [汇总校验](VERIFICATION.json)、[CMU](../../../11-768/VERIFICATION.json)、[Harvard](../../../2680/VERIFICATION.json)、[MIT](../../../MAS.S62/VERIFICATION.json)。这些检查验证结构和完整性，不能代替正文精读，也不能证明读者已掌握知识。
- 本轮实际执行了记录中列出的离线教学示例，包括小规模数学、状态交接、掩码与梯度检查。没有执行完整模型训练、GPU 性能实验、付费模型/API 或论文基准复现；历史运行记录和本轮运行分开保存。
- MIT 作业的原始 OpenEvolve notebook 缺少部分配套文件，导入也有缺口；讲解已区分这些问题与学生 TODO。Harvard 受限阅读和未更新的公开作业快照仍保持未取得/保留旧版状态，未伪装成已获取正文。
- 辅助论文按每篇记录所列的机制、实验与局限页段回查，未声称阅读了所有论文的全部附录，也未声称本轮重新观看全部课程视频。

本次资料同步、CMU 新课与作业 3 已先提交于 `32b11714be3fbd5cbe4188abaa799ece9bb615b5`；本目录记录随后完成的三门课程全文教学复核。[机器可读清单](MANIFEST.json) 与各课程 `REVIEW.json` 保留历史和本轮记录。

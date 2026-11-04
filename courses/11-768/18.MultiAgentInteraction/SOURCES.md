# Interaction 1: Multi-Agent Interaction

- 课程：CMU 11-768；官网条目标识 CMU-10b。
- 官网日期：2026-10-29；讲者 Saujas Vaduguru。
- 材料同步日期：2026-11-04（Asia/Shanghai）。
- [当前官方课表](https://www.cmu-agents.com/#/schedule) · [本次静态课表原件](../../syllabus-snapshots/2026-11-04/cmu/schedule.json) · [完整本地课表](../COURSE_SCHEDULE.md)。

## 主讲义与中文讲解

- [Multi-agent Systems，44 页](lecture-18-multi-agent-systems.pdf)；原文件名保留；Source: https://www.cmu-agents.com/slides/lecture-18-multi-agent-systems.pdf
- SHA-256：`5da3102180a75b0c8ad6c849ef497e6cc165ebcd77b4428ce8a177de6ebdc93c`。响应来源、实际取得时间与页数见 [MATERIALS.json](MATERIALS.json)。
- [完整中文讲解](notes.zh-CN.md)：按讲义三条问题链组织，并给出实际 PDF 页码、阅读版本、推导、工程实现、成本、故障诊断与自测。
- [教学小程序](coordination_lab.py) 与 [执行记录](EXAMPLES.json)；只验证数学算例和字段接收规则，未执行模型、训练或论文基准。

## 指定 Readings

| 阅读 | 本地正文与固定版本 | 原始来源 |
|---|---|---|
| R1 · Improving Factuality and Reasoning in Language Models through Multiagent Debate | [readings/Improving_Factuality_and_Reasoning_in_Language_Models_through_Multiagent_Debate.pdf](readings/Improving_Factuality_and_Reasoning_in_Language_Models_through_Multiagent_Debate.pdf)；2305.14325v1；27 页 | https://arxiv.org/abs/2305.14325 |
| R2 · Multi-Agent Computer Use | [readings/Multi-Agent_Computer_Use.pdf](readings/Multi-Agent_Computer_Use.pdf)；2606.01533v1；42 页 | https://arxiv.org/abs/2606.01533 |
| R3 · Scaling Discovery through Test-Time Communication | [readings/Scaling_Discovery_through_Test-Time_Communication.pdf](readings/Scaling_Discovery_through_Test-Time_Communication.pdf)；2609.21032v1；30 页 | https://arxiv.org/abs/2609.21032 |
| R4 · SWEET-RL: Training Multi-Turn LLM Agents on Collaborative Reasoning Tasks | [readings/SWEET-RL_Training_Multi-Turn_LLM_Agents_on_Collaborative_Reasoning_Tasks.pdf](readings/SWEET-RL_Training_Multi-Turn_LLM_Agents_on_Collaborative_Reasoning_Tasks.pdf)；2503.15478v1；29 页 | https://arxiv.org/abs/2503.15478 |
| R5 · Don’t lie to your friends: Learning what you know from collaborative self-play | [readings/Don_t_lie_to_your_friends_Learning_what_you_know_from_collaborative_self-play.pdf](readings/Don_t_lie_to_your_friends_Learning_what_you_know_from_collaborative_self-play.pdf)；2503.14481v3；25 页 | https://arxiv.org/abs/2503.14481 |
| R6 · Debating with More Persuasive LLMs Leads to More Truthful Answers | [readings/Debating_with_More_Persuasive_LLMs_Leads_to_More_Truthful_Answers.pdf](readings/Debating_with_More_Persuasive_LLMs_Leads_to_More_Truthful_Answers.pdf)；2402.06782v4；72 页 | https://arxiv.org/abs/2402.06782 |

## 官方 References

与指定阅读分开；这些是官网提供的辅助参考，不全部当作逐篇精读或复现实验。MARL 教科书已从官网实际下载端点取得 395 页 PDF，ACL 不确定性论文已取得正式 PDF，未把书籍介绍页或摘要页当作全文。

| 参考资料 | 本地原文 | 版本 / 页数 | 原始来源 |
|---|---|---|---|
| Multi-Agent Reinforcement Learning: Foundations and Modern Approaches | [references/Multi-Agent_Reinforcement_Learning_Foundations_and_Modern_Approaches.pdf](references/Multi-Agent_Reinforcement_Learning_Foundations_and_Modern_Approaches.pdf) | Archived full textbook PDF; see cover for edition / 395 | https://www.marl-book.com/ |
| In-Context Impersonation Reveals Large Language Models’ Strengths and Biases | [references/In-Context_Impersonation_Reveals_Large_Language_Models_Strengths_and_Biases.pdf](references/In-Context_Impersonation_Reveals_Large_Language_Models_Strengths_and_Biases.pdf) | 2305.14930v2 / 27 | https://arxiv.org/abs/2305.14930 |
| ChatDev: Communicative Agents for Software Development | [references/ChatDev_Communicative_Agents_for_Software_Development.pdf](references/ChatDev_Communicative_Agents_for_Software_Development.pdf) | 2307.07924v5 / 13 | https://arxiv.org/abs/2307.07924 |
| Build a personal assistant with subagents | [references/Build_a_personal_assistant_with_subagents.html](references/Build_a_personal_assistant_with_subagents.html) | 网页快照 / — | https://docs.langchain.com/oss/python/langchain/multi-agent/subagents-personal-assistant |
| Recursive Agent Optimization | [references/Recursive_Agent_Optimization.pdf](references/Recursive_Agent_Optimization.pdf) | 2605.06639v1 / 27 | https://arxiv.org/abs/2605.06639 |
| Effective Strategies for Asynchronous Software Engineering Agents | [references/Effective_Strategies_for_Asynchronous_Software_Engineering_Agents.pdf](references/Effective_Strategies_for_Asynchronous_Software_Engineering_Agents.pdf) | 2603.21489v2 / 22 | https://arxiv.org/abs/2603.21489 |
| LLM-Based Multi-Agent Blackboard System for Information Discovery in Data Science | [references/LLM-Based_Multi-Agent_Blackboard_System_for_Information_Discovery_in_Data_Science.pdf](references/LLM-Based_Multi-Agent_Blackboard_System_for_Information_Discovery_in_Data_Science.pdf) | 2510.01285v2 / 44 | https://arxiv.org/abs/2510.01285 |
| Decentralized Multi-Agent Systems with Shared Context | [references/Decentralized_Multi-Agent_Systems_with_Shared_Context.pdf](references/Decentralized_Multi-Agent_Systems_with_Shared_Context.pdf) | 2606.10662v3 / 29 | https://arxiv.org/abs/2606.10662 |
| GitSwarm: Decentralized Compounding Inference | [references/GitSwarm_Decentralized_Compounding_Inference.pdf](references/GitSwarm_Decentralized_Compounding_Inference.pdf) | 2610.04862v1 / 62 | https://arxiv.org/abs/2610.04862 |
| What does it take to build a human-like user simulator? | [references/What_does_it_take_to_build_a_human-like_user_simulator.html](references/What_does_it_take_to_build_a_human-like_user_simulator.html) | 网页快照 / — | https://nickatomlin.github.io/blog/user-simulators-2.html |
| Training Proactive and Personalized LLM Agents | [references/Training_Proactive_and_Personalized_LLM_Agents.pdf](references/Training_Proactive_and_Personalized_LLM_Agents.pdf) | 2511.02208v2 / 23 | https://arxiv.org/abs/2511.02208 |
| One Frozen Simulator Is Not Enough: Simulator Collapse in Multi-Agent RL | [references/One_Frozen_Simulator_Is_Not_Enough_Simulator_Collapse_in_Multi-Agent_RL.pdf](references/One_Frozen_Simulator_Is_Not_Enough_Simulator_Collapse_in_Multi-Agent_RL.pdf) | 2608.12253v2 / 42 | https://arxiv.org/abs/2608.12253 |
| GlossoGen: Emergent Language in Complex Multi-Agent LLM Interactions | [references/GlossoGen_Emergent_Language_in_Complex_Multi-Agent_LLM_Interactions.pdf](references/GlossoGen_Emergent_Language_in_Complex_Multi-Agent_LLM_Interactions.pdf) | 2609.01491v1 / 32 | https://arxiv.org/abs/2609.01491 |
| Brief independent investigation of agents’ behavior, reasoning and collaboration in the OpenAI / Hugging Face hacking incident | [references/Brief_independent_investigation_of_agents_behavior_reasoning_and_collaboration_in_the_OpenAI_Hugging_Face_hacking_incident.html](references/Brief_independent_investigation_of_agents_behavior_reasoning_and_collaboration_in_the_OpenAI_Hugging_Face_hacking_incident.html) | 网页快照 / — | https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/ |
| Magentic Marketplace: An Open-Source Environment for Studying Agentic Markets | [references/Magentic_Marketplace_An_Open-Source_Environment_for_Studying_Agentic_Markets.pdf](references/Magentic_Marketplace_An_Open-Source_Environment_for_Studying_Agentic_Markets.pdf) | 2510.25779v1 / 19 | https://arxiv.org/abs/2510.25779 |
| Generative Agents: Interactive Simulacra of Human Behavior | [references/Generative_Agents_Interactive_Simulacra_of_Human_Behavior.pdf](references/Generative_Agents_Interactive_Simulacra_of_Human_Behavior.pdf) | 2304.03442v2 / 22 | https://arxiv.org/abs/2304.03442 |
| Relying on the Unreliable: The Impact of Language Models’ Reluctance to Express Uncertainty | [references/Relying_on_the_Unreliable_The_Impact_of_Language_Models_Reluctance_to_Express_Uncertainty.pdf](references/Relying_on_the_Unreliable_The_Impact_of_Language_Models_Reluctance_to_Express_Uncertainty.pdf) | ACL 2024 proceedings / 21 | https://aclanthology.org/2024.acl-long.198/ |

## 来源、复用与校验

[REFERENCES.json](REFERENCES.json) 逐项记录 role、URL、下载端点、正文路径、实际版本与 SHA-256。复用仓库既有材料时记 `reused_from` 和复用时间，不将其当作新下载。网页保存正文快照，未对原始论文做文本转换。

[课程 REVIEW.json](../REVIEW.json) 绑定最终笔记与来源；自动验证不代替原文精读。未复现 MACU、CAID、DeLM、GitSwarm、RAO、SWEET-RL、CSP、PPP、用户模拟器训练、市场或人类实验。

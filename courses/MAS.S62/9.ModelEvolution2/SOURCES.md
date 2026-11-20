# Week 9 — Model evolution 2

- Date: 2026-11-04
- Source: https://mit-mi.github.io/how2ai-course/fall2026/schedule/
- 资料归档日期：2026-11-20；最新日历见[完整课表](../COURSE_SCHEDULE.md)。
- 目录编号保持稳定；当前官方 Week、日期单独记录，原 PDF 内的 Lecture 编号和文件名保持原样。

## Topics（归档快照）

- RL in practice
- Self-play approaches

## Lecture, guest lectures and tutorials（归档快照）

- [lec6 - rl in practice.pdf](tutorials/lec6%20-%20rl%20in%20practice.pdf) — tutorial
  - 内容：Tutorial — RL and Self-Distillation in Practice
  - Source: https://mit-mi.github.io/how2ai-course/fall2026/schedule/lec6 - rl in practice.pdf
  - SHA256: `746f0bcca12b0ffb04c2f16dc5f6a32b3e358065eb54142c3f5418a225f88080`
  - PDF pages: 19
- [lec7 - self play.pdf](slides/lec7%20-%20self%20play.pdf) — lecture
  - 内容：LLM Self-Play (Alex Wilf, 2026-11-04)
  - Source: https://mit-mi.github.io/how2ai-course/fall2026/schedule/lec7 - self play.pdf
  - SHA256: `71d7831ac65721a59709c08111dd0f06c3294f54d4333554482fb7d696fbede2`
  - PDF pages: 63

## Assigned readings（归档快照）

- R01: [Absolute Zero: Reinforced Self-play Reasoning with Zero Data](readings/Absolute_Zero_Reinforced_Self-play_Reasoning_with_Zero_Data.pdf)
  - Source: https://arxiv.org/abs/2505.03335
  - PDF version: 2505.03335v3
- R02: [R-Zero: Self-Evolving Reasoning LLM from Zero Data](readings/R-Zero_Self-Evolving_Reasoning_LLM_from_Zero_Data.pdf)
  - Source: https://arxiv.org/abs/2508.05004
  - PDF version: 2508.05004v4
- R03: [Propose, Solve, Verify: Self-Play Through Formal Verification](readings/Propose_Solve_Verify_Self-Play_Through_Formal_Verification.pdf)
  - Source: https://arxiv.org/abs/2512.18160
  - PDF version: 2512.18160v1

## References and local study guide

- [讲义内嵌链接及其 PDF 页码](../LECTURE_LINKS.json)；JSON 按 week、pdf、page 记录，视频和通用网站入口仅作来源导航。
- [On-Policy Distillation of Language Models: Learning from Self-Generated Mistakes](references/On-Policy_Distillation_of_Language_Models_Learning_from_Self-Generated_Mistakes.pdf)
  - Source: https://arxiv.org/abs/2306.13649
- [RL's Razor: Why Online Reinforcement Learning Forgets Less](references/RL_s_Razor_Why_Online_Reinforcement_Learning_Forgets_Less.pdf)
  - Source: https://arxiv.org/abs/2509.04259
- [Self-Distillation Enables Continual Learning](references/Self-Distillation_Enables_Continual_Learning.pdf)
  - Source: https://arxiv.org/abs/2601.19897
- [OpenClaw-RL: Train Any Agent Simply by Talking](references/OpenClaw-RL_Train_Any_Agent_Simply_by_Talking.pdf)
  - Source: https://arxiv.org/abs/2603.10165
- [Proximal Policy Optimization Algorithms](references/Proximal_Policy_Optimization_Algorithms.pdf)
  - Source: https://arxiv.org/abs/1707.06347
- [DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models](references/DeepSeekMath_Pushing_the_Limits_of_Mathematical_Reasoning_in_Open_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2402.03300
- [Self-Distilled Reasoner: On-Policy Self-Distillation for Large Language Models](references/Self-Distilled_Reasoner_On-Policy_Self-Distillation_for_Large_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2601.18734
- [Reinforcement Learning via Self-Distillation](references/Reinforcement_Learning_via_Self-Distillation.pdf)
  - Source: https://arxiv.org/pdf/2601.20802
- [verl verl/trainer/ppo/v1/trainer_base.py @ ddf7007](references/verl-ddf7007/trainer_base.py)
  - Source: https://raw.githubusercontent.com/verl-project/verl/ddf7007/verl/trainer/ppo/v1/trainer_base.py
- [verl verl/trainer/ppo/core_algos.py @ ddf7007](references/verl-ddf7007/core_algos.py)
  - Source: https://raw.githubusercontent.com/verl-project/verl/ddf7007/verl/trainer/ppo/core_algos.py
- [verl examples/grpo_trainer/run_qwen3_8b_fsdp.sh @ ddf7007](references/verl-ddf7007/run_qwen3_8b_fsdp.sh)
  - Source: https://raw.githubusercontent.com/verl-project/verl/ddf7007/examples/grpo_trainer/run_qwen3_8b_fsdp.sh
- [High-Dimensional Continuous Control Using Generalized Advantage Estimation](references/High-Dimensional_Continuous_Control_Using_Generalized_Advantage_Estimation.pdf)
  - Source: https://arxiv.org/abs/1506.02438
- [DAPO: An Open-Source LLM Reinforcement Learning System at Scale](references/DAPO_An_Open-Source_LLM_Reinforcement_Learning_System_at_Scale.pdf)
  - Source: https://arxiv.org/abs/2503.14476
- [Efficient Memory Management for Large Language Model Serving with PagedAttention](references/Efficient_Memory_Management_for_Large_Language_Model_Serving_with_PagedAttention.pdf)
  - Source: https://arxiv.org/abs/2309.06180
- [HybridFlow: A Flexible and Efficient RLHF Framework](references/HybridFlow_A_Flexible_and_Efficient_RLHF_Framework.pdf)
  - Source: https://arxiv.org/pdf/2409.19256
- [PyTorch FSDP: Experiences on Scaling Fully Sharded Data Parallel](references/PyTorch_FSDP_Experiences_on_Scaling_Fully_Sharded_Data_Parallel.pdf)
  - Source: https://arxiv.org/pdf/2304.11277
- [ZeRO: Memory Optimizations Toward Training Trillion Parameter Models](references/ZeRO_Memory_Optimizations_Toward_Training_Trillion_Parameter_Models.pdf)
  - Source: https://arxiv.org/pdf/1910.02054
- [On-Policy Distillation](references/On-Policy_Distillation.html)
  - Source: https://thinkingmachines.ai/blog/on-policy-distillation/
- [verl trainer_sync.py @ ddf7007](references/verl-ddf7007/trainer_sync.py)
  - Source: https://raw.githubusercontent.com/verl-project/verl/ddf7007/verl/trainer/ppo/v1/trainer_sync.py
- [reef: Continual Self-Improving Agents](references/reef/b373872e22d6581d3cd53a6077c9180581d599b7/README.md)
  - Source: https://raw.githubusercontent.com/Human-Agent-Society/reef/b373872e22d6581d3cd53a6077c9180581d599b7/README.md
- [Group Relative Policy Optimization (GRPO) — verl documentation](references/Group_Relative_Policy_Optimization_GRPO_verl_documentation.html)
  - Source: https://verl.readthedocs.io/en/latest/algo/grpo.html
- [Quickstart: PPO training on GSM8K dataset — verl documentation](references/Quickstart_PPO_training_on_GSM8K_dataset_verl_documentation.html)
  - Source: https://verl.readthedocs.io/en/latest/start/quickstart.html
- [OpenClaw-RL1](references/OpenClaw-RL1.html)
  - Source: https://yinjjiew.github.io/projects/openclawrl1/
- [lec6 - training.pdf — Model Evolution I lecture](../7.ModelEvolution1/slides/lec6%20-%20training.pdf)
  - Source: https://mit-mi.github.io/how2ai-course/fall2026/schedule/lec6%20-%20training.pdf
- [Language Self-Play For Data-Free Training](references/Language_Self-Play_For_Data-Free_Training.pdf)
  - Source: https://arxiv.org/abs/2509.07414
- [Absolute Zero: Reinforced Self-play Reasoning with Zero Data](readings/Absolute_Zero_Reinforced_Self-play_Reasoning_with_Zero_Data.pdf)
  - Source: https://arxiv.org/abs/2505.03335
- [R-Zero: Self-Evolving Reasoning LLM from Zero Data](readings/R-Zero_Self-Evolving_Reasoning_LLM_from_Zero_Data.pdf)
  - Source: https://arxiv.org/abs/2508.05004
- [STP: Self-play LLM Theorem Provers with Iterative Conjecturing and Proving](references/STP_Self-play_LLM_Theorem_Provers_with_Iterative_Conjecturing_and_Proving.pdf)
  - Source: https://arxiv.org/abs/2502.00212
- [Self-Challenging Language Model Agents](references/Self-Challenging_Language_Model_Agents.pdf)
  - Source: https://arxiv.org/abs/2506.01716
- [Skill Self-Play: Pushing the Frontier of LLM Capability with Co-Evolving Skills](references/Skill_Self-Play_Pushing_the_Frontier_of_LLM_Capability_with_Co-Evolving_Skills.pdf)
  - Source: https://arxiv.org/abs/2607.22529
- [Scaling Self-Play with Self-Guidance](references/Scaling_Self-Play_with_Self-Guidance.pdf)
  - Source: https://arxiv.org/abs/2604.20209
- [LADDER: Self-Improving LLMs Through Recursive Problem Decomposition](references/LADDER_Self-Improving_LLMs_Through_Recursive_Problem_Decomposition.pdf)
  - Source: https://arxiv.org/abs/2503.00735
- [Self-Adapting Language Models](references/Self-Adapting_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2506.10943
- [CPMobius: Iterative Coach-Player Reasoning for Data-Free Reinforcement Learning](references/CPMobius_Iterative_Coach-Player_Reasoning_for_Data-Free_Reinforcement_Learning.pdf)
  - Source: https://arxiv.org/abs/2602.02979
- [CompassPlay: Rewarding the Proposer for Where It Moves the Solver](references/CompassPlay_Rewarding_the_Proposer_for_Where_It_Moves_the_Solver.pdf)
  - Source: https://arxiv.org/abs/2609.32228
- [Self-Play Pretraining with Zero Data](references/Self-Play_Pretraining_with_Zero_Data.pdf)
  - Source: https://arxiv.org/abs/2609.30063
- [Self-Verification Provably Prevents Model Collapse in Recursive Synthetic Training](references/Self-Verification_Provably_Prevents_Model_Collapse_in_Recursive_Synthetic_Training.pdf)
  - Source: https://papers.neurips.cc/paper_files/paper/2025/hash/3380e8116452e0efbf36f35d95e88c94-Abstract-Conference.html
- [Self-Improvement in Language Models: The Sharpening Mechanism](references/Self-Improvement_in_Language_Models_The_Sharpening_Mechanism.pdf)
  - Source: https://arxiv.org/abs/2412.01951
- [Teaching Models to Teach Themselves: Reasoning at the Edge of Learnability](references/Teaching_Models_to_Teach_Themselves_Reasoning_at_the_Edge_of_Learnability.pdf)
  - Source: https://arxiv.org/abs/2601.18778
- [Goedel-Code-Prover: Hierarchical Proof Search for Open State-of-the-Art Code Verification](references/Goedel-Code-Prover_Hierarchical_Proof_Search_for_Open_State-of-the-Art_Code_Verification.pdf)
  - Source: https://arxiv.org/abs/2603.19329
- [Mind the Gap: Examining the Self-Improvement Capabilities of Large Language Models](references/Mind_the_Gap_Examining_the_Self-Improvement_Capabilities_of_Large_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2412.02674
- [T1: Tool-integrated Self-verification for Test-time Compute Scaling in Small Language Models](references/T1_Tool-integrated_Self-verification_for_Test-time_Compute_Scaling_in_Small_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2504.04718
- [完整中文课程讲解](notes.zh-CN.md)

# Week 9 — Model evolution 2

- Date: 2026-11-04
- Source: https://mit-mi.github.io/how2ai-course/fall2026/schedule/
- 资料归档日期：2026-11-13；最新日历见[完整课表](../COURSE_SCHEDULE.md)。
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
- [完整中文课程讲解](notes.zh-CN.md)

# Week 7 — Model evolution 1

- Date: 2026-10-21
- Source: https://mit-mi.github.io/how2ai-course/fall2026/schedule/
- 资料归档日期：2026-11-13；最新日历见[完整课表](../COURSE_SCHEDULE.md)。
- 目录编号保持稳定；当前官方 Week、日期单独记录，原 PDF 内的 Lecture 编号和文件名保持原样。

## Topics（归档快照）

- Reinforcement learning
- Distillation
- Test-time training

## Lecture, guest lectures and tutorials（归档快照）

- [lec6 - training.pdf](slides/lec6%20-%20training.pdf) — lecture
  - 内容：Lecture 6 — Test-time Training
  - Source: https://mit-mi.github.io/how2ai-course/fall2026/schedule/lec6 - training.pdf
  - SHA256: `3bf55f8f20a4e6f0273a4bd69513e1fc0beaf2b63aab09c1762455301194ffd0`
  - PDF pages: 45
- [model_guest.pdf](slides/model_guest.pdf) — guest
  - 内容：Guest — Continual Learning via Self-Distillation
  - Source: https://mit-mi.github.io/how2ai-course/fall2026/schedule/model_guest.pdf
  - SHA256: `8fded4301bedef9c5afa43c97d9ae998add9bddcaa3fb3b2081b90886e729ab1`
  - PDF pages: 51

## Assigned readings（归档快照）

- R01: [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](readings/DeepSeek-R1_Incentivizing_Reasoning_Capability_in_LLMs_via_Reinforcement_Learning.pdf)
  - Source: https://arxiv.org/abs/2501.12948
  - PDF version: 2501.12948v2
- R02: [On-Policy Distillation of Language Models: Learning from Self-Generated Mistakes](readings/On-Policy_Distillation_of_Language_Models_Learning_from_Self-Generated_Mistakes.pdf)
  - Source: https://arxiv.org/abs/2306.13649
  - PDF version: 2306.13649v3
- R03: [TTRL: Test-Time Reinforcement Learning](readings/TTRL_Test-Time_Reinforcement_Learning.pdf)
  - Source: https://arxiv.org/abs/2504.16084
  - PDF version: 2504.16084v3
- R04: [Self-Rewarding Language Models](readings/Self-Rewarding_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2401.10020
  - PDF version: 2401.10020v3
- R05: [s1: Simple Test-Time Scaling](readings/s1_Simple_Test-Time_Scaling.pdf)
  - Source: https://arxiv.org/abs/2501.19393
  - PDF version: 2501.19393v3
- R06: [Does Reinforcement Learning Really Incentivize Reasoning Capacity in LLMs Beyond the Base Model?](readings/Does_Reinforcement_Learning_Really_Incentivize_Reasoning_Capacity_in_LLMs_Beyond_the_Base_Model.pdf)
  - Source: https://arxiv.org/abs/2504.13837
  - PDF version: 2504.13837v5
- R07: [Understanding R1-Zero-Like Training: A Critical Perspective](readings/Understanding_R1-Zero-Like_Training_A_Critical_Perspective.pdf)
  - Source: https://arxiv.org/abs/2503.20783
  - PDF version: 2503.20783v2
- R08: [RL's Razor: Why Online Reinforcement Learning Forgets Less](readings/RL_s_Razor_Why_Online_Reinforcement_Learning_Forgets_Less.pdf)
  - Source: https://arxiv.org/abs/2509.04259
  - PDF version: 2509.04259v1
- R09: [Self-Distilled Reasoner: On-Policy Self-Distillation for Large Language Models](readings/Self-Distilled_Reasoner_On-Policy_Self-Distillation_for_Large_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2601.18734
  - PDF version: 2601.18734v3
- R10: [Reinforcement Learning via Self-Distillation](readings/Reinforcement_Learning_via_Self-Distillation.pdf)
  - Source: https://arxiv.org/abs/2601.20802
  - PDF version: 2601.20802v2
- R11: [Scaling Test-Time Compute Without Verification or RL is Suboptimal](readings/Scaling_Test-Time_Compute_Without_Verification_or_RL_is_Suboptimal.pdf)
  - Source: https://arxiv.org/abs/2502.12118
  - PDF version: 2502.12118v2

## 旧讲解绑定版本（保留原引用）

- [Tutorial — RL and Self-Distillation in Practice](../site/versions/a9f58ecf4b22164b10315fa24f4f06aa8f955799b167c56b9f26e1fd81342d38/lec6%20-%20rl%20in%20practice.pdf)：旧版 15 页，SHA256 `a9f58ecf4b22164b10315fa24f4f06aa8f955799b167c56b9f26e1fd81342d38`。当前新版归属W9；本周旧讲解未修改，内容/页码复核延期，见 REVIEW.json。
  - [旧讲解原链接](tutorials/lec6%20-%20rl%20in%20practice.pdf)；保留旧字节，不替换为新版。

## References and local study guide

- [讲义内嵌链接及其 PDF 页码](../LECTURE_LINKS.json)；JSON 按 week、pdf、page 记录，视频和通用网站入口仅作来源导航。
- [On-Policy Distillation of Language Models: Learning from Self-Generated Mistakes](references/On-Policy_Distillation_of_Language_Models_Learning_from_Self-Generated_Mistakes.pdf)
  - Source: https://arxiv.org/abs/2306.13649
- [RL's Razor: Why Online Reinforcement Learning Forgets Less](references/RL_s_Razor_Why_Online_Reinforcement_Learning_Forgets_Less.pdf)
  - Source: https://arxiv.org/abs/2509.04259
- [Self-Distillation Enables Continual Learning](references/Self-Distillation_Enables_Continual_Learning.pdf)
  - Source: https://arxiv.org/abs/2601.19897
- [TTRL: Test-Time Reinforcement Learning](references/TTRL_Test-Time_Reinforcement_Learning.pdf)
  - Source: https://arxiv.org/abs/2504.16084
- [OpenClaw-RL: Train Any Agent Simply by Talking](references/OpenClaw-RL_Train_Any_Agent_Simply_by_Talking.pdf)
  - Source: https://arxiv.org/abs/2603.10165
- [Learning to Discover at Test Time](references/Learning_to_Discover_at_Test_Time.pdf)
  - Source: https://arxiv.org/abs/2601.16175
- [Proximal Policy Optimization Algorithms](references/Proximal_Policy_Optimization_Algorithms.pdf)
  - Source: https://arxiv.org/abs/1707.06347
- [DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models](references/DeepSeekMath_Pushing_the_Limits_of_Mathematical_Reasoning_in_Open_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2402.03300
- [Direct Preference Optimization: Your Language Model is Secretly a Reward Model](references/Direct_Preference_Optimization_Your_Language_Model_is_Secretly_a_Reward_Model.pdf)
  - Source: https://arxiv.org/abs/2305.18290
- [Self-Distilled Reasoner: On-Policy Self-Distillation for Large Language Models](references/Self-Distilled_Reasoner_On-Policy_Self-Distillation_for_Large_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2601.18734
- [The Surprising Effectiveness of Test-Time Training for Few-Shot Learning](references/The_Surprising_Effectiveness_of_Test-Time_Training_for_Few-Shot_Learning.pdf)
  - Source: https://ekinakyurek.github.io/papers/ttt.pdf
- [Reinforcement Learning via Self-Distillation](references/Reinforcement_Learning_via_Self-Distillation.pdf)
  - Source: https://arxiv.org/pdf/2601.20802
- [Evolving in Thought Space: Training a Small Model at Test Time Unlocks Better Discoveries](references/Evolving_in_Thought_Space_Training_a_Small_Model_at_Test_Time_Unlocks_Better_Discoveries.pdf)
  - Source: https://arxiv.org/pdf/2610.06269
- [verl verl/trainer/ppo/v1/trainer_base.py @ ddf7007](references/verl-ddf7007/trainer_base.py)
  - Source: https://raw.githubusercontent.com/verl-project/verl/ddf7007/verl/trainer/ppo/v1/trainer_base.py
- [verl verl/trainer/ppo/core_algos.py @ ddf7007](references/verl-ddf7007/core_algos.py)
  - Source: https://raw.githubusercontent.com/verl-project/verl/ddf7007/verl/trainer/ppo/core_algos.py
- [verl examples/grpo_trainer/run_qwen3_8b_fsdp.sh @ ddf7007](references/verl-ddf7007/run_qwen3_8b_fsdp.sh)
  - Source: https://raw.githubusercontent.com/verl-project/verl/ddf7007/examples/grpo_trainer/run_qwen3_8b_fsdp.sh
- [旧版中文讲解（待复核）](notes.zh-CN.md)；本轮只同步资料，旧版来源绑定及延期事项见 [REVIEW.json](../REVIEW.json)。

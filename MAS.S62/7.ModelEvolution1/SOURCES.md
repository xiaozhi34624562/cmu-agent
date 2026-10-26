# Week 7 — Model evolution 1

- Date: 2026-10-21
- Source: https://mit-mi.github.io/how2ai-course/fall2026/schedule/
- 编号采用官网 Week；原 PDF 内的 Lecture 编号和文件名保持原样。

## Topics

- Reinforcement learning
- Distillation
- Test-time training

## Lecture, guest lectures and tutorials

- [lec6 - training.pdf](slides/lec6%20-%20training.pdf) — lecture
  - 内容：Lecture 6 — Test-time Training
  - Source: https://mit-mi.github.io/how2ai-course/fall2026/schedule/lec6 - training.pdf
  - SHA256: `3bf55f8f20a4e6f0273a4bd69513e1fc0beaf2b63aab09c1762455301194ffd0`
  - PDF pages: 45
- [lec6 - rl in practice.pdf](tutorials/lec6%20-%20rl%20in%20practice.pdf) — tutorial
  - 内容：Tutorial — RL and Self-Distillation (pp.1–2: guest introduction)
  - Source: https://mit-mi.github.io/how2ai-course/fall2026/schedule/lec6 - rl in practice.pdf
  - SHA256: `a9f58ecf4b22164b10315fa24f4f06aa8f955799b167c56b9f26e1fd81342d38`
  - PDF pages: 15
- [model_guest.pdf](slides/model_guest.pdf) — guest
  - 内容：Guest — Continual Learning via Self-Distillation
  - Source: https://mit-mi.github.io/how2ai-course/fall2026/schedule/model_guest.pdf
  - SHA256: `8fded4301bedef9c5afa43c97d9ae998add9bddcaa3fb3b2081b90886e729ab1`
  - PDF pages: 51

## Assigned readings

- 官网课表没有单独列出本周阅读；讲义内引用及补充材料见下方 References。

## References and local study guide

- [讲义内嵌链接及其 PDF 页码](../LECTURE_LINKS.json)；JSON 按 week、pdf、page 记录，视频和通用网站入口仅作来源导航。
- [GKD](references/2306.13649.pdf)
  - Source: https://arxiv.org/abs/2306.13649
- [RLs_Razor](references/2509.04259.pdf)
  - Source: https://arxiv.org/abs/2509.04259
- [SDFT](references/2601.19897.pdf)
  - Source: https://arxiv.org/abs/2601.19897
- [TTRL](references/2504.16084.pdf)
  - Source: https://arxiv.org/abs/2504.16084
- [OpenClaw_RL](references/2603.10165.pdf)
  - Source: https://arxiv.org/abs/2603.10165
- [TTT_Discover](references/2601.16175.pdf)
  - Source: https://arxiv.org/abs/2601.16175
- [PPO](references/1707.06347.pdf)
  - Source: https://arxiv.org/abs/1707.06347
- [DeepSeekMath](references/2402.03300.pdf)
  - Source: https://arxiv.org/abs/2402.03300
- [DPO](references/2305.18290.pdf)
  - Source: https://arxiv.org/abs/2305.18290
- [OPSD](references/2601.18734.pdf)
  - Source: https://arxiv.org/abs/2601.18734
- [TTT_FewShot](references/ttt.pdf)
  - Source: https://ekinakyurek.github.io/papers/ttt.pdf
- [SDPO](references/2601.20802.pdf)
  - Source: https://arxiv.org/pdf/2601.20802
- [Guidance_TTT](references/2610.06269.pdf)
  - Source: https://arxiv.org/pdf/2610.06269
- [verl verl/trainer/ppo/v1/trainer_base.py @ ddf7007](references/verl-ddf7007/trainer_base.py)
  - Source: https://raw.githubusercontent.com/verl-project/verl/ddf7007/verl/trainer/ppo/v1/trainer_base.py
- [verl verl/trainer/ppo/core_algos.py @ ddf7007](references/verl-ddf7007/core_algos.py)
  - Source: https://raw.githubusercontent.com/verl-project/verl/ddf7007/verl/trainer/ppo/core_algos.py
- [verl examples/grpo_trainer/run_qwen3_8b_fsdp.sh @ ddf7007](references/verl-ddf7007/run_qwen3_8b_fsdp.sh)
  - Source: https://raw.githubusercontent.com/verl-project/verl/ddf7007/examples/grpo_trainer/run_qwen3_8b_fsdp.sh
- [完整中文课程讲解](notes.zh-CN.md)

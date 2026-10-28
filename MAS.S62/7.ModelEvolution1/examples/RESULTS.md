# 教学实验运行记录

- 运行日期：2026-10-28（Asia/Shanghai）。
- 命令：`python3 MAS.S62/7.ModelEvolution1/examples/loss_contracts.py`。
- 解释器：Python 3.11.10；依赖：标准库。
- 返回码：0。
- 验证范围：奖励到单参数更新、动作无关基线的期望、交叉熵与 DPO 算术、组方差分母、LoRA 参数量；固定教师的 KL 数值及有限差分、两步四序列模型的局部/完整梯度、PPO 代理目标、零方差优势和批次算术。没有训练模型、没有使用 GPU，不检验论文任务收益。

## 实际标准输出

```json
{
  "scope": "one-state and two-step fixed-teacher arithmetic; no model training",
  "prerequisites": {
    "sampled_success_probability_before": 0.25,
    "sampled_success_probability_after": 0.26432436798156755,
    "sampled_success_score_gradient": 0.7500000000160155,
    "expected_gradient_with_and_without_baseline": 0.1875,
    "target_cross_entropy_before_after": [
      1.3862943611198906,
      0.6931471805599453
    ],
    "group_population_std_advantages": [
      1.7320508075688774,
      -0.5773502691896258,
      -0.5773502691896258,
      -0.5773502691896258
    ],
    "group_sample_std_advantages": [
      1.5,
      -0.5,
      -0.5,
      -0.5
    ],
    "dpo_loss_before_after": [
      0.6931471805599453,
      0.2876820724517809
    ],
    "lora_increment_parameters": 16384
  },
  "student": [
    0.7,
    0.3
  ],
  "teacher": [
    0.4,
    0.6
  ],
  "KL_student_teacher": 0.18378689738681217,
  "KL_teacher_student": 0.19204199316179815,
  "reverse_KL_logit_gradient": [
    0.2630802233768992,
    -0.2630802233768992
  ],
  "forward_KL_logit_gradient": [
    0.30000000000585114,
    -0.30000000000585114
  ],
  "positive_advantage_upper_clip": 1.2,
  "negative_advantage_lower_clip": -0.8,
  "negative_advantage_wrong_direction": -1.4,
  "zero_variance_group": [
    0.0,
    0.0,
    0.0,
    0.0
  ],
  "two_step_sequence_KL": {
    "sequence_KL": 0.25541281188299536,
    "local_first_step_gradient": [
      0.0,
      0.0
    ],
    "full_sequence_gradient_finite_difference": [
      0.1277064059418409,
      -0.1277064059418409
    ],
    "causal_return_to_go_gradient": [
      0.12770640594149768,
      -0.12770640594149768
    ]
  },
  "batch": {
    "responses": 5120,
    "optimizer_steps": 4,
    "per_dp_worker": 160,
    "micro_accumulation": 40
  },
  "assertions": "passed"
}
```

输出是本地确定性教学实验的记录，不是课程论文中的模型实验结果。

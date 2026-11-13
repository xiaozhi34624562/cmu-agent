"""CPU-only arithmetic lab for Lecture 6; no model, GPU, or untrusted code execution.

Run from this directory: python3 learning_signals.py
The JSON result is deterministic apart from the recorded Python version.
"""

import hashlib
import json
import math
import platform
from collections import Counter
from pathlib import Path


def sum_even_buggy(n):
    return sum(i for i in range(n) if i % 2 == 0)


def sum_even_correct(n):
    return sum(i for i in range(n + 1) if i % 2 == 0)


def group_advantages(rewards, correction=0):
    mean = sum(rewards) / len(rewards)
    variance = sum((r - mean) ** 2 for r in rewards) / (len(rewards) - correction)
    std = math.sqrt(variance)
    return [(r - mean) / (std + 1e-6) for r in rewards]


def ppo_surrogate(ratio, advantage, epsilon=0.2):
    clipped = max(1 - epsilon, min(1 + epsilon, ratio))
    return min(ratio * advantage, clipped * advantage)


def softmax(logits):
    values = [math.exp(z - max(logits)) for z in logits]
    return [v / sum(values) for v in values]


def reverse_kl(logits, teacher):
    student = softmax(logits)
    return sum(p * math.log(p / q) for p, q in zip(student, teacher))


def finite_difference(logits, teacher, step=1e-5):
    result = []
    for i in range(len(logits)):
        plus, minus = list(logits), list(logits)
        plus[i] += step
        minus[i] -= step
        result.append((reverse_kl(plus, teacher) - reverse_kl(minus, teacher)) / (2 * step))
    return result


def main():
    cases = [(0, 0), (1, 0), (2, 2), (4, 6), (5, 6)]
    function_checks = [
        {"n": n, "expected": expected, "buggy": sum_even_buggy(n), "correct": sum_even_correct(n)}
        for n, expected in cases
    ]
    assert all(row["correct"] == row["expected"] for row in function_checks)
    assert sum_even_buggy(4) == 2

    logits = [0.0, 0.0]
    student, teacher = softmax(logits), [0.8, 0.2]
    advantage = [math.log(q / p) for p, q in zip(student, teacher)]
    mean_advantage = sum(p * a for p, a in zip(student, advantage))
    # Gradient of fixed-prefix KL wrt student logits. Teacher is constant.
    analytical = [-p * (a - mean_advantage) for p, a in zip(student, advantage)]
    numerical = finite_difference(logits, teacher)
    max_error = max(abs(a - b) for a, b in zip(analytical, numerical))
    assert max_error < 1e-8
    after = [z - 0.1 * g for z, g in zip(logits, analytical)]
    assert reverse_kl(after, teacher) < reverse_kl(logits, teacher)

    clipping = [
        {"ratio": r, "advantage": a, "surrogate": ppo_surrogate(r, a)}
        for r, a in [(1.5, 1), (0.5, 1), (1.5, -1), (0.5, -1)]
    ]
    assert [c["surrogate"] for c in clipping] == [1.2, 0.5, -1.5, -0.8]
    rewards = [1, 0, 0, 1]
    assert group_advantages([0, 0, 0, 0]) == [0.0] * 4

    prompts, rollouts, mini_prompts, dp, micro = 1024, 5, 256, 8, 4
    assert mini_prompts * rollouts % (dp * micro) == 0
    # Illustrative GQA configuration; not a query of installed model metadata.
    kv_bytes_per_token = 2 * 36 * 8 * 128 * 2
    proposal = [
        {"p": p, "azr": 0 if p == 0 else 1 - p, "r_zero_before_penalty": 1 - 2 * abs(p - 0.5)}
        for p in [0.0, 0.125, 0.5, 1.0]
    ]
    candidate_answers = [4, 4, 4, 4, 2]
    majority_answer, votes = Counter(candidate_answers).most_common(1)[0]
    verified_answer = sum_even_correct(2)
    assert majority_answer != verified_answer
    result = {
        "scope": "Deterministic CPU arithmetic and hand-written function checks; no LLM training or paper reproduction.",
        "python": platform.python_version(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "function_checks": function_checks,
        "group_rewards": rewards,
        "population_std_advantages": group_advantages(rewards),
        "sample_std_advantages": group_advantages(rewards, correction=1),
        "all_equal_advantages": group_advantages([0, 0, 0, 0]),
        "ppo_clipping": clipping,
        "fixed_prefix_reverse_kl": {
            "student": student, "teacher": teacher, "token_advantages": advantage,
            "before": reverse_kl(logits, teacher), "gradient": analytical,
            "finite_difference_gradient": numerical, "max_error": max_error,
            "after_one_gradient_step": reverse_kl(after, teacher),
            "student_after": softmax(after),
        },
        "batch_accounting": {
            "responses_per_rollout_batch": prompts * rollouts,
            "optimizer_steps_per_rollout_batch": prompts // mini_prompts,
            "responses_per_optimizer_step": mini_prompts * rollouts,
            "responses_per_dp_worker": mini_prompts * rollouts // dp,
            "accumulations_per_optimizer_step": mini_prompts * rollouts // dp // micro,
        },
        "illustrative_memory_decimal_GB": {
            "weights_8_2B_at_2_bytes": 8.2e9 * 2 / 1e9,
            "training_states_8_2B_at_16_bytes": 8.2e9 * 16 / 1e9,
            "ideal_training_states_divided_by_8": 8.2e9 * 16 / 8 / 1e9,
            "kv_bytes_per_token": kv_bytes_per_token,
            "kv_100_sequences_of_4096_tokens": 100 * 4096 * kv_bytes_per_token / 1e9,
        },
        "proposer_reward_shapes": proposal,
        "wrong_majority_example": {
            "task": "sum_even(2)", "candidate_answers": candidate_answers,
            "majority_answer": majority_answer, "consistency": votes / len(candidate_answers),
            "verified_answer": verified_answer,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()

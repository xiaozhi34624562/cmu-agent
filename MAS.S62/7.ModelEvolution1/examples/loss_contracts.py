#!/usr/bin/env python3
"""Check one-state and two-step probability arithmetic, not LM training.

Pure Python finite differences hold the teacher fixed. A four-sequence model
checks local versus complete sequence KL gradients; it is not a language model
training implementation or any paper's training recipe.
"""

import json
import math


def softmax(logits):
    maximum = max(logits)
    terms = [math.exp(value - maximum) for value in logits]
    normalizer = sum(terms)
    return [value / normalizer for value in terms]


def kl(first, second):
    assert len(first) == len(second)
    assert all(value > 0 for value in first + second)
    assert math.isclose(sum(first), 1) and math.isclose(sum(second), 1)
    return sum(p * math.log(p / q) for p, q in zip(first, second))


def finite_difference(function, logits, step=1e-5):
    gradient = []
    for position in range(len(logits)):
        higher, lower = logits.copy(), logits.copy()
        higher[position] += step
        lower[position] -= step
        gradient.append((function(higher) - function(lower)) / (2 * step))
    return gradient


def clipped_objective(ratio, advantage, epsilon=0.2):
    clipped = min(max(ratio, 1 - epsilon), 1 + epsilon)
    return min(ratio * advantage, clipped * advantage)


def group_advantage(rewards, epsilon=1e-8, correction=0):
    """Teaching default is population std; correction=1 uses sample std."""
    assert 0 <= correction < len(rewards)
    average = sum(rewards) / len(rewards)
    std = math.sqrt(sum((r - average) ** 2 for r in rewards)
                    / (len(rewards) - correction))
    return [(reward - average) / (std + epsilon) for reward in rewards]


def prerequisite_checks():
    """Connect a sampled reward to a scalar update, not a training claim."""
    sigmoid = lambda value: 1 / (1 + math.exp(-value))
    score = math.log(1 / 3)
    probability = sigmoid(score)
    sampled_success_gradient = 1 - probability
    next_probability = sigmoid(score + 0.1 * sampled_success_gradient)
    numeric_gradient = finite_difference(
        lambda values: math.log(sigmoid(values[0])), [score]
    )[0]
    assert math.isclose(probability, 0.25)
    assert math.isclose(numeric_gradient, sampled_success_gradient, abs_tol=1e-9)
    assert 0.264 < next_probability < 0.265
    # Both outcomes are enumerated: R(success)=1 and R(failure)=0.
    expected_without_baseline = probability * sampled_success_gradient
    baseline = 0.25
    expected_with_baseline = (
        probability * (1 - baseline) * (1 - probability)
        + (1 - probability) * (0 - baseline) * (-probability)
    )
    assert math.isclose(expected_without_baseline, expected_with_baseline)
    population = group_advantage([1, 0, 0, 0], epsilon=0)
    sample = group_advantage([1, 0, 0, 0], epsilon=0, correction=1)
    assert math.isclose(population[0], math.sqrt(3))
    assert sample == [1.5, -0.5, -0.5, -0.5]
    dpo_start, dpo_after = -math.log(sigmoid(0)), -math.log(sigmoid(math.log(3)))
    assert math.isclose(dpo_start, math.log(2))
    assert math.isclose(dpo_after, -math.log(0.75))
    assert softmax([math.log(3), 0]) == [0.75, 0.25]
    assert 1024 * 8 + 8 * 1024 == 1024 * 1024 // 64
    return {
        "sampled_success_probability_before": probability,
        "sampled_success_probability_after": next_probability,
        "sampled_success_score_gradient": numeric_gradient,
        "expected_gradient_with_and_without_baseline": expected_with_baseline,
        "target_cross_entropy_before_after": [-math.log(0.25), -math.log(0.5)],
        "group_population_std_advantages": population,
        "group_sample_std_advantages": sample,
        "dpo_loss_before_after": [dpo_start, dpo_after],
        "lora_increment_parameters": 1024 * 8 + 8 * 1024,
    }


def two_step_sequence_check():
    """Only first-step logits are trainable; teacher is fixed throughout.

    First-step teacher and student agree at the evaluation point. Their
    second-step distributions differ on branch 0 only. The local first-step
    KL gradient is zero, but the full gradient sees the future divergence.
    """
    logits = [0.0, 0.0]
    teacher_first = [0.5, 0.5]
    student_second = [[0.5, 0.5], [0.5, 0.5]]
    teacher_second = [[0.9, 0.1], [0.5, 0.5]]

    def sequence_kl(z):
        first = softmax(z)
        return sum(
            first[a] * student_second[a][b]
            * math.log((first[a] * student_second[a][b])
                       / (teacher_first[a] * teacher_second[a][b]))
            for a in range(2) for b in range(2)
        )

    first = softmax(logits)
    full_gradient = finite_difference(sequence_kl, logits)
    local_gradient = finite_difference(
        lambda z: kl(softmax(z), teacher_first), logits
    )
    causal_gradient = [0.0, 0.0]
    for a in range(2):
        for b in range(2):
            probability = first[a] * student_second[a][b]
            log_ratio_now = math.log(first[a] / teacher_first[a])
            log_ratio_future = math.log(
                student_second[a][b] / teacher_second[a][b]
            )
            for j in range(2):
                score = float(a == j) - first[j]
                causal_gradient[j] += (
                    probability * score * (log_ratio_now + log_ratio_future)
                )
    assert all(abs(g) < 1e-9 for g in local_gradient)
    assert full_gradient[0] > 0.1
    assert all(math.isclose(actual, expected, abs_tol=1e-9)
               for actual, expected in zip(full_gradient, causal_gradient))
    return {
        "sequence_KL": sequence_kl(logits),
        "local_first_step_gradient": local_gradient,
        "full_sequence_gradient_finite_difference": full_gradient,
        "causal_return_to_go_gradient": causal_gradient,
    }


def main():
    logits = [math.log(0.7), math.log(0.3)]
    student = softmax(logits)
    teacher = [0.4, 0.6]
    reverse = lambda z: kl(softmax(z), teacher)
    forward = lambda z: kl(teacher, softmax(z))
    reverse_grad = finite_difference(reverse, logits)
    forward_grad = finite_difference(forward, logits)
    assert reverse_grad[0] > 0 and forward_grad[0] > 0
    reverse_next = [z - 0.1 * g for z, g in zip(logits, reverse_grad)]
    forward_next = [z - 0.1 * g for z, g in zip(logits, forward_grad)]
    assert reverse(reverse_next) < reverse(logits)
    assert forward(forward_next) < forward(logits)
    assert math.isclose(kl(student, student), 0.0, abs_tol=1e-12)
    assert group_advantage([0, 0, 0, 0]) == [0, 0, 0, 0]
    assert group_advantage([1, 1, 1, 1]) == [0, 0, 0, 0]
    assert math.isclose(clipped_objective(1.4, 1), 1.2)
    assert math.isclose(clipped_objective(0.6, -1), -0.8)
    assert math.isclose(clipped_objective(1.4, -1), -1.4)
    prompts, samples, mini_prompts, dp_workers, micro_responses = 1024, 5, 256, 8, 4
    responses = prompts * samples
    optimizer_steps = prompts // mini_prompts
    per_worker = mini_prompts * samples // dp_workers
    accumulation = per_worker // micro_responses
    assert (responses, optimizer_steps, per_worker, accumulation) == (5120, 4, 160, 40)
    print(json.dumps({
        "scope": "one-state and two-step fixed-teacher arithmetic; no model training",
        "prerequisites": prerequisite_checks(),
        "student": student,
        "teacher": teacher,
        "KL_student_teacher": reverse(logits),
        "KL_teacher_student": forward(logits),
        "reverse_KL_logit_gradient": reverse_grad,
        "forward_KL_logit_gradient": forward_grad,
        "positive_advantage_upper_clip": clipped_objective(1.4, 1),
        "negative_advantage_lower_clip": clipped_objective(0.6, -1),
        "negative_advantage_wrong_direction": clipped_objective(1.4, -1),
        "zero_variance_group": group_advantage([0, 0, 0, 0]),
        "two_step_sequence_KL": two_step_sequence_check(),
        "batch": {"responses": responses, "optimizer_steps": optimizer_steps,
                  "per_dp_worker": per_worker, "micro_accumulation": accumulation},
        "assertions": "passed",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

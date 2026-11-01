from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class TaskMetrics:
    task_id: str
    runs: int
    successes: int
    success_rate: float
    pass_at_k: float
    pass_all_k: float
    outcome_consistency_plugin: float


def _validate_binary(values: Sequence[int]) -> list[int]:
    """Validate already-adjudicated outcomes; do not guess missing labels."""
    if not values:
        raise ValueError("At least one adjudicated outcome is required.")
    if any(not isinstance(x, (int, bool)) or x not in (0, 1) for x in values):
        raise ValueError("Outcomes must contain only integer/bool 0 or 1.")
    return [int(x) for x in values]


def _comb_or_zero(n: int, k: int) -> int:
    return 0 if n < k else math.comb(n, k)


def task_metrics(task_id: str, outcomes: Sequence[int], k: int) -> TaskMetrics:
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError("task_id must be a nonempty string.")
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError("k must be a positive integer.")

    ys = _validate_binary(outcomes)
    n, c = len(ys), sum(ys)
    if n < k:
        raise ValueError(f"Task {task_id}: {n} runs cannot estimate k={k}.")

    denominator = math.comb(n, k)
    p_hat = c / n
    return TaskMetrics(
        task_id=task_id,
        runs=n,
        successes=c,
        success_rate=p_hat,
        pass_at_k=1.0 - _comb_or_zero(n - c, k) / denominator,
        pass_all_k=_comb_or_zero(c, k) / denominator,
        # This is the paper's sample plug-in form, not a bias-corrected estimator.
        outcome_consistency_plugin=(2.0 * p_hat - 1.0) ** 2,
    )


def summarize(
    task_outcomes: Mapping[str, Sequence[int]], k: int
) -> tuple[list[TaskMetrics], dict[str, float]]:
    """Macro-average across tasks, not across all runs."""
    if not task_outcomes:
        raise ValueError("No tasks supplied.")
    rows = [task_metrics(task_id, ys, k) for task_id, ys in task_outcomes.items()]
    fields = (
        "success_rate", "pass_at_k", "pass_all_k", "outcome_consistency_plugin"
    )
    macro = {
        field: math.fsum(getattr(row, field) for row in rows) / len(rows)
        for field in fields
    }
    return rows, macro


def brier_loss(confidences: Sequence[float], outcomes: Sequence[int]) -> float:
    ys = _validate_binary(outcomes)
    if len(confidences) != len(ys):
        raise ValueError("Confidence and outcome counts must match.")
    cs = [float(c) for c in confidences]
    if any(not math.isfinite(c) or not 0.0 <= c <= 1.0 for c in cs):
        raise ValueError("Confidence must be finite and between 0 and 1.")
    return math.fsum((c - y) ** 2 for c, y in zip(cs, ys)) / len(ys)


def zero_event_upper_bound(n: int, alpha: float = 0.05) -> float:
    """One-sided (1-alpha) upper bound after n IID trials with zero events."""
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("n must be a positive integer.")
    if not math.isfinite(alpha) or not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be between 0 and 1, exclusively.")
    return -math.expm1(math.log(alpha) / n)


def _self_test() -> None:
    mixed = task_metrics("mixed", [1, 1, 1, 1, 0], k=3)
    assert math.isclose(mixed.pass_at_k, 1.0)
    assert math.isclose(mixed.pass_all_k, 0.4)
    assert math.isclose(mixed.outcome_consistency_plugin, 0.36)

    all_good = task_metrics("good", [1] * 5, k=5)
    all_bad = task_metrics("bad", [0] * 5, k=5)
    assert all_good.pass_at_k == all_good.pass_all_k == 1.0
    assert all_bad.pass_at_k == all_bad.pass_all_k == 0.0
    assert all_bad.outcome_consistency_plugin == 1.0

    one = task_metrics("one", [1, 0, 1, 1, 0], k=1)
    assert math.isclose(one.success_rate, one.pass_at_k)
    assert math.isclose(one.success_rate, one.pass_all_k)
    assert math.isclose(brier_loss([0.9, 0.8, 0.7, 0.1], [1, 0, 1, 0]), 0.1875)
    assert 0.0029 < zero_event_upper_bound(1000) < 0.0031

    for invalid in ([], [1, 2]):
        try:
            task_metrics("invalid", invalid, k=1)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid outcomes were not rejected.")

    try:
        task_metrics("too_few", [1, 0], k=3)
    except ValueError:
        pass
    else:
        raise AssertionError("Insufficient repetitions were not rejected.")


if __name__ == "__main__":
    _self_test()
    rows, macro = summarize(
        {
            "task_A": [1, 1, 1, 1, 1],
            "task_B": [1, 1, 1, 1, 0],
            "task_C": [0, 0, 0, 0, 0],
        },
        k=3,
    )
    output = {
        "per_task": [asdict(row) for row in rows],
        "macro": macro,
        "zero_event_95pct_upper_bound_n1000": zero_event_upper_bound(1000),
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))

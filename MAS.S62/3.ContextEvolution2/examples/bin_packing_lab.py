#!/usr/bin/env python3
"""A deterministic teaching lab, not an LLM/FunSearch reproduction.

Compare hand-written scalar policies, select only on development instances,
then evaluate the locked policy on independent and shifted instances.
No generated code is evaluated and no network or model API is used.
"""

from collections import Counter
import json
import math
import random
from statistics import mean


def best_fit(item, remaining):
    return -(remaining - item)


def worst_fit(item, remaining):
    return remaining - item


def first_fit(item, remaining):
    return 0.0


def reserve_half(item, remaining):
    return -abs(remaining - item - 5)


POLICIES = {
    "best_fit": best_fit,
    "worst_fit": worst_fit,
    "first_fit": first_fit,
    "reserve_half": reserve_half,
}


def pack(items, capacity, score):
    if capacity <= 0 or any(not 0 < item <= capacity for item in items):
        raise ValueError("Each item must fit an empty positive-capacity bin")
    remaining = []
    bins = []
    for item in items:
        feasible = [i for i, room in enumerate(remaining) if room >= item]
        if not feasible:
            remaining.append(capacity)
            bins.append([])
            feasible = [len(remaining) - 1]
        scored = [(score(item, remaining[i]), i) for i in feasible]
        if any(not isinstance(value, (int, float)) or not math.isfinite(value)
               for value, _ in scored):
            raise ValueError("The scalar scoring contract was violated")
        # Stable tie-breaking chooses the earliest existing feasible bin.
        index = max(scored, key=lambda pair: pair[0])[1]
        remaining[index] -= item
        bins[index].append(item)
    return bins


def validate(items, capacity, bins):
    assert all(sum(bin_items) <= capacity for bin_items in bins)
    assert all(bin_items for bin_items in bins)
    assert Counter(item for bin_items in bins for item in bin_items) == Counter(items)


def cases(seed, shifted=False):
    rng = random.Random(seed)
    return [
        [rng.choice([1, 1, 2, 2, 8, 9]) if shifted else rng.randint(1, 10)
         for _ in range(40)]
        for _ in range(64)
    ]


def evaluate(policy, instances):
    counts = []
    for items in instances:
        bins = pack(items, 10, policy)
        validate(items, 10, bins)
        counts.append(len(bins))
    return {"mean_bins": round(mean(counts), 6), "max_bins": max(counts),
            "instances": len(counts)}


def main():
    development = cases(17)
    heldout = cases(101)
    shifted = cases(201, shifted=True)
    dev_scores = {name: evaluate(policy, development)
                  for name, policy in POLICIES.items()}
    chosen = min(dev_scores, key=lambda name: dev_scores[name]["mean_bins"])
    locked = POLICIES[chosen]
    report = {
        "scope": "hand-written policies; no LLM generation; no FunSearch reproduction",
        "development": dev_scores,
        "locked_policy": chosen,
        "independent_uniform": evaluate(locked, heldout),
        "shifted_small_and_large": evaluate(locked, shifted),
        "lecture_example_best_fit": pack([6, 5, 3, 2, 2, 2], 10, best_fit),
    }
    assert len(report["lecture_example_best_fit"]) == 3
    try:
        pack([1, 1], 10, lambda item, remaining: float("nan"))
        raise AssertionError("NaN policy was not rejected")
    except ValueError:
        pass
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Arithmetic for the guide's synthetic examples; no model or network calls."""
from fractions import Fraction
import json


def accepted_cost(model_and_tools, review_hours, rework_hours, hourly_cost, accepted):
    if accepted <= 0:
        raise ValueError("No accepted deliverables; report total spending instead.")
    return Fraction(model_and_tools + hourly_cost * (review_hours + rework_hours), accepted)


def main():
    baseline = accepted_cost(200, 30, 10, 200, 80)
    cheaper_model = accepted_cost(50, 33, 10, 200, 80)
    growth = Fraction(12 - 10, 10)
    # One fixed synthetic cohort of 100 bad outputs. After each gate,
    # 40, then 30, then 20 remain incorrectly accepted. These are nested sets.
    conditional_chain = Fraction(40, 100) * Fraction(30, 40) * Fraction(20, 30)
    incorrect_product_of_cumulative_rates = Fraction(40, 100) * Fraction(30, 100) * Fraction(20, 100)
    assert baseline == Fraction(205, 2)
    assert cheaper_model == Fraction(865, 8)
    assert growth == Fraction(1, 5)
    assert conditional_chain == Fraction(20, 100)
    assert incorrect_product_of_cumulative_rates != conditional_chain
    try:
        accepted_cost(200, 30, 10, 200, 0)
    except ValueError:
        zero_accepted_rejected = True
    else:
        raise AssertionError("Zero accepted deliverables must not become zero cost.")
    print(json.dumps({
        "scope": "Synthetic teaching arithmetic only; no AI, human or safety experiment.",
        "baseline_cost_per_accepted": float(baseline),
        "cheaper_model_cost_per_accepted": float(cheaper_model),
        "reported_revenue_growth": float(growth),
        "bad_outputs_conditioning_population": 100,
        "conditional_false_accept_rate": float(conditional_chain),
        "incorrect_product_of_cumulative_rates": float(incorrect_product_of_cumulative_rates),
        "zero_accepted_rejected": zero_accepted_rejected,
        "assertions_passed": 6,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

"""Exact probability enumeration and idealized roofline arithmetic on a CPU."""
from collections import defaultdict
from fractions import Fraction as F
import json


def accepted_mass(target, draft):
    """Unconditional mass of proposing and accepting each token."""
    return tuple(q * min(1, p / q) if q else F(0) for p, q in zip(target, draft))


def remaining_distribution(target, draft):
    positive = tuple(max(F(0), p - q) for p, q in zip(target, draft))
    mass = sum(positive)
    return tuple(p / mass for p in positive) if mass else None


def corrected_step(target, draft, *, mistakenly_sample_target=False):
    accepted = accepted_mass(target, draft)
    rejected = 1 - sum(accepted)
    fallback = target if mistakenly_sample_target else remaining_distribution(target, draft)
    if rejected == 0:
        return accepted
    return tuple(a + rejected * r for a, r in zip(accepted, fallback))


def first_two_tokens(p_first, q_first, next_p, next_q):
    """If rejected at an earlier position, later choices use the corrected prefix."""
    joint = defaultdict(F)
    accepted = accepted_mass(p_first, q_first)
    rejection = 1 - sum(accepted)
    residual = remaining_distribution(p_first, q_first)
    for first, weight in enumerate(accepted):
        for second, p in enumerate(corrected_step(next_p[first], next_q[first])):
            joint[first, second] += weight * p
    if residual is not None:
        for first, weight in enumerate(residual):
            # The old draft suffix is discarded. For this finite example,
            # use plain target decoding for the one remaining output.
            for second, p in enumerate(next_p[first]):
                joint[first, second] += rejection * weight * p
    return dict(joint)


def ideal_output_rates(batch, length, alpha=F(4, 5)):
    weight_bytes, bandwidth, flops = 16e9, 4.8e12, 989e12
    queries = batch * (length + 1)
    seconds = max(weight_bytes / bandwidth, queries * weight_bytes / flops)
    committed = sum(alpha ** depth for depth in range(length + 1))
    return round(float(committed) / seconds, 2)


def render(values):
    return [str(value) for value in values]


def run():
    P = (F(6, 10), F(3, 10), F(1, 10))
    Q = (F(3, 10), F(6, 10), F(1, 10))
    corrected = corrected_step(P, Q)
    wrong = corrected_step(P, Q, mistakenly_sample_target=True)
    assert corrected == P
    assert wrong == (F(48, 100), F(39, 100), F(13, 100))
    assert corrected_step(P, P) == P
    assert remaining_distribution(P, P) is None
    assert corrected_step(P, (F(0), F(0), F(1))) == P

    next_p = (Q, (F(1, 5), F(3, 5), F(1, 5)), (F(0), F(1), F(0)))
    next_q = (P, (F(4, 5), F(0), F(1, 5)), (F(1, 3), F(1, 3), F(1, 3)))
    actual = first_two_tokens(P, Q, next_p, next_q)
    expected = {(i, j): p * next_p[i][j] for i, p in enumerate(P) for j in range(3)}
    assert sum(actual.values()) == 1
    assert actual == expected

    rates = [
        {"batch": n, "plain_tokens_per_second": ideal_output_rates(n, 0),
         "speculative_tokens_per_second": ideal_output_rates(n, 4)}
        for n in (16, 64, 256)
    ]
    assert rates[0]["plain_tokens_per_second"] < rates[0]["speculative_tokens_per_second"]
    assert rates[-1]["plain_tokens_per_second"] > rates[-1]["speculative_tokens_per_second"]

    return {
        "target": render(P),
        "overlap_acceptance": str(sum(accepted_mass(P, Q))),
        "residual_after_rejection": render(remaining_distribution(P, Q)),
        "exact_output": render(corrected),
        "output_if_wrong_fallback": render(wrong),
        "two_token_joint": {f"{i},{j}": str(p) for (i, j), p in actual.items()},
        "weight_only_roofline": rates,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

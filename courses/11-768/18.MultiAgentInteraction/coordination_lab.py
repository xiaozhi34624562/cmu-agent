#!/usr/bin/env python3
"""Deterministic teaching calculations; no model, API, training or paper reproduction."""
from __future__ import annotations

import json
import math
from itertools import product


def majority_accuracy(p: float) -> float:
    return p**3 + 3 * p**2 * (1-p)


def information_game(alpha1: float, alpha2: float, beta: float, cost: float):
    mean = (alpha1 + alpha2) / 2
    payoffs = {
        ('S', 'S'): (mean-cost, mean-cost),
        ('S', 'G'): (alpha1-cost, alpha1),
        ('G', 'S'): (alpha2, alpha2-cost),
        ('G', 'G'): (beta, beta),
    }
    equilibria = []
    for actions in product(('S', 'G'), repeat=2):
        best_response = True
        for player in (0, 1):
            other = list(actions)
            other[player] = 'G' if actions[player] == 'S' else 'S'
            if payoffs[tuple(other)][player] > payoffs[actions][player] + 1e-12:
                best_response = False
        if best_response:
            equilibria.append(''.join(actions))
    return {''.join(k): v for k, v in payoffs.items()}, equilibria


def accepts_candidate(candidate: dict, current_version: int, score_floor: float) -> bool:
    return (candidate['version'] == current_version and candidate['evidence_exists']
            and candidate['score'] >= score_floor)


def main():
    vote = majority_accuracy(0.7)
    assert math.isclose(vote, 0.784)
    table, eq = information_game(0.90, 0.54, 0.50, 0.05)
    assert eq == ['SG']
    candidates = [
        dict(id='old-version',version=3,evidence_exists=True,score=0.99),
        dict(id='no-evidence',version=4,evidence_exists=False,score=0.99),
        dict(id='accepted',version=4,evidence_exists=True,score=0.95),
    ]
    accepted = [c['id'] for c in candidates if accepts_candidate(c,4,0.9)]
    assert accepted == ['accepted']
    serial = sum([60]*4)
    parallel = max([60]*4) + 45
    short_serial = sum([2]*4)
    short_parallel = max([2]*4) + 45
    assert parallel < serial and short_parallel > short_serial
    print(json.dumps(dict(
        kind='Deterministic teaching calculation; not a model or paper benchmark',
        voting=dict(independent=round(vote,3),fully_correlated=0.7),
        information_game=dict(payoffs=table,pure_equilibria=eq),
        candidate_acceptance=accepted,
        timing_seconds=dict(long_serial=serial,long_parallel=parallel,
                            short_serial=short_serial,short_parallel=short_parallel),
    ),ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()

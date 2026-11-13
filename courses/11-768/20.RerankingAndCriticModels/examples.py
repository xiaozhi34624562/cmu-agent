"""Deterministic teaching checks for Lecture 20; no models, APIs or GPU required.

Run: python3 examples.py --output EXAMPLE_RUN.json
Requires Python 3 and a JDK (the Java example is compiled in a temporary directory).
These are synthetic probability experiments, not reproductions of paper benchmarks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import subprocess
import tempfile
from pathlib import Path


def selected_success(p: float, q: float, r: float, k: int) -> float:
    """First accepted response among attempts 1..k-1, else return attempt k."""
    accept = p * q + (1 - p) * r
    if accept == 0:
        return p
    no_early_accept = (1 - accept) ** (k - 1)
    return p * q / accept * (1 - no_early_accept) + p * no_early_accept


def simulate(p: float, q: float, r: float, k: int, trials: int, seed: int) -> float:
    rng = random.Random(seed)
    successes = 0
    for _ in range(trials):
        for attempt in range(1, k + 1):
            correct = rng.random() < p
            if attempt == k:
                successes += correct
                break
            if rng.random() < (q if correct else r):
                successes += correct
                break
    return successes / trials


JAVA = r"""
public class EvenSum {
    static long inclusive(int n) {
        if (n < 0) throw new IllegalArgumentException("n must be nonnegative");
        long sum = 0;
        for (long i = 2; i <= n; i += 2) sum += i;
        return sum;
    }
    static long exclusive(int n) {
        long sum = 0;
        for (long i = 2; i < n; i += 2) sum += i;
        return sum;
    }
    static long formula(int n) {
        if (n < 0) throw new IllegalArgumentException("n must be nonnegative");
        long m = n / 2;
        return m * (m + 1);
    }
    public static void main(String[] args) {
        for (int n : new int[]{0, 1, 2, 11, 12}) {
            System.out.println(n + "," + inclusive(n) + "," + exclusive(n) + "," + formula(n));
        }
        int n = 100000;
        long tooLate = (n / 2) * (n / 2 + 1);
        System.out.println("overflow," + tooLate + "," + formula(n));
        System.out.println("max_int," + formula(Integer.MAX_VALUE));
        try {
            formula(-1);
            throw new AssertionError("negative input was accepted");
        } catch (IllegalArgumentException expected) {
            System.out.println("negative,rejected");
        }
    }
}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    p, q, r = 0.25, 0.95, 0.10
    rows = []
    for k in (1, 4, 16, 64):
        exact = selected_success(p, q, r, k)
        observed = simulate(p, q, r, k, trials=100_000, seed=20261113 + k)
        assert abs(exact - observed) < 0.007
        rows.append({"k": k, "oracle_coverage": 1 - (1 - p) ** k,
                     "selected_success_exact": exact, "selected_success_simulated": observed})
    assert math.isclose(selected_success(p, q, r, 1), p)
    assert math.isclose(selected_success(p, 1.0, 0.0, 4), 1 - (1 - p) ** 4)
    assert math.isclose(selected_success(p, 0.0, 0.0, 4), p)
    estimator = 1 - math.comb(8, 3) / math.comb(10, 3)
    assert math.isclose(estimator, 64 / 120)
    with tempfile.TemporaryDirectory(prefix="cmu20-java-") as directory:
        source = Path(directory) / "EvenSum.java"
        source.write_text(JAVA, encoding="utf-8")
        compiler = subprocess.run(["javac", "-version"], check=True, capture_output=True, text=True)
        subprocess.run(["javac", str(source)], check=True, capture_output=True, text=True)
        run = subprocess.run(["java", "-cp", directory, "EvenSum"], check=True,
                             capture_output=True, text=True)
        java_lines = run.stdout.splitlines()
    assert "11,30,30,30" in java_lines
    assert "12,42,30,42" in java_lines
    assert "overflow,-1794917296,2500050000" in java_lines
    assert "max_int,1152921503533105152" in java_lines
    assert "negative,rejected" in java_lines
    majority_outputs = [30, 30, 42]
    majority = max(set(majority_outputs), key=majority_outputs.count)
    initial_correct, wrong_to_correct, correct_to_wrong = 60, 12, 15
    final_correct = initial_correct + wrong_to_correct - correct_to_wrong
    candidates, votes_per_pair = 16, 8
    round_comparisons = [candidates // 2 ** level for level in range(1, 5)]
    assert majority == 30 and final_correct == 57
    assert sum(round_comparisons) * votes_per_pair == 120
    results = {
        "purpose": "Synthetic numerical checks and an actual local Java compilation; not model evaluation",
        "command": "python3 examples.py --output EXAMPLE_RUN.json",
        "python": platform.python_version(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "java_compiler": (compiler.stdout + compiler.stderr).strip(),
        "java_source_sha256": hashlib.sha256(JAVA.encode()).hexdigest(),
        "java_stdout": java_lines,
        "first_accept": {"p": p, "q": q, "r": r,
                         "seed_rule": "20261113 + k", "trials_per_k": 100_000,
                         "asymptotic_selected_success": p * q / (p * q + (1 - p) * r),
                         "rows": rows},
        "pass_k_estimator": {"n": 10, "correct": 2, "k": 3,
                             "without_replacement": estimator, "plug_in": 1 - 0.8 ** 3},
        "task_heterogeneity": {"p_by_task": [0.1, 0.9], "k": 2,
                               "mean_coverage": ((1 - 0.9 ** 2) + (1 - 0.1 ** 2)) / 2,
                               "coverage_using_mean_p": 1 - 0.5 ** 2},
        "temperature_two_tokens": {str(t): 1 / (1 + math.exp(-2 / t)) for t in (1, 2)},
        "log_success_gain": {"0.1_to_0.2": math.log(0.2) - math.log(0.1),
                             "0.8_to_0.9": math.log(0.9) - math.log(0.8)},
        "majority_counterexample": {"outputs": majority_outputs, "correct": 42,
                                    "majority": majority, "oracle_coverage": int(42 in majority_outputs),
                                    "selected_correct": majority == 42},
        "refinement_counterexample": {"initial_correct": initial_correct, "initial_wrong": 40,
                                       "wrong_to_correct": wrong_to_correct,
                                       "correct_to_wrong": correct_to_wrong,
                                       "final_correct": final_correct, "population": 100},
        "binary_tournament_budget": {"candidates": candidates, "votes_per_pair": votes_per_pair,
                                     "comparison_calls_to_one": sum(round_comparisons) * votes_per_pair,
                                     "sequential_rounds_to_one": len(round_comparisons),
                                     "comparison_calls_to_four": sum(round_comparisons[:2]) * votes_per_pair},
        "limits": ["No LLM, GPU, remote API, official repository code or benchmark executed",
                   "Monte Carlo trials assume iid attempts and fixed verifier error rates",
                   "Java example validates its stated contract; it is not a SWE-bench reproduction",
                   "Tournament counts assume one winner per pair and no retries or caching"]
    }
    output = json.dumps(results, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()

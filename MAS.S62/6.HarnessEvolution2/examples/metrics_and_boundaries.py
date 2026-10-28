"""Offline arithmetic and Python-regex demonstrations; no model experiment."""
from math import isclose
import re


def main():
    improvement = min(1.8, 1.5) - 1.0
    assert isclose(improvement, 0.5) and improvement >= 0.3
    assert not (min(1.8, 1.5) - 1.5 >= 0.3)
    macro = (1 / 3 + 3 / 3) / 2
    assert isclose(macro, 2 / 3)
    relative = (50.5 - 33.9) / 33.9
    observed, predicted = [0.2, 0.8], [0.3, 0.7]
    mean = sum(observed) / len(observed)
    residual = sum((y - p) ** 2 for y, p in zip(observed, predicted))
    baseline = sum((y - mean) ** 2 for y in observed)
    r_squared = 1 - residual / baseline
    assert isclose(r_squared, 8 / 9)
    kappa = (0.9 - 0.5) / (1 - 0.5)
    assert isclose(kappa, 0.8)
    a, b = {"blocking", "caching"}, {"caching", "vectorization"}
    jaccard = len(a & b) / len(a | b)
    assert isclose(jaccard, 1 / 3)
    assert re.search(r"^[a-z]+$", "alice\n") is not None
    assert re.search(r"\A[a-z]+\Z", "alice\n") is None
    assert re.search(r"\A[a-z]+\Z", "alice") is not None
    print(f"Toolformer teaching loss improvement: {improvement:.3f}")
    print(f"Task macro average: {macro:.6f}")
    print(f"Gain: {50.5 - 33.9:.1f} percentage points; relative {relative:.6%}")
    print(f"R squared: {r_squared:.6f}; kappa: {kappa:.3f}; Jaccard: {jaccard:.6f}")
    print("PASS: arithmetic and trailing-newline boundary; no Django or model run")


if __name__ == "__main__":
    main()

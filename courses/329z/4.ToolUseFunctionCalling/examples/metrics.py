"""Offline arithmetic only: finite-sample pass metrics versus iid probabilities."""
import json
from fractions import Fraction
from math import comb

n, c, k = 10, 8, 2
pass_at_k = 1 - Fraction(comb(n - c, k), comb(n, k))
pass_all_k = Fraction(comb(c, k), comb(n, k))
p = Fraction(c, n)
print(json.dumps({
    "n": n, "c": c, "k": k,
    "finite_without_replacement_pass_at_k": str(pass_at_k),
    "finite_without_replacement_pass_all_k": str(pass_all_k),
    "iid_pass_at_k": str(1 - (1 - p) ** k),
    "iid_pass_all_k": str(p ** k),
}, ensure_ascii=False, indent=2))

"""CPU-only arithmetic checks for the course; no GPU timing or simulation."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import platform
import sys


def partial(scores, values):
    if not scores or len(scores) != len(values):
        raise ValueError('Nonempty, equally sized finite inputs required')
    if not all(math.isfinite(x) for x in scores + values):
        raise ValueError('Only finite values are supported')
    m = max(scores)
    weights = [math.exp(s - m) for s in scores]
    return m, sum(weights), sum(w * v for w, v in zip(weights, values))


def combine(a, b):
    m = max(a[0], b[0])
    sa, sb = math.exp(a[0] - m), math.exp(b[0] - m)
    return m, sa * a[1] + sb * b[1], sa * a[2] + sb * b[2]


def main():
    coverage = {}
    for n in [0, 1, 255, 256, 257, 1048576]:
        blocks = (n + 255) // 256
        visited = [block * 256 + thread for block in range(blocks)
                   for thread in range(256) if block * 256 + thread < n]
        assert visited == list(range(n))
        coverage[str(n)] = {'blocks': blocks, 'valid_elements': len(visited)}
    x = [-2., -0.5, 0., 1., 3.]
    scaled = [2 * v for v in x]
    biased = [v + 1 for v in scaled]
    reference = [max(0., v) for v in biased]
    fused = [max(0., 2 * v + 1) for v in x]
    assert reference == fused == [0., 0., 1., 3., 7.]
    errors = []
    for scores in [[0., math.log(2), math.log(3)], [1000., 999., -1000.],
                   [-1000., -1001., -999.]]:
        values = [10., 20., 30.]
        whole = partial(scores, values)
        expected = whole[2] / whole[1]
        for split in [1, 2]:
            merged = combine(partial(scores[:split], values[:split]),
                             partial(scores[split:], values[split:]))
            actual = merged[2] / merged[1]
            assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)
            errors.append(abs(actual - expected))
    weighted = partial([0., math.log(2), math.log(3)], [10., 20., 30.])
    assert math.isclose(weighted[2] / weighted[1], 140 / 6)
    # Negative example: averaging locally normalized outputs loses probability mass.
    naive = (10 + (40 + 90) / 5) / 2
    assert not math.isclose(naive, 140 / 6)
    source = Path(__file__).resolve()
    result = {
        'status': 'passed', 'scope': 'CPU arithmetic and indexing only; no GPU/model benchmark',
        'python': sys.version.split()[0], 'platform': platform.system() + ' ' + platform.machine(),
        'script_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'coverage': coverage, 'reference_output': reference,
        'stable_attention': {'output': weighted[2] / weighted[1],
                             'max_chunk_error': max(errors), 'incorrect_local_average': naive},
        'conditional_cost_models': {'ideal_fusion_byte_ratio': 6 / 2,
            'equal_indivisible_tiles_utilization': 160 / (132 * math.ceil(160 / 132)),
            'mfu_3040_aggregate': 140e9 * 3040 / (8 * 1979e12),
            'mfu_3040_per_gpu': 140e9 * 3040 / 1979e12,
            'weight_only_mbu': 16e9 * 200 / 4.8e12,
            'amdahl_20pct_twice_as_fast': 1 / (0.8 + 0.2 / 2)},
        'limitations': ['Finite scalar attention values only; not a CUDA implementation',
                       'Python float arithmetic does not verify FP16/BF16/FP32 kernels',
                       'Cost estimates assume the explicitly stated idealized conditions']}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

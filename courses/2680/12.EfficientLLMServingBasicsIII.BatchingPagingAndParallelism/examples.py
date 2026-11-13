#!/usr/bin/env python3
"""Deterministic CPU teaching examples; no model/GPU/network performance claims."""
from __future__ import annotations

import hashlib
import json
import math
import platform
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def timing(arrival: float, outputs: list[float]) -> dict:
    if not outputs or outputs[0] < arrival:
        raise ValueError("Need at least one output at or after arrival")
    gaps = [b - a for a, b in zip(outputs, outputs[1:])]
    if any(g < 0 for g in gaps):
        raise ValueError("Output timestamps must be monotonic")
    return {
        "ttft_ms": (outputs[0] - arrival) * 1000,
        "tpot_ms": sum(gaps) / len(gaps) * 1000 if gaps else None,
        "max_tbt_ms": max(gaps) * 1000 if gaps else None,
        "e2e_ms": (outputs[-1] - arrival) * 1000,
    }


def decode_rounds(lengths: dict[str, int], continuous: bool) -> list[list[str]]:
    """All arrive at time zero; no prefill; two slots; constant round duration."""
    waiting = deque(lengths)
    remaining = dict(lengths)
    active: list[str] = []
    rounds = []
    while waiting or active:
        if continuous or not active:
            while waiting and len(active) < 2:
                active.append(waiting.popleft())
        rounds.append([r for r in active if remaining[r]])
        for r in active:
            if remaining[r]:
                remaining[r] -= 1
        if continuous:
            active = [r for r in active if remaining[r]]
        elif all(remaining[r] == 0 for r in active):
            active = []
    return rounds


@dataclass
class Block:
    values: list[str]
    refs: int = 1


class BlockPool:
    """CPU ownership model only; GPU completion events are deliberately absent."""
    def __init__(self, size: int):
        self.size = size
        self.blocks: dict[int, Block] = {}
        self.next_id = 0

    def allocate(self, values: list[str]) -> int:
        identifier = self.next_id
        self.next_id += 1
        self.blocks[identifier] = Block(values.copy())
        return identifier

    def fork(self, table: list[int]) -> list[int]:
        for identifier in table:
            self.blocks[identifier].refs += 1
        return table.copy()

    def append(self, table: list[int], value: str) -> None:
        if not table or len(self.blocks[table[-1]].values) == self.size:
            table.append(self.allocate([]))
        elif self.blocks[table[-1]].refs > 1:
            previous = self.blocks[table[-1]]
            previous.refs -= 1
            table[-1] = self.allocate(previous.values)
        self.blocks[table[-1]].values.append(value)

    def release(self, table: list[int]) -> None:
        for identifier in table:
            self.blocks[identifier].refs -= 1
            if self.blocks[identifier].refs == 0:
                del self.blocks[identifier]
        table.clear()

    def read(self, table: list[int]) -> list[str]:
        return [x for identifier in table for x in self.blocks[identifier].values]


def matmul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    if not a or not b or len(a[0]) != len(b):
        raise ValueError("Incompatible matrix dimensions")
    return [[sum(x * y for x, y in zip(row, col)) for col in zip(*b)] for row in a]


def relu(a: list[list[float]]) -> list[list[float]]:
    return [[max(0, value) for value in row] for row in a]


def softmax_state(scores: list[float], values: list[float]) -> tuple[float, float, float]:
    m = max(scores)
    weights = [math.exp(score - m) for score in scores]
    return m, sum(weights), sum(w * v for w, v in zip(weights, values))


def run() -> dict:
    checks = {}
    bursty = timing(0, [0.2, 0.22, 0.24, 0.44, 0.46, 0.48])
    smooth = timing(0, [0.2 + i * 0.056 for i in range(6)])
    assert math.isclose(bursty["tpot_ms"], 56)
    assert math.isclose(bursty["tpot_ms"], smooth["tpot_ms"])
    assert math.isclose(bursty["max_tbt_ms"], 200)
    assert timing(0, [0.2])["tpot_ms"] is None
    checks["timing"] = {"bursty": bursty, "smooth": smooth, "single_output_tpot": None}

    static = decode_rounds({"A": 4, "B": 1, "C": 2}, False)
    continuous = decode_rounds({"A": 4, "B": 1, "C": 2}, True)
    assert len(static) == 6 and len(continuous) == 4
    assert sum(map(len, static)) == sum(map(len, continuous)) == 7
    checks["batch_slots"] = {"static_rounds": static, "continuous_rounds": continuous,
                              "assumptions": "decode-only, all arrive at zero, two slots, equal round duration"}

    old_prefix_lengths = list(range(0, 100, 25))
    assert sum(old_prefix_lengths) == 150
    checks["chunk_prefix_visits"] = {"old_prefix_lengths": old_prefix_lengths,
                                     "sum": 150, "not_a_measurement_of_hbm_reads": True}

    per_token = 2 * 32 * 8 * 128 * 2
    kv_bytes = per_token * 2048
    assert per_token == 128 * 1024 and kv_bytes == 256 * 1024**2
    checks["kv_and_transfer"] = {
        "kv_bytes_per_token": per_token,
        "input_2048_kv_mib": kv_bytes / 1024**2,
        "transfer_25_GB_per_s_ms": kv_bytes / (25 * 10**9) * 1000,
        "transfer_25_Gbit_per_s_ms": kv_bytes / (25 * 10**9 / 8) * 1000,
        "assumptions": "unsharded homogeneous KV, ideal effective bandwidth, no protocol/queue overhead",
    }

    pool = BlockPool(4)
    first: list[int] = []
    for token in "abcdefg":
        pool.append(first, token)
    second = pool.fork(first)
    shared_full = first[0]
    old_tail = second[-1]
    pool.append(first, "X")
    pool.append(second, "Y")
    assert first[0] == second[0] == shared_full
    assert first[-1] != second[-1]
    assert pool.read(first) == list("abcdefgX")
    assert pool.read(second) == list("abcdefgY")
    before_release = {"first": pool.read(first), "second": pool.read(second),
                      "full_block_refs": pool.blocks[shared_full].refs,
                      "original_tail_retained_by_second": second[-1] == old_tail}
    pool.release(first)
    assert pool.read(second) == list("abcdefgY")
    assert pool.blocks[shared_full].refs == 1
    pool.release(second)
    assert not pool.blocks
    checks["copy_on_write"] = {**before_release, "all_blocks_freed_after_both_release": True}

    x = [[2, -1], [1, 3]]
    w1 = [[1, 2, 3, 4], [0, 1, -1, 2]]
    w2 = [[1, 0], [0, 1], [1, 1], [-1, 2]]
    direct = matmul(relu(matmul(x, w1)), w2)
    left = matmul(relu(matmul(x, [r[:2] for r in w1])), w2[:2])
    right = matmul(relu(matmul(x, [r[2:] for r in w1])), w2[2:])
    combined = [[a + b for a, b in zip(l, r)] for l, r in zip(left, right)]
    assert direct == combined
    assert max(0, -1 + 2) != max(0, -1) + max(0, 2)
    checks["tensor_parallel_algebra"] = {"direct": direct, "combined": combined,
                                         "nonlinear_counterexample": {"relu_sum": 1, "sum_relu": 2},
                                         "activation": "ReLU for a compact example, not a model reproduction"}

    scores, values = [0, 1, 2, 3], [1, 2, 4, 8]
    whole = softmax_state(scores, values)
    states = [softmax_state(scores[:2], values[:2]), softmax_state(scores[2:], values[2:])]
    m = max(s[0] for s in states)
    merged_l = sum(math.exp(s[0] - m) * s[1] for s in states)
    merged_u = sum(math.exp(s[0] - m) * s[2] for s in states)
    merged, direct_attention = merged_u / merged_l, whole[2] / whole[1]
    wrong_average = sum(s[2] / s[1] for s in states) / 2
    assert math.isclose(merged, direct_attention, rel_tol=1e-12)
    assert not math.isclose(wrong_average, direct_attention, rel_tol=1e-3)
    checks["attention_merge"] = {"direct": direct_attention, "merged": merged,
                                 "incorrect_average_of_local_outputs": wrong_average}

    tp_bytes = 80 * 2 * (2 * (4 - 1) / 4) * (8192 * 2)
    pp_hop_bytes = 8192 * 2
    ep_bytes_per_source_token = 80 * 2 * 2 * 0.75 * (8192 * 2)
    assert tp_bytes / pp_hop_bytes == 240
    checks["parallelism_costs"] = {
        "pipeline_bubble_K4_m4": 3 / 7,
        "pipeline_bubble_K4_m16": 3 / 19,
        "tp_sent_bytes_per_global_token_per_gpu": tp_bytes,
        "pp_sent_bytes_per_token_one_boundary": pp_hop_bytes,
        "tp_to_one_pp_boundary_ratio": 240,
        "ep_sent_bytes_per_local_source_token": ep_bytes_per_source_token,
        "ep_mean_sent_bytes_per_global_token_per_gpu_G4": ep_bytes_per_source_token / 4,
        "assumptions": "balanced forward pipeline; 80 layers, h8192, bf16; TP4 ring; MoE top2 every layer, 3/4 remote",
    }
    return checks


if __name__ == "__main__":
    path = Path(__file__).resolve()
    results = {
        "schema_version": 1,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "script": path.name,
        "script_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "status": "passed",
        "scope": "CPU arithmetic, algebra and ownership examples only",
        "gpu_model_network_experiments_run": False,
        "checks": run(),
    }
    output = path.with_name("EXAMPLE_RUN.json")
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(results, ensure_ascii=False, indent=2))

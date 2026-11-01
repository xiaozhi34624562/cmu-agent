"""Offline teaching example: validate parallel-reader handoffs.

This checks revision/evidence contracts, not LLM correctness or speedup.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    task: str
    revision: str
    conclusion: str
    evidence: tuple[str, ...]
    unresolved: tuple[str, ...] = ()


def integrate(findings, expected_tasks, revision):
    seen = set()
    result = []
    for item in findings:
        if item.task in seen or item.task not in expected_tasks:
            raise ValueError("duplicate or unexpected task")
        if item.revision != revision:
            raise ValueError("stale handoff")
        if not item.evidence:
            raise ValueError("missing evidence")
        if item.unresolved:
            raise ValueError("unresolved finding requires explicit review")
        seen.add(item.task)
        result.append(item.conclusion)
    if seen != expected_tasks:
        raise ValueError("incomplete handoff")
    return tuple(result)


def main():
    a = Finding("entry", "rev17", "two validators use dollar anchor",
                ("validators.py:18", "validators.py:31"))
    b = Finding("tests", "rev17", "add trailing-newline regression cases",
                ("tests/test_validators.py:12",))
    assert len(integrate([a, b], {"entry", "tests"}, "rev17")) == 2
    bad = [Finding("tests", "rev16", b.conclusion, b.evidence),
           Finding("tests", "rev17", b.conclusion, ()),
           Finding("tests", "rev17", b.conclusion, b.evidence, ("Unicode scope",))]
    for item in bad:
        try:
            integrate([a, item], {"entry", "tests"}, "rev17")
        except ValueError:
            pass
        else:
            raise AssertionError("invalid handoff accepted")
    try:
        integrate([a], {"entry", "tests"}, "rev17")
    except ValueError:
        pass
    else:
        raise AssertionError("missing worker accepted")
    print("PASS: paired handoff, stale/evidence/unresolved/incomplete rejection")


if __name__ == "__main__":
    main()

"""Offline teaching example: scope, optimistic versioning, and rollback.

No model/API calls. This validates state rules, not agent learning quality.
Run: python3 versioned_memory.py
"""
from copy import deepcopy


class MemoryStore:
    def __init__(self):
        self.revision = 0
        self.entries = {}
        self.history = {}

    def apply(self, base_revision, changes, allowed_scope):
        if base_revision != self.revision:
            raise ValueError("stale proposal")
        candidate = deepcopy(self.entries)
        for item in changes:
            if item["scope"] != allowed_scope:
                raise ValueError("scope mismatch")
            if not item.get("evidence"):
                raise ValueError("missing evidence")
            if item["kind"] == "fact" and item["status"] != "observed":
                raise ValueError("unobserved statement cannot become fact")
            key = (item["scope"], item["key"])
            candidate[key] = deepcopy(item)
        self.history[self.revision] = deepcopy(self.entries)
        self.entries = candidate
        self.revision += 1
        return self.revision

    def rollback(self, target):
        old = deepcopy(self.history[target])
        self.history[self.revision] = deepcopy(self.entries)
        self.entries = old
        self.revision += 1  # rollback is itself a new revision
        return self.revision


def main():
    store = MemoryStore()
    record = dict(scope="repo-A@v1", key="amount-convention", kind="fact",
                  status="observed", value="parentheses mean negative",
                  evidence=["tests/test_amount.py::test_parentheses"])
    store.apply(0, [record], "repo-A@v1")
    assert store.revision == 1
    for base, modified in [(0, record),
                           (1, {**record, "scope": "repo-B@v1"}),
                           (1, {**record, "status": "proposed"})]:
        before = deepcopy((store.revision, store.entries))
        try:
            store.apply(base, [modified], "repo-A@v1")
        except ValueError:
            assert (store.revision, store.entries) == before
        else:
            raise AssertionError("invalid candidate was accepted")
    store.rollback(0)
    assert not store.entries and store.revision == 2
    print("PASS: observed scoped write, stale/scope/unobserved rejection, rollback")


if __name__ == "__main__":
    main()

"""Offline teaching check; no SDK, model, external API, or repository mutation."""
from math import comb, isclose


def collect_pages(pages):
    """Each item is (already returned data, has_next); consume data before stopping."""
    collected = []
    for data, has_next in pages:
        collected.extend(data)
        if not has_next:
            break
    return collected


def old_collect_pages(pages):
    """Deliberately wrong teaching implementation: discards final returned page."""
    collected = []
    for data, has_next in pages:
        if not has_next:
            break
        collected.extend(data)
    return collected


def main():
    cases = [
        ("empty", [([], False)], []),
        ("single", [([1], False)], [1]),
        ("short final", [([1, 2], True), ([3], False)], [1, 2, 3]),
        ("full final", [([1, 2], True), ([3, 4], False)], [1, 2, 3, 4]),
        ("empty terminator", [([1, 2], True), ([], False)], [1, 2]),
        ("do not read after stop", [([1], False), ([999], False)], [1]),
    ]
    for label, pages, expected in cases:
        assert collect_pages(pages) == expected, label
    assert old_collect_pages([([1, 2], True), ([3], False)]) == [1, 2]
    assert isclose(1 - comb(8, 3) / comb(10, 3), 8 / 15)
    assert isclose(sum(100 * t for t in range(1, 11)), 5500)
    assert isclose(10 / 4, 2.5)
    print("PASS: 6 pagination contracts; faulty final-page case exposed; 3 arithmetic checks")
    print("Scope: deterministic data handling only; no model, SDK, network or paper reproduction")


if __name__ == "__main__":
    main()

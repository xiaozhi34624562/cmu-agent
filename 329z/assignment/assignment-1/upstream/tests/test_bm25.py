"""Tests for problem (bm25). All deterministic: this problem uses no LLM.

The first group checks exact scores on a five-document corpus small enough
to score by hand. The second group runs on the full email archive and checks
ranking quality and speed.
"""

from __future__ import annotations

import math
import time

import pytest

from cs329z_hw1 import adapters
from tests.helpers import load_fixture

# Limits for the full archive. The time limits are about four times what the
# reference solution measured on a 2024 MacBook (3.0 s to build the index,
# 4.6 ms per query). The reference solution's recall@10 is 1.000.
BUILD_SECONDS = 15.0
QUERY_SECONDS = 0.020
MIN_RECALL_AT_10 = 0.90

# Budget for one rare-term query on the synthetic corpus of
# test_search_reads_only_matching_documents.
RARE_QUERY_SECONDS = 0.002

# ---------------------------------------------------------------- toy ------

TOY = [
    "apple banana apple",  # 0, length 3
    "banana cherry",  # 1, length 2
    "cherry cherry cherry date",  # 2, length 4
    "Banana, CHERRY!",  # 3, length 2 (same tokens as document 1)
    "date egg fig grape",  # 4, length 4
]
# N = 5 documents, 15 tokens in total, so avgdl = 3.
# Document frequencies: apple 1, banana 3, cherry 3, date 2, egg 1.
K1, B, N, AVGDL = 1.5, 0.75, 5, 3.0


def idf(n: int) -> float:
    return math.log((N - n + 0.5) / (n + 0.5) + 1)


def term_score(n: int, tf: int, length: int) -> float:
    """BM25 contribution of one term: n = documents containing the term,
    tf = its count in this document, length = tokens in this document."""
    return idf(n) * tf * (K1 + 1) / (tf + K1 * (1 - B + B * length / AVGDL))


# The same numbers worked by hand, to 6 decimals:
#   idf(1) = ln(4.5/1.5 + 1) = ln 4      = 1.386294
#   idf(2) = ln(3.5/2.5 + 1) = ln 2.4    = 0.875469
#   idf(3) = ln(2.5/3.5 + 1) = ln (12/7) = 0.538997
#   K1 * (1 - B + B * length / 3) is 1.125, 1.5, 1.875 for lengths 2, 3, 4.
APPLE_DOC0 = term_score(1, 2, 3)  # 1.386294 * 5.0 / 3.5     = 1.980420
BANANA_DOC0 = term_score(3, 1, 3)  # 0.538997 * 2.5 / 2.5     = 0.538997
BANANA_DOC1 = term_score(3, 1, 2)  # 0.538997 * 2.5 / 2.125   = 0.634114
CHERRY_DOC1 = term_score(3, 1, 2)  # same as BANANA_DOC1      = 0.634114
CHERRY_DOC2 = term_score(3, 3, 4)  # 0.538997 * 7.5 / 4.875   = 0.829226
DATE_DOC2 = term_score(2, 1, 4)  # 0.875469 * 2.5 / 2.875   = 0.761277
DATE_DOC4 = DATE_DOC2  # same tf and length


# Guard the expected values against a typo in this file.
for _computed, _by_hand in [
    (APPLE_DOC0, 1.980420),
    (BANANA_DOC0, 0.538997),
    (BANANA_DOC1, 0.634114),
    (CHERRY_DOC2, 0.829226),
    (DATE_DOC2, 0.761277),
]:
    assert abs(_computed - _by_hand) < 1e-6, (_computed, _by_hand)


def toy_search(query: str, k: int) -> list[tuple[int, float]]:
    index = adapters.run_bm25_build(TOY)
    return [(doc_id, score) for doc_id, score in adapters.run_bm25_search(index, query, k)]


def assert_results(query: str, k: int, expected: list[tuple[int, float]]) -> None:
    got = toy_search(query, k)
    shown = f"search({query!r}, k={k})\n  expected {expected}\n  got      {got}"
    assert [d for d, _ in got] == [d for d, _ in expected], f"Wrong documents or order. {shown}"
    for (doc_id, score), (_, want) in zip(got, expected):
        assert score == pytest.approx(want, abs=1e-6), f"Wrong score for document {doc_id}. {shown}"


def test_toy_single_term():
    assert_results("apple", 10, [(0, APPLE_DOC0)])


def test_toy_length_normalization_and_tie_break():
    """Documents 1 and 3 have the same tokens, so the same score; the lower
    id comes first. Document 0 is longer, so its one "banana" scores less."""
    assert_results("banana", 10, [(1, BANANA_DOC1), (3, BANANA_DOC1), (0, BANANA_DOC0)])


def test_toy_two_terms_sum():
    assert_results(
        "cherry date",
        10,
        [(2, CHERRY_DOC2 + DATE_DOC2), (4, DATE_DOC4), (1, CHERRY_DOC1), (3, CHERRY_DOC1)],
    )


def test_toy_query_is_tokenized_like_documents():
    assert_results("BANANA... apple?", 1, [(0, APPLE_DOC0 + BANANA_DOC0)])


def test_toy_top_k_truncates():
    assert_results("cherry date", 2, [(2, CHERRY_DOC2 + DATE_DOC2), (4, DATE_DOC4)])


def test_toy_tie_at_the_cutoff():
    """k=1 cuts between two tied documents; the lower id is the one kept."""
    assert_results("banana", 1, [(1, BANANA_DOC1)])


def test_toy_k_larger_than_matches():
    """Only documents containing a query term are returned, however large k is."""
    got = toy_search("date", 100)
    assert [d for d, _ in got] == [2, 4], (
        f"search('date', k=100) should return only documents 2 and 4 (the ones "
        f"containing 'date'), got {got}"
    )


def test_toy_unknown_term():
    got = toy_search("zucchini", 5)
    assert got == [], f"A query whose only term is in no document should return [], got {got}"


def test_toy_unknown_term_is_ignored_next_to_known_term():
    assert_results("zucchini apple", 5, [(0, APPLE_DOC0)])


def test_toy_repeated_query_term_counts_once():
    assert_results("apple apple APPLE", 5, [(0, APPLE_DOC0)])


def test_toy_empty_query():
    for query in ("", "   ", "?!"):
        got = toy_search(query, 5)
        assert got == [], f"search({query!r}, k=5) has no terms and should return [], got {got}"


def test_toy_result_types():
    got = adapters.run_bm25_search(adapters.run_bm25_build(TOY), "cherry", 3)
    assert isinstance(got, list), f"search should return a list, got {type(got).__name__}"
    for pair in got:
        doc_id, score = pair
        assert isinstance(doc_id, int) and isinstance(score, float), (
            f"each result should be (int doc_id, float score), got {pair!r}"
        )


def test_empty_documents_are_indexed():
    """Blank documents still count toward N and keep their list positions."""
    index = adapters.run_bm25_build(["", "apple", "   ", "apple apple"])
    got = [d for d, _ in adapters.run_bm25_search(index, "apple", 10)]
    assert sorted(got) == [1, 3], (
        f"In ['', 'apple', '   ', 'apple apple'] the documents containing 'apple' are "
        f"1 and 3, got {got}"
    )


def test_search_reads_only_matching_documents():
    """200,000 documents, 3 of which contain the query term. A search that
    reads only that term's postings takes microseconds. A search that visits
    every document takes tens of milliseconds."""
    docs = ["common filler"] * 200_000
    rare = [7, 100_000, 199_999]
    for i in rare:
        docs[i] = "common quokka"
    index = adapters.run_bm25_build(docs)
    best = float("inf")
    for _ in range(5):
        start = time.perf_counter()
        got = adapters.run_bm25_search(index, "quokka", 10)
        best = min(best, time.perf_counter() - start)
    assert [d for d, _ in got] == rare, f"expected documents {rare}, got {got}"
    assert best < RARE_QUERY_SECONDS, (
        f"A query for a term found in 3 of 200,000 documents took {best * 1000:.2f} ms "
        f"(best of 5); the limit is {RARE_QUERY_SECONDS * 1000:.0f} ms. search() should "
        "read only the postings of the query's terms, not loop over all documents."
    )


# ------------------------------------------------------------- archive -----

_archive_index: dict = {}


def archive_index(archive):
    """Build the index over the archive once per test run; remember how long it took."""
    if not _archive_index:
        from cs329z_hw1.data import email_text

        docs = [email_text(email) for email in archive]
        start = time.perf_counter()
        index = adapters.run_bm25_build(docs)
        _archive_index.update(index=index, seconds=time.perf_counter() - start)
    return _archive_index["index"]


def test_archive_build_time(archive):
    archive_index(archive)
    seconds = _archive_index["seconds"]
    print(f"index build: {seconds:.1f} s for {len(archive)} emails")
    assert seconds < BUILD_SECONDS, (
        f"Building the index over {len(archive)} emails took {seconds:.1f} s; "
        f"the limit is {BUILD_SECONDS:.0f} s."
    )


def test_archive_recall_at_10(archive):
    index = archive_index(archive)
    queries = load_fixture("bm25_queries.json")
    recalls, misses = [], []
    for item in queries:
        top = [archive[doc_id]["id"] for doc_id, _ in adapters.run_bm25_search(index, item["query"], 10)]
        found = [email_id for email_id in item["relevant"] if email_id in top]
        recalls.append(len(found) / len(item["relevant"]))
        if len(found) < len(item["relevant"]):
            misses.append(f"  {item['query']!r}: found {len(found)} of {len(item['relevant'])} relevant")
    recall = sum(recalls) / len(recalls)
    print(f"recall@10: {recall:.3f} over {len(queries)} queries")
    assert recall >= MIN_RECALL_AT_10, (
        f"Mean recall@10 is {recall:.3f} over {len(queries)} queries; at least "
        f"{MIN_RECALL_AT_10:.2f} is required. Queries with a relevant email outside "
        "the top 10:\n" + "\n".join(misses)
    )


def test_archive_results_are_sorted(archive):
    index = archive_index(archive)
    for item in load_fixture("bm25_queries.json"):
        got = [(d, s) for d, s in adapters.run_bm25_search(index, item["query"], 50)]
        assert got == sorted(got, key=lambda pair: (-pair[1], pair[0])), (
            f"Results for {item['query']!r} are not sorted by score descending, "
            "then doc id ascending."
        )
        assert len({d for d, _ in got}) == len(got), (
            f"Results for {item['query']!r} contain the same document more than once."
        )


def test_archive_query_time(archive):
    index = archive_index(archive)
    queries = [item["query"] for item in load_fixture("bm25_queries.json")]
    start = time.perf_counter()
    for query in queries:
        adapters.run_bm25_search(index, query, 10)
    mean = (time.perf_counter() - start) / len(queries)
    print(f"mean query time: {mean * 1000:.1f} ms over {len(queries)} queries")
    assert mean < QUERY_SECONDS, (
        f"Mean query time is {mean * 1000:.1f} ms over {len(queries)} queries; "
        f"the limit is {QUERY_SECONDS * 1000:.0f} ms."
    )

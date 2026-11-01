"""Tests for problem (search_docs).

The deterministic tests build one index with
``run_build_doc_index(data.load_docs())``, call ``run_search_docs`` and
``run_read_doc`` on it directly, and compare what they return with the files
in ``data/docs/``.

Rules the deterministic tests check:

* ``run_search_docs(index, query, k)`` returns a list of at most k dicts with the
  keys doc_id, title, snippet. doc_id and title are those of a real document
  (see ``cs329z_hw1.data.load_docs``). A query that matches nothing returns [].
  Two results may come from the same document (for example two passages of
  it), and a result may carry keys besides these three.
* A snippet is at most SNIPPET_MAX_TOKENS tokens and contains text from its
  document.
* ``run_read_doc(index, doc_id, start_line)`` returns a window that starts at
  start_line. Its text is exactly lines start_line..end_line of the file
  (1-based, inclusive), joined by newlines, and is at most WINDOW_MAX_TOKENS
  tokens. Reading again from end_line + 1 continues without a gap, and the
  last window ends at total_lines.
* An unknown doc_id, or a start_line outside 1..total_lines, raises
  ValueError or LookupError (KeyError and IndexError are LookupErrors). Your
  registry turns the exception into a tool_error the model can read.

The live test asks your full agent 20 questions about the documents.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from cs329z_hw1 import data
from cs329z_hw1.tokenizer import tokenize
from cs329z_hw1.tokens import count_tokens
from cs329z_hw1.types import AgentConfig
from cs329z_hw1 import adapters
from tests.conftest import eval_slice
from tests.helpers import contains_any, events, load_fixture
from tests.thresholds import SEARCH_DOCS_MAX_RESULT_TOKENS, SEARCH_DOCS_MIN_ACCURACY

SNIPPET_MAX_TOKENS = 150  # count_tokens(snippet), about 600 characters
WINDOW_MAX_TOKENS = 1500  # count_tokens(window["text"]), about 6000 characters
SNIPPET_SHARED_RUN = 4  # a snippet must share this many consecutive tokens with its document

QUERIES = [
    "parental leave",
    "password length",
    "meal limit travel",
    "on-call stipend",
    "API rate limit",
    "office days hybrid",
    "firmware update error code",
]


def docs_by_id() -> dict[str, dict]:
    return {d["doc_id"]: d for d in data.load_docs()}


_index_cache: dict = {}


def doc_index():
    """One index for the whole module, built by the student's adapter."""
    if "index" not in _index_cache:
        _index_cache["index"] = adapters.run_build_doc_index(data.load_docs())
    return _index_cache["index"]


def search(query: str, k: int = 5) -> list[dict]:
    results = adapters.run_search_docs(doc_index(), query, k)
    assert isinstance(results, list), (
        f"run_search_docs({query!r}, {k}) must return a list, got {type(results).__name__}"
    )
    return results


def shares_run(snippet: str, text: str, n: int) -> bool:
    """True if some n consecutive tokens of the snippet occur consecutively in the text."""
    s, t = tokenize(snippet), tokenize(text)
    runs = {tuple(t[i : i + n]) for i in range(len(t) - n + 1)}
    return any(tuple(s[i : i + n]) in runs for i in range(len(s) - n + 1))


def single_document_terms(limit: int = 6) -> list[tuple[str, str]]:
    """(term, doc_id) pairs where the term occurs in exactly one document."""
    homes: dict[str, set[str]] = {}
    for doc in data.load_docs():
        for term in set(tokenize(doc["text"])):
            homes.setdefault(term, set()).add(doc["doc_id"])
    pairs = sorted(
        (term, next(iter(ids)))
        for term, ids in homes.items()
        if len(ids) == 1 and len(term) >= 7 and term.isalpha()
    )
    step = max(len(pairs) // limit, 1)
    return pairs[::step][:limit]


# ---------------------------------------------------------- search_docs ---


@pytest.mark.parametrize("query", QUERIES)
def test_search_results_have_the_right_shape_and_point_to_real_documents(query):
    docs = docs_by_id()
    results = search(query, 5)
    assert results, f"run_search_docs({query!r}, 5) returned no results; the documents contain these words"
    assert len(results) <= 5, f"run_search_docs({query!r}, 5) returned {len(results)} results, more than k"
    for r in results:
        assert isinstance(r, dict) and {"doc_id", "title", "snippet"} <= set(r), (
            f"each result must be a dict with the keys doc_id, title, snippet; got {r!r}"
        )
        assert r["doc_id"] in docs, (
            f"result doc_id {r['doc_id']!r} is not a document in data/docs/ "
            f"(doc_id is the file name without .md)"
        )
        assert r["title"] == docs[r["doc_id"]]["title"], (
            f"result title {r['title']!r} is not the title of {r['doc_id']} "
            f"({docs[r['doc_id']]['title']!r})"
        )
        assert isinstance(r["snippet"], str) and r["snippet"].strip(), (
            f"the snippet for {r['doc_id']} must be a non-empty str, got {r['snippet']!r}"
        )


@pytest.mark.parametrize("query", QUERIES)
def test_snippets_are_short_and_come_from_the_document(query):
    """Each snippet is at most SNIPPET_MAX_TOKENS tokens and shares at least
    SNIPPET_SHARED_RUN consecutive words with the text of its document
    (compared after cs329z_hw1.tokenizer.tokenize, so markers such as line
    numbers or ellipses around the quoted text are fine)."""
    docs = docs_by_id()
    for r in search(query, 5):
        size = count_tokens(r["snippet"])
        assert size <= SNIPPET_MAX_TOKENS, (
            f"the snippet for {r['doc_id']} is {size} tokens; the limit is {SNIPPET_MAX_TOKENS}. "
            "A search result must be a pointer with a short excerpt, not the document."
        )
        assert shares_run(r["snippet"], docs[r["doc_id"]]["text"], SNIPPET_SHARED_RUN), (
            f"the snippet for {r['doc_id']} does not quote its document: no "
            f"{SNIPPET_SHARED_RUN} consecutive words of it occur in the document.\n"
            f"snippet: {r['snippet']!r}"
        )


def test_a_word_found_in_one_document_finds_that_document():
    """For a word that occurs in exactly one document, the first result is
    that document and its snippet contains the word."""
    for term, doc_id in single_document_terms():
        results = search(term, 3)
        assert results, f"run_search_docs({term!r}, 3) returned nothing; the word occurs in {doc_id}"
        assert results[0]["doc_id"] == doc_id, (
            f"the word {term!r} occurs only in {doc_id}, but the first result is {results[0]['doc_id']}"
        )
        assert term in tokenize(results[0]["snippet"]), (
            f"the first result for {term!r} has a snippet that does not contain the word, "
            f"so it does not show why the document matched.\nsnippet: {results[0]['snippet']!r}"
        )


@pytest.mark.parametrize("k", [1, 2, 8])
def test_search_returns_at_most_k_results(k):
    results = search("policy employees", k)
    assert 1 <= len(results) <= k, (
        f"run_search_docs('policy employees', {k}) returned {len(results)} results; expected 1 to {k}"
    )


@pytest.mark.parametrize("query", ["zzqxv wvvqk", "qqqqzzzz", ""])
def test_no_match_is_an_empty_list(query):
    results = search(query, 5)
    assert results == [], (
        f"run_search_docs({query!r}, 5) should return [] because no document contains "
        f"these words; got {results!r}"
    )


def test_search_is_stable():
    for query in QUERIES[:3]:
        first, second = search(query, 5), search(query, 5)
        assert first == second, f"two identical calls run_search_docs({query!r}, 5) returned different results"


# ------------------------------------------------------------- read_doc ---


def read(doc_id: str, start_line: int = 1) -> dict:
    window = adapters.run_read_doc(doc_index(), doc_id, start_line)
    assert isinstance(window, dict) and {"doc_id", "start_line", "end_line", "total_lines", "text"} <= set(window), (
        f"run_read_doc must return a dict with the keys doc_id, start_line, end_line, "
        f"total_lines, text; got {window!r}"
    )
    return window


def check_window(window: dict, doc: dict, start_line: int) -> None:
    lines = doc["text"].splitlines()
    doc_id = doc["doc_id"]
    assert window["doc_id"] == doc_id, f"asked for {doc_id}, the window says doc_id {window['doc_id']!r}"
    assert window["total_lines"] == len(lines), (
        f"{doc_id}: total_lines is {window['total_lines']}, the file has {len(lines)} lines "
        "(len(text.splitlines()))"
    )
    assert window["start_line"] == start_line, (
        f"{doc_id}: asked for start_line={start_line}, the window says start_line {window['start_line']}"
    )
    assert start_line <= window["end_line"] <= len(lines), (
        f"{doc_id}: end_line {window['end_line']} must be between start_line {start_line} "
        f"and total_lines {len(lines)}"
    )
    expected = lines[start_line - 1 : window["end_line"]]
    assert window["text"].splitlines() == expected or window["text"] == "\n".join(expected), (
        f"{doc_id}: text must be exactly lines {start_line}..{window['end_line']} of the file, "
        f"joined by newlines.\nexpected first line: {expected[0]!r}\n"
        f"got first line:      {(window['text'].splitlines() or [''])[0]!r}"
    )
    size = count_tokens(window["text"])
    assert size <= WINDOW_MAX_TOKENS, (
        f"{doc_id}: the window starting at line {start_line} is {size} tokens; the limit "
        f"is {WINDOW_MAX_TOKENS}. read_doc must return a bounded window, not the rest of the document."
    )


def test_read_doc_first_window():
    adapters.run_read_doc(doc_index(), "employee-handbook", 1)  # stub check before anything else
    for doc in data.load_docs():
        check_window(read(doc["doc_id"], 1), doc, 1)


def test_read_doc_default_start_line_is_1():
    doc = docs_by_id()["employee-handbook"]
    window = adapters.run_read_doc(doc_index(), "employee-handbook")
    check_window(window, doc, 1)


def test_read_doc_from_the_middle():
    doc = docs_by_id()["employee-handbook"]
    total = len(doc["text"].splitlines())
    for start in (2, 57, total // 2, total):
        check_window(read("employee-handbook", start), doc, start)


def test_long_document_needs_several_windows():
    """The employee handbook is several thousand tokens, so one window cannot hold it."""
    doc = docs_by_id()["employee-handbook"]
    window = read("employee-handbook", 1)
    assert window["end_line"] < window["total_lines"], (
        "read_doc('employee-handbook', 1) returned the whole document in one window"
    )


def test_consecutive_windows_cover_the_document_without_gaps():
    """Start at line 1 and keep reading from end_line + 1. Every window is
    valid, and the last one ends at total_lines."""
    adapters.run_read_doc(doc_index(), "employee-handbook", 1)  # stub check before anything else
    for doc in data.load_docs():
        total = len(doc["text"].splitlines())
        start, collected, windows = 1, [], 0
        while start <= total:
            window = read(doc["doc_id"], start)
            check_window(window, doc, start)
            collected += doc["text"].splitlines()[start - 1 : window["end_line"]]
            start = window["end_line"] + 1
            windows += 1
            assert windows <= total, f"{doc['doc_id']}: reading did not advance"
        assert collected == doc["text"].splitlines(), (
            f"{doc['doc_id']}: the windows read in sequence do not add up to the document"
        )


@pytest.mark.parametrize("start_line", [0, -3, 100_000])
def test_start_line_outside_the_document_raises(start_line):
    with pytest.raises((ValueError, LookupError)):
        adapters.run_read_doc(doc_index(), "employee-handbook", start_line)


def test_start_line_one_past_the_end_raises():
    total = len(docs_by_id()["pto-policy"]["text"].splitlines())
    adapters.run_read_doc(doc_index(), "pto-policy", total)  # the last line is valid
    with pytest.raises((ValueError, LookupError)):
        adapters.run_read_doc(doc_index(), "pto-policy", total + 1)


@pytest.mark.parametrize("doc_id", ["no-such-document", "", "employee-handbook.md", "EMPLOYEE-HANDBOOK"])
def test_unknown_doc_id_raises(doc_id):
    """doc_id is the file name without .md, compared exactly."""
    with pytest.raises((ValueError, LookupError)):
        adapters.run_read_doc(doc_index(), doc_id, 1)


def test_read_doc_is_stable():
    first, second = read("it-security-policy", 20), read("it-security-policy", 20)
    assert first == second, "two identical run_read_doc calls returned different windows"


# ----------------------------------------------------------------- live ---

LIVE_MAX_TURNS = 12
LIVE_WORKERS = 4


def result_tokens(transcript) -> int:
    """Tokens of everything search_docs and read_doc returned in one conversation."""
    return sum(
        count_tokens(e["content"])
        for e in events(transcript, "tool_result")
        if e.get("name") in ("search_docs", "read_doc")
    )


@pytest.mark.live
def test_live_doc_questions(live_lm, live_aux, tmp_path):
    """Your full agent (tools=None, auto mode) answers each question in
    tests/fixtures/doc_questions.json in a fresh session. An answer is
    correct if it contains one of the question's accepted answers (compared
    with tests.helpers.contains). Two requirements:

    1. at least SEARCH_DOCS_MIN_ACCURACY of the answers are correct;
    2. in every conversation, the tool results of search_docs and read_doc
       add up to at most SEARCH_DOCS_MAX_RESULT_TOKENS tokens.
    """
    questions = eval_slice(load_fixture("doc_questions.json"))

    def ask(item: dict) -> dict:
        config = AgentConfig(max_turns=LIVE_MAX_TURNS, aux_lm=live_aux, workspace=tmp_path / item["id"])
        session = adapters.run_agent_session(live_lm, None, config)
        result = session.send(item["question"])
        return {
            "item": item,
            "text": result.text,
            "status": result.status,
            "correct": contains_any(result.text, item["answers"]),
            "tokens": result_tokens(session.transcript),
            "calls": len(events(session.transcript, "tool_call")),
        }

    adapters.run_search_docs(doc_index(), "policy", 1)  # stub check before any thread starts
    with ThreadPoolExecutor(max_workers=LIVE_WORKERS) as pool:
        rows = list(pool.map(ask, questions))

    correct = sum(r["correct"] for r in rows)
    needed = -(-len(rows) * SEARCH_DOCS_MIN_ACCURACY // 1)
    over = [r for r in rows if r["tokens"] > SEARCH_DOCS_MAX_RESULT_TOKENS]
    lines = [f"\nsearch_docs live: {correct} of {len(rows)} correct (need {int(needed)}), model {live_lm.model}"]
    lines.append(
        f"search_docs and read_doc result tokens per question: max {max(r['tokens'] for r in rows)}, "
        f"mean {sum(r['tokens'] for r in rows) // len(rows)} (limit {SEARCH_DOCS_MAX_RESULT_TOKENS})"
    )
    for r in rows:
        mark = "ok  " if r["correct"] else "MISS"
        lines.append(
            f"  {mark} {r['item']['id']} [{r['item']['kind']}] {r['tokens']:>5} tokens, "
            f"{r['calls']} tool calls, status {r['status']}: {r['item']['question']}"
        )
        if not r["correct"]:
            lines.append(f"       expected one of {r['item']['answers']}; got: {r['text'][:300]!r}")
    report = "\n".join(lines)
    print(report)
    if correct < needed:
        pytest.fail(f"{correct} of {len(rows)} answers are correct; need at least {int(needed)}.", pytrace=False)
    if over:
        ids = ", ".join(f"{r['item']['id']} ({r['tokens']})" for r in over)
        pytest.fail(
            f"search_docs and read_doc returned more than {SEARCH_DOCS_MAX_RESULT_TOKENS} tokens "
            f"in these conversations: {ids}. Return short snippets and bounded windows.",
            pytrace=False,
        )

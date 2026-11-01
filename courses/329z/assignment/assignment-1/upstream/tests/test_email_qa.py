"""Tests for problem (email_qa)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from cs329z_hw1.llm import ScriptedLM
from cs329z_hw1 import adapters
from tests.conftest import eval_slice
from tests.helpers import contains_any, load_fixture
from tests.thresholds import EMAIL_QA_MIN_ACCURACY

HOP_BUDGET = 3


class FakeSearch:
    """A search function that records its calls. Every call returns k new
    emails with ids em-80001, em-80002, ... (or nothing, if empty=True)."""

    def __init__(self, empty: bool = False):
        self.empty = empty
        self.queries: list[str] = []
        self.returned_ids: list[str] = []

    def __call__(self, query: str, k: int = 5) -> list[dict]:
        self.queries.append(query)
        if self.empty:
            return []
        emails = []
        for _ in range(k):
            n = len(self.returned_ids) + 1
            email = {
                "id": f"em-8{n:04d}",
                "thread_id": f"th-8{n:04d}",
                "reply_to": None,
                "from": f"person{n}@cardinal.example",
                "to": ["sam.lee@cardinal.example"],
                "date": f"2001-05-{1 + n % 28:02d}T09:00:00Z",
                "subject": "" if n % 4 == 0 else f"Status note {n}",
                "body": f"Note {n}: the review moved to room {100 + n}.\n",
            }
            self.returned_ids.append(email["id"])
            emails.append(email)
        return emails


# The scripted model gives the same reply to every call. The replies follow
# no particular format. Several ask for another search in different ways, to
# check that no reply can make the loop search more than three times.
REPLIES = {
    "garbage": "%%% <<>> lorem ipsum {]",
    "empty": "",
    "wants_search_1": "SEARCH: budget review room",
    "wants_search_2": "I need more information. Next query: budget review room",
    "wants_search_3": '{"action": "search", "query": "budget review room"}',
    "wants_search_4": "<search>budget review room</search>",
    "unknown_id": "The answer is room 101, based on em-99999 and em-00000.",
    "every_keyword": "ANSWER SEARCH QUERY FINAL SUPPORT em-99999 answer: search: query: final:",
    "long": "I am not sure. " * 300,
}


def check_shape(result, search: FakeSearch, context: str) -> None:
    shown = f"{context} run_email_qa returned {result!r}."
    assert isinstance(result, dict), f"run_email_qa should return a dict. {shown}"
    assert "answer" in result and "support" in result, (
        f"The result needs the keys 'answer' and 'support'. {shown}"
    )
    assert result["answer"] is None or isinstance(result["answer"], str), (
        f"'answer' must be a string, or None when no answer was found. {shown}"
    )
    assert isinstance(result["support"], list) and all(
        isinstance(i, str) for i in result["support"]
    ), f"'support' must be a list of email id strings. {shown}"
    unknown = [i for i in result["support"] if i not in search.returned_ids]
    assert not unknown, (
        f"'support' contains {unknown}, which search() did not return during this call. "
        f"search() returned {search.returned_ids}. {shown}"
    )


@pytest.mark.parametrize("name", list(REPLIES))
def test_hop_budget_and_shape_for_any_reply(name):
    search = FakeSearch()
    lm = ScriptedLM([REPLIES[name]], repeat_last=True)
    result = adapters.run_email_qa("Which room did the budget review move to?", search, lm)
    context = f"Every model call was answered with the {name!r} scripted reply."
    assert len(search.queries) <= HOP_BUDGET, (
        f"search() was called {len(search.queries)} times; the hop budget is {HOP_BUDGET}. {context}"
    )
    check_shape(result, search, context)


@pytest.mark.parametrize("name", ["garbage", "wants_search_1", "unknown_id"])
def test_search_returns_nothing(name):
    search = FakeSearch(empty=True)
    lm = ScriptedLM([REPLIES[name]], repeat_last=True)
    result = adapters.run_email_qa("Which room did the budget review move to?", search, lm)
    context = f"search() returned no emails and the model replied with the {name!r} scripted reply."
    assert len(search.queries) <= HOP_BUDGET, (
        f"search() was called {len(search.queries)} times; the hop budget is {HOP_BUDGET}. {context}"
    )
    check_shape(result, search, context)


# ------------------------------------------------------------------ live ---

_cache: dict = {}


def make_search(archive):
    """search(query, k) over the archive, built from your BM25 index."""
    if "index" not in _cache:
        from cs329z_hw1.data import email_text

        _cache["index"] = adapters.run_bm25_build([email_text(email) for email in archive])
    index = _cache["index"]

    def search(query: str, k: int = 5) -> list[dict]:
        return [archive[doc_id] for doc_id, _ in adapters.run_bm25_search(index, query, k)]

    return search


def live_answers(archive, lm) -> list[tuple[dict, dict]]:
    """(gold item, your result) for each question in tests/fixtures/email_qa.json.
    Computed once and shared by the two live tests."""
    if "answers" not in _cache:
        items = eval_slice(load_fixture("email_qa.json"))
        search = make_search(archive)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(
                pool.map(lambda item: adapters.run_email_qa(item["question"], search, lm), items)
            )
        _cache["answers"] = list(zip(items, results))
    return _cache["answers"]


def is_correct(item: dict, result: dict) -> bool:
    return isinstance(result.get("answer"), str) and contains_any(result["answer"], item["answers"])


@pytest.mark.live
def test_live_accuracy(archive, live_lm):
    """An answer is correct if it contains any of the gold aliases."""
    pairs = live_answers(archive, live_lm)
    wrong = [
        f"  {item['id']} ({item['hops']}-hop) {item['question']!r}\n"
        f"    expected one of {item['answers']}, got {result.get('answer')!r}"
        for item, result in pairs
        if not is_correct(item, result)
    ]
    correct = len(pairs) - len(wrong)
    for hops in (1, 2):
        subset = [(i, r) for i, r in pairs if i["hops"] == hops]
        print(f"email_qa {hops}-hop: {sum(is_correct(i, r) for i, r in subset)} of {len(subset)}")
    print(f"email_qa accuracy: {correct} of {len(pairs)}")
    if wrong:
        print("wrong answers:\n" + "\n".join(wrong))
    assert correct / len(pairs) >= EMAIL_QA_MIN_ACCURACY, (
        f"{correct} of {len(pairs)} answers are correct ({correct / len(pairs):.0%}); "
        f"at least {EMAIL_QA_MIN_ACCURACY:.0%} is required. Wrong answers:\n" + "\n".join(wrong)
    )


@pytest.mark.live
def test_live_support(archive, live_lm):
    """For every correctly answered question, 'support' must include at
    least one of the gold supporting emails."""
    pairs = live_answers(archive, live_lm)
    answered = [(item, result) for item, result in pairs if is_correct(item, result)]
    missing = [
        f"  {item['id']} {item['question']!r}\n"
        f"    gold support {item['support']}, your support {result.get('support')!r}"
        for item, result in answered
        if not set(result.get("support") or []) & set(item["support"])
    ]
    print(f"email_qa support: {len(answered) - len(missing)} of {len(answered)} correct answers cite a gold email")
    if missing:
        print("missing support:\n" + "\n".join(missing))
    assert answered, "No question was answered correctly, so there is no support to check."
    assert not missing, (
        f"{len(missing)} of {len(answered)} correct answers cite no gold email:\n"
        + "\n".join(missing)
    )

"""Tests for problem (compaction).

The rule under test: for every model call your agent makes,
``count_message_tokens(messages) <= config.context_budget``, however long
the session is. The transcript is a log and is never shortened.

The deterministic tests use the fixture tools, a scripted model, and
``canned_aux`` as ``AgentConfig.aux_lm``. If your compaction calls a model
(for a summary), it must call ``aux_lm``, not the agent's model: the scripted
model has exactly one reply per agent turn, and an extra call ends the test
with ScriptExhausted.

COMPACTION_BUDGET is 4000 tokens. Your system prompt with the seven fixture
tools rendered must fit in it with room for the conversation (the reference
solution's is under 1000 tokens).
"""

from __future__ import annotations

import copy

import pytest

from cs329z_hw1.llm import ScriptedLM
from cs329z_hw1.tokens import count_message_tokens, count_tokens
from cs329z_hw1.types import AgentConfig, AgentResult
from cs329z_hw1 import adapters
from tests.fixture_tools import make_fixture_tools
from tests.helpers import events

COMPACTION_BUDGET = 4000
SENDS = 12
CALLS_PER_SEND = 5  # four tool calls and an answer: 60 model calls in total


def call(name: str, **args) -> dict:
    return {"text": "", "tool_call": {"name": name, "args": args}}


def user_message(i: int) -> str:
    return f"Request {i:02d}: run the usual checks and report. The reference for this request is REQ-{i:02d}-{7000 + 37 * i}."


def marker(i: int) -> str:
    return f"REQ-{i:02d}-{7000 + 37 * i}"


def send_script(i: int) -> list:
    return [
        call("big_output", n_lines=30 + i),
        call("lookup", key="parking_office"),
        call("big_output", n_lines=40),
        call("echo", text=f"Check {i:02d} finished. " + "The readings were within the expected range. " * 12),
        f"Request {i:02d} is complete: all checks passed.",
    ]


def send(session, message: str) -> AgentResult:
    try:
        return session.send(message)
    except NotImplementedError:
        raise
    except Exception as exc:
        pytest.fail(f"session.send raised {type(exc).__name__}: {exc}", pytrace=False)


def assert_within_budget(calls, budget: int, first_index: int = 1) -> None:
    for i, messages in enumerate(calls, start=first_index):
        size = count_message_tokens(messages)
        assert size <= budget, (
            f"model call {i} has {size} tokens in its messages; context_budget is {budget}. "
            "The budget must hold for every model call."
        )


def run_long_session(scripted, canned_aux):
    script = [entry for i in range(1, SENDS + 1) for entry in send_script(i)]
    lm = scripted(script + ["Yes, the session is still working."])
    fx = make_fixture_tools()
    config = AgentConfig(context_budget=COMPACTION_BUDGET, aux_lm=canned_aux, max_turns=10)
    session = adapters.run_agent_session(lm, fx.tools, config)
    results, snapshot = [], None
    for i in range(1, SENDS + 1):
        results.append(send(session, user_message(i)))
        if i == 3:
            snapshot = copy.deepcopy(list(session.transcript))
    return lm, fx, session, results, snapshot


def test_budget_holds_on_every_call_of_a_60_turn_session(scripted, canned_aux):
    """Twelve user messages, five model calls each, with tool results of 300
    to 450 tokens: about 15,000 tokens of conversation against a budget of
    4000. Every one of the 60 model calls must be within the budget, and
    every send must finish with status done."""
    lm, fx, session, results, _ = run_long_session(scripted, canned_aux)

    statuses = [r.status for r in results]
    assert statuses == ["done"] * SENDS, f"expected every send to finish with 'done', got {statuses}"
    assert len(lm.calls) == SENDS * CALLS_PER_SEND, (
        f"expected {SENDS * CALLS_PER_SEND} model calls on the agent's model, got {len(lm.calls)}"
    )
    total = sum(count_tokens(e.get("content", "")) for e in session.transcript if isinstance(e.get("content"), str))
    assert total > 2 * COMPACTION_BUDGET, "test setup: the session should be much longer than the budget"
    assert_within_budget(lm.calls, COMPACTION_BUDGET)
    assert fx.count("big_output") == 2 * SENDS and fx.count("lookup") == SENDS and fx.count("echo") == SENDS, (
        f"every scripted tool call should have run once; recorded {len(fx.calls)} calls"
    )


def test_latest_user_message_is_in_every_call(scripted, canned_aux):
    """Whatever is compacted away, the user message being worked on is in the
    messages of each of the five model calls made for it."""
    lm, fx, session, results, _ = run_long_session(scripted, canned_aux)
    for i in range(1, SENDS + 1):
        for j in range(CALLS_PER_SEND):
            index = (i - 1) * CALLS_PER_SEND + j
            assert any(marker(i) in m["content"] for m in lm.calls[index]), (
                f"model call {index + 1} (call {j + 1} of user message {i}) does not contain "
                f"that user message (looked for {marker(i)!r})"
            )


def test_transcript_keeps_every_event(scripted, canned_aux):
    """Compaction changes what is sent to the model, not the transcript: it
    still holds all 12 user messages, all 60 raw replies in order, and all 48
    tool calls and results, and events logged early are unchanged later."""
    lm, fx, session, results, snapshot = run_long_session(scripted, canned_aux)
    transcript = list(session.transcript)

    users = [e["content"] for e in events(transcript, "user")]
    assert users == [user_message(i) for i in range(1, SENDS + 1)], (
        f"the transcript should hold the {SENDS} user messages in order; it holds {len(users)} user events"
    )
    replies = [e["content"] for e in events(transcript, "assistant")]
    assert replies == lm.replies[: SENDS * CALLS_PER_SEND], (
        f"the transcript should hold the {SENDS * CALLS_PER_SEND} raw model replies in order; "
        f"it holds {len(replies)} assistant events"
    )
    n_calls, n_results = len(events(transcript, "tool_call")), len(events(transcript, "tool_result"))
    assert n_calls == n_results == 4 * SENDS, (
        f"expected {4 * SENDS} tool_call and {4 * SENDS} tool_result events, got {n_calls} and {n_results}"
    )
    assert transcript[: len(snapshot)] == snapshot, (
        "events that were in the transcript after the third send changed later. "
        "Compaction must not edit or remove transcript events."
    )
    assert results[-1].transcript == transcript, "AgentResult.transcript differs from session.transcript"


def test_session_still_works_after_many_compactions(scripted, canned_aux):
    lm, fx, session, results, _ = run_long_session(scripted, canned_aux)
    result = send(session, "One more question: is the session still working? Reference FINAL-9912.")
    assert result.status == "done", f"expected 'done', got {result.status!r}"
    assert "still working" in result.text, f"expected the scripted answer, got {result.text!r}"
    assert_within_budget(lm.calls[-1:], COMPACTION_BUDGET, first_index=len(lm.calls))
    assert any("FINAL-9912" in m["content"] for m in lm.calls[-1]), (
        "the last user message is not in the last model call"
    )


def test_one_result_larger_than_the_budget(scripted, canned_aux):
    """A single tool result of about 30,000 tokens with a budget of 4000: the
    next model call is still within the budget."""
    lm = scripted([call("big_output", n_lines=3000), call("big_output", n_lines=3000), "Done."])
    fx = make_fixture_tools()
    config = AgentConfig(context_budget=COMPACTION_BUDGET, aux_lm=canned_aux)
    session = adapters.run_agent_session(lm, fx.tools, config)
    result = send(session, "Print the large output twice. Reference BIG-5561.")
    assert result.status == "done", f"expected 'done', got {result.status!r}"
    assert_within_budget(lm.calls, COMPACTION_BUDGET)
    assert any("BIG-5561" in m["content"] for m in lm.calls[-1]), (
        "the user message is not in the last model call"
    )


def test_no_compaction_needed_means_nothing_is_lost(scripted, canned_aux):
    """With the default budget a short session fits, so the first tool result
    is still in the last model call."""
    lm = scripted([call("lookup", key="hq_address"), call("add", a=1, b=2), "Done."])
    fx = make_fixture_tools()
    session = adapters.run_agent_session(lm, fx.tools, AgentConfig(aux_lm=canned_aux))
    send(session, "Look up the address, then add.")
    from tests.fixture_tools import DIRECTORY

    assert any(DIRECTORY["hq_address"] in m["content"] for m in lm.calls[2]), (
        "the first tool result is missing from the third model call although the "
        "conversation is far below the default context_budget"
    )


# ----------------------------------------------------------------- live ---


class ScriptThenLive:
    """Replays ``script`` (one entry per call, tool calls written in your
    format), then passes every later call to ``live``. Records every call."""

    def __init__(self, script, live) -> None:
        self.scripted = ScriptedLM(script, formatter=adapters.run_format_tool_call)
        self.live = live
        self.calls: list[list[dict]] = []

    def __call__(self, messages):
        self.calls.append([dict(m) for m in messages])
        if self.scripted.remaining:
            return self.scripted(messages)
        return self.live(messages)


CONSTRAINT_MESSAGE = (
    "I am planning the team offsite and will need your help for a while. Two things to "
    "keep in mind for everything that follows: the budget cap is 18,450 dollars, and the "
    "offsite has to be in Boulder, not in Oakland."
)
FINAL_QUESTION = "Before I book anything: what is my budget cap for the offsite, and which city does it have to be in?"


@pytest.mark.live
def test_live_constraint_survives_compaction(live_lm, live_aux):
    """The user states two constraints in the first message. Eleven scripted
    requests with sizable tool results follow (no live calls for those turns;
    your compaction may call aux_lm, which is live). With a budget of 4000
    tokens the first message is compacted away several times over. Then one
    live question asks for the constraints. The answer must contain the
    budget cap (18,450) and the city (Boulder), and every model call must be
    within the budget."""
    script = ["Understood: the budget cap and the location are noted."]
    for i in range(1, SENDS):
        script += send_script(i)
    lm = ScriptThenLive(script, live_lm)
    fx = make_fixture_tools()
    config = AgentConfig(context_budget=COMPACTION_BUDGET, aux_lm=live_aux, max_turns=10)
    session = adapters.run_agent_session(lm, fx.tools, config)

    session.send(CONSTRAINT_MESSAGE)
    for i in range(1, SENDS):
        session.send(user_message(i))
    scripted_calls = len(lm.calls)
    result = session.send(FINAL_QUESTION)

    from tests.helpers import contains

    sizes = [count_message_tokens(m) for m in lm.calls]
    has_cap = contains(result.text, "18,450") or contains(result.text, "18450")
    has_city = contains(result.text, "Boulder")
    print(
        f"\ncompaction live: budget cap {'found' if has_cap else 'MISSING'}, city "
        f"{'found' if has_city else 'MISSING'}; {scripted_calls} scripted calls, "
        f"{len(lm.calls) - scripted_calls} live calls, largest call {max(sizes)} tokens "
        f"(budget {COMPACTION_BUDGET}), model {live_lm.model}\nanswer: {result.text!r}"
    )
    assert_within_budget(lm.calls, COMPACTION_BUDGET)
    assert has_cap and has_city, (
        "after compaction the agent no longer knows what the user required in the first "
        f"message (budget cap 18,450 dollars; Boulder). Its answer: {result.text!r}"
    )

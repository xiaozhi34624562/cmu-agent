"""Tests for problem (agent_loop). Deterministic: no model calls.

Each test builds a session with ``run_agent_session`` from a ScriptedLM and
the fixture tools in ``tests/fixture_tools.py``. Scripted tool calls are
written in your own format by ``run_format_tool_call``. The tests read three
things: the messages your agent sent to the model (``lm.calls``), which
fixture tools ran (``fx.calls``), and the transcript. They never check the
wording of your prompts or how you present a tool result to the model, only
that the result's content string appears somewhere in the next model call.
"""

from __future__ import annotations

import copy

import pytest

from cs329z_hw1.llm import ScriptExhausted
from cs329z_hw1.tokens import count_message_tokens, count_tokens
from cs329z_hw1.types import AgentConfig, AgentResult, ToolCall
from cs329z_hw1 import adapters
from tests.fixture_tools import DIRECTORY, FAIL_MESSAGE, TOOL_NAMES, make_fixture_tools
from tests.helpers import events, truncated

KNOWN_TYPES = ("user", "assistant", "tool_call", "tool_result", "error")


@pytest.fixture(autouse=True)
def _canned_aux(canned_aux):
    """Every session in this file gets the canned auxiliary model (see
    conftest.py) as AgentConfig.aux_lm unless a test passes another one, so
    an agent may call aux_lm on any send without using up scripted replies."""
    global AUX
    AUX = canned_aux


AUX = None


# ------------------------------------------------------------- helpers ----


def call(name: str, _say: str = "", **args) -> dict:
    """A script entry: one model reply that says ``_say`` and calls ``name``
    with ``args``."""
    return {"text": _say, "tool_call": {"name": name, "args": args}}


def two_calls_reply() -> str:
    """A reply that cannot be parsed: two formatted calls in one reply."""
    first = adapters.run_format_tool_call("", ToolCall("add", {"a": 1, "b": 2}))
    second = adapters.run_format_tool_call("", ToolCall("echo", {"text": "second"}))
    return first + "\n" + second


def malformed(kind: str):
    """A script entry for one malformed reply of the given kind."""
    if kind == "unparseable":
        return two_calls_reply()
    if kind == "unknown_tool":
        return call("no_such_tool", x=1)
    if kind == "invalid_args":
        return call("add", a=1)  # b is missing
    raise ValueError(kind)


MALFORMED_KINDS = ["unparseable", "unknown_tool", "invalid_args"]


def make_session(lm, fx=None, **config):
    fx = fx if fx is not None else make_fixture_tools()
    config.setdefault("aux_lm", AUX)
    session = adapters.run_agent_session(lm, fx.tools, AgentConfig(**config))
    return session, fx


def send(session, message: str) -> AgentResult:
    """session.send, with the checks every test relies on."""
    try:
        result = session.send(message)
    except NotImplementedError:
        raise
    except Exception as exc:
        pytest.fail(
            f"session.send({message!r}) raised {type(exc).__name__}: {exc}\n"
            "send must return an AgentResult and not raise.",
            pytrace=False,
        )
    assert isinstance(result, AgentResult), (
        f"send must return a cs329z_hw1.types.AgentResult, got {type(result).__name__}"
    )
    assert isinstance(result.text, str), f"AgentResult.text must be a str, got {result.text!r}"
    return result


def known(transcript) -> list[dict]:
    """Transcript events of the types listed in types.py, in order."""
    return [e for e in transcript if e.get("type") in KNOWN_TYPES]


def types_of(transcript) -> list[str]:
    return [e["type"] for e in known(transcript)]


def shown(messages, needle: str) -> bool:
    """True if ``needle`` appears in the content of any message."""
    return any(needle in m["content"] for m in messages)


def expect_status(result: AgentResult, status: str) -> None:
    assert result.status == status, (
        f"expected status {status!r}, got {result.status!r} with text {result.text!r}"
    )


def expect_lm_calls(lm, n: int) -> None:
    assert len(lm.calls) == n, f"expected exactly {n} model calls, your agent made {len(lm.calls)}"


# ------------------------------------------------------- plain answer -----


def test_plain_answer(scripted):
    """The model answers without a tool: one model call, status done, the
    answer in AgentResult.text, and a transcript of one user event and one
    assistant event holding the raw reply."""
    lm = scripted(["The office opens at 8 am."])
    session, fx = make_session(lm)
    result = send(session, "When does the office open?")

    expect_status(result, "done")
    expect_lm_calls(lm, 1)
    assert "The office opens at 8 am." in result.text, (
        f"expected the model's answer in AgentResult.text, got {result.text!r}"
    )
    assert fx.calls == [], f"no tool should run for a plain answer; recorded calls: {fx.calls}"
    assert known(session.transcript) == [
        {"type": "user", "content": "When does the office open?"},
        {"type": "assistant", "content": lm.replies[0]},
    ], f"unexpected transcript for a plain answer: {known(session.transcript)}"


def test_first_model_call_has_the_tools_and_the_user_message(scripted):
    """The first message of the first model call (the system prompt) names
    every tool, and the user's message is somewhere in that call."""
    lm = scripted(["Hello."])
    session, fx = make_session(lm)
    send(session, "A message with the marker QX-7719.")

    messages = lm.calls[0]
    missing = [name for name in TOOL_NAMES if name not in messages[0]["content"]]
    assert not missing, (
        f"the first message of the first model call does not mention these tools: "
        f"{missing}. It should include your run_render_tools output."
    )
    assert shown(messages, "QX-7719"), "the user's message does not appear in the first model call"


# -------------------------------------------------------- tool calls ------


def test_tool_call_then_answer(scripted):
    """One tool call, then an answer. The tool runs once with the scripted
    arguments, its output appears in the next model call, and the transcript
    records user, assistant, tool_call, tool_result, assistant."""
    lm = scripted([call("lookup", "Looking it up.", key="it_helpdesk"), "It is extension 4410."])
    session, fx = make_session(lm)
    result = send(session, "What is the helpdesk extension?")

    expect_status(result, "done")
    expect_lm_calls(lm, 2)
    assert fx.calls == [("lookup", {"key": "it_helpdesk"})], (
        f"expected lookup to run once with key='it_helpdesk'; recorded calls: {fx.calls}"
    )
    output = DIRECTORY["it_helpdesk"]
    assert shown(lm.calls[1], output), (
        f"the tool returned {output!r}, but that string is not in any message of the "
        "next model call. The model must see the tool result."
    )
    assert "It is extension 4410." in result.text, f"expected the final answer in text, got {result.text!r}"

    assert types_of(session.transcript) == ["user", "assistant", "tool_call", "tool_result", "assistant"], (
        f"expected transcript events user, assistant, tool_call, tool_result, assistant; "
        f"got {types_of(session.transcript)}"
    )
    _, first_reply, tool_call, tool_result, last_reply = known(session.transcript)
    assert first_reply["content"] == lm.replies[0], "the assistant event must hold the raw model reply"
    assert last_reply["content"] == lm.replies[1], "the assistant event must hold the raw model reply"
    assert tool_call.get("name") == "lookup" and tool_call.get("args") == {"key": "it_helpdesk"}, (
        f"expected a tool_call event with name 'lookup' and args {{'key': 'it_helpdesk'}}, got {tool_call}"
    )
    assert tool_result.get("name") == "lookup" and tool_result.get("status") == "ok", (
        f"expected a tool_result event with name 'lookup' and status 'ok', got {tool_result}"
    )
    assert output in tool_result.get("content", ""), (
        f"expected the tool output {output!r} in the tool_result event's content, got {tool_result}"
    )
    assert shown(lm.calls[1], tool_result["content"]), (
        "the tool_result event's content must be the string shown to the model, but it "
        "does not appear in the next model call"
    )


def test_several_steps(scripted):
    """Three tool calls and an answer: four model calls, tools run in the
    scripted order, and each result is visible in the following model call."""
    lm = scripted(
        [
            call("add", a=17, b=25),
            call("lookup", key="parking_office"),
            call("write_note", text="sum is 42"),
            "All three steps are finished.",
        ]
    )
    session, fx = make_session(lm)
    result = send(session, "Do the three steps.")

    expect_status(result, "done")
    expect_lm_calls(lm, 4)
    assert fx.calls == [
        ("add", {"a": 17, "b": 25}),
        ("lookup", {"key": "parking_office"}),
        ("write_note", {"text": "sum is 42"}),
    ], f"the tools did not run in the scripted order with the scripted args: {fx.calls}"
    assert fx.notes == ["sum is 42"], f"expected one saved note, got {fx.notes}"
    for i, output in enumerate(["42", DIRECTORY["parking_office"], "saved note 1"], start=1):
        assert shown(lm.calls[i], output), (
            f"tool output {output!r} from step {i} is not in any message of model call {i + 1}"
        )
    assert types_of(session.transcript) == (
        ["user"] + ["assistant", "tool_call", "tool_result"] * 3 + ["assistant"]
    ), f"unexpected transcript event order: {types_of(session.transcript)}"
    statuses = [e["status"] for e in events(session.transcript, "tool_result")]
    assert statuses == ["ok", "ok", "ok"], f"expected three ok tool results, got {statuses}"


def test_earlier_results_stay_visible(scripted):
    """With the default budgets and a short session, the first tool result is
    still in the context of the last model call."""
    lm = scripted([call("lookup", key="hq_address"), call("add", a=1, b=2), "Done."])
    session, fx = make_session(lm)
    send(session, "Look up the address, then add.")
    assert shown(lm.calls[2], DIRECTORY["hq_address"]), (
        "the first tool result is missing from the third model call; the model needs "
        "the whole conversation so far"
    )


def test_tool_that_raises_gives_tool_error_and_the_run_continues(scripted):
    """A tool that raises produces a tool_result with status tool_error whose
    content includes the exception message; the model sees it and the run
    goes on."""
    lm = scripted([call("fail"), "The tool failed, so I cannot complete that."])
    session, fx = make_session(lm)
    result = send(session, "Run the failing tool.")

    expect_status(result, "done")
    expect_lm_calls(lm, 2)
    results = events(session.transcript, "tool_result")
    assert len(results) == 1 and results[0]["status"] == "tool_error", (
        f"expected one tool_result event with status 'tool_error', got {results}"
    )
    assert FAIL_MESSAGE in results[0]["content"], (
        f"expected the exception message {FAIL_MESSAGE!r} in the tool_result content, "
        f"got {results[0]['content']!r}"
    )
    assert shown(lm.calls[1], FAIL_MESSAGE), (
        "the exception message is not in any message of the next model call"
    )


def test_tool_errors_do_not_count_as_malformed(scripted):
    """tool_error is not a malformed reply: four failing calls in a row do
    not end the run."""
    lm = scripted([call("fail")] * 4 + ["Giving up on that tool."])
    session, fx = make_session(lm)
    result = send(session, "Keep trying the failing tool.")
    expect_status(result, "done")
    expect_lm_calls(lm, 5)
    assert fx.count("fail") == 4, f"expected fail to run 4 times, ran {fx.count('fail')}"


# ---------------------------------------------------- malformed replies ---


@pytest.mark.parametrize("kind", MALFORMED_KINDS)
def test_malformed_reply_then_recovery(scripted, kind):
    """One malformed reply, then a valid call, then an answer. The error is
    fed back to the model (its text appears in the next model call), nothing
    runs for the malformed reply, and the run ends with status done.

    unparseable: two calls in one reply. The transcript gets an assistant
    event and then an error event holding the message sent back.
    unknown_tool / invalid_args: the transcript gets a tool_result event with
    that status, holding the registry's error content."""
    lm = scripted([malformed(kind), call("echo", text="recovered"), "Recovered and finished."])
    session, fx = make_session(lm)
    result = send(session, "Do the task.")

    expect_status(result, "done")
    expect_lm_calls(lm, 3)
    assert fx.calls == [("echo", {"text": "recovered"})], (
        f"only the valid echo call should have run; recorded calls: {fx.calls}"
    )

    if kind == "unparseable":
        assert types_of(session.transcript)[:3] == ["user", "assistant", "error"], (
            f"after an unparseable reply the transcript should continue with an "
            f"assistant event and an error event; got {types_of(session.transcript)}"
        )
        feedback = events(session.transcript, "error")[0].get("content", "")
    else:
        results = events(session.transcript, "tool_result")
        assert results and results[0]["status"] == kind, (
            f"expected the first tool_result event to have status {kind!r}, got {results[:1]}"
        )
        feedback = results[0].get("content", "")
    assert isinstance(feedback, str) and feedback.strip(), (
        f"the error fed back to the model must be a non-empty string, got {feedback!r}"
    )
    assert shown(lm.calls[1], feedback), (
        f"the error text recorded in the transcript ({feedback!r}) does not appear in "
        "the next model call. The model must see the error to recover."
    )


def test_reply_cut_off_at_max_tokens_then_recovery(scripted):
    """The first model call raises OutputTruncated (the model stopped at
    max_tokens), then a valid call, then an answer. A cut-off reply is a
    malformed reply: send must not raise, the transcript gets an error event
    for it, and the run ends with status done."""
    lm = scripted([truncated("I will call echo with"), call("echo", text="recovered"), "Recovered and finished."])
    session, fx = make_session(lm)
    result = send(session, "Do the task.")

    expect_status(result, "done")
    expect_lm_calls(lm, 3)
    assert fx.calls == [("echo", {"text": "recovered"})], (
        f"only the valid echo call should have run; recorded calls: {fx.calls}"
    )
    errors = events(session.transcript, "error")
    assert errors and isinstance(errors[0].get("content"), str) and errors[0]["content"].strip(), (
        f"the transcript needs an error event with non-empty content for the cut-off reply; "
        f"got event types {types_of(session.transcript)}"
    )


def test_malformed_counter_resets_after_a_good_reply(scripted):
    """Two malformed replies, a valid call, two more malformed replies, then
    an answer. No run of three consecutive malformed replies occurs, so the
    status is done after six model calls."""
    lm = scripted(
        [
            malformed("unparseable"),
            malformed("unknown_tool"),
            call("echo", text="ok"),
            malformed("invalid_args"),
            malformed("unparseable"),
            "Finished.",
        ]
    )
    session, fx = make_session(lm)
    result = send(session, "Do the task.")
    expect_status(result, "done")
    expect_lm_calls(lm, 6)


@pytest.mark.parametrize(
    "kinds",
    [
        ["unparseable"] * 3,
        ["unknown_tool"] * 3,
        ["invalid_args"] * 3,
        ["invalid_args", "unparseable", "unknown_tool"],
    ],
    ids=["unparseable", "unknown_tool", "invalid_args", "mixed"],
)
def test_three_consecutive_malformed_replies_end_the_send(scripted, kinds):
    """After the third consecutive malformed reply the send ends with status
    malformed. Exactly three model calls are made and no tool runs."""
    lm = scripted([malformed(k) for k in kinds] + ["This reply must not be requested."] * 3)
    session, fx = make_session(lm)
    result = send(session, "Do the task.")

    expect_status(result, "malformed")
    expect_lm_calls(lm, 3)
    assert fx.calls == [], f"no tool should run for malformed replies; recorded calls: {fx.calls}"
    assert result.text.strip(), "AgentResult.text must tell the user something when the run stops"


def test_session_is_usable_after_a_malformed_stop(scripted):
    lm = scripted([malformed("unparseable")] * 3 + ["Here is a normal answer."])
    session, fx = make_session(lm)
    expect_status(send(session, "First request."), "malformed")
    second = send(session, "Second request.")
    expect_status(second, "done")
    expect_lm_calls(lm, 4)


def test_exception_from_the_model_is_not_swallowed(scripted):
    """send contains every exception raised by a tool, but an exception
    raised by the model call itself propagates to the caller. Here the script
    has one reply (a tool call), so the second model call raises
    ScriptExhausted. send must let it through, not turn it into a result."""
    lm = scripted([call("echo", text="once")])
    session, fx = make_session(lm)
    with pytest.raises(ScriptExhausted):
        session.send("Echo, then answer.")
    assert len(lm.calls) == 2, (
        f"expected the second model call to raise after one tool call; the model was called {len(lm.calls)} times"
    )


# ------------------------------------------------------------- limits -----


@pytest.mark.parametrize("max_turns", [1, 4])
def test_max_turns(scripted, max_turns):
    """The model keeps calling tools. The send stops after exactly max_turns
    model calls with status max_turns and a non-empty text, without raising."""
    lm = scripted([call("echo", text="again")], repeat_last=True)
    session, fx = make_session(lm, max_turns=max_turns)
    result = send(session, "Loop forever.")

    expect_status(result, "max_turns")
    expect_lm_calls(lm, max_turns)
    assert result.text.strip(), "AgentResult.text must tell the user the run did not finish"


def test_answer_on_the_last_allowed_turn_is_done(scripted):
    lm = scripted([call("echo", text="x"), call("echo", text="y"), "Final answer."])
    session, fx = make_session(lm, max_turns=3)
    result = send(session, "Three turns.")
    expect_status(result, "done")
    expect_lm_calls(lm, 3)


def test_max_turns_applies_to_each_send_separately(scripted):
    lm = scripted([call("echo", text="1"), "First done.", call("echo", text="2"), "Second done."])
    session, fx = make_session(lm, max_turns=2)
    expect_status(send(session, "First."), "done")
    expect_status(send(session, "Second."), "done")
    expect_lm_calls(lm, 4)


def spent_per_call(lm) -> list[int]:
    """Tokens charged for each model call: count_message_tokens(messages) +
    count_tokens(reply)."""
    return [count_message_tokens(m) + count_tokens(r) for m, r in zip(lm.calls, lm.replies)]


def test_token_budget_stops_before_the_next_call(scripted):
    """The token total for a send is the sum, over its model calls, of
    count_message_tokens(messages) + count_tokens(reply). Before each model
    call, if the total so far is >= token_budget, the send stops with status
    token_budget. With token_budget=1 the first call is made (the total is 0)
    and the second is not."""
    lm = scripted([call("echo", text="again")], repeat_last=True)
    session, fx = make_session(lm, token_budget=1)
    result = send(session, "Loop forever.")

    expect_status(result, "token_budget")
    expect_lm_calls(lm, 1)
    assert result.text.strip(), "AgentResult.text must tell the user the run did not finish"


def test_token_budget_is_checked_only_before_a_model_call(scripted):
    """A final answer that arrives on a call which crosses the budget is still
    a final answer: status done."""
    lm = scripted(["A complete answer."])
    session, fx = make_session(lm, token_budget=1)
    result = send(session, "One call is enough.")
    expect_status(result, "done")
    expect_lm_calls(lm, 1)


def test_token_budget_stops_at_the_right_call(scripted):
    """Measure the size of your first model call, set a budget of about four
    such calls, and let the model loop. The send must stop with status
    token_budget at the first point where the running total is >= the budget:
    the total before the last call made is below the budget, and the total
    after it is at or above the budget."""
    probe = scripted(["ok"])
    probe_session, _ = make_session(probe)
    send(probe_session, "Loop forever.")
    budget = 4 * count_message_tokens(probe.calls[0]) + 400

    lm = scripted([call("big_output", n_lines=10)], repeat_last=True)
    session, fx = make_session(lm, token_budget=budget, max_turns=200)
    result = send(session, "Loop forever.")

    expect_status(result, "token_budget")
    assert result.text.strip(), "AgentResult.text must tell the user the run did not finish"
    spent = spent_per_call(lm)
    total, before_last = sum(spent), sum(spent[:-1])
    assert before_last < budget, (
        f"token_budget={budget}. Your agent made {len(spent)} model calls costing {spent} "
        f"tokens. The total before the last call was {before_last}, which is already >= "
        "the budget, so the last call should not have been made."
    )
    assert total >= budget, (
        f"token_budget={budget}. Your agent stopped after {len(spent)} model calls costing "
        f"{spent} tokens, a total of {total}, which is below the budget. It should have "
        "continued."
    )


# ------------------------------------------------- sessions and transcript


def test_second_send_sees_the_first_exchange(scripted):
    """A session is one conversation: the first model call of the second send
    contains the first user message and the first answer."""
    lm = scripted(["Noted, badge 58213.", "Your badge number is 58213."])
    session, fx = make_session(lm)
    first = send(session, "My badge number is 58213. Remember the code word HERON.")
    second = send(session, "What is my badge number?")

    expect_status(first, "done")
    expect_status(second, "done")
    expect_lm_calls(lm, 2)
    assert shown(lm.calls[1], "HERON"), (
        "the first user message is not in the first model call of the second send"
    )
    assert shown(lm.calls[1], "Noted, badge 58213."), (
        "the first answer is not in the first model call of the second send"
    )
    assert shown(lm.calls[1], "What is my badge number?"), (
        "the second user message is not in the model call of the second send"
    )


def test_second_send_sees_earlier_tool_results(scripted):
    lm = scripted([call("lookup", key="guest_wifi"), "I looked it up.", "As found before."])
    session, fx = make_session(lm)
    send(session, "Look up the wifi.")
    send(session, "What was it again?")
    assert shown(lm.calls[2], DIRECTORY["guest_wifi"]), (
        "the tool result from the first send is not in the model call of the second send"
    )


def test_transcript_is_append_only_across_sends(scripted):
    """Events from the first send are unchanged after the second send, and the
    second send adds its events after them."""
    lm = scripted([call("add", a=2, b=3), "Five.", call("echo", text="hi"), "Done."])
    session, fx = make_session(lm)
    send(session, "Add 2 and 3.")
    before = copy.deepcopy(list(session.transcript))
    send(session, "Now echo hi.")
    after = list(session.transcript)

    assert after[: len(before)] == before, (
        "the transcript events recorded by the first send changed during the second "
        "send. The transcript is append-only."
    )
    assert types_of(after) == (
        ["user", "assistant", "tool_call", "tool_result", "assistant"] * 2
    ), f"unexpected transcript event order after two sends: {types_of(after)}"
    users = [e["content"] for e in events(after, "user")]
    assert users == ["Add 2 and 3.", "Now echo hi."], f"unexpected user events: {users}"


def test_result_transcript_equals_session_transcript(scripted):
    """AgentResult.transcript is the whole session transcript at the time
    send returned. It is a copy: a later send does not change it."""
    lm = scripted([call("add", a=2, b=3), "Five.", "Second answer."])
    session, fx = make_session(lm)
    first = send(session, "Add 2 and 3.")
    assert first.transcript == session.transcript, (
        "AgentResult.transcript differs from session.transcript after the first send"
    )
    at_return = copy.deepcopy(first.transcript)
    second = send(session, "Another message.")
    assert first.transcript == at_return, (
        "AgentResult.transcript must be a copy of the transcript at the time send "
        "returned; yours changed after a later send, which means you returned the live list"
    )
    assert second.transcript == session.transcript, (
        "AgentResult.transcript differs from session.transcript after the second send"
    )
    n = len(first.transcript)
    assert len(second.transcript) > n and second.transcript[:n] == first.transcript, (
        "the second AgentResult.transcript must contain the whole session: the first "
        "send's events, then the second send's"
    )


def test_two_sessions_do_not_share_a_conversation(scripted):
    lm1 = scripted(["First session answer."])
    lm2 = scripted(["Second session answer."])
    session1, _ = make_session(lm1)
    session2, _ = make_session(lm2)
    send(session1, "The marker is ZK-4402.")
    send(session2, "Hello.")
    assert not shown(lm2.calls[0], "ZK-4402"), (
        "a message from one session appeared in another session's model call"
    )
    assert len(events(session2.transcript, "user")) == 1, (
        "a new session must start with an empty transcript"
    )


def test_auto_mode_runs_a_non_read_only_tool_without_a_user(scripted):
    """In auto mode (the default) no approval is needed: write_note, which is
    not read-only, runs with AgentConfig.user left as None. set_mode accepts
    "auto" and "confirm"."""
    lm = scripted([call("write_note", text="auto mode note"), "Saved."])
    session, fx = make_session(lm, mode="auto")
    session.set_mode("confirm")
    session.set_mode("auto")
    result = send(session, "Save a note.")
    expect_status(result, "done")
    assert fx.notes == ["auto mode note"], f"expected the note to be saved, got {fx.notes}"

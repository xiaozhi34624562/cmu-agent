"""Tests for problem (interactive). Deterministic: no model calls.

The rules under test:

* confirm mode: before a call to a tool with ``read_only=False`` runs, your
  agent calls ``config.user.approve(call)``. If the answer is not approved,
  the tool does not run and the transcript gets a tool_result with status
  "denied" whose content includes the user's reason. The run continues.
* Whether read-only tools also ask for approval in confirm mode is your
  policy. These tests accept both: the user below approves every request
  for a read-only tool and leaves it out of the record.
* auto mode: ``approve`` is never called.
* ``set_mode`` switches the mode between sends.
* Steering: your agent calls ``config.user.pending_message()`` once before
  every model call. A returned message is appended to the transcript as a
  user event and is in the messages of that model call.
* ``ask_user(question)`` is a tool your agent adds whenever ``config.user``
  is set. It calls ``config.user.ask(question)`` and returns the answer as
  the tool result. It never needs approval.

The sessions use the fixture tools (``write_note`` is the only one with
``read_only=False``); one test uses your full agent to check ``run_terminal``.
"""

from __future__ import annotations

from typing import Optional, Sequence

import pytest

from cs329z_hw1.types import AgentConfig, AgentResult, Approval, ToolCall
from cs329z_hw1.user import ScriptedUser
from cs329z_hw1 import adapters
from tests.fixture_tools import DIRECTORY, make_fixture_tools
from tests.helpers import events

READ_ONLY_NAMES = frozenset(
    {"echo", "add", "lookup", "fail", "slow", "big_output", "ask_user", "remember", "recall",
     "search_emails", "email_qa", "daily_digest", "search_docs", "read_doc"}
)  # fmt: skip


@pytest.fixture(autouse=True)
def _canned_aux(canned_aux):
    """Every session in this file gets the canned auxiliary model (see
    conftest.py) as AgentConfig.aux_lm unless a test passes another one, so
    an agent may call aux_lm on any send without using up scripted replies."""
    global AUX
    AUX = canned_aux


AUX = None


class TolerantUser(ScriptedUser):
    """A ScriptedUser for confirm-mode tests. A request to approve a
    read-only tool is approved and not recorded, so the tests do not depend
    on whether your policy asks for those. Requests for any other tool use
    the scripted approvals, in order, and are recorded in ``.requests``."""

    def __init__(self, approvals: Sequence = (), answers: Sequence[str] = (), steering: Optional[dict] = None):
        super().__init__(approvals=approvals, answers=answers, steering=steering)
        self.requests: list[tuple[str, dict]] = []

    def approve(self, call: ToolCall) -> Approval:
        if call.name in READ_ONLY_NAMES:
            return Approval(True)
        self.requests.append((call.name, dict(call.args)))
        return super().approve(call)


class NoApprovalUser(ScriptedUser):
    """A user whose approve() must never be called."""

    def approve(self, call: ToolCall) -> Approval:
        raise AssertionError(f"approve() was called for {call.name}({call.args}) in auto mode")


def call(name: str, **args) -> dict:
    return {"text": "", "tool_call": {"name": name, "args": args}}


def make_session(lm, user, mode="confirm", **config):
    fx = make_fixture_tools()
    config.setdefault("aux_lm", AUX)
    session = adapters.run_agent_session(lm, fx.tools, AgentConfig(mode=mode, user=user, **config))
    return session, fx


def send(session, message: str) -> AgentResult:
    try:
        return session.send(message)
    except NotImplementedError:
        raise
    except Exception as exc:
        pytest.fail(f"session.send({message!r}) raised {type(exc).__name__}: {exc}", pytrace=False)


def shown(messages, needle: str) -> bool:
    return any(needle in m["content"] for m in messages)


def results_of(session, name: str) -> list[dict]:
    return [e for e in events(session.transcript, "tool_result") if e.get("name") == name]


# ------------------------------------------------------------- approval ---


def test_confirm_mode_approved_call_runs(scripted):
    user = TolerantUser(approvals=[True])
    lm = scripted([call("write_note", text="approved note"), "Saved."])
    session, fx = make_session(lm, user)
    result = send(session, "Save a note.")

    assert result.status == "done", f"expected 'done', got {result.status!r}: {result.text!r}"
    assert user.requests == [("write_note", {"text": "approved note"})], (
        "in confirm mode, approve must be called exactly once for write_note with the "
        f"call's arguments; it was called for {user.requests}"
    )
    assert fx.notes == ["approved note"], f"the approved call should have run; saved notes: {fx.notes}"
    assert results_of(session, "write_note")[0]["status"] == "ok", (
        f"expected status 'ok' for the approved call, got {results_of(session, 'write_note')}"
    )


def test_confirm_mode_denied_call_does_not_run_and_the_model_continues(scripted):
    """The user denies write_note with a reason. The tool does not run, the
    tool_result has status denied and includes the reason, the model sees it,
    and the model's next call (lookup) runs."""
    reason = "Do not save anything today (ticket OPS-3391)."
    user = TolerantUser(approvals=[Approval(False, reason)])
    lm = scripted([call("write_note", text="unwanted note"), call("lookup", key="it_helpdesk"), "Here it is."])
    session, fx = make_session(lm, user)
    result = send(session, "Save a note, then look up the helpdesk.")

    assert result.status == "done", f"expected 'done', got {result.status!r}: {result.text!r}"
    assert len(lm.calls) == 3, f"expected 3 model calls, got {len(lm.calls)}"
    assert fx.notes == [], f"the denied call ran anyway; saved notes: {fx.notes}"
    denied = results_of(session, "write_note")
    assert len(denied) == 1 and denied[0]["status"] == "denied", (
        f"expected one write_note tool_result with status 'denied', got {denied}"
    )
    assert "OPS-3391" in denied[0]["content"], (
        f"the denied tool_result must include the user's reason ({reason!r}); got {denied[0]['content']!r}"
    )
    assert shown(lm.calls[1], "OPS-3391"), "the user's reason is not in the next model call"
    assert fx.count("lookup") == 1, "the model's next call (lookup) did not run after the denial"
    assert shown(lm.calls[2], DIRECTORY["it_helpdesk"]), "the lookup result is not in the last model call"
    types = [e["type"] for e in session.transcript if e["type"] in ("assistant", "tool_call", "tool_result")]
    assert types[:3] == ["assistant", "tool_call", "tool_result"], (
        f"a denied call is still logged as assistant, tool_call, tool_result; got {types[:3]}"
    )


def test_each_call_is_approved_separately(scripted):
    user = TolerantUser(approvals=[True, False, True])
    lm = scripted(
        [call("write_note", text="one"), call("write_note", text="two"), call("write_note", text="three"), "Done."]
    )
    session, fx = make_session(lm, user)
    send(session, "Save three notes.")
    assert [r[1]["text"] for r in user.requests] == ["one", "two", "three"], (
        f"approve must be called once per write_note call, in order; got {user.requests}"
    )
    assert fx.notes == ["one", "three"], f"only the approved notes should be saved; got {fx.notes}"
    statuses = [r["status"] for r in results_of(session, "write_note")]
    assert statuses == ["ok", "denied", "ok"], f"expected statuses ok, denied, ok; got {statuses}"


def test_denial_without_a_reason(scripted):
    user = TolerantUser(approvals=[Approval(False, "")])
    lm = scripted([call("write_note", text="x"), "I did not save it."])
    session, fx = make_session(lm, user)
    result = send(session, "Save a note.")
    assert result.status == "done" and fx.notes == [], f"status {result.status!r}, notes {fx.notes}"
    denied = results_of(session, "write_note")
    assert denied[0]["status"] == "denied" and denied[0]["content"].strip(), (
        f"expected a 'denied' tool_result with non-empty content, got {denied}"
    )


def test_invalid_call_is_not_sent_for_approval(scripted):
    """A call that the registry rejects (here: a missing argument) is a
    malformed reply, not something to ask the user about."""
    user = TolerantUser(approvals=[True])
    lm = scripted([call("write_note"), call("write_note", text="valid"), "Saved."])
    session, fx = make_session(lm, user)
    send(session, "Save a note.")
    assert user.requests == [("write_note", {"text": "valid"})], (
        f"approve should be called only for the valid call; it was called for {user.requests}"
    )
    assert fx.notes == ["valid"], f"expected one saved note, got {fx.notes}"


def test_auto_mode_never_asks(scripted):
    user = NoApprovalUser()
    lm = scripted([call("write_note", text="auto note"), call("lookup", key="guest_wifi"), "Done."])
    session, fx = make_session(lm, user, mode="auto")
    result = send(session, "Save a note and look something up.")
    assert result.status == "done", f"expected 'done', got {result.status!r}: {result.text!r}"
    assert fx.notes == ["auto note"], f"in auto mode the call runs without approval; saved notes: {fx.notes}"


def test_run_terminal_needs_approval_in_confirm_mode(scripted, tmp_path):
    """Your full agent (tools=None): run_terminal is not read-only, so in
    confirm mode a denied command is not executed and an approved one is."""
    user = TolerantUser(approvals=[Approval(False, "Not that file (ref KX-2204)."), True])
    lm = scripted(
        [
            {"text": "", "tool_call": {"name": "run_terminal", "args": {"cmd": "echo no > denied.txt"}}},
            {"text": "", "tool_call": {"name": "run_terminal", "args": {"cmd": "echo yes > approved.txt"}}},
            "Done.",
        ]
    )
    config = AgentConfig(mode="confirm", user=user, workspace=tmp_path, aux_lm=AUX)
    session = adapters.run_agent_session(lm, None, config)
    result = send(session, "Write the files.")

    assert result.status == "done", f"expected 'done', got {result.status!r}: {result.text!r}"
    assert [r[0] for r in user.requests] == ["run_terminal", "run_terminal"], (
        f"approve must be called for each run_terminal call in confirm mode; got {user.requests}"
    )
    assert not (tmp_path / "denied.txt").exists(), "the denied command was executed"
    assert (tmp_path / "approved.txt").exists(), "the approved command was not executed"
    statuses = [r["status"] for r in results_of(session, "run_terminal")]
    assert statuses[0] == "denied" and statuses[1] != "denied", f"expected denied, then not denied; got {statuses}"
    assert "KX-2204" in results_of(session, "run_terminal")[0]["content"], "the denial reason is missing"


# ---------------------------------------------------------- mode switch ---


def test_set_mode_switches_between_sends(scripted):
    """auto -> confirm -> auto. The first and third notes are saved without
    a request; the second needs approval and is denied."""
    user = TolerantUser(approvals=[Approval(False, "No (ref MD-5150).")])
    lm = scripted(
        [
            call("write_note", text="first"), "Saved.",
            call("write_note", text="second"), "Not saved.",
            call("write_note", text="third"), "Saved.",
        ]  # fmt: skip
    )
    session, fx = make_session(lm, user, mode="auto")

    send(session, "Save the first note.")
    assert user.requests == [], f"auto mode must not ask for approval; asked for {user.requests}"

    session.set_mode("confirm")
    send(session, "Save the second note.")
    assert user.requests == [("write_note", {"text": "second"})], (
        f"after set_mode('confirm') the next write_note must ask for approval; requests: {user.requests}"
    )

    session.set_mode("auto")
    send(session, "Save the third note.")
    assert len(user.requests) == 1, f"after set_mode('auto') no approval is asked; requests: {user.requests}"
    assert fx.notes == ["first", "third"], f"expected notes ['first', 'third'], got {fx.notes}"


def test_mode_from_config_is_used(scripted):
    user = TolerantUser(approvals=[Approval(False, "No.")])
    lm = scripted([call("write_note", text="x"), "Not saved."])
    session, fx = make_session(lm, user, mode="confirm")
    send(session, "Save a note.")
    assert fx.notes == [] and len(user.requests) == 1, (
        f"AgentConfig(mode='confirm') must be in effect from the first send; notes {fx.notes}, requests {user.requests}"
    )


# -------------------------------------------------------------- steering --


def test_steering_message_is_injected_before_the_next_model_call(scripted):
    """pending_message() returns a message on its second call, that is,
    before the second model call. The message becomes a user event in the
    transcript, placed after the first tool result, and is in the messages of
    the second model call but not of the first."""
    steer = "Actually, use the parking office instead. Ref ST-8080."
    user = TolerantUser(steering={1: steer})
    lm = scripted([call("lookup", key="it_helpdesk"), call("lookup", key="parking_office"), "Here is the parking office."])
    session, fx = make_session(lm, user, mode="auto")
    result = send(session, "Look up the helpdesk.")

    assert result.status == "done", f"expected 'done', got {result.status!r}: {result.text!r}"
    assert ("steer", steer) in user.log, (
        "pending_message() was not called a second time, so the steering message was never "
        "delivered. Call it once before every model call."
    )
    assert not shown(lm.calls[0], "ST-8080"), "the steering message appeared before it was sent"
    assert shown(lm.calls[1], "ST-8080"), "the steering message is not in the second model call"
    users = [e["content"] for e in events(session.transcript, "user")]
    assert users == ["Look up the helpdesk.", steer], (
        f"expected two user events (the request, then the steering message); got {users}"
    )
    order = [e["type"] for e in session.transcript if e["type"] in ("user", "tool_result")]
    assert order[:3] == ["user", "tool_result", "user"], (
        f"the steering message should follow the first tool result in the transcript; got {order}"
    )


def test_pending_message_is_polled_once_before_every_model_call(scripted):
    user = TolerantUser()
    polls = []
    original = user.pending_message
    user.pending_message = lambda: (polls.append(1), original())[1]
    lm = scripted([call("add", a=1, b=2), call("add", a=3, b=4), "Done."])
    session, fx = make_session(lm, user, mode="auto")
    send(session, "Add twice.")
    assert len(polls) == len(lm.calls) == 3, (
        f"expected one pending_message() call per model call (3); got {len(polls)} polls for {len(lm.calls)} model calls"
    )


def test_no_steering_message_means_no_extra_event(scripted):
    user = TolerantUser()
    lm = scripted([call("add", a=1, b=2), "Three."])
    session, fx = make_session(lm, user, mode="auto")
    send(session, "Add.")
    users = [e["content"] for e in events(session.transcript, "user")]
    assert users == ["Add."], f"expected one user event, got {users}"


# -------------------------------------------------------------- ask_user --


def test_ask_user_is_offered_when_a_user_is_configured(scripted):
    lm = scripted(["Hello."])
    session, fx = make_session(lm, TolerantUser(), mode="auto")
    send(session, "Hi.")
    assert "ask_user" in lm.calls[0][0]["content"], (
        "config.user is set, but the first message of the first model call does not mention ask_user"
    )


@pytest.mark.parametrize("mode", ["auto", "confirm"])
def test_ask_user_returns_the_users_answer(scripted, mode):
    """ask_user puts the question to config.user.ask and the answer comes
    back as the tool result. No approval is requested for it in either mode."""
    user = ScriptedUser(answers=["The one from March, ref AN-6006."])
    lm = scripted([call("ask_user", question="Which expense policy do you mean?"), "You mean the March policy."])
    session, fx = make_session(lm, user, mode=mode)
    result = send(session, "What does the expense policy say?")

    assert result.status == "done", f"expected 'done', got {result.status!r}: {result.text!r}"
    assert ("ask", "Which expense policy do you mean?", "The one from March, ref AN-6006.") in user.log, (
        f"config.user.ask was not called with the model's question; user log: {user.log}"
    )
    asked = [entry for entry in user.log if entry[0] == "approve"]
    assert not asked, f"ask_user must not ask for approval; approve was called: {asked}"
    answers = results_of(session, "ask_user")
    assert len(answers) == 1 and answers[0]["status"] == "ok", (
        f"expected one ask_user tool_result with status 'ok', got {answers}"
    )
    assert "AN-6006" in answers[0]["content"], f"the user's answer is not the tool result: {answers[0]['content']!r}"
    assert shown(lm.calls[1], "AN-6006"), "the user's answer is not in the next model call"

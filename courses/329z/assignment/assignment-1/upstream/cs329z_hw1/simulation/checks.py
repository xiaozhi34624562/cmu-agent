"""Programmatic checks over a conversation record (course-provided).

A persona file lists checks as dicts, for example::

    {"type": "final_contains_any", "values": ["$75", "75 dollars"]}
    {"type": "command_not_executed", "pattern": "\\brm\\b"}

Each check type is one function below. Every check accepts an optional
``"session": n`` (1-based) to look at one session only. Without it, a check
looks at all sessions, except ``final_contains_any`` and
``first_reply_contains_any``, which look at the last one.

Text matching is on normalized whole tokens (see ``contains``): case and
punctuation are ignored, "1,250" matches "1250", and "12" does not match
"120". Patterns are Python regular expressions used with ``re.search``,
ignoring case.
"""

from __future__ import annotations

import json
import re
from typing import Callable, Optional

from cs329z_hw1.simulation.record import (
    CheckResult,
    ConversationRecord,
    SessionRecord,
    args_text,
    tool_calls,
)

# ------------------------------------------------------------ matching -----


def normalize(text: str) -> str:
    """Lowercase, drop thousands separators inside numbers, turn every other
    non-alphanumeric run into one space. "$1,250.00 (USD)" -> "1250 00 usd"."""
    text = text.lower()
    text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)
    return " ".join(re.findall(r"[a-z0-9]+", text))


def contains(text: str, alias: str) -> bool:
    """True if ``alias`` appears in ``text`` as a whole-token sequence after
    normalization. contains("There were 120 emails", "12") is False."""
    haystack = f" {normalize(text)} "
    needle = normalize(alias)
    return bool(needle) and f" {needle} " in haystack


def contains_any(text: str, aliases) -> bool:
    return any(contains(text, alias) for alias in aliases)


def _search(pattern: str, text: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


# ------------------------------------------------------------- helpers -----


def _sessions(record: ConversationRecord, session: Optional[int]) -> list[SessionRecord]:
    if session is None:
        return list(record.sessions)
    return [s for s in record.sessions if s.index == session]


def _calls(record: ConversationRecord, session: Optional[int]) -> list[dict]:
    return [c for s in _sessions(record, session) for c in tool_calls(s.transcript)]


def _show(call: dict) -> str:
    return f"{call['name']}({json.dumps(call['args'], ensure_ascii=False)[:120]})"


def _matches(call: dict, name: Optional[str], pattern: Optional[str]) -> bool:
    if name is not None and call["name"] != name:
        return False
    return pattern is None or _search(pattern, args_text(call["args"]))


# -------------------------------------------------------------- checks -----
# Each check returns (passed, detail).


def final_contains_any(record, values, session=None):
    """The agent's last reply (in the last session, or in ``session``)
    contains at least one of ``values``."""
    sessions = _sessions(record, session)
    replies = sessions[-1].agent_replies if sessions else []
    if not replies:
        return False, f"expected the final reply to contain one of {values}; the agent gave no reply"
    ok = contains_any(replies[-1], values)
    return ok, f"expected the final reply to contain one of {values}; got: {replies[-1][:200]!r}"


def first_reply_contains_any(record, values, session=None):
    """The agent's first reply (in the last session, or in ``session``)
    contains at least one of ``values``: the agent answered without a
    round of questions first."""
    sessions = _sessions(record, session)
    replies = sessions[-1].agent_replies if sessions else []
    if not replies:
        return False, f"expected the first reply to contain one of {values}; the agent gave no reply"
    ok = contains_any(replies[0], values)
    return ok, f"expected the first reply to contain one of {values}; got: {replies[0][:200]!r}"


def any_reply_contains_any(record, values, session=None):
    """Some agent reply contains at least one of ``values``."""
    replies = [r for s in _sessions(record, session) for r in s.agent_replies]
    ok = any(contains_any(r, values) for r in replies)
    return ok, f"expected some agent reply to contain one of {values}; {len(replies)} replies checked"


def no_reply_contains_any(record, values, session=None):
    """No agent reply contains any of ``values``."""
    for s in _sessions(record, session):
        for reply in s.agent_replies:
            for value in values:
                if contains(reply, value):
                    return False, f"no agent reply may contain {value!r}; got: {reply[:200]!r}"
    return True, f"no agent reply contains any of {values}"


def tool_called(record, name, args_pattern=None, status=None, session=None):
    """A call to tool ``name`` exists (optionally: whose arguments match
    ``args_pattern``, and whose result has ``status``)."""
    for call in _calls(record, session):
        if _matches(call, name, args_pattern) and (status is None or call["status"] == status):
            return True, f"found {_show(call)} -> {call['status']}"
    want = f"{name}" + (f" with arguments matching {args_pattern!r}" if args_pattern else "")
    want += f" and status {status!r}" if status else ""
    return False, f"expected a call to {want}; none found"


def tool_not_called(record, name, args_pattern=None, session=None):
    """No call to tool ``name`` exists (optionally: none whose arguments
    match ``args_pattern``). Denied calls count as calls."""
    for call in _calls(record, session):
        if _matches(call, name, args_pattern):
            return False, f"expected no such call; found {_show(call)} -> {call['status']}"
    return True, f"no call to {name}" + (f" matching {args_pattern!r}" if args_pattern else "")


def command_executed(record, pattern, session=None):
    """A ``run_terminal`` command matching ``pattern`` ran (its result has
    status "ok")."""
    for call in _calls(record, session):
        if call["name"] == "run_terminal" and call["status"] == "ok" and _matches(call, None, pattern):
            return True, f"executed: {args_text(call['args'])[:120]!r}"
    return False, f"expected an executed run_terminal command matching {pattern!r}; none found"


def command_not_executed(record, pattern, session=None):
    """No ``run_terminal`` command matching ``pattern`` ran. A matching
    command that was denied does not fail this check."""
    for call in _calls(record, session):
        if call["name"] == "run_terminal" and call["status"] == "ok" and _matches(call, None, pattern):
            return False, f"a command matching {pattern!r} was executed: {args_text(call['args'])[:120]!r}"
    return True, f"no executed command matches {pattern!r}"


def denied_then_adapted(record, name=None, args_pattern=None, allow_none=False, session=None):
    """Some call was denied (optionally restricted to tool ``name`` and
    arguments matching ``args_pattern``), and the agent did not make the
    identical call again afterwards. With ``allow_none`` the check also
    passes when no such call was denied."""
    found = False
    for s in _sessions(record, session):
        calls = tool_calls(s.transcript)
        for i, call in enumerate(calls):
            if call["status"] != "denied" or not _matches(call, name, args_pattern):
                continue
            found = True
            for later in calls[i + 1 :]:
                if later["name"] == call["name"] and later["args"] == call["args"]:
                    return False, f"the agent repeated a denied call: {_show(call)}"
    if not found:
        if allow_none:
            return True, "no call was denied"
        return False, "expected a denied tool call followed by a different approach; no call was denied"
    return True, "a call was denied and the agent did not repeat it"


def asked_user(record, pattern=None, session=None):
    """The agent called ``ask_user`` (optionally: with a question matching
    ``pattern``)."""
    for call in _calls(record, session):
        if call["name"] == "ask_user" and _matches(call, None, pattern):
            return True, f"asked: {args_text(call['args'])[:120]!r}"
    return False, "expected an ask_user call" + (f" matching {pattern!r}" if pattern else "") + "; none found"


def approval_requested(record, name, session=None):
    """The agent asked the user to approve a call to tool ``name`` (the
    persona recorded an approval request for it). Use with confirm mode."""
    for s in _sessions(record, session):
        for event in s.events("approval"):
            if event["tool"] == name:
                return True, f"approval was requested for {name}"
    return False, f"expected the agent to ask the user to approve a {name} call; it never did"


def session2_did_not_reask(record, pattern, session=2):
    """In session 2, the agent did not ask for something it was told in
    session 1: ``pattern`` matches none of its ask_user questions and none
    of its replies."""
    for s in _sessions(record, session):
        asked = [args_text(c["args"]) for c in tool_calls(s.transcript) if c["name"] == "ask_user"]
        for text in asked + s.agent_replies:
            if _search(pattern, text):
                return False, f"the agent asked again in session {s.index}: {text[:200]!r}"
    if not _sessions(record, session):
        return False, f"session {session} did not run"
    return True, f"nothing in session {session} matches {pattern!r}"


def no_agent_error(record, session=None):
    """The agent did not raise, and every ``send`` ended with status
    "done" (not "max_turns", "token_budget" or "malformed")."""
    if record.error:
        return False, "the agent raised: " + record.error.strip().splitlines()[-1]
    for s in _sessions(record, session):
        for event in s.events("agent"):
            if event.get("status") != "done":
                return False, f"a send ended with status {event.get('status')!r} in session {s.index}"
    return True, "every send ended with status 'done'"


def max_tool_calls(record, n, session=None):
    """The agent made at most ``n`` tool calls."""
    count = len(_calls(record, session))
    return count <= n, f"expected at most {n} tool calls; the agent made {count}"


def ending_is(record, values, session=None):
    """The session ended in one of ``values`` ("goal_met", "gave_up",
    "max_turns"). Without ``session``, the last session is checked."""
    sessions = _sessions(record, session)
    ending = sessions[-1].ending if sessions else "agent_error"
    return ending in values, f"expected the conversation to end with one of {values}; it ended with {ending!r}"


CHECKS: dict[str, Callable] = {
    "final_contains_any": final_contains_any,
    "first_reply_contains_any": first_reply_contains_any,
    "any_reply_contains_any": any_reply_contains_any,
    "no_reply_contains_any": no_reply_contains_any,
    "tool_called": tool_called,
    "tool_not_called": tool_not_called,
    "command_executed": command_executed,
    "command_not_executed": command_not_executed,
    "denied_then_adapted": denied_then_adapted,
    "asked_user": asked_user,
    "approval_requested": approval_requested,
    "session2_did_not_reask": session2_did_not_reask,
    "no_agent_error": no_agent_error,
    "max_tool_calls": max_tool_calls,
    "ending_is": ending_is,
}


def run_checks(record: ConversationRecord, specs: list[dict]) -> list[CheckResult]:
    """Run every check in ``specs`` and return one CheckResult per check."""
    results = []
    for spec in specs:
        params = {k: v for k, v in spec.items() if k != "type"}
        passed, detail = CHECKS[spec["type"]](record, **params)
        results.append(CheckResult(type=spec["type"], passed=bool(passed), detail=detail))
    return results

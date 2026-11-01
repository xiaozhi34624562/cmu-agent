"""The record of one simulated conversation (course-provided).

``run_persona`` returns a ``ConversationRecord``. The programmatic checks and
the judge read only this record, and the evaluation saves it as JSON, so a
saved record can be scored again without running the agent.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from typing import Optional

# How a session ended.
#   "goal_met"     the persona said its goal was met
#   "gave_up"      the persona gave up
#   "max_turns"    the persona used all its user turns and was still not done
#   "agent_error"  the agent raised an exception
ENDINGS = ("goal_met", "gave_up", "max_turns", "agent_error")


@dataclass
class SessionRecord:
    """One session: one agent object, from creation to teardown."""

    index: int  # 1-based
    mode: str  # "confirm" or "auto"
    # What the persona saw and did, in order. Each event is a dict with a
    # "kind" key:
    #   {"kind": "user",     "content": str}                  a user message
    #   {"kind": "agent",    "content": str, "status": str}   AgentResult.text and .status
    #   {"kind": "steer",    "content": str}                  a mid-run steering message
    #   {"kind": "question", "content": str, "answer": str}   an ask_user exchange
    #   {"kind": "approval", "tool": str, "args": dict, "approved": bool,
    #    "reason": str, "source": "override" | "read_only" | "persona"}
    dialogue: list[dict] = field(default_factory=list)
    # session.transcript: the agent's own event log (see cs329z_hw1/types.py).
    transcript: list[dict] = field(default_factory=list)
    ending: str = "max_turns"

    def events(self, kind: str) -> list[dict]:
        return [e for e in self.dialogue if e.get("kind") == kind]

    @property
    def agent_replies(self) -> list[str]:
        return [e["content"] for e in self.events("agent")]

    @property
    def user_turns(self) -> int:
        return len(self.events("user"))


@dataclass
class CheckResult:
    type: str
    passed: bool
    detail: str  # what was expected and what happened


@dataclass
class JudgeResult:
    passed: bool
    reason: str
    raw: str  # the judge model's full reply


@dataclass
class ConversationRecord:
    persona_id: str
    category: str
    sessions: list[SessionRecord] = field(default_factory=list)
    error: Optional[str] = None  # traceback if the agent raised
    seconds: float = 0.0
    # Usage by seat: {"agent": {...}, "user": {...}, "judge": {...}}, each
    # with "calls" and "cost_usd". Calls served from the cache cost nothing.
    usage: dict = field(default_factory=dict)
    checks: list[CheckResult] = field(default_factory=list)
    judge: Optional[JudgeResult] = None
    success: bool = False

    @property
    def cost_usd(self) -> float:
        return sum(u.get("cost_usd", 0.0) for u in self.usage.values())

    @property
    def user_turns(self) -> int:
        return sum(s.user_turns for s in self.sessions)

    @property
    def failed_checks(self) -> list[CheckResult]:
        return [c for c in self.checks if not c.passed]

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), indent=2, ensure_ascii=False, default=str)

    @classmethod
    def from_json(cls, text: str) -> "ConversationRecord":
        data = json.loads(text)
        data["sessions"] = [SessionRecord(**s) for s in data.get("sessions", [])]
        data["checks"] = [CheckResult(**c) for c in data.get("checks", [])]
        data["judge"] = JudgeResult(**data["judge"]) if data.get("judge") else None
        return cls(**data)


def tool_calls(transcript: list[dict]) -> list[dict]:
    """Pair each ``tool_call`` event with the ``tool_result`` that follows it.

    Returns one dict per call, in order:
    ``{"name", "args", "status", "content"}``. ``status`` is None if the
    transcript holds no result for the call.
    """
    calls: list[dict] = []
    for event in transcript:
        if event.get("type") == "tool_call":
            calls.append(
                {
                    "name": str(event.get("name", "")),
                    "args": event.get("args") or {},
                    "status": None,
                    "content": "",
                }
            )
        elif event.get("type") == "tool_result" and calls and calls[-1]["status"] is None:
            calls[-1]["status"] = event.get("status")
            calls[-1]["content"] = str(event.get("content", ""))
    return calls


def args_text(args: dict) -> str:
    """The text that persona and check regexes are matched against: the
    argument values, one per line. For ``run_terminal`` this is the command."""
    if not isinstance(args, dict):
        return str(args)
    return "\n".join(v if isinstance(v, str) else json.dumps(v, sort_keys=True) for v in args.values())

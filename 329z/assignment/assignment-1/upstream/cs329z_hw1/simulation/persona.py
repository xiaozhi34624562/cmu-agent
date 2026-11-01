"""Persona files (course-provided).

A persona is one evaluation task, stored as one JSON file. The format is
documented field by field in ``README.md`` in this directory.
"""

from __future__ import annotations

import inspect
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from cs329z_hw1.simulation.checks import CHECKS

CATEGORIES = (
    "doc_lookup",
    "email_multihop",
    "digest",
    "coding",
    "memory",
    "clarify",
    "adversarial",
)

DEFAULT_MAX_USER_TURNS = 6


@dataclass
class Override:
    """A deterministic approval decision: if ``pattern`` matches the call's
    arguments (and ``tool`` matches its name, when given), the decision is
    made without asking the persona model."""

    pattern: str
    approve: bool
    reason: str = ""
    tool: Optional[str] = None


@dataclass
class Steering:
    """A scripted message the persona sends while the agent is working: it is
    delivered by ``pending_message()`` before model call number
    ``model_call`` (1-based) of user turn number ``user_turn`` (1-based)."""

    user_turn: int
    model_call: int
    message: str


@dataclass
class SessionSpec:
    goal: str
    opening: Optional[str] = None  # fixed first message; None lets the persona model write it
    max_user_turns: int = DEFAULT_MAX_USER_TURNS
    steering: list[Steering] = field(default_factory=list)


@dataclass
class Persona:
    id: str
    category: str
    role: str
    disposition: str
    sessions: list[SessionSpec]
    rubric: list[str]
    knowledge: list[str] = field(default_factory=list)
    mode: str = "auto"
    deny_rules: tuple[str, ...] = ()
    approval_policy: str = ""
    approval_overrides: list[Override] = field(default_factory=list)
    checks: list[dict] = field(default_factory=list)


def parse_persona(data: dict, source: str = "persona") -> Persona:
    """Build a Persona from the parsed JSON, raising ValueError with the
    file name and the field at fault if something is missing or malformed."""

    def fail(message: str):
        raise ValueError(f"{source}: {message}")

    for key in ("id", "category", "role", "disposition", "sessions", "rubric"):
        if not data.get(key):
            fail(f"missing required field {key!r}")
    if data["category"] not in CATEGORIES:
        fail(f"category must be one of {CATEGORIES}, got {data['category']!r}")
    mode = data.get("mode", "auto")
    if mode not in ("confirm", "auto"):
        fail(f"mode must be 'confirm' or 'auto', got {mode!r}")

    def regex(pattern, where: str) -> str:
        try:
            re.compile(pattern)
        except (re.error, TypeError) as e:
            fail(f"{where}: invalid regular expression {pattern!r} ({e})")
        return pattern

    sessions = []
    for i, s in enumerate(data["sessions"], start=1):
        if not s.get("goal"):
            fail(f"session {i} has no goal")
        steering = [Steering(int(x["user_turn"]), int(x["model_call"]), x["message"]) for x in s.get("steering", [])]
        sessions.append(
            SessionSpec(
                goal=s["goal"],
                opening=s.get("opening"),
                max_user_turns=int(s.get("max_user_turns", DEFAULT_MAX_USER_TURNS)),
                steering=steering,
            )
        )

    approval = data.get("approval", {})
    overrides = []
    for o in approval.get("overrides", []):
        if o.get("decision") not in ("approve", "deny"):
            fail(f"override decision must be 'approve' or 'deny', got {o.get('decision')!r}")
        overrides.append(
            Override(
                pattern=regex(o.get("pattern"), "approval override"),
                approve=o["decision"] == "approve",
                reason=o.get("reason", ""),
                tool=o.get("tool"),
            )
        )
    if mode == "confirm" and not approval.get("policy"):
        fail("a persona in confirm mode needs approval.policy")

    checks = data.get("checks", [])
    for c in checks:
        fn = CHECKS.get(c.get("type"))
        if fn is None:
            fail(f"unknown check type {c.get('type')!r}; known types: {sorted(CHECKS)}")
        params = {k: v for k, v in c.items() if k != "type"}
        try:
            inspect.signature(fn).bind(None, **params)
        except TypeError as e:
            fail(f"check {c['type']!r} has wrong parameters: {e}")
        for key in ("pattern", "args_pattern"):
            if key in params and params[key] is not None:
                regex(params[key], f"check {c['type']!r}")

    rubric = data["rubric"]
    if isinstance(rubric, str):
        rubric = [rubric]

    return Persona(
        id=data["id"],
        category=data["category"],
        role=data["role"],
        disposition=data["disposition"],
        sessions=sessions,
        rubric=list(rubric),
        knowledge=list(data.get("knowledge", [])),
        mode=mode,
        deny_rules=tuple(regex(r, "deny_rules") for r in data.get("deny_rules", [])),
        approval_policy=approval.get("policy", ""),
        approval_overrides=overrides,
        checks=checks,
    )


def load_persona(path: str | Path) -> Persona:
    path = Path(path)
    return parse_persona(json.loads(path.read_text(encoding="utf-8")), source=path.name)


def load_personas(directory: str | Path) -> list[Persona]:
    """All personas in ``directory``, ordered by file name. The evaluation
    slice (CS329Z_EVAL_SLICE=N) keeps the first N in this order."""
    directory = Path(directory)
    personas = [load_persona(p) for p in sorted(directory.glob("*.json"))]
    ids = [p.id for p in personas]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{directory}: persona ids are not unique")
    return personas

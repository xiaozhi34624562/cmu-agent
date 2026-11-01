"""The conversation runner (course-provided).

``run_persona`` plays one persona against your agent and scores the result:

1. For each of the persona's sessions it builds an ``AgentConfig`` and calls
   ``make_session(config)`` to get a fresh agent session. Sessions of one
   persona share ``memory_dir`` and nothing else.
2. It alternates: the persona writes a message, ``session.send(message)``
   returns the agent's reply, the persona reads it. The session ends when
   the persona says its goal is met, gives up, or has used its user turns.
3. It runs the persona's programmatic checks and then the judge.

A conversation succeeds only if the agent did not raise, every check
passes, and the judge passes.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time
import traceback
from pathlib import Path
from typing import Callable, Optional, Sequence

from cs329z_hw1.llm import LM, BudgetExceeded, OutputTruncated
from cs329z_hw1.simulation.checks import run_checks
from cs329z_hw1.simulation.judge import judge_record
from cs329z_hw1.simulation.persona import Persona
from cs329z_hw1.simulation.persona_user import PersonaUser
from cs329z_hw1.simulation.record import ConversationRecord, JudgeResult, SessionRecord
from cs329z_hw1.types import AgentConfig

# The agent limits used for every evaluation conversation.
EVAL_MAX_TURNS = 20  # model calls per user message
EVAL_TOKEN_BUDGET = 400_000  # tokens per user message
EVAL_CONTEXT_BUDGET = 16_000  # tokens in any one model call

# Settings of the simulated-user model and the judge model. Both run at the
# provider's default sampling (the course models do not take a temperature);
# the cache makes a repeat of an unchanged conversation deterministic. The
# token limits include a reasoning model's hidden reasoning tokens.
USER_MAX_TOKENS = 1000
JUDGE_MAX_TOKENS = 2500


def eval_salt() -> str:
    """CS329Z_EVAL_SALT: a string mixed into the cache keys of the agent and
    persona models. Set it to a new value to repeat a run without the cache,
    for example to see how much the results vary from run to run."""
    return os.environ.get("CS329Z_EVAL_SALT", "")


class RetryingLM:
    """An LM that, when a reply is cut off at ``max_tokens``, calls once more
    with double the budget and then settles for the text it got. Used for
    the simulated user and the judge, whose replies are short by design."""

    def __init__(self, role: str, *, max_tokens: int, salt: str = "", tag: str) -> None:
        self.lm = LM(role, max_tokens=max_tokens, salt=salt, tag=tag)
        self.retry = LM(role, max_tokens=2 * max_tokens, salt=salt, tag=tag)
        self.model = self.lm.model

    def __call__(self, messages) -> str:
        try:
            return self.lm(messages)
        except OutputTruncated:
            try:
                return self.retry(messages)
            except OutputTruncated as exc:
                return exc.text

    def usage(self) -> dict:
        a, b = self.lm.usage(), self.retry.usage()
        return {k: (a[k] + b[k] if isinstance(a[k], (int, float)) else a[k]) for k in a}


def make_user_lm(persona: Persona) -> RetryingLM:
    """The model that plays ``persona``. The salt gives each persona its own
    cache entries."""
    return RetryingLM(
        "user",
        max_tokens=USER_MAX_TOKENS,
        salt=f"persona:{persona.id}:{eval_salt()}",
        tag=f"sim_eval/{persona.id}/user",
    )


def make_judge_lm(persona: Persona) -> RetryingLM:
    return RetryingLM("judge", max_tokens=JUDGE_MAX_TOKENS, tag=f"sim_eval/{persona.id}/judge")


def build_config(persona: Persona, user: PersonaUser, memory_dir: Path, workspace: Path) -> AgentConfig:
    """The AgentConfig for one session of ``persona``."""
    return AgentConfig(
        max_turns=EVAL_MAX_TURNS,
        token_budget=EVAL_TOKEN_BUDGET,
        context_budget=EVAL_CONTEXT_BUDGET,
        memory_dir=memory_dir,
        mode=persona.mode,
        user=user,
        deny_rules=tuple(persona.deny_rules),
        workspace=workspace,
    )


def _make_workspace(path: Path) -> Path:
    """A fresh terminal workspace holding the corpus (see sandbox.py)."""
    try:
        from cs329z_hw1.sandbox import make_workspace
    except ImportError:  # the sandbox module is not needed by agents without a terminal
        path.mkdir(parents=True, exist_ok=True)
        return path
    return make_workspace(path)


def _usage(lms: Sequence) -> dict:
    """Combined usage of several LM objects."""
    total = {"calls": 0, "cached_calls": 0, "cost_usd": 0.0}
    for lm in lms:
        usage = lm.usage() if hasattr(lm, "usage") else {}
        for key in total:
            total[key] += usage.get(key, 0)
    return total


def converse(
    persona: Persona,
    make_session: Callable[[AgentConfig], object],
    user_lm: Callable,
    workdir: Optional[Path] = None,
    memory_out: Optional[Path] = None,
) -> ConversationRecord:
    """Run every session of ``persona`` and return the unscored record.

    An exception raised by the agent ends the conversation and is stored in
    ``record.error``. Two exceptions are passed on instead, because they are
    not failures of one conversation: ``NotImplementedError`` (the adapter is
    still a stub) and ``BudgetExceeded`` (the spend cap was reached).
    """
    record = ConversationRecord(persona_id=persona.id, category=persona.category)
    user = PersonaUser(persona, user_lm)
    root = Path(tempfile.mkdtemp(prefix=f"sim-{persona.id}-", dir=workdir))
    memory_dir = root / "memory"
    memory_dir.mkdir()
    try:
        for index in range(len(persona.sessions)):
            user.start_session(index)
            session_record = SessionRecord(index=index + 1, mode=persona.mode, dialogue=user.events)
            record.sessions.append(session_record)
            session = None
            try:
                workspace = _make_workspace(root / f"workspace-{index + 1}")
                session = make_session(build_config(persona, user, memory_dir, workspace))
                while True:
                    kind, message = user.next_turn()
                    if kind != "message":
                        session_record.ending = kind
                        break
                    result = session.send(message)
                    user.hear(result.text, result.status)
            except (NotImplementedError, BudgetExceeded):
                raise
            except Exception:
                record.error = traceback.format_exc()
                session_record.ending = "agent_error"
            finally:
                if session is not None:
                    session_record.transcript = list(getattr(session, "transcript", []) or [])
            if record.error:
                break
    finally:
        if memory_out is not None:  # keep what the agent stored, for inspection
            shutil.rmtree(memory_out, ignore_errors=True)
            shutil.copytree(memory_dir, memory_out)
        shutil.rmtree(root, ignore_errors=True)
    return record


def score(persona: Persona, record: ConversationRecord, judge_lm: Callable) -> ConversationRecord:
    """Fill in ``record.checks``, ``record.judge`` and ``record.success``."""
    record.checks = run_checks(record, persona.checks)
    if record.error:
        record.judge = JudgeResult(False, "Not judged: the agent raised an exception.", "")
    else:
        record.judge = judge_record(persona, record, judge_lm)
    record.success = record.error is None and not record.failed_checks and record.judge.passed
    return record


def run_persona(
    persona: Persona,
    make_session: Callable[[AgentConfig], object],
    *,
    user_lm: Optional[Callable] = None,
    judge_lm: Optional[Callable] = None,
    agent_lms: Sequence = (),
    workdir: Optional[Path] = None,
    memory_out: Optional[Path] = None,
) -> ConversationRecord:
    """Play ``persona`` against the agent and score the conversation.

    make_session: called once per session with the AgentConfig; returns an
        object with ``send(message) -> AgentResult`` and ``transcript``.
    user_lm, judge_lm: default to the pinned "user" and "judge" models.
    agent_lms: the LM objects the agent uses in this conversation, if the
        caller wants their usage in ``record.usage["agent"]``.
    workdir: where the temporary memory and workspace directories are made.
    memory_out: if given, the persona's memory_dir is copied there when the
        conversation ends (the temporary directories are deleted).
    """
    user_lm = user_lm or make_user_lm(persona)
    judge_lm = judge_lm or make_judge_lm(persona)
    start = time.time()
    record = converse(persona, make_session, user_lm, workdir, memory_out)
    score(persona, record, judge_lm)
    record.seconds = round(time.time() - start, 2)
    record.usage = {"agent": _usage(agent_lms), "user": _usage([user_lm]), "judge": _usage([judge_lm])}
    return record

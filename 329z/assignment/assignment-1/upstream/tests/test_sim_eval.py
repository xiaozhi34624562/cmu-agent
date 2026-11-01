"""Tests for problem (sim_eval): the simulated-user evaluation.

The deterministic test plays one scripted persona against your agent with
the fixture tools, so you can check that your session works with the
evaluation's user object before paying for a live run.

The live test plays every persona in ``tests/fixtures/personas/`` against
your full agent (``run_agent_session(lm, None, config)``), scores each
conversation with the programmatic checks and the judge, and prints one row
per persona. How a conversation is run and scored is documented in
``cs329z_hw1/simulation/README.md``. The same run is available as
``uv run python -m cs329z_hw1.simulation``.

Environment variables for the live test:
    CS329Z_EVAL_SLICE=N        run only the first N personas
    CS329Z_EVAL_CONCURRENCY=N  conversations run at the same time (default 4)
    CS329Z_EVAL_SALT=text      repeat the run without the cache
"""

from __future__ import annotations

import os

import pytest

from cs329z_hw1.llm import ScriptedLM
from cs329z_hw1.simulation import (
    adapter_agent_factory,
    format_table,
    load_personas,
    parse_persona,
    required_successes,
    run_eval,
    run_persona,
)
from cs329z_hw1.simulation.evaluate import DEFAULT_CONCURRENCY, EVAL_SIZE, new_run_dir
from cs329z_hw1.simulation.record import tool_calls
from cs329z_hw1 import adapters
from tests import thresholds
from tests.conftest import eval_slice
from tests.fixture_tools import DIRECTORY, make_fixture_tools
from tests.helpers import FIXTURES

PERSONA_DIR = FIXTURES / "personas"

SCRIPTED_PERSONA = {
    "id": "scripted-helpdesk",
    "category": "coding",
    "role": "An office manager at Cardinal Energy.",
    "disposition": "Brief.",
    "sessions": [{"goal": "Learn the IT helpdesk extension.", "opening": "What is the IT helpdesk extension?"}],
    "mode": "confirm",
    "approval": {
        "policy": "Approve lookups. Deny anything that saves data.",
        "overrides": [
            {"tool": "write_note", "pattern": ".*", "decision": "deny", "reason": "Do not save notes. Just tell me."},
            {"tool": "lookup", "pattern": ".*", "decision": "approve"},
        ],
    },
    "checks": [
        {"type": "final_contains_any", "values": ["4410"]},
        {"type": "tool_called", "name": "lookup", "status": "ok"},
        {"type": "denied_then_adapted", "name": "write_note"},
        {"type": "no_agent_error"},
    ],
    "rubric": ["The agent tells the user that the IT helpdesk is at extension 4410."],
}

JUDGE_PASS = "CRITERIA:\n1. MET: the reply gives extension 4410\nFABRICATION: NO\nREASON: The agent looked it up and answered.\nVERDICT: PASS"


def test_scripted_persona_conversation(scripted, canned_aux, tmp_path):
    """One conversation in confirm mode with no live calls. The scripted
    model first tries write_note (the persona denies it), then calls lookup,
    then answers. The persona says its goal is met and the scripted judge
    passes the conversation."""
    fx = make_fixture_tools()
    lm = scripted(
        [
            {"text": "Saving a note first.", "tool_call": {"name": "write_note", "args": {"text": "helpdesk question"}}},
            {"text": "Looking it up.", "tool_call": {"name": "lookup", "args": {"key": "it_helpdesk"}}},
            f"The IT helpdesk is at {DIRECTORY['it_helpdesk']}.",
        ]
    )
    persona = parse_persona(SCRIPTED_PERSONA)
    user_lm = ScriptedLM(["STATUS: DONE\nMESSAGE:"])
    judge_lm = ScriptedLM([JUDGE_PASS])

    def make_session(config):
        config.aux_lm = canned_aux
        return adapters.run_agent_session(lm, fx.tools, config)

    record = run_persona(persona, make_session, user_lm=user_lm, judge_lm=judge_lm, workdir=tmp_path)

    assert record.error is None, f"your agent raised during the conversation:\n{record.error}"
    session = record.sessions[0]
    assert fx.notes == [], (
        "write_note ran although the user denied it. In confirm mode a tool with read_only=False "
        "must wait for config.user.approve(call), and a denied call must not be executed."
    )
    denials = [a for a in session.events("approval") if not a["approved"]]
    assert [a["tool"] for a in denials] == ["write_note"], (
        "expected exactly one denied approval request, for write_note; the persona recorded "
        f"these approval requests: {session.events('approval')}"
    )
    calls = tool_calls(session.transcript)
    denied = [c for c in calls if c["status"] == "denied"]
    assert denied and "Do not save notes" in denied[0]["content"], (
        "expected a tool_result event with status 'denied' whose content includes the user's reason "
        f"('Do not save notes. Just tell me.'); tool calls in your transcript: {calls}"
    )
    assert session.agent_replies == [f"The IT helpdesk is at {DIRECTORY['it_helpdesk']}."], (
        f"expected one agent reply (the scripted final answer), got {session.agent_replies}"
    )
    assert session.ending == "goal_met"
    failed = [f"{c.type}: {c.detail}" for c in record.failed_checks]
    assert not failed, f"programmatic checks failed: {failed}"
    assert record.success


@pytest.mark.live
def test_live_simulated_users(archive):
    personas = eval_slice(load_personas(PERSONA_DIR))
    if not personas:
        pytest.fail(f"no persona files found in {PERSONA_DIR}", pytrace=False)
    out_dir = new_run_dir()
    records = run_eval(
        personas,
        adapter_agent_factory(adapters),
        concurrency=int(os.environ.get("CS329Z_EVAL_CONCURRENCY") or DEFAULT_CONCURRENCY),
        out_dir=out_dir,
    )
    table = format_table(records)
    successes = sum(r.success for r in records)
    needed = required_successes(len(personas), thresholds.SIM_EVAL_FULL_CREDIT, EVAL_SIZE)
    print(f"\n{table}\nsim_eval live: {successes} of {len(records)} conversations succeeded (need {needed}).")
    print(f"Conversation records are saved in {out_dir}/")
    assert successes >= needed, (
        f"{successes} of {len(records)} conversations succeeded; full credit needs {needed}. "
        f"Records are in {out_dir}/.\n{table}"
    )

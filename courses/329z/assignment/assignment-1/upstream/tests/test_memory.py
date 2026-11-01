"""Tests for problem (memory).

A session built with ``AgentConfig.memory_dir`` set has two more tools,
whatever tool list it was given:

    remember(fact: str)    store one fact so later sessions can use it
    recall(query: str)     search the stored facts

Everything your agent stores must be in files under ``memory_dir``. A new
session with the same ``memory_dir`` can recall what earlier sessions stored;
a session with a different ``memory_dir`` cannot. Neither tool ever needs the
user's approval.

The deterministic tests use the fixture tools and a scripted model. The
"sessions" of one test are separate objects created one after the other, the
way separate program runs would create them.
"""

from __future__ import annotations

import pytest

from cs329z_hw1.types import AgentConfig, AgentResult
from cs329z_hw1.user import ScriptedUser
from cs329z_hw1 import adapters
from tests.fixture_tools import make_fixture_tools
from tests.helpers import contains, events
from tests.thresholds import MEMORY_MIN_CORRECT

FACT = "The user's cost center code is ZEPHYR4471 and it goes on every travel request."
TOKEN = "ZEPHYR4471"


@pytest.fixture(autouse=True)
def _canned_aux(canned_aux):
    """Every session in this file gets the canned auxiliary model (see
    conftest.py) as AgentConfig.aux_lm unless a test passes another one, so
    an agent may call aux_lm on any send without using up scripted replies."""
    global AUX
    AUX = canned_aux


AUX = None


def call(name: str, **args) -> dict:
    return {"text": "", "tool_call": {"name": name, "args": args}}


def make_session(lm, memory_dir, **config):
    fx = make_fixture_tools()
    config.setdefault("aux_lm", AUX)
    return adapters.run_agent_session(lm, fx.tools, AgentConfig(memory_dir=memory_dir, **config))


def send(session, message: str) -> AgentResult:
    try:
        return session.send(message)
    except NotImplementedError:
        raise
    except Exception as exc:
        pytest.fail(f"session.send({message!r}) raised {type(exc).__name__}: {exc}", pytrace=False)


def results_of(session, name: str) -> list[dict]:
    return [e for e in events(session.transcript, "tool_result") if e.get("name") == name]


def files_containing(directory, needle: str) -> list[str]:
    found = []
    for path in directory.rglob("*"):
        if path.is_file():
            try:
                if needle in path.read_text(encoding="utf-8", errors="ignore"):
                    found.append(str(path.relative_to(directory)))
            except OSError:
                pass
    return found


def store_fact(scripted, memory_dir, fact: str = FACT):
    """Session 1: the scripted model stores one fact."""
    lm = scripted([call("remember", fact=fact), "Stored."])
    session = make_session(lm, memory_dir)
    result = send(session, "Please remember my cost center code: ZEPHYR4471. It goes on every travel request.")
    return lm, session, result


# -------------------------------------------------------- deterministic ---


def test_memory_tools_are_offered_when_memory_dir_is_set(scripted, tmp_path):
    lm = scripted(["Hello."])
    session = make_session(lm, tmp_path)
    send(session, "Hi.")
    system = lm.calls[0][0]["content"]
    missing = [name for name in ("remember", "recall") if name not in system]
    assert not missing, (
        f"memory_dir is set, but the first message of the first model call does not mention {missing}"
    )


def test_remember_writes_the_fact_under_memory_dir(scripted, tmp_path):
    lm, session, result = store_fact(scripted, tmp_path)
    assert result.status == "done", f"expected 'done', got {result.status!r}: {result.text!r}"
    stored = results_of(session, "remember")
    assert len(stored) == 1 and stored[0]["status"] == "ok", (
        f"expected one remember tool_result with status 'ok', got {stored}"
    )
    assert files_containing(tmp_path, TOKEN), (
        f"after remember(fact={FACT!r}) no file under memory_dir ({tmp_path}) contains "
        f"{TOKEN!r}. Persistent memory must be stored in files under AgentConfig.memory_dir."
    )


def test_new_session_with_the_same_dir_recalls_the_fact(scripted, tmp_path):
    store_fact(scripted, tmp_path)

    lm = scripted([call("recall", query="cost center code"), "Your cost center code is ZEPHYR4471."])
    session = make_session(lm, tmp_path)
    result = send(session, "What is my cost center code?")

    assert result.status == "done", f"expected 'done', got {result.status!r}: {result.text!r}"
    recalled = results_of(session, "recall")
    assert len(recalled) == 1 and recalled[0]["status"] == "ok", (
        f"expected one recall tool_result with status 'ok', got {recalled}"
    )
    assert TOKEN in recalled[0]["content"], (
        f"an earlier session stored {FACT!r}; recall(query='cost center code') in a new "
        f"session with the same memory_dir returned {recalled[0]['content']!r}"
    )
    assert any(TOKEN in m["content"] for m in lm.calls[1]), (
        "the recalled fact is not in the model call after recall"
    )


def test_recall_works_inside_the_session_that_stored_the_fact(scripted, tmp_path):
    lm = scripted([call("remember", fact=FACT), call("recall", query="cost center"), "Done."])
    session = make_session(lm, tmp_path)
    send(session, "Remember my cost center code ZEPHYR4471, then check that you have it.")
    recalled = results_of(session, "recall")
    assert recalled and TOKEN in recalled[0]["content"], (
        f"recall right after remember did not return the fact: {recalled}"
    )


def test_session_with_a_different_dir_does_not_see_the_fact(scripted, tmp_path):
    first_dir, other_dir = tmp_path / "first", tmp_path / "other"
    first_dir.mkdir()
    other_dir.mkdir()
    store_fact(scripted, first_dir)

    lm = scripted([call("recall", query="cost center code"), "I have nothing stored about that."])
    session = make_session(lm, other_dir)
    result = send(session, "What is my cost center code?")

    assert result.status == "done", f"expected 'done', got {result.status!r}: {result.text!r}"
    recalled = results_of(session, "recall")
    assert len(recalled) == 1, f"expected one recall tool_result, got {recalled}"
    assert recalled[0]["status"] == "ok", (
        "recall on an empty memory is a normal outcome and should have status 'ok', got "
        f"{recalled[0]['status']!r} with content {recalled[0]['content']!r}"
    )
    assert recalled[0]["content"].strip(), "recall on an empty memory returned an empty string; say that nothing matched"
    leaked = [i for i, messages in enumerate(lm.calls, 1) if any(TOKEN in m["content"] for m in messages)]
    assert not leaked, (
        f"a fact stored under one memory_dir appeared in model calls {leaked} of a session "
        "that uses a different memory_dir"
    )
    assert not files_containing(other_dir, TOKEN), "the fact was written under the wrong memory_dir"


def test_several_facts_and_sessions(scripted, tmp_path):
    """Facts stored by two earlier sessions are both available to a third."""
    lm = scripted([call("remember", fact="The user works on the Firmware team in Boulder."), "Noted."])
    send(make_session(lm, tmp_path), "I work on the Firmware team in Boulder.")
    lm = scripted([call("remember", fact="The user wants dates written as YYYY-MM-DD."), "Noted."])
    send(make_session(lm, tmp_path), "Write dates as YYYY-MM-DD for me.")

    lm = scripted([call("recall", query="which team does the user work on"), call("recall", query="dates format"), "Done."])
    session = make_session(lm, tmp_path)
    send(session, "What do you know about me?")
    recalled = results_of(session, "recall")
    assert len(recalled) == 2, f"expected two recall results, got {recalled}"
    assert "Firmware" in recalled[0]["content"], (
        f"recall(query='which team does the user work on') did not return the stored fact "
        f"about the Firmware team: {recalled[0]['content']!r}"
    )
    assert "YYYY-MM-DD" in recalled[1]["content"], (
        f"recall(query='dates format') did not return the stored fact about dates: {recalled[1]['content']!r}"
    )


def test_memory_tools_need_no_approval(scripted, tmp_path):
    """In confirm mode, remember and recall run without a call to
    config.user.approve. The scripted user has no approvals to give, so an
    approval request for either tool fails this test."""
    user = ScriptedUser()
    lm = scripted([call("remember", fact=FACT), call("recall", query="cost center"), "Done."])
    session = make_session(lm, tmp_path, mode="confirm", user=user)
    result = send(session, "Remember my cost center code ZEPHYR4471.")

    assert result.status == "done", f"expected 'done', got {result.status!r}: {result.text!r}"
    asked = [entry for entry in user.log if entry[0] == "approve"]
    assert not asked, f"remember and recall must not ask for approval; approve was called for {asked}"
    statuses = [e["status"] for e in events(session.transcript, "tool_result")]
    assert statuses == ["ok", "ok"], f"expected both memory calls to run with status 'ok', got {statuses}"
    assert files_containing(tmp_path, TOKEN), "the fact was not stored under memory_dir in confirm mode"


# ----------------------------------------------------------------- live ---

PAIRS = [
    {
        "id": "the-spec",
        "session_1": "I'm on the firmware team; when I say 'the spec' I mean the firmware spec.",
        "session_2": "What is the current version of the spec, and who wrote it?",
        "any_of": ["3.2"],
        "none_of": ["2.1", "Mehta"],
    },
    {
        "id": "my-team",
        "session_1": "For future conversations: I work on the Site Reliability Engineering team.",
        "session_2": "Who is the manager of my team?",
        "any_of": ["Nwosu"],
        "none_of": [],
    },
    {
        "id": "cost-center",
        "session_1": "Please keep this for later: my cost center is CC-8812 and my employee number is 40417.",
        "session_2": "I am filling in a travel request. What is my cost center?",
        "any_of": ["CC-8812", "8812"],
        "none_of": [],
    },
]


def run_pair(pair: dict, live_lm, live_aux, base_dir, share_memory: bool = True) -> dict:
    """Session 1 with one memory_dir, then a new session 2. With
    share_memory=False session 2 gets an empty memory_dir instead."""
    first_dir = base_dir / f"{pair['id']}-memory"
    first_dir.mkdir(parents=True, exist_ok=True)
    second_dir = first_dir
    if not share_memory:
        second_dir = base_dir / f"{pair['id']}-empty"
        second_dir.mkdir(parents=True, exist_ok=True)

    def config(memory_dir):
        return AgentConfig(memory_dir=memory_dir, aux_lm=live_aux, max_turns=12, workspace=base_dir / "workspace")

    session_1 = adapters.run_agent_session(live_lm, None, config(first_dir))
    first = session_1.send(pair["session_1"])
    session_2 = adapters.run_agent_session(live_lm, None, config(second_dir))
    second = session_2.send(pair["session_2"])
    ok = any(contains(second.text, a) for a in pair["any_of"]) and not any(
        contains(second.text, a) for a in pair["none_of"]
    )
    return {"pair": pair, "first": first.text, "second": second.text, "ok": ok}


@pytest.mark.live
def test_live_paired_sessions(live_lm, live_aux, tmp_path):
    """Each pair is two sessions of your full agent (tools=None) that share a
    memory_dir and nothing else. In session 1 the user states a fact about
    themselves. In session 2 the user asks a question that can only be
    answered correctly with that fact. At least MEMORY_MIN_CORRECT of the 3
    pairs must be answered correctly.

    the-spec: the answer must give the firmware spec's revision (3.2) and
    must not give the API spec's version (2.1) or its author (Mehta).
    my-team: the answer must name the manager of Site Reliability Engineering.
    cost-center: the answer must give the cost center stated in session 1."""
    rows = [run_pair(pair, live_lm, live_aux, tmp_path) for pair in PAIRS]
    correct = sum(r["ok"] for r in rows)
    lines = [f"\nmemory live: {correct} of {len(rows)} pairs correct (need {MEMORY_MIN_CORRECT}), model {live_lm.model}"]
    for r in rows:
        lines.append(f"  {'ok  ' if r['ok'] else 'MISS'} {r['pair']['id']}")
        if not r["ok"]:
            lines.append(f"       session 1 reply: {r['first'][:300]!r}")
            lines.append(
                f"       session 2 reply: {r['second'][:400]!r}\n       expected one of "
                f"{r['pair']['any_of']} and none of {r['pair']['none_of']}"
            )
    report = "\n".join(lines)
    print(report)
    if correct < MEMORY_MIN_CORRECT:
        pytest.fail(f"{correct} of {len(rows)} paired sessions passed; need {MEMORY_MIN_CORRECT}.", pytrace=False)

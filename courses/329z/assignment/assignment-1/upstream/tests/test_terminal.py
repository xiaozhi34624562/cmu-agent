"""Tests for problem (terminal).

The deterministic tests build your full agent (``tools=None``) with a
scripted model and an empty temporary directory as ``AgentConfig.workspace``.
The scripted model calls ``run_terminal`` with real commands, which run in
the course sandbox. The tests then read the transcript and the messages of
the next model call. They do not check how you lay out a command's result,
only that the output, the error output and the exit code are in it.

Status rule for run_terminal results: the tool_result has status "ok" only
when the command ran and exited with code 0. A non-zero exit code, a timeout
and a sandbox rejection have status "tool_error". (A command blocked by a
deny rule or refused by the user has status "denied"; see the guardrails and
interactive tests.) The content is shown to the model in every case.

Only ``run_terminal`` is called in these tests, so the other Cardinal tools
do not have to work yet, but ``run_agent_session(lm, None, config)`` must
build a session.
"""

from __future__ import annotations

import re
import time

import pytest

from cs329z_hw1.tokens import count_message_tokens, count_tokens
from cs329z_hw1.types import AgentConfig, AgentResult
from cs329z_hw1 import adapters
from tests.conftest import eval_slice
from tests.helpers import FIXTURES, contains_any, events, load_fixture
from tests.thresholds import TERMINAL_MIN_CORRECT_FRACTION


@pytest.fixture(autouse=True)
def _canned_aux(canned_aux):
    """Every session in this file gets the canned auxiliary model (see
    conftest.py) as AgentConfig.aux_lm unless a test passes another one, so
    an agent may call aux_lm on any send without using up scripted replies."""
    global AUX
    AUX = canned_aux


AUX = None


def run(cmd: str, say: str = "") -> dict:
    """A script entry: the model calls run_terminal with ``cmd``."""
    return {"text": say, "tool_call": {"name": "run_terminal", "args": {"cmd": cmd}}}


def make_session(lm, workspace, **config):
    config.setdefault("aux_lm", AUX)
    return adapters.run_agent_session(lm, None, AgentConfig(workspace=workspace, **config))


def send(session, message: str) -> AgentResult:
    try:
        result = session.send(message)
    except NotImplementedError:
        raise
    except Exception as exc:
        pytest.fail(
            f"session.send({message!r}) raised {type(exc).__name__}: {exc}\n"
            "A failing, rejected or timed-out command must come back as a tool result, "
            "not as an exception.",
            pytrace=False,
        )
    assert isinstance(result, AgentResult), f"send must return an AgentResult, got {type(result).__name__}"
    return result


def shown(messages, needle: str) -> bool:
    return any(needle in m["content"] for m in messages)


def terminal_results(session) -> list[dict]:
    return [e for e in events(session.transcript, "tool_result") if e.get("name") == "run_terminal"]


def expect_done(result: AgentResult, lm, n_calls: int) -> None:
    assert result.status == "done", f"expected status 'done', got {result.status!r} with text {result.text!r}"
    assert len(lm.calls) == n_calls, f"expected {n_calls} model calls, your agent made {len(lm.calls)}"


# -------------------------------------------------------- deterministic ---


def test_run_terminal_is_offered_to_the_model(scripted, tmp_path):
    lm = scripted(["Hello."])
    session = make_session(lm, tmp_path)
    send(session, "Hi.")
    assert "run_terminal" in lm.calls[0][0]["content"], (
        "the first message of the first model call does not mention run_terminal"
    )


def test_stdout_reaches_the_model(scripted, tmp_path):
    lm = scripted([run("echo marker-4471"), "The command printed marker-4471."])
    session = make_session(lm, tmp_path)
    result = send(session, "Print the marker.")

    expect_done(result, lm, 2)
    results = terminal_results(session)
    assert len(results) == 1, f"expected one run_terminal tool_result event, got {results}"
    assert results[0]["status"] == "ok", (
        f"a command that ran and exited with 0 should give status 'ok', got {results[0]['status']!r} "
        f"with content {results[0]['content']!r}"
    )
    assert "marker-4471" in results[0]["content"], (
        f"the command printed 'marker-4471' but the tool result does not contain it: {results[0]['content']!r}"
    )
    assert shown(lm.calls[1], "marker-4471"), "the command's stdout is not in the next model call"


def test_commands_run_in_the_configured_workspace(scripted, tmp_path):
    """AgentConfig.workspace is the working directory: a file written by one
    command is on disk there and is readable by the next command."""
    lm = scripted([run("echo saved-7782 > note.txt"), run("cat note.txt"), "Done."])
    session = make_session(lm, tmp_path)
    result = send(session, "Write then read a file.")

    expect_done(result, lm, 3)
    assert (tmp_path / "note.txt").exists(), (
        f"the command `echo saved-7782 > note.txt` did not create note.txt in the configured "
        f"workspace {tmp_path}. Pass AgentConfig.workspace to sandbox.run_terminal."
    )
    assert shown(lm.calls[2], "saved-7782"), "the output of `cat note.txt` is not in the next model call"


def test_exit_code_and_stderr_are_visible(scripted, tmp_path):
    """A command that prints to stdout and stderr and exits with code 3: all
    three are in the tool result the model sees, and the status is tool_error."""
    cmd = "python3 -c \"import sys; print('out-5521'); sys.stderr.write('err-8834\\n'); sys.exit(3)\""
    lm = scripted([run(cmd), "It failed with exit code 3."])
    session = make_session(lm, tmp_path)
    result = send(session, "Run the failing script.")

    expect_done(result, lm, 2)
    assert terminal_results(session)[0]["status"] == "tool_error", (
        "a command that exits with a non-zero code must give status 'tool_error', got "
        f"{terminal_results(session)[0]['status']!r}"
    )
    content = terminal_results(session)[0]["content"]
    assert "out-5521" in content, f"stdout ('out-5521') is missing from the tool result: {content!r}"
    assert "err-8834" in content, f"stderr ('err-8834') is missing from the tool result: {content!r}"
    assert re.search(r"(?<!\d)3(?!\d)", content.replace("out-5521", "").replace("err-8834", "")), (
        f"the exit code 3 is missing from the tool result: {content!r}"
    )
    assert shown(lm.calls[1], content), "the tool result is not in the next model call"


def test_exit_code_zero_is_visible(scripted, tmp_path):
    lm = scripted([run("echo fine"), "Done."])
    session = make_session(lm, tmp_path)
    send(session, "Run it.")
    content = terminal_results(session)[0]["content"]
    assert re.search(r"(?<!\d)0(?!\d)", content), f"the exit code 0 is missing from the tool result: {content!r}"


def test_rejected_command_is_an_observation_and_the_run_continues(scripted, tmp_path):
    """curl is not on the sandbox allowlist. The rejection comes back as a
    tool result, the model sees it, and its next command runs."""
    lm = scripted([run("curl http://example.com/data"), run("echo after-rejection-3319"), "Done."])
    session = make_session(lm, tmp_path)
    result = send(session, "Fetch the data.")

    expect_done(result, lm, 3)
    results = terminal_results(session)
    assert len(results) == 2, f"expected two run_terminal tool_result events, got {len(results)}"
    assert results[0]["status"] == "tool_error", (
        f"a command the sandbox rejects must give status 'tool_error', got {results[0]['status']!r}"
    )
    assert results[1]["status"] == "ok", f"expected 'ok' for the echo command, got {results[1]['status']!r}"
    assert results[0]["content"].strip(), "the tool result for the rejected command is empty"
    assert "curl" in results[0]["content"], (
        "the tool result for the rejected command should carry the sandbox's reason, which "
        f"names the program that is not allowed; got {results[0]['content']!r}"
    )
    assert shown(lm.calls[1], results[0]["content"]), "the rejection is not in the next model call"
    assert "after-rejection-3319" in results[1]["content"], (
        f"the command after the rejected one did not run: {results[1]['content']!r}"
    )


def test_timeout_is_an_observation_and_the_run_continues(scripted, tmp_path):
    """AgentConfig.terminal_timeout is 1 second here and must be passed to
    sandbox.run_terminal. A command that sleeps for 60 seconds is killed
    after 1 second. The timeout comes back as a tool result and the next
    command runs."""
    lm = scripted(
        [
            run("python3 -c \"import time; print('started-6120', flush=True); time.sleep(60)\""),
            run("echo after-timeout-9043"),
            "Done.",
        ]
    )
    session = make_session(lm, tmp_path, terminal_timeout=1.0)
    start = time.time()
    result = send(session, "Run the slow script.")
    elapsed = time.time() - start

    expect_done(result, lm, 3)
    assert elapsed < 8, (
        f"the send took {elapsed:.0f} seconds with terminal_timeout=1.0. Pass "
        "AgentConfig.terminal_timeout as the timeout of sandbox.run_terminal."
    )
    results = terminal_results(session)
    assert len(results) == 2, f"expected two run_terminal tool_result events, got {len(results)}"
    assert results[0]["status"] == "tool_error", (
        f"a command that times out must give status 'tool_error', got {results[0]['status']!r}"
    )
    assert results[0]["content"].strip(), "the tool result for the timed-out command is empty"
    assert re.search(r"tim(ed|e)[ -]?out|time limit|killed", results[0]["content"], re.IGNORECASE), (
        "the tool result for the timed-out command does not say that it timed out "
        f"(looked for 'timed out', 'timeout', 'time limit' or 'killed'): {results[0]['content']!r}"
    )
    assert shown(lm.calls[1], results[0]["content"]), "the timeout is not in the next model call"
    assert "after-timeout-9043" in results[1]["content"], (
        f"the command after the timed-out one did not run: {results[1]['content']!r}"
    )


BIG_COMMAND = "python3 -c \"for i in range(12000): print('row %06d ' % i + 'x' * 40)\""  # about 612,000 characters


@pytest.mark.parametrize("context_budget", [16_000, 6_000])
def test_large_output_stays_within_the_context_budget(scripted, canned_aux, tmp_path, context_budget):
    """A command prints about 600 KB (150,000 tokens). Every model call after
    it must still satisfy count_message_tokens(messages) <= context_budget,
    and the run continues normally."""
    lm = scripted([run(BIG_COMMAND), run(BIG_COMMAND), run("echo small-2207"), "Done."])
    session = make_session(lm, tmp_path, context_budget=context_budget, aux_lm=canned_aux)
    result = send(session, "Print the big table twice.")

    expect_done(result, lm, 4)
    for i, messages in enumerate(lm.calls, start=1):
        size = count_message_tokens(messages)
        assert size <= context_budget, (
            f"model call {i} has {size} tokens; context_budget is {context_budget}. "
            "The output of a command must be cut down before it enters the context."
        )
    results = terminal_results(session)
    assert len(results) == 3, f"expected three run_terminal tool_result events, got {len(results)}"
    for r in results[:2]:
        assert r["content"].strip(), "the tool result for the large command is empty"
        assert count_tokens(r["content"]) <= context_budget, (
            f"a tool_result event holds {count_tokens(r['content'])} tokens. The event's content "
            "must be what you showed the model, not the full output."
        )
    assert shown(lm.calls[3], "small-2207"), "the output of the last command is not in the next model call"


# ----------------------------------------------------------------- live ---

LIVE_MAX_TURNS = 15


class Recording:
    """Wraps an LM and records the size of every call's messages."""

    def __init__(self, lm) -> None:
        self.lm = lm
        self.sizes: list[int] = []

    def __call__(self, messages):
        self.sizes.append(count_message_tokens(messages))
        return self.lm(messages)


@pytest.mark.live
def test_live_terminal_questions(live_lm, live_aux, archive):
    """Your full agent (tools=None, auto mode, the sandbox's default
    workspace) answers each question in tests/fixtures/terminal_questions.json
    in a fresh session. The questions have exact answers that need a
    computation over the email archive. One question makes the agent run a
    command with very large output and is followed, in the same session, by
    a second question about a detail inside that output. An answer is
    correct if it contains one of the accepted answers (tests.helpers.contains).

    Requirements: at least TERMINAL_MIN_CORRECT_FRACTION of the answers
    (follow-up included) are correct, and every model call stays within
    context_budget."""
    adapters.run_agent_session(live_lm, None, AgentConfig(aux_lm=live_aux))  # stub check before anything else
    path = FIXTURES / "terminal_questions.json"
    if not path.exists():
        pytest.fail(f"{path} is missing; it ships with the repository.", pytrace=False)
    items = eval_slice(load_fixture("terminal_questions.json"))
    config_budget = AgentConfig().context_budget

    rows, over = [], []
    for item in items:
        lm = Recording(live_lm)
        session = adapters.run_agent_session(lm, None, AgentConfig(max_turns=LIVE_MAX_TURNS, aux_lm=live_aux))
        turns = [(item["id"], item["question"], item["answers"])]
        if item.get("followup"):
            turns.append((item["id"] + "-followup", item["followup"]["question"], item["followup"]["answers"]))
        for turn_id, question, answers in turns:
            result = session.send(question)
            commands = [
                e["args"].get("cmd", "") for e in events(session.transcript, "tool_call") if e.get("name") == "run_terminal"
            ]
            rows.append(
                {
                    "id": turn_id,
                    "question": question,
                    "answers": answers,
                    "text": result.text,
                    "status": result.status,
                    "correct": contains_any(result.text, answers),
                    "commands": len(commands),
                }
            )
        if lm.sizes and max(lm.sizes) > config_budget:
            over.append(f"{item['id']} ({max(lm.sizes)} tokens)")

    correct = sum(r["correct"] for r in rows)
    needed = int(-(-len(rows) * TERMINAL_MIN_CORRECT_FRACTION // 1))
    lines = [f"\nterminal live: {correct} of {len(rows)} correct (need {needed}), model {live_lm.model}"]
    for r in rows:
        mark = "ok  " if r["correct"] else "MISS"
        lines.append(f"  {mark} {r['id']} ({r['commands']} commands so far, status {r['status']}): {r['question']}")
        if not r["correct"]:
            lines.append(f"       expected one of {r['answers']}; got: {r['text'][:300]!r}")
    report = "\n".join(lines)
    print(report)
    if over:
        pytest.fail(
            f"a model call exceeded context_budget ({config_budget} tokens) in: {', '.join(over)}.",
            pytrace=False,
        )
    if correct < needed:
        pytest.fail(f"{correct} of {len(rows)} answers are correct; need at least {needed}.", pytrace=False)

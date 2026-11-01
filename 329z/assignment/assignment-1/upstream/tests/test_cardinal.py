"""Tests for problem (cardinal). Deterministic: no model calls.

``run_agent_session(lm, None, config)`` builds a session with the Cardinal
toolset, the ten tools named in ``cs329z_hw1/cardinal.py``. These tests
check the toolset itself, not what the tools do (later problems test that):

* With ``tools=None`` the system prompt of the first model call names all
  ten tools.
* Creating a session does not read the email archive. The archive is 58 MB;
  build the email index the first time a tool needs it.
* With an explicit tool list, the session has exactly those tools, plus
  ``ask_user`` when ``config.user`` is set and ``remember`` and ``recall``
  when ``config.memory_dir`` is set.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cs329z_hw1 import data
from cs329z_hw1.cardinal import CARDINAL_TOOLS
from cs329z_hw1.types import AgentConfig
from cs329z_hw1.user import ScriptedUser
from cs329z_hw1 import adapters
from tests.fixture_tools import TOOL_NAMES, make_fixture_tools

CARDINAL_NAMES = list(CARDINAL_TOOLS)


@pytest.fixture(autouse=True)
def _canned_aux(canned_aux):
    global AUX
    AUX = canned_aux


AUX = None


def system_prompt(lm) -> str:
    """The first message of the first model call."""
    assert lm.calls, "the session made no model call"
    return lm.calls[0][0]["content"]


def mentioned(prompt: str, names) -> list[str]:
    return [name for name in names if name in prompt]


# ------------------------------------------------------- the full toolset --


def test_full_toolset_is_named_in_the_system_prompt(scripted, tmp_path):
    """tools=None: the first model call names every Cardinal tool."""
    lm = scripted(["Hello."])
    session = adapters.run_agent_session(lm, None, AgentConfig(aux_lm=AUX, workspace=tmp_path))
    session.send("Hi.")
    missing = [name for name in CARDINAL_NAMES if name not in system_prompt(lm)]
    assert not missing, (
        f"with tools=None the system prompt must name all ten Cardinal tools; missing: {missing}"
    )


def test_creating_a_session_does_not_read_the_archive(scripted, tmp_path, monkeypatch):
    """Building a session must not load data/emails/emails.jsonl. The archive
    is replaced by a missing file and the loader by one that fails, so any
    read at creation time raises here."""

    def refuse(*args, **kwargs):
        raise AssertionError("the email archive was read while creating a session")

    monkeypatch.setattr(data, "_read_emails", refuse)
    monkeypatch.setattr(data, "load_emails", refuse)
    monkeypatch.setattr(data, "emails_on", refuse)
    monkeypatch.setattr(data, "EMAILS_PATH", Path(tmp_path) / "no-such-archive.jsonl")
    lm = scripted(["Hello."])
    try:
        adapters.run_agent_session(lm, None, AgentConfig(aux_lm=AUX, workspace=tmp_path))
    except (AssertionError, NotImplementedError):
        raise
    except Exception as exc:
        pytest.fail(
            f"run_agent_session(lm, None, config) raised {type(exc).__name__}: {exc} with the "
            "archive unavailable. Creating a session must not touch the archive.",
            pytrace=False,
        )


# ------------------------------------------------------ explicit tool lists --


def test_explicit_list_gives_exactly_those_tools(scripted):
    """An explicit list, no user, no memory_dir: the prompt names the listed
    tools and none of the Cardinal ones."""
    fx = make_fixture_tools()
    lm = scripted(["Hello."])
    session = adapters.run_agent_session(lm, fx.tools, AgentConfig(aux_lm=AUX))
    session.send("Hi.")
    prompt = system_prompt(lm)
    missing = [name for name in TOOL_NAMES if name not in prompt]
    assert not missing, f"the system prompt does not name these listed tools: {missing}"
    extra = mentioned(prompt, CARDINAL_NAMES)
    assert not extra, (
        f"with an explicit tool list and no user or memory_dir, the session must not have "
        f"Cardinal tools; the prompt mentions {extra}"
    )


def test_explicit_list_plus_user_adds_ask_user(scripted):
    fx = make_fixture_tools()
    lm = scripted(["Hello."])
    config = AgentConfig(aux_lm=AUX, user=ScriptedUser())
    session = adapters.run_agent_session(lm, fx.tools, config)
    session.send("Hi.")
    prompt = system_prompt(lm)
    assert "ask_user" in prompt, "config.user is set, so the session must have the ask_user tool"
    extra = mentioned(prompt, [n for n in CARDINAL_NAMES if n != "ask_user"])
    assert not extra, f"only ask_user should be added for config.user; the prompt mentions {extra}"


def test_explicit_list_plus_memory_dir_adds_remember_and_recall(scripted, tmp_path):
    fx = make_fixture_tools()
    lm = scripted(["Hello."])
    config = AgentConfig(aux_lm=AUX, memory_dir=tmp_path / "memory")
    session = adapters.run_agent_session(lm, fx.tools, config)
    session.send("Hi.")
    prompt = system_prompt(lm)
    missing = [name for name in ("remember", "recall") if name not in prompt]
    assert not missing, f"config.memory_dir is set, so the session must have {missing}"
    extra = mentioned(prompt, [n for n in CARDINAL_NAMES if n not in ("remember", "recall")])
    assert not extra, f"only remember and recall should be added for memory_dir; the prompt mentions {extra}"

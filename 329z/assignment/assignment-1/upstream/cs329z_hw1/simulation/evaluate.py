"""Run many personas and report the results (course-provided)."""

from __future__ import annotations

import dataclasses
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Optional, Sequence

from cs329z_hw1.llm import LM
from cs329z_hw1.simulation.persona import Persona
from cs329z_hw1.simulation.record import ConversationRecord
from cs329z_hw1.simulation.runner import eval_salt, run_persona

EVAL_SIZE = 20  # conversations in the full evaluation
FULL_CREDIT = 16  # successful conversations needed for full credit
MAX_POINTS = 10
DEFAULT_CONCURRENCY = 4

# An agent factory is called once per persona and returns
# (make_session, agent_lms): the function that creates a session from an
# AgentConfig, and the LM objects that session uses (for the cost column).
AgentFactory = Callable[[Persona], tuple[Callable, Sequence]]


def adapter_agent_factory(adapters, model: Optional[str] = None) -> AgentFactory:
    """The factory the evaluation uses: your ``run_agent_session`` adapter
    with the full Cardinal toolset (``tools=None``).

    ``adapters`` is the ``cs329z_hw1.adapters`` module. ``model`` is a role or
    model name for the agent; None means "grading".
    Each persona gets its own LM objects so cost can be reported per
    conversation. A second LM is passed as ``AgentConfig.aux_lm``.
    """

    def factory(persona: Persona):
        lm = LM(model, tag=f"sim_eval/{persona.id}/agent", salt=eval_salt())
        aux = LM(model, tag=f"sim_eval/{persona.id}/agent_aux", salt=eval_salt())

        def make_session(config):
            return adapters.run_agent_session(lm, None, dataclasses.replace(config, aux_lm=aux))

        return make_session, [lm, aux]

    return factory


def run_eval(
    personas: Sequence[Persona],
    agent_factory: AgentFactory,
    *,
    concurrency: int = DEFAULT_CONCURRENCY,
    out_dir: Optional[Path] = None,
    workdir: Optional[Path] = None,
) -> list[ConversationRecord]:
    """Run every persona (``concurrency`` conversations at a time) and
    return the records in the order of ``personas``. If ``out_dir`` is
    given, each record is saved there as ``<persona id>.json``, the persona's
    memory directory as ``<persona id>.memory/``, and the table as
    ``summary.txt``."""

    def one(persona: Persona) -> ConversationRecord:
        make_session, agent_lms = agent_factory(persona)
        memory_out = out_dir / f"{persona.id}.memory" if out_dir is not None else None
        record = run_persona(persona, make_session, agent_lms=agent_lms, workdir=workdir, memory_out=memory_out)
        if out_dir is not None:
            (out_dir / f"{persona.id}.json").write_text(record.to_json(), encoding="utf-8")
        return record

    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        records = list(pool.map(one, personas))
    if out_dir is not None:
        (out_dir / "summary.txt").write_text(format_table(records) + "\n", encoding="utf-8")
    return records


def required_successes(n: int, full_credit: int = FULL_CREDIT, eval_size: int = EVAL_SIZE) -> int:
    """Successes needed for full credit when ``n`` conversations are run:
    the same fraction as 16 of 20, rounded down. 20 -> 16, 5 -> 4, 3 -> 2."""
    return (full_credit * n) // eval_size


def points(successes: int, n: int = EVAL_SIZE) -> int:
    """The handout's rule for (sim_eval): full credit (10 points) at 16 or
    more successes out of 20, one point less for each conversation below
    16, never below zero. For ``n`` other than 20 the full-credit line is
    ``required_successes(n)``."""
    return max(0, MAX_POINTS - max(0, required_successes(n) - successes))


def format_table(records: Sequence[ConversationRecord], verbose: bool = False) -> str:
    """The per-persona table and totals. Failed conversations are followed
    by the failed checks and the judge's reason; ``verbose`` prints the
    judge's reason for passed conversations too."""
    width = max([len(r.persona_id) for r in records] + [7])
    lines = [f"{'persona':<{width}}  {'category':<15}{'result':<7}{'turns':>5}{'tools':>6}{'new USD':>9}{'sec':>7}"]
    for r in records:
        tools = sum(1 for s in r.sessions for e in s.transcript if e.get("type") == "tool_call")
        lines.append(
            f"{r.persona_id:<{width}}  {r.category:<15}{'PASS' if r.success else 'FAIL':<7}"
            f"{r.user_turns:>5}{tools:>6}{r.cost_usd:>9.4f}{r.seconds:>7.1f}"
        )
        if r.error:
            lines.append("    agent raised: " + r.error.strip().splitlines()[-1])
        for check in r.failed_checks:
            lines.append(f"    check failed: {check.type}: {check.detail}")
        if r.judge is not None and not r.error and (verbose or not r.judge.passed):
            lines.append(f"    judge {'PASS' if r.judge.passed else 'FAIL'}: {r.judge.reason}")
    n = len(records)
    successes = sum(r.success for r in records)
    cost = sum(r.cost_usd for r in records)
    lines.append("")
    lines.append(
        f"Successful conversations: {successes} of {n} "
        f"(full credit at this size needs {required_successes(n)}). "
        f"New spending: ${cost:.4f}."
    )
    lines.append(
        "\"new USD\" is what this run added to your bill. A conversation whose model calls were all in the "
        "cache shows 0.0000: it was replayed from the cache. Any change to your agent's prompt or tool descriptions "
        "changes its model calls, so the conversation runs again and is charged."
    )
    if n == EVAL_SIZE:
        lines.append(f"Points under the handout's rule: {points(successes)} of {MAX_POINTS}.")
    return "\n".join(lines)


def new_run_dir(base: Path | str = "runs") -> Path:
    return Path(base) / time.strftime("sim-%Y%m%d-%H%M%S")

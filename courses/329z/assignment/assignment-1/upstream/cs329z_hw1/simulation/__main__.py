"""Command line for the simulated-user evaluation.

    uv run python -m cs329z_hw1.simulation                 # all public personas
    uv run python -m cs329z_hw1.simulation --slice 3       # the first 3
    uv run python -m cs329z_hw1.simulation --only coding   # ids or categories containing "coding"
    uv run python -m cs329z_hw1.simulation --rescore runs/sim-20261001-120000

Run it from the repository root. It plays each persona against the agent
behind ``cs329z_hw1/adapters.py:run_agent_session``, prints one row per persona,
and saves every conversation record as JSON under ``runs/``.
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path

from cs329z_hw1.simulation.evaluate import (
    DEFAULT_CONCURRENCY,
    adapter_agent_factory,
    format_table,
    new_run_dir,
    run_eval,
)
from cs329z_hw1.simulation.persona import load_personas
from cs329z_hw1.simulation.record import ConversationRecord
from cs329z_hw1.simulation.runner import make_judge_lm, score

DEFAULT_PERSONA_DIR = Path("tests/fixtures/personas")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m cs329z_hw1.simulation", description=__doc__.split("\n")[0])
    parser.add_argument("personas", nargs="?", type=Path, default=DEFAULT_PERSONA_DIR, help="directory of persona JSON files (default: tests/fixtures/personas)")
    parser.add_argument("--slice", type=int, default=None, help="run only the first N personas (default: CS329Z_EVAL_SLICE, else all)")
    parser.add_argument("--only", default=None, help="run only personas whose id or category contains this text")
    parser.add_argument("--out", type=Path, default=None, help="directory for the records (default: runs/sim-<time>)")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY, help="conversations run at the same time")
    parser.add_argument("--model", default=None, help='agent model: "grading" (default) or a model name')
    parser.add_argument("--salt", default=None, help="repeat the run without the cache: a string mixed into the cache keys of the agent and persona models (same as CS329Z_EVAL_SALT)")
    parser.add_argument("--adapters", default="cs329z_hw1.adapters", help="module that defines run_agent_session")
    parser.add_argument("--verbose", action="store_true", help="print the judge's reason for passed conversations too")
    parser.add_argument("--rescore", type=Path, default=None, help="score the saved records in this directory again without running the agent")
    args = parser.parse_args(argv)

    if args.salt is not None:
        os.environ["CS329Z_EVAL_SALT"] = args.salt
    personas = load_personas(args.personas)
    if not personas:
        print(f"No persona files (*.json) found in {args.personas}.")
        return 2
    if args.only:
        personas = [p for p in personas if args.only in p.id or args.only in p.category]
    n = args.slice if args.slice is not None else int(os.environ.get("CS329Z_EVAL_SLICE") or 0)
    if n:
        personas = personas[:n]

    if args.rescore is not None:
        records = []
        for persona in personas:
            path = args.rescore / f"{persona.id}.json"
            if not path.exists():
                continue
            record = ConversationRecord.from_json(path.read_text(encoding="utf-8"))
            judge = make_judge_lm(persona)
            score(persona, record, judge)
            record.usage = {"judge": {"calls": judge.calls, "cost_usd": judge.cost_usd}}
            path.write_text(record.to_json(), encoding="utf-8")
            records.append(record)
        if not records:
            print(f"No saved records for these personas in {args.rescore}.")
            return 2
        print(format_table(records, verbose=args.verbose))
        return 0

    sys.path.insert(0, os.getcwd())  # so that "cs329z_hw1.adapters" resolves from the repository root
    adapters = importlib.import_module(args.adapters)
    out_dir = args.out or new_run_dir()
    records = run_eval(
        personas,
        adapter_agent_factory(adapters, args.model),
        concurrency=args.concurrency,
        out_dir=out_dir,
    )
    print(format_table(records, verbose=args.verbose))
    print(f"Records saved in {out_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

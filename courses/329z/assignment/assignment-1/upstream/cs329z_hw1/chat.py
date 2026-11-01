"""Talk to your agent in the terminal (course-provided).

    uv run python -m cs329z_hw1.chat [--mode confirm|auto] [--memory-dir DIR] [--out DIR]

This builds one session with ``cs329z_hw1.adapters.run_agent_session(LM(), None,
config)``, so it runs your full Cardinal toolset on the grading model.
You are the user: in confirm mode you are asked to approve
tool calls, and ``ask_user`` questions are put to you. Type ``exit`` or
press Ctrl-D to leave.

Every conversation is saved when it ends, as ``runs/chat-<timestamp>.json``
(or under --out): the full transcript of events, plus what you typed and what
the agent replied, and the model usage. Problem (field_notes) asks you to
submit these files.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `cs329z_hw1.adapters` imports from any directory

from cs329z_hw1.llm import LM
from cs329z_hw1.types import AgentConfig
from cs329z_hw1.user import ConsoleUser


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat with your Cardinal Agent.")
    parser.add_argument("--mode", choices=["confirm", "auto"], default="confirm")
    parser.add_argument("--memory-dir", type=Path, default=Path(".lm_cache/chat_memory"))
    parser.add_argument("--out", type=Path, default=Path("runs"), help="where to save the conversation")
    args = parser.parse_args()

    from cs329z_hw1 import adapters  # your wiring

    config = AgentConfig(
        mode=args.mode,
        user=ConsoleUser(),
        memory_dir=args.memory_dir,
        aux_lm=LM(tag="chat/aux"),
    )
    lm = LM(tag="chat")
    session = adapters.run_agent_session(lm, None, config)
    print(f"Cardinal Agent ({args.mode} mode, memory in {args.memory_dir}). Type exit to leave.")
    started = time.strftime("%Y%m%d-%H%M%S")
    turns: list[dict] = []
    while True:
        try:
            message = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if message.lower() in ("exit", "quit"):
            break
        if not message:
            continue
        result = session.send(message)
        note = "" if result.status == "done" else f" [stopped: {result.status}]"
        print(f"\nagent{note}> {result.text}")
        turns.append({"user": message, "agent": result.text, "status": result.status})

    if turns:
        args.out.mkdir(parents=True, exist_ok=True)
        path = args.out / f"chat-{started}.json"
        record = {
            "started": started,
            "mode": args.mode,
            "model": lm.model,
            "turns": turns,
            "transcript": session.transcript,
            "usage": {"agent": lm.usage(), "aux": config.aux_lm.usage()},
        }
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        print(f"Saved this conversation to {path}")


if __name__ == "__main__":
    main()

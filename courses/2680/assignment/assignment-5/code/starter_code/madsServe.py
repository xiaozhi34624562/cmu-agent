#!/usr/bin/env python3
"""madsServe.py — DISPATCHER driver of the CS2680 Assignment 5 harness.
(Assignment 3 shipped this file as madsOpt.py, with traces in madsOpt_logs/.)

    python madsServe.py [--log]

This file is course infrastructure: the leaderboard grader runs its own copy of
it (only your src/ is taken from your submission). Everything that is yours
lives in src/ — see src/agentic_loop.py.

YOUR agent drives the task flow. The dispatcher only serves requests and enforces the rules:

    dispatcher = Dispatcher(...)               # built here
    Agent(dispatcher).run()                    # your main loop (src/agentic_loop.py)

Calls your Agent may make (all block until the dispatcher answers; the client lives in
dispatcher/dispatcher.py: `from dispatcher import Dispatcher, DispatcherError`):
    task = dispatcher.next_task()        open a new task: its sandbox is started and the task
                                         dict returned ({task (index k), instruction, sandbox_url,
                                         workdir, time_limit_s}); None when no tasks are left;
                                         raises DispatcherError when A3_MAX_LIVE tasks are live.
                                         k says nothing about which task it is (the leaderboard
                                         hands the tasks out in a random order).
                                         time_limit_s: the most seconds the task may stay open
                                         from now, i.e. its own limit (Terminal-Bench: task.toml)
                                         or what is left of the run's limit (6 h for Terminal-Bench,
                                         4 h for Assignment 4's tasks, which have no limit of their
                                         own), whichever is less; None only when no limit applies
                                         (an Assignment 4 task in a local run with A3_RUN_LIMIT_S=0)
    dispatcher.done(k, reason, iterations) task k is finished: the course grades the task's final
                                         state (its container as the agent left it). Returns at
                                         once and does not report the result. A task still open
                                         time_limit_s seconds after it was opened is graded at
                                         that moment, as if done(k) had been called. At the run's
                                         limit the run stops (the next call raises
                                         DispatcherShutdown); tasks never opened count as not solved.
    dispatcher.logger(k)                 the TraceLogger for task k (madsServe_logs/<k>/run.jsonl):
                                         log api_request / tool_call / tool_result to it
Assignment 4's extract_patch, submit_patch, evaluate and continue_task are gone: no task's tests
run before done(k).

File handshake with evaluation_scripts/run_all.py, all under .tasks/seq/:
    agent -> host  req_<n>.json   {"n", "op", "k", ...}     (one at a time, n = 0,1,2,...)
    host  -> agent resp_<n>.json  {"n", "ok", ...payload | "error"}
    host  -> agent ready | shutdown ;  agent -> host  end   (agent finished)
Model calls: run_all.py sets CS2680_BASE_URL to the egress proxy (http://a3proxy_<run>:3128/v1,
the agent container's only way out, which forwards to your server, A3_API_UPSTREAM);
CS2680_API_KEY and the model ids CS2680_MODEL_EXPERT / _STANDARD / _STARTER come from the host
(run_all.py passes every CS2680_* variable into the agent container). Your Agent reads them with
os.environ — never a hard-coded URL.
Requires Python 3.10+, the `openai` package, and the stdlib.
"""

import argparse
import os
import sys
import traceback

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from dispatcher import Dispatcher, DispatcherShutdown, SEQ_DIR, _log  # noqa: E402  (dispatcher client)
from src.agentic_loop import Agent                                # noqa: E402  (student code)


def main() -> int:
    parser = argparse.ArgumentParser(description="CS2680 Assignment 5 harness driver (dispatcher)")
    parser.add_argument("--log", action="store_true", help="write per-task JSONL traces to ./madsServe_logs/<k>/")
    args = parser.parse_args()
    if not os.environ.get("CS2680_BASE_URL"):
        sys.exit("CS2680_BASE_URL is not set: run the agent with evaluation_scripts/run_all.py")
    dispatcher = Dispatcher(log_enabled=args.log)
    rc = 0
    try:
        Agent(dispatcher).run()
    except DispatcherShutdown:
        _log("shutdown by the dispatcher")
    except Exception as e:           # run_all.py reports the run as crashed: this process exits 1
        _log(f"Agent.run raised {type(e).__name__}: {e}")
        traceback.print_exc()
        rc = 1
    finally:
        for lg in dispatcher._loggers.values():
            lg.close()
        tmp = os.path.join(SEQ_DIR, ".end.tmp")
        with open(tmp, "w") as f:
            f.write("end\n")
        os.replace(tmp, os.path.join(SEQ_DIR, "end"))
    return rc


if __name__ == "__main__":
    sys.exit(main())

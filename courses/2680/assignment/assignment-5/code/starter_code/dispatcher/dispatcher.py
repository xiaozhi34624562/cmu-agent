"""dispatcher/dispatcher.py — the agent's client to the DISPATCHER (course infrastructure, not yours).

Your code imports it as `from dispatcher import Dispatcher, DispatcherError`; madsServe.py builds
the Dispatcher and hands it to Agent(dispatcher).run(). See madsServe.py for the call list.
"""

import json
import os
import sys
import threading
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the harness root (this file lives in dispatcher/)
sys.path.insert(0, HERE)

from evaluation_scripts.trace_logger import TraceLogger    # noqa: E402  (course trace format)

SEQ_DIR = os.path.join(HERE, ".tasks", "seq")
POLL_S = 1


def _log(msg: str):
    print(f"[madsServe] {msg}", file=sys.stderr, flush=True)


class DispatcherError(Exception):
    """The dispatcher refused a call (too many live tasks, unknown task, ...)."""


class DispatcherShutdown(Exception):
    """The dispatcher ended the run."""


class TaskTraceLogger(TraceLogger):
    """The course TraceLogger, but writing to a fixed per-task file."""

    def __init__(self, path: str, enabled: bool):
        super().__init__(False)
        self.enabled = enabled
        if enabled:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self._fh = open(path, "a", buffering=1)


class Dispatcher:
    def __init__(self, log_enabled: bool):
        self._lock = threading.Lock()
        self._n = 0
        self._loggers = {}
        self._log_enabled = log_enabled

    # -- transport -----------------------------------------------------------
    def _wait_for(self, path: str) -> dict:
        while not os.path.exists(path):
            if os.path.exists(os.path.join(SEQ_DIR, "shutdown")):
                raise DispatcherShutdown("the dispatcher ended the run")
            time.sleep(POLL_S)
        with open(path) as f:
            return json.load(f)

    def _request(self, op: str, **fields) -> dict:
        with self._lock:                       # the lock only orders the request numbers
            n = self._n; self._n += 1
            req = {"n": n, "op": op, **fields}
            tmp = os.path.join(SEQ_DIR, f".req_{n}.json")
            with open(tmp, "w") as f:
                json.dump(req, f)
            os.replace(tmp, os.path.join(SEQ_DIR, f"req_{n}.json"))
        resp = self._wait_for(os.path.join(SEQ_DIR, f"resp_{n}.json"))   # outside the lock: other threads proceed
        if not resp.get("ok"):
            raise DispatcherError(resp.get("error", "dispatcher refused the request"))
        return resp

    # -- the API -------------------------------------------------------------
    def next_task(self):
        """Open the next task: {task (index k), instruction, sandbox_url, workdir, time_limit_s}, or None when
        no tasks are left. time_limit_s is the most seconds the task may stay open from now: its own limit or
        what is left of the run's limit, whichever is less; None only when no limit applies (an Assignment 4
        task in a local run with A3_RUN_LIMIT_S=0)."""
        resp = self._request("next_task")
        task = resp.get("task")
        if task is not None:
            self.logger(task["task"]).run_start(task.get("workdir", "/app"))
            lim = task.get("time_limit_s")
            _log(f"task #{task['task']} opened (sandbox {task.get('sandbox_url') or '(none)'}, "
                 f"{'no time limit' if lim is None else f'time limit {lim} s'})")
        return task

    def done(self, k: int, reason: str = "done", iterations=None) -> dict:
        """Task k is finished: the course grades the task's final state (after this call, the task's
        sandbox no longer answers). Returns at once; the result is not reported to the agent. A task
        that already reached its own time limit returns {"ok": True, "timed_out": True}; after the run's
        limit this call raises DispatcherShutdown."""
        resp = self._request("done", k=int(k))
        self.logger(k).run_end(reason, int(iterations or 0))
        self.logger(k).close()
        _log(f"task #{k} done ({reason})" + (" after its time limit" if resp.get("timed_out") else ""))
        return resp

    def logger(self, k: int) -> TraceLogger:
        if k not in self._loggers:
            self._loggers[k] = TaskTraceLogger(os.path.join("madsServe_logs", str(k), "run.jsonl"), self._log_enabled)
        return self._loggers[k]

"""Your agent. Everything in src/ is yours: replace this starter with your own design.

madsServe.py (course code) builds the dispatcher client and calls

    Agent(dispatcher).run()

That is all it needs from src/. This starter only shows how to use
what the course provides. It does no work on the tasks, so every task fails until you
write your agent:

- the dispatcher (dispatcher/dispatcher.py) opens tasks and ends them: Agent.run() and
  Agent.solve() below show every call;
- a Sandbox (src/sandbox.py) is the only way to read, write or run anything in a task's
  container;
- your server (environment variables: CS2680_BASE_URL, CS2680_API_KEY and the model ids
  CS2680_MODEL_EXPERT / CS2680_MODEL_STANDARD / CS2680_MODEL_STARTER) is used by call_model() below;
- the trace (dispatcher.logger(k)) must get every model call and every tool call: the
  leaderboard counts your turns from it.
"""

import os
import sys
import time

from .sandbox import Sandbox


def _debug(msg: str):
    print(f"[madsServe] {msg}", file=sys.stderr, flush=True)


def call_model(client, model_id: str, messages: list, logger, iteration: int, **kwargs):
    """One chat-completions request to your server, logged in the task's trace.

    `messages` is an OpenAI-style message list; extra keyword arguments (e.g. tools=[...]) are
    passed to the API unchanged. Nothing else is done for you here.
    """
    response = client.chat.completions.create(model=model_id, messages=messages, **kwargs)
    usage = response.usage
    logger.api_request(iteration,
                       getattr(usage, "prompt_tokens", None),
                       getattr(usage, "completion_tokens", None),
                       getattr(usage, "total_tokens", None),
                       model_id)                  # the model this request used (one run may use several)
    return response


class Agent:
    def __init__(self, dispatcher):
        from openai import OpenAI                       # installed in the agent container

        self.dispatcher = dispatcher
        self.model_id = os.environ["CS2680_MODEL_STANDARD"]   # this starter's model; any CS2680_MODEL_* may be used
        self.client = OpenAI(base_url=os.environ["CS2680_BASE_URL"], api_key=os.environ["CS2680_API_KEY"])

    def run(self):
        """Work through the tasks. This starter takes them one at a time, in the order given."""
        from dispatcher import DispatcherShutdown
        while True:
            try:
                # Opens the next task (its task container is started for you) and returns its
                # dict, or None when no tasks are left. Raises DispatcherError
                # (from dispatcher import DispatcherError) when A3_MAX_LIVE tasks are already open.
                task = self.dispatcher.next_task()
            except DispatcherShutdown:                   # the dispatcher ended the run (e.g. time limit)
                return
            if task is None:
                return
            try:
                self.solve(task)
            except DispatcherShutdown:
                return

    def solve(self, task: dict):
        k = task["task"]                                  # the task index
        logger = self.dispatcher.logger(k)                # this task's trace: madsServe_logs/<k>/run.jsonl
        sb = Sandbox(task["sandbox_url"], task["workdir"])  # this task's container
        # What to do: task["instruction"]. Time: task["time_limit_s"] seconds from next_task() (the
        # task's own limit or what is left of the run's, whichever is less; None: no limit); then the
        # task is graded as it is, whether or not done(k) was called.
        limit = task["time_limit_s"]
        deadline = None if limit is None else time.monotonic() + limit
        iterations = 0

        # ---- your agent's work on the task goes here -----------------------------------------
        # Ask the model:  response = call_model(self.client, self.model_id, messages, logger, iterations)
        # Container:      r = sb.exec("ls -la", timeout_s=60)  # {"output", "exit_code", "timed_out"}
        #                 text = sb.read_text("path/to/file");  sb.write_text("path/to/file", text)
        # In background:  sb.exec("cmd > /tmp/cmd.log 2>&1 < /dev/null &", timeout_s=60)  # redirected: without it,
        #                 exec waits 10 s for the job and returns only the output so far (src/sandbox_server.py)
        # Log tool use:   logger.tool_call(iterations, name, args)
        #                 logger.tool_result(iterations, name, result, is_error)
        # Time left:      None if deadline is None else deadline - time.monotonic()
        # ---------------------------------------------------------------------------------------

        # The course grades the container's final state: files where the instruction asks for
        # them, and anything the task asks to keep running. The result is not reported back.
        _debug(f"task #{k}: done, " + ("no time limit" if deadline is None else f"{deadline - time.monotonic():.0f} s left"))
        self.dispatcher.done(k, "done", iterations)

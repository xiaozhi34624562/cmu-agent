"""Run one episode of agent <-> environment interaction (given)."""

from __future__ import annotations

import contextlib
import contextvars
import time

from scottyrl.agents.base import Agent
from scottyrl.envs.base import Env
from scottyrl.types import Trajectory

# Completed episodes waiting to be written to disk. `MetricsLogger` drains this
# on every log() call; it is the only given component that knows the current
# training step, which is what the on-disk layout is keyed by. Buffering here
# keeps run_episode's signature (and the student-facing trainers) unchanged.
#
# Each entry: (phase, step_tag, policy_version, task, tool_docs, reward,
# num_steps, turns). `phase` and `step_tag` come from the enclosing
# rollout_phase block ("train" and None by default); `policy_version` is the
# agent's policy.version when the trainer stamped one (the async trainer's
# publish_policy does), else None. `turns` holds one dict per turn with the
# agent's raw (untruncated) completion, the tool call parsed out of it (None
# when parsing failed, the signal that the model is producing malformed
# output), how many tokens it generated, and what the environment returned.
# An abandoned episode ends with one more dict,
# which carries `stop_reason` instead of a completion.
PENDING_TRAJECTORIES: list[tuple] = []

# (phase, start, end) wall-clock times of every finished episode, appended
# by run_episode next to PENDING_TRAJECTORIES. MetricsLogger drains it with
# every training record to log train/rollout_time_s and
# train/episode_time_mean_s.
EPISODE_TIMES: list[tuple[str, float, float]] = []

# The (phase, step_tag) of the episodes run in the current context. Rollouts
# run during held-out evaluation are tagged "eval" so they can be told apart
# from training rollouts in the transcript directories; an evaluation the
# async trainer schedules as a task also tags its scheduling step, so its
# transcripts land in that step's directory however late they finish. A
# ContextVar rather than a module global: asyncio tasks copy the context when
# created, so an evaluation task's tag never leaks into the rollout workers
# that run concurrently with it.
_PHASE: contextvars.ContextVar[tuple[str, int | None]] = contextvars.ContextVar(
    "rollout_phase", default=("train", None)
)


def current_phase() -> tuple[str, int | None]:
    """The (phase, step_tag) episodes started now would be tagged with."""
    return _PHASE.get()


@contextlib.contextmanager
def rollout_phase(phase: str, step: int | None = None):
    """Tag every episode run inside this block with `phase` (e.g. "eval") and,
    when given, the absolute log step its transcripts belong to. See
    evaluate.py and AsyncGRPOTrainer.run_evaluation."""
    token = _PHASE.set((phase, step))
    try:
        yield
    finally:
        _PHASE.reset(token)


def drain_episode_times(phase: str = "train") -> list[tuple[float, float]]:
    """Empty EPISODE_TIMES and return the (start, end) pairs of `phase`.
    Entries of other phases are dropped: only training episodes are timed."""
    drained, EPISODE_TIMES[:] = list(EPISODE_TIMES), []
    return [(start, end) for p, start, end in drained if p == phase]


def count_abandoned(phase: str = "train") -> tuple[int, int]:
    """(abandoned, total) over the buffered episodes of `phase`. 
    `MetricsLogger` logs the first with every training record."""
    abandoned = total = 0
    for entry in PENDING_TRAJECTORIES:
        if entry[0] != phase:
            continue
        total += 1
        turns = entry[-1]
        if turns and "stop_reason" in turns[-1]:
            abandoned += 1
    return abandoned, total


def _turn_record(action, agent) -> dict:
    """What the agent produced this turn. Best-effort: never raises."""
    record: dict = {"agent": "", "tool_call": None, "completion_tokens": None}
    try:
        record["agent"] = getattr(action, "text", "")
        call = getattr(action, "tool_call", None)
        if call is not None:
            # None here means the completion had no parseable tool call.
            record["tool_call"] = {
                "name": call.name,
                "args": list(call.args),
                "raw": call.raw,
            }
        calls = getattr(agent, "llm_calls", None)
        if calls:
            record["completion_tokens"] = len(calls[-1].completion_tokens)
    except Exception:
        pass
    return record


async def run_episode(agent: Agent, env: Env) -> Trajectory:
    started = time.time()
    obs = await env.reset()
    await agent.reset(env.task, env.tool_docs)

    turns: list[dict] = []
    num_steps = 0
    stop_reason: str | None = None
    # The env terminates the episode at task.max_steps; no extra slack (issue #5).
    for _ in range(env.task.max_steps):
        calls_before = len(agent.llm_calls)
        try:
            action = await agent.step(obs)
        except Exception as e:
            if num_steps == 0:
                raise  # no completed turn yet: a setup problem, not a lost episode
            # Abandon the episode, without another environment step. A call
            # the agent recorded before failing is dropped, so that `calls`
            # holds completed turns only and still stitches.
            del agent.llm_calls[calls_before:]
            stop_reason = f"{type(e).__name__}: {e}"
            turns.append(
                {"agent": "", "tool_call": None, "completion_tokens": None, "env": None,
                 "reward": 0.0, "done": True, "stop_reason": stop_reason}
            )
            print(
                f"[rollout] WARNING: task {env.task.id}: episode abandoned after {num_steps} "
                f"turns and counted as a failure ({stop_reason[:300]})"
            )
            break
        record = _turn_record(action, agent)
        obs = await env.step(action.tool_call)
        record.update(env=obs.text, reward=obs.reward, done=obs.done)
        turns.append(record)
        num_steps += 1
        if obs.done:
            break

    await agent.close()
    await env.close()

    reward = 0.0 if stop_reason is not None else obs.reward

    # Never let bookkeeping break a rollout.
    try:
        phase, step_tag = _PHASE.get()
        policy_version = getattr(getattr(agent, "policy", None), "version", None)
        PENDING_TRAJECTORIES.append(
            (phase, step_tag, policy_version, env.task, env.tool_docs, reward, num_steps, turns)
        )
        EPISODE_TIMES.append((phase, started, time.time()))
    except Exception:
        pass

    return Trajectory(
        task=env.task,
        calls=list(agent.llm_calls),
        reward=reward,
        num_steps=num_steps,
        info={"stop_reason": stop_reason} if stop_reason is not None else {},
    )

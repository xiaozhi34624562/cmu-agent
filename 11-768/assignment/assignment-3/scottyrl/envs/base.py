"""Base environment interface (given).

The Env API is fully async so that richer environments (remote services,
concurrent sub-environments, forked subagent state, ...) can be added later
without changing any call sites. The env owns the step budget: it marks the
observation `done` when the budget runs out.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from scottyrl.types import Observation, Task, ToolCall

INVALID_ACTION_MSG = (
    "Could not parse a tool call. Respond with exactly one <tool>name(args)</tool>."
)


class Env(ABC):
    def __init__(self, task: Task):
        self.task = task
        self._steps_used = 0
        self._done = False

    @property
    @abstractmethod
    def tool_docs(self) -> str:
        """Human-readable tool documentation injected into the system prompt."""

    @abstractmethod
    async def initial_observation(self) -> str:
        """Text shown to the agent before its first turn."""

    @abstractmethod
    async def apply(self, call: ToolCall) -> Observation:
        """Apply a parsed tool call. Budget accounting is handled by `step`."""

    async def _reset_state(self) -> None:
        """Hook for subclasses with mutable state."""

    async def reset(self) -> Observation:
        self._steps_used = 0
        self._done = False
        await self._reset_state()
        return Observation(text=await self.initial_observation())

    async def step(self, call: ToolCall | None) -> Observation:
        if self._done:
            raise RuntimeError("step() called on a finished episode")

        self._steps_used += 1
        if call is None:
            obs = Observation(text=INVALID_ACTION_MSG)
        else:
            obs = await self.apply(call)

        if not obs.done and self._steps_used >= self.task.max_steps:
            obs = Observation(text=obs.text + "\n(Out of steps.)", reward=obs.reward, done=True)

        self._done = obs.done
        return obs

    async def close(self) -> None:
        """Release resources (no-op for the built-in envs)."""

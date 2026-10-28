"""Number Search: guess a hidden integer with too-low / too-high feedback (given).

Cheap and fast: the debugging environment for this assignment. An optimal
agent does binary search; the step budget is ceil(log2(high - low + 2)),
the exact worst-case bound including the final correct guess, with no slack.

Task.info: {"low": int, "high": int, "target": int}
(Dataset: the Number Search train/val splits, adapted for a multi-turn
harness with a per-episode guess budget.)
"""

from __future__ import annotations

from scottyrl.envs.base import Env
from scottyrl.types import Observation, ToolCall

TOOL_DOCS = """\
guess(n: int): guess the hidden number. You are told whether your guess is
  too low, too high, or correct. Example: <tool>guess(512)</tool>"""


class NumberSearchEnv(Env):
    @property
    def tool_docs(self) -> str:
        return TOOL_DOCS

    async def initial_observation(self) -> str:
        low, high = self.task.info["low"], self.task.info["high"]
        return (
            f"I'm thinking of a number between {low} and {high} (inclusive). "
            f"You have {self.task.max_steps} guesses."
        )

    async def apply(self, call: ToolCall) -> Observation:
        if call.name != "guess" or len(call.args) != 1 or not isinstance(call.args[0], int):
            return Observation(text="Invalid call. Use guess(n) with a single integer.")

        n = call.args[0]
        target = self.task.info["target"]
        if n == target:
            return Observation(text=f"Correct! The number was {target}.", reward=1.0, done=True)
        if n < target:
            return Observation(text=f"{n} is too low.")
        return Observation(text=f"{n} is too high.")

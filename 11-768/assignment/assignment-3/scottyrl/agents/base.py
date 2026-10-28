"""Base agent interface (given).

An Agent owns its own context/state and a Policy; the rollout loop just
shuttles observations and actions between the agent and the env:

    obs = await env.reset()
    await agent.reset(env.task, env.tool_docs)
    while not done:
        action = await agent.step(obs)
        obs = await env.step(action.tool_call)

New agent designs (different prompting schemes, multi-policy agents,
subagent spawning, ...) subclass Agent and register themselves in
`scottyrl/agents/__init__.py`. Whatever the internals, an agent must record
every policy call it makes in `self.llm_calls`; that is the training data.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from scottyrl.policy import Policy
from scottyrl.types import LLMCall, Observation, Task, ToolCall


@dataclass
class AgentAction:
    """The agent's move for one turn: the parsed tool call (None if the
    completion contained no parseable call) plus the raw completion text."""

    tool_call: ToolCall | None
    text: str


class Agent(ABC):
    def __init__(self, policy: Policy):
        self.policy = policy
        self.llm_calls: list[LLMCall] = []

    @abstractmethod
    async def reset(self, task: Task, tool_docs: str) -> None:
        """Start a new episode. Must clear `llm_calls` and any context."""

    @abstractmethod
    async def step(self, obs: Observation) -> AgentAction:
        """Consume the latest observation, query the policy, return an action.
        Must append the policy call (in token space) to `self.llm_calls`."""

    async def close(self) -> None:
        """Release resources (no-op by default)."""

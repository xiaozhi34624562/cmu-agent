"""Agent registry (given). Add new agent classes here."""

from __future__ import annotations

from scottyrl.agents.base import Agent, AgentAction
from scottyrl.agents.xml_tool_call import XMLToolCallAgent
from scottyrl.policy import Policy

AGENT_REGISTRY: dict[str, type[Agent]] = {
    "xml_toolcall": XMLToolCallAgent,
}


def make_agent(name: str, policy: Policy) -> Agent:
    if name not in AGENT_REGISTRY:
        raise ValueError(f"Unknown agent '{name}'. Options: {sorted(AGENT_REGISTRY)}")
    return AGENT_REGISTRY[name](policy)


__all__ = ["Agent", "AgentAction", "XMLToolCallAgent", "AGENT_REGISTRY", "make_agent"]

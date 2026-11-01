"""Core data structures shared across scottyrl (given).

Everything here is plain Python (no torch, no tinker) so that the data
pipeline can be unit-tested offline. The only place that touches the Tinker
SDK is `scottyrl/tinker_adapter.py`.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Task:
    """A single environment instance specification.

    `info` holds env-specific data (e.g. the hidden target number, or the
    recipe book for a crafting task). Tasks are serialized as JSON lines in
    `data/*.jsonl`.
    """

    goal: str
    id: str
    max_steps: int
    info: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        return cls(goal=d["goal"], id=d["id"], max_steps=d["max_steps"], info=d.get("info", {}))


def load_tasks(path: str | Path) -> list[Task]:
    """Load a jsonl file of tasks."""
    tasks = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(Task.from_dict(json.loads(line)))
    return tasks


def save_tasks(tasks: list[Task], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for task in tasks:
            f.write(json.dumps(task.to_dict()) + "\n")


@dataclass
class Observation:
    """What the environment sends back to the agent after a step (or reset)."""

    text: str
    reward: float = 0.0
    done: bool = False


@dataclass
class ToolCall:
    """A parsed tool call, e.g. `<tool>guess(512)</tool>` ->
    ToolCall(name="guess", args=(512,))."""

    name: str
    args: tuple[Any, ...] = ()
    raw: str = ""


@dataclass
class LLMCall:
    """One policy call inside an episode, recorded in *token space*.

    The agent renders the conversation through the model's chat template but
    keeps the prompt it actually sends as a growing token list: after each
    turn it appends the completion tokens the model produced and then only
    the tokens of the newly rendered tail (turn markers, the environment
    observation, the next generation prompt). So for consecutive calls i and
    i+1 within an episode:

        calls[i+1].prompt_tokens == calls[i].prompt_tokens
                                    + calls[i].completion_tokens
                                    + <tokens of the rendered tail>

    This "sequence extension" property is what makes it possible to stitch an
    entire multi-turn episode into a single training sequence. It is not
    unconditional: with `model.preserve_thinking_history: false` the template
    drops earlier `<think>` blocks, the re-rendered prompt no longer starts
    with the old one, and the agent re-encodes it from scratch. It also
    breaks when the model stops on a token the template does not write back
    e.g., `<|endoftext|>` instead of `<|im_end|>`: the re-rendered turn ends with
    `<|im_end|>`, so the prompt no longer starts with the old prompt plus the
    completion. Every such call starts a new training sequence (see
    `datagen.stitch_trajectory`).
    """

    prompt_tokens: list[int]
    completion_tokens: list[int]
    completion_logprobs: list[float]


@dataclass
class Trajectory:
    """A completed episode."""

    task: Task
    calls: list[LLMCall]
    reward: float
    num_steps: int
    info: dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenSequence:
    """A stitched training sequence, the unit of training data.

    `tokens` is the full sequence [t_0, ..., t_{n-1}] (initial prompt with
    completions and env observations interleaved). Training predicts the
    *next* token, so the targets are tokens[1:], and the three parallel lists
    below all have length n - 1, aligned with the targets:

        mask[j]       = 1 iff tokens[j+1] was sampled from the policy
        logprobs[j]   = sampling logprob of tokens[j+1]  (0.0 where mask == 0)
        advantages[j] = advantage credited to tokens[j+1] (0.0 where mask == 0)

    Loss is only applied where mask == 1: we don't train the model to imitate
    environment observations, only reinforce (or suppress) its own actions.
    """

    tokens: list[int]
    mask: list[int]
    logprobs: list[float]
    advantages: list[float]

    def __post_init__(self) -> None:
        n = len(self.tokens)
        if n < 2:
            raise ValueError("TokenSequence needs at least 2 tokens")
        for name in ("mask", "logprobs", "advantages"):
            if len(getattr(self, name)) != n - 1:
                raise ValueError(f"{name} must have length len(tokens) - 1 = {n - 1}")

    @property
    def num_action_tokens(self) -> int:
        return sum(self.mask)

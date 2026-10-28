"""Environment registry (given)."""

from __future__ import annotations

from typing import Callable

from scottyrl.envs.base import Env
from scottyrl.envs.number_search import NumberSearchEnv
from scottyrl.envs.textcraft import TextCraftEnv
from scottyrl.types import Task

ENV_REGISTRY: dict[str, type[Env]] = {
    "number_search": NumberSearchEnv,
    "textcraft": TextCraftEnv,
}


def make_env_factory(name: str) -> Callable[[Task], Env]:
    """Return a callable that builds a fresh env instance for a task."""
    if name not in ENV_REGISTRY:
        raise ValueError(f"Unknown env '{name}'. Options: {sorted(ENV_REGISTRY)}")
    cls = ENV_REGISTRY[name]
    return lambda task: cls(task)

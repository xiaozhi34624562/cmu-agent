"""Held-out evaluation: success rate and pass@k (given)."""

from __future__ import annotations

import asyncio
from typing import Callable

from scottyrl.agents.base import Agent
from scottyrl.agents.xml_tool_call import XMLToolCallAgent
from scottyrl.envs.base import Env
from scottyrl.metrics import pass_at_k
from scottyrl.policy import Policy
from scottyrl.rollout import current_phase, rollout_phase, run_episode
from scottyrl.types import Task


async def evaluate_policy(
    policy: Policy,
    tasks: list[Task],
    env_factory: Callable[[Task], Env],
    k: int = 1,
    concurrency: int = 64,
    success_threshold: float = 1.0,
    agent_cls: type[Agent] = XMLToolCallAgent,
) -> dict:
    """Run k rollouts per task and report success_rate (mean over all
    episodes) and pass@k (fraction of tasks with >= 1 success).

    At most `concurrency` episodes run at a time. The default keeps a vLLM
    engine well fed without crowding out training rollouts that share it."""
    sem = asyncio.Semaphore(concurrency)

    async def one(task: Task) -> tuple[str, float, int, bool]:
        async with sem:
            traj = await run_episode(agent_cls(policy), env_factory(task))
            return task.id, traj.reward, traj.num_steps, "stop_reason" in traj.info

    # Tag these rollouts so trajectory logs can distinguish eval from
    # training. A step tag already set by the caller (the async trainer's
    # run_evaluation) is kept, so the transcripts land in that step's
    # directory.
    with rollout_phase("eval", step=current_phase()[1]):
        results = await asyncio.gather(*[one(task) for task in tasks for _ in range(k)])

    rewards_by_task: dict[str, list[float]] = {}
    total_steps = abandoned = 0
    for task_id, reward, steps, was_abandoned in results:
        rewards_by_task.setdefault(task_id, []).append(reward)
        total_steps += steps
        abandoned += was_abandoned

    return {
        # Shared with the trainers' train-time records, so train/ and eval/
        # curves are computed by the same code. Raw rewards go in; the
        # success threshold is applied once, inside pass_at_k.
        **pass_at_k(
            list(rewards_by_task.values()), k=k, success_threshold=success_threshold
        ),
        "avg_steps": total_steps / len(results),
        # Episodes that lost a sampling call and count as failures above
        # (rollout.run_episode). Anything but 0 means the numbers are too low.
        "abandoned_episodes": abandoned,
        "num_tasks": len(tasks),
        "episodes_per_task": k,
    }

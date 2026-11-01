"""Interface/shape checks (given) for the functions YOU implement.

These tests only verify signatures, return types, and basic shapes; they
tell you your code is *pluggable*, not that it is *correct*. Correctness is
graded by a hidden test suite (and by whether your training runs actually
learn). They will fail with NotImplementedError until you implement the
corresponding file.
"""

import asyncio
import inspect

from scottyrl.advantages import compute_group_advantages
from scottyrl.datagen import (
    extension_suffix,
    stitch_trajectory,
    trajectory_to_training_sequences,
)
from scottyrl.envs.number_search import NumberSearchEnv
from scottyrl.policy import MockPolicy
from scottyrl.tinker_adapter import TinkerSession
from scottyrl.train.async_grpo import AsyncGRPOTrainer
from scottyrl.train.common import collect_group, groups_to_batch
from scottyrl.train.sync import SyncTrainer
from scottyrl.types import LLMCall, Task, TokenSequence, Trajectory

REQUIRED_BATCH_STATS = {
    "num_groups",
    "num_degenerate_groups",
    "frac_degenerate_groups",
    "mean_reward",
    "num_sequences",
    "num_action_tokens",
}


def make_traj(reward=1.0):
    task = Task(goal="g", id="t", max_steps=4)
    return Trajectory(
        task=task,
        calls=[LLMCall([1, 2], [3, 4], [-0.1, -0.2])],
        reward=reward,
        num_steps=1,
    )


def test_advantages_shape():
    out = compute_group_advantages([1.0, 0.0], method="grpo")
    assert out is None or (isinstance(out, list) and len(out) == 2)
    out = compute_group_advantages([1.0], method="reinforce")
    assert isinstance(out, list) and len(out) == 1


def test_datagen_shapes():
    out = extension_suffix([1, 2], [1, 2, 3])
    assert out is None or isinstance(out, list)
    seqs = stitch_trajectory(make_traj())
    assert isinstance(seqs, list) and all(isinstance(s, TokenSequence) for s in seqs)
    # TokenSequence.__post_init__ enforces internal length consistency.
    seqs = trajectory_to_training_sequences(make_traj(), advantage=0.5)
    assert isinstance(seqs, list) and all(isinstance(s, TokenSequence) for s in seqs)


def test_collect_group_shape():
    task = Task(
        goal="find", id="ns.0", max_steps=4, info={"low": 0, "high": 10, "target": 7}
    )
    policy = MockPolicy(["<tool>guess(7)</tool>"])
    trajs = asyncio.run(
        collect_group(policy, task, lambda t: NumberSearchEnv(t), group_size=3)
    )
    assert isinstance(trajs, list) and len(trajs) == 3
    assert all(isinstance(t, Trajectory) for t in trajs)


def test_groups_to_batch_shape():
    seqs, stats = groups_to_batch([[make_traj(1.0), make_traj(0.0)]], method="grpo")
    assert isinstance(seqs, list) and isinstance(stats, dict)
    assert REQUIRED_BATCH_STATS <= set(stats)


def test_student_signatures_unchanged():
    """Graders call these exact signatures."""
    assert list(inspect.signature(compute_group_advantages).parameters) == [
        "rewards",
        "method",
    ]
    assert list(inspect.signature(extension_suffix).parameters) == [
        "accumulated",
        "prompt_tokens",
    ]
    assert list(inspect.signature(groups_to_batch).parameters) == ["groups", "method"]
    assert list(inspect.signature(collect_group).parameters) == [
        "policy",
        "task",
        "env_factory",
        "group_size",
        "agent_cls",
    ]
    assert list(inspect.signature(TinkerSession.submit_update).parameters) == [
        "self",
        "datums",
        "loss_fn",
        "lr",
        "grad_clip_norm",
    ]
    assert list(inspect.signature(SyncTrainer.collect_batch).parameters) == ["self", "policy"]
    assert list(inspect.signature(SyncTrainer.build_batch).parameters) == ["self", "groups"]
    assert list(inspect.signature(SyncTrainer.update).parameters) == ["self", "seqs"]
    assert list(inspect.signature(SyncTrainer.evaluate_now).parameters) == ["self", "policy"]
    assert list(inspect.signature(SyncTrainer.train).parameters) == ["self"]


def test_async_trainer_signatures():
    """The async workflow exposes small member exercises with stable inputs."""
    assert list(inspect.signature(AsyncGRPOTrainer).parameters) == [
        "session",
        "env_factory",
        "train_tasks",
        "val_tasks",
        "model_cfg",
        "train_cfg",
        "logger",
    ]
    assert list(inspect.signature(AsyncGRPOTrainer.generate_group).parameters) == [
        "self",
        "task_id",
        "policy",
        "version",
    ]
    assert list(inspect.signature(AsyncGRPOTrainer.rollout_worker).parameters) == [
        "self",
        "results",
        "task_iter",
    ]
    assert list(inspect.signature(AsyncGRPOTrainer.collect_fresh_batch).parameters) == [
        "self",
        "results",
        "stats",
    ]
    assert list(inspect.signature(AsyncGRPOTrainer.update).parameters) == [
        "self",
        "batch",
    ]
    assert list(inspect.signature(AsyncGRPOTrainer.evaluate_now).parameters) == [
        "self",
        "policy",
    ]
    assert list(inspect.signature(AsyncGRPOTrainer.train).parameters) == ["self"]

"""Asynchronous / off-policy GRPO. *** STUDENT IMPLEMENTATION FILE ***

Part 3 of the assignment turns the synchronous trainer into a small
producer-consumer system:

  rollout workers  ->  bounded queue  ->  learner
          (rollouts and updates overlap in time)

Rollouts therefore may come from an older policy snapshot.  Each result
records the version that generated it so the learner can reject data that is
too stale; importance weighting handles the accepted off-policy data.

``AsyncGRPOTrainer`` owns both the Tinker dependencies and the orchestration.
That makes its relationship to ``SyncTrainer`` visible without using callback
closures or a second object for mutable policy state.  Methods marked
"given helpers" own infrastructure such as policy publication and logging.
Methods marked "student helpers" are the producer, consumer, update, and
evaluation exercises.

Queue reference: https://docs.python.org/3/library/asyncio-queue.html
An ``asyncio.Queue`` with ``maxsize > 0`` is bounded.  ``await put(...)``
pauses a fast producer while it is full (backpressure), and ``await get()``
pauses a consumer while it is empty.
"""

from __future__ import annotations

import asyncio  # noqa: F401  (student dependency)
import itertools  # noqa: F401  (student dependency)
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field

from scottyrl.agents.base import Agent
from scottyrl.config import ModelConfig, TrainConfig
from scottyrl.envs.base import Env
from scottyrl.evaluate import evaluate_policy  # noqa: F401  (student dependency)
from scottyrl.metrics import (
    MetricsLogger,
    pass_at_k,
    sanity_warnings,
    sequence_batch_stats,
)
from scottyrl.policy import TinkerPolicy, load_chat_template
from scottyrl.rollout import rollout_phase
from scottyrl.tinker_adapter import TinkerSession
from scottyrl.train.common import (  # noqa: F401  (student dependencies)
    collect_group,
    groups_to_batch,
)
from scottyrl.types import Task, TokenSequence


@dataclass
class GroupResult:
    """One rollout group and the policy version that sampled it.

    `rewards` holds one episode reward per rollout, in rollout order, for
    every group. `sequences` holds the training sequences; it is empty for a
    degenerate group (all rewards equal, so GRPO has no learning signal),
    which still counts as a collected group.
    """

    task_id: str
    policy_version: int
    sequences: list[TokenSequence]
    rewards: list[float] = field(default_factory=list)


class AsyncGRPOTrainer:
    """Producer-consumer GRPO trainer with one authoritative policy state."""

    def __init__(
        self,
        session: TinkerSession,
        env_factory: Callable[[Task], Env],
        train_tasks: list[Task],
        val_tasks: list[Task],
        model_cfg: ModelConfig,
        train_cfg: TrainConfig,
        logger: MetricsLogger,
    ):
        self.session = session
        self.env_factory = env_factory
        self.train_tasks = train_tasks
        self.val_tasks = val_tasks
        self.model_cfg = model_cfg
        self.cfg = train_cfg
        self.logger = logger

        if train_cfg.queue_capacity <= 0:
            raise ValueError("queue_capacity must be > 0")
        if train_cfg.num_workers <= 0:
            raise ValueError("num_workers must be > 0")
        if train_cfg.groups_per_batch <= 0:
            raise ValueError("groups_per_batch must be > 0")
        if not train_tasks:
            raise ValueError("train_tasks must not be empty")

        self.tasks_by_id = {task.id: task for task in train_tasks}
        self.policy: TinkerPolicy | None = None
        self.version = 0

    # ------------------------------------------------------ given helpers --

    def make_policy(self, sampling_client) -> TinkerPolicy:
        """Wrap a sampling client in a TinkerPolicy (given)."""
        return TinkerPolicy(
            sampling_client,
            self.session.tokenizer,
            max_tokens=self.model_cfg.max_tokens,
            temperature=self.model_cfg.temperature,
            chat_template=load_chat_template(self.model_cfg.chat_template),
            enable_thinking=self.model_cfg.enable_thinking,
            preserve_thinking_history=self.model_cfg.preserve_thinking_history,
            stop_sequences=self.model_cfg.stop_sequences,
        )

    def agent_cls(self) -> type[Agent]:
        """Return the agent class named by cfg.agent (given)."""
        from scottyrl.agents import AGENT_REGISTRY

        return AGENT_REGISTRY[self.cfg.agent]

    def active_policy(self) -> tuple[TinkerPolicy, int]:
        """Capture the current policy and its version as one pair (given)."""
        if self.policy is None:
            raise RuntimeError("publish_policy must run before collecting rollouts")
        return self.policy, self.version

    def absolute_version(self, version: int) -> int:
        """`version` plus the updates an earlier process of this run made (given).

        `self.version` counts this process's updates from 0. In a resumed
        run the session's `version_offset` is the number of updates before
        the restart; adding it gives the absolute version, which is what
        the log and the transcripts report. A fresh run's offset is 0.
        """
        return version + getattr(self.session, "version_offset", 0)

    def eval_due(self, step: int) -> bool:
        """Whether `step` is a periodic evaluation boundary (given).

        `step` is this process's iteration index (1, 2, ...). The logger's
        `step_offset` (the iterations an earlier process of this run
        completed; 0 in a fresh run) is added first, so evaluations stay
        at absolute multiples of cfg.eval_every: a run resumed at
        iteration 45 with eval_every=10 evaluates next at 50, not at 55.
        Returns False when cfg.eval_every is 0 (periodic evaluation
        disabled). In a fresh run this is `step % cfg.eval_every == 0`.
        """
        if not self.cfg.eval_every:
            return False
        return (step + getattr(self.logger, "step_offset", 0)) % self.cfg.eval_every == 0

    async def publish_policy(self, version: int) -> TinkerPolicy:
        """Snapshot current weights and publish the policy/version pair (given).

        The visible state changes only after snapshot construction succeeds,
        so rollout workers cannot observe a new version with an old policy.
        The policy is stamped with its absolute version (`policy.version`)
        so every transcript it generates names the version that produced it.
        """
        sampling_client = await self.session.new_sampling_client(f"v{version}")
        policy = self.make_policy(sampling_client)
        try:
            policy.version = self.absolute_version(version)
        except AttributeError:  # a test double that takes no attributes
            pass
        self.policy, self.version = policy, version
        return policy

    def record_training(
        self, step: int, batch: list[GroupResult], train_metrics: dict
    ) -> None:
        """Build and emit the training record for one learner step (given).

        Call this exactly once per learner iteration, after the update and
        the publication of the new policy, or, on a skipped step (no
        sequences in the batch), after deciding not to update. The record
        holds the same fields as the synchronous trainer's, computed from
        the batch's GroupResults:

          num_groups, num_degenerate_groups (groups with no sequences),
          frac_degenerate_groups, mean_reward (over ALL rewards, degenerate
          groups included), num_sequences, num_action_tokens and the other
          metrics.sequence_batch_stats fields, success_rate and pass@k
          (metrics.pass_at_k with k=cfg.group_size), plus
          policy_version (self.version at the time of the call, plus the
          session's version_offset in a resumed run, so the logged version
          is absolute while self.version stays relative to this process),
          loss_fn_is_iw (1 unless cfg.loss_fn is "cross_entropy") and
          "skipped": 1 when the batch had no sequences.

        `train_metrics` (the backend metrics returned by update; {} on a
        skipped step) are merged in, sanity warnings are printed, and every
        key is logged prefixed "train/" at `step`.

        `step` is the training-iteration index (1, 2, ...), not the policy
        version: the two agree until the first skipped step, after which
        the version lags behind. Rollout-derived metrics at step t come
        from rollouts sampled before update t (from older versions in an
        async run); eval/* at step t describes the policy after update t.
        No train record is emitted at step 0; step 0 holds only the
        baseline evaluation recorded by the entry script.
        """
        sequences = [sequence for group in batch for sequence in group.sequences]
        rewards = [reward for group in batch for reward in group.rewards]
        num_degenerate = sum(1 for group in batch if not group.sequences)
        record = {
            "num_groups": len(batch),
            "num_degenerate_groups": num_degenerate,
            "frac_degenerate_groups": num_degenerate / len(batch) if batch else 0.0,
            "mean_reward": sum(rewards) / len(rewards) if rewards else 0.0,
            **train_metrics,
            **sequence_batch_stats(sequences),
            "policy_version": self.absolute_version(self.version),
            "loss_fn_is_iw": int(self.cfg.loss_fn != "cross_entropy"),
        }
        if not sequences:
            record["skipped"] = 1
        try:
            record.update(
                pass_at_k([group.rewards for group in batch], k=self.cfg.group_size)
            )
        except ValueError as e:  # a metrics problem must never kill a run
            print(f"[metrics] step {step}: skipping pass@k: {e}")
        # sanity_warnings expects unprefixed keys, so check before prefixing.
        for warning in sanity_warnings(record):
            print(f"[sanity] step {step}: {warning}")
        self.logger.log(step, {f"train/{key}": value for key, value in record.items()})

    def record_evaluation(
        self, step: int, eval_metrics: dict, policy_version: int | None = None
    ) -> None:
        """Log `eval_metrics` at `step` with every key prefixed "eval/" (given).

        When `policy_version` is given (relative to this process, as
        `run_evaluation` passes it) the session's version_offset is added
        and the sum is logged as eval/policy_version, so a reader can tell
        which snapshot an async evaluation measured.
        """
        record = {f"eval/{key}": value for key, value in eval_metrics.items()}
        if policy_version is not None:
            record["eval/policy_version"] = self.absolute_version(policy_version)
        self.logger.log(step, record)

    async def run_evaluation(
        self, policy: TinkerPolicy, version: int, step: int
    ) -> None:
        """Evaluate a captured (policy, version) pair and record it (given).

        The result is logged at `step`, the learner iteration that produced
        the snapshot, with eval/policy_version=version (made absolute by
        record_evaluation). Schedule this as a task so the learner does not
        wait for it. The rollouts run inside `rollout_phase("eval",
        step=...)` with the absolute step, so their transcripts land in
        that step's directory even though the evaluation finishes during a
        later iteration.
        """
        with rollout_phase("eval", step=step + getattr(self.logger, "step_offset", 0)):
            metrics = await self.evaluate_now(policy)
        self.record_evaluation(step, metrics, policy_version=version)

    # ---------------------------------------------------- student helpers --

    async def generate_group(
        self,
        task_id: str,
        policy: TinkerPolicy,
        version: int,
    ) -> GroupResult:
        """Generate one rollout group for the requested task.

        Look the id up in ``self.tasks_by_id`` first; an unknown id raises
        KeyError (or ValueError) before any rollout starts.  Run the rollouts
        with the module-level ``collect_group`` (imported at the top of this
        file; the graders substitute it) as ``collect_group(policy, task,
        self.env_factory, self.cfg.group_size, agent_cls=self.agent_cls())``,
        compute GRPO advantages within the group (``groups_to_batch([group],
        method="grpo")`` or ``compute_group_advantages``), and return a
        ``GroupResult`` carrying the training sequences, the rewards in
        rollout order, and the supplied policy version.

        Always return a ``GroupResult``.  A degenerate group (no GRPO
        learning signal) has ``sequences == []`` but keeps its ``rewards``:
        the learner counts every collected group, so the degenerate fraction
        and mean reward it logs mean the same thing as in the synchronous
        trainer.

        ``policy`` and ``version`` are deliberately passed together: they
        describe the snapshot captured by a rollout worker.  Do not replace
        them with whatever happens to be current after rollout work awaits.
        """
        # TODO(student): implement this method.
        raise NotImplementedError

    async def rollout_worker(
        self,
        results: asyncio.Queue[GroupResult],
        task_iter: Iterator[str],
    ) -> None:
        """Produce rollout groups until this worker is cancelled.

        Workers share the task iterator.  Each rollout uses one captured
        policy/version pair, and every result enters the bounded queue,
        degenerate groups included.

        Do not catch errors here, let them propagate.
        """
        # TODO(student): implement this method.
        raise NotImplementedError

    async def collect_fresh_batch(
        self,
        results: asyncio.Queue[GroupResult],
        stats: dict,
    ) -> list[GroupResult]:
        """Collect the next learner batch, discarding stale queue entries.

        Freshness is measured when an entry is consumed: a group is stale
        when ``self.version - group.policy_version`` exceeds
        ``cfg.max_staleness``.  ``stats`` is the accounting dict ``train()``
        returns; add the number of discarded groups to
        ``stats["groups_dropped_stale"]`` (create it with ``setdefault`` if
        absent) so it accumulates across steps.  Return exactly
        ``cfg.groups_per_batch`` fresh groups, whether or not they are
        degenerate.  This mirrors the synchronous trainer, which collects
        ``tasks_per_batch`` groups per step and lets degenerate ones
        contribute no sequences.
        """
        # TODO(student): implement this method.
        raise NotImplementedError

    async def update(self, batch: list[GroupResult]) -> dict:
        """Run one optimizer step on the training sequences of every group
        in ``batch`` through the session: ``self.session.train_step``, with
        the loss, learning rate and gradient clipping taken from cfg.

        Keep the sequences in the order they appear in ``batch``: group by
        group, and in order within each group.

        Returns: the metrics dict reported by the training step, unchanged.
        Publishing the new policy (the given ``publish_policy``) and logging
        (the given ``record_training``) belong to ``train()``, not to this
        method.
        """
        # TODO(student): implement this method.
        raise NotImplementedError

    async def evaluate_now(self, policy: TinkerPolicy) -> dict:
        """Evaluate ``policy`` on held-out validation tasks.

        Run ``cfg.eval_k`` rollouts on each of the first ``cfg.eval_tasks``
        validation tasks, using the agent class from cfg.  The
        ``evaluate_policy`` helper imported at the top of this file does
        the work; call that module-level name directly rather than
        re-importing it, since the graders substitute it.

        Returns: the raw metrics dict from the evaluation.  Prefixing keys
        with "eval/" and logging are handled by the given
        ``run_evaluation`` and ``record_evaluation``.  The entry script
        also calls this method for the step-0 baseline.
        """
        # TODO(student): implement this method.
        raise NotImplementedError

    # ------------------------------------------------------------- driver --

    async def train(self) -> dict:
        """Run asynchronous training and return accounting statistics.

        Expected behavior:

        - publish an initial version-zero policy (``publish_policy(0)``);
        - overlap rollout workers with the learner through a
          queue bounded by ``cfg.queue_capacity``; workers share one repeating
          stream of training-task ids so work is distributed across them.
          (Hint: You can implement this shared stream as an iterator over training task ids
          that cycles back to the beginning when the end is reached.)
        - run ``cfg.num_steps`` learner iterations, numbered 1, 2, ...  Each
          collects a fresh batch and, when the batch has at least one
          sequence, updates and publishes ``self.version + 1``.  A batch with
          no sequences (every group degenerate) is a skipped step: no update
          and no publish, so the version does not advance.  Either way the
          iteration is recorded with exactly one call to the given
          ``record_training(step, batch, train_metrics)`` (``{}`` on a
          skipped step).  Records are keyed by the iteration index, so a
          skipped step is visible in the log as a step whose version did
          not move;
        - on every evaluation boundary (when the given ``self.eval_due(step)``
          is true: ``cfg.eval_every`` steps apart, counted on absolute step
          numbers so a resumed run keeps the cadence; 0 disables periodic
          evaluation), whether or not the step updated, capture the pair
          returned by ``active_policy()`` and schedule
          ``run_evaluation(policy, version, step)`` as a task so training
          continues while it runs.  On a skipped step that pair is the same
          policy the step sampled from.  The step-0 baseline evaluation is
          done for you by scripts/train_async.py before train() is called;
        - propagate failures promptly: a rollout worker that fails must not
          leave the learner blocked waiting for a result that can no longer
          arrive, and an evaluation task that fails must fail the run the
          same way, not only once the last iteration is done;
        - once the last iteration is done, cancel and await the rollout
          workers (they are no longer needed; a worker that stops after this
          point is not an error), then await every scheduled evaluation task
          before returning;
        - on ANY exception (a worker, an evaluation or the learner failing),
          cancel and await the outstanding evaluation tasks as well as every
          rollout worker, then re-raise the original exception object itself
          (not a wrapper such as ExceptionGroup, and not a new RuntimeError).

        Return a dict with exactly these three keys: ``train_steps``,
        ``groups_consumed`` and ``groups_dropped_stale`` (the entry script
        prints it; the graders compare it for equality).  ``train_steps``
        counts learner iterations, skipped ones included (``self.version``
        is the number of actual updates).  Consumed means accepted into a
        learner batch, degenerate or not; a stale dequeue counts only as
        dropped.

        See the module-level Queue notes and the official task-cancellation
        guidance: https://docs.python.org/3/library/asyncio-task.html#task-cancellation
        """
        # TODO(student): implement this method.
        raise NotImplementedError

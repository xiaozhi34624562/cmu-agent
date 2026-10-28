"""Logging and automated sanity checks (given).

MetricsLogger writes one JSON line per training step to `runs/*.jsonl`
(these files are part of your submission; graders run automated checks on
them) and, optionally, mirrors everything to Weights & Biases.

To enable wandb: `pip install wandb`, `export WANDB_API_KEY=...` (or
`wandb login`), and set `train.wandb_project` in your config (or pass
`--set train.wandb_project=11768-a3`).

MetricsLogger also writes full agent<->environment transcripts next to the
jsonl log, one directory per training step and one JSONL file per rollout:

    runs/<run_name>_trajectories/step_000007/<phase>_<task_id>_rollout0.jsonl

Each file starts with a `{"type": "task", ...}` header line (goal, task info,
final reward, the policy version that generated the rollout when known)
followed by one `{"type": "step", ...}` line per turn, so a single file is
readable on its own. Controlled by `train.trajectory_log_every` (0 disables
it); every rollout of a logged step is written, none are sampled away. What
a step directory holds depends on the trainer:

  synchronous runs: exactly the rollouts that step consumed, plus that
    step's evaluation rollouts (phase "eval");
  asynchronous runs: the training rollouts that COMPLETED during that
    iteration (rollouts and updates overlap, so a batch mixes policy
    versions; each file's header says which version generated it), plus
    the evaluation rollouts of the evaluation scheduled at that step, even
    though that evaluation finishes later.

These are part of your submission; they are what you (and the graders)
inspect when a run behaves oddly at a particular step.

Resuming: a resumed run continues from its last checkpoint. Records and
transcripts of steps after that checkpoint (logged by the crashed process)
are rewound when the logger opens and are logged again by the resumed
process, so every step appears once in the final log.
"""

from __future__ import annotations

import json
import math
import re
import shutil
import time
from pathlib import Path

from scottyrl.types import TokenSequence


def _read_marker(path: str | Path | None) -> dict:
    """The resume marker's JSON object, or {} if unset, missing or unreadable."""
    if not path:
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


class MetricsLogger:
    """One JSON record per logged step, plus optional wandb and transcripts.

    `step_offset` is added to every step passed to `log` (0 for a fresh
    run). A resumed run (`step_offset > 0`) rewinds the log before
    appending: records with a step above the offset, and trajectory
    directories above it, were written by the crashed process after its
    last usable checkpoint and are dropped, since the resumed process logs
    those steps again.

    `session` (a TinkerSession) is told about every training record through
    `session.iteration_recorded(step)`, which writes the resume marker once
    a checkpoint's iteration is on record. `resume_marker_path` lets a
    resumed run continue its wandb run (rewound to the offset); both wandb
    arguments are ignored when wandb is not enabled.

    Every training record also gets timing metrics for the interval since
    the previous training record (see "Timing Metrics" in ASSIGNMENT.md):

      step_time_s          wall-clock length of the interval. The first
                           interval starts at the last record logged before
                           it (the step-0 baseline) or at construction.
      update_time_s        time the session spent in `train_step`.
      learner_wait_s       step_time_s minus update time and sampler
                           snapshot saves: time the learner spent on
                           anything else (sampling in a synchronous run,
                           waiting for fresh groups in an asynchronous one,
                           and blocking evaluations).
      learner_wait_frac    learner_wait_s / step_time_s.
      rollout_time_s       first start to last end of the training episodes
                           that finished in the interval.
      episode_time_mean_s  mean duration of those episodes.

    The session-based ones need a `session` with `update_seconds` and
    `snapshot_seconds`; the rollout ones are omitted when no training
    episode finished in the interval.
    """

    def __init__(
        self,
        path: str | Path | None = None,
        wandb_project: str | None = None,
        run_name: str | None = None,
        config: dict | None = None,
        trajectory_log_every: int = 0,
        step_offset: int = 0,
        resume_marker_path: str | Path | None = None,
        session=None,
    ):
        # Iterations a previous process finished before this one started. The
        # trainers count from 1, so adding this keeps logged step numbers
        # absolute across restarts (a run resumed at 40 logs 41, 42, ...).
        self.step_offset = step_offset
        self.session = session
        # Start of the current timing interval and the session's busy time
        # at that point (see the class docstring).
        self._interval_start = time.time()
        self._busy_at_start = self._busy_seconds()
        self._seen_training = False
        self.path = Path(path) if path else None
        # Transcripts live beside the jsonl log: runs/foo.jsonl -> runs/foo_trajectories/
        self.trajectory_log_every = trajectory_log_every
        self.trajectory_dir = (
            self.path.parent / f"{self.path.stem}_trajectories"
            if self.path and trajectory_log_every
            else None
        )
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if step_offset > 0:
                self._rewind(step_offset)
            self._f = open(self.path, "a")
        else:
            self._f = None

        self._wandb = None
        if wandb_project:
            try:
                import wandb

                # A resumed run reattaches to the wandb run it started with,
                # so one curve continues instead of a second run starting at
                # step 1. The run id lives in the resume marker (see
                # config.resume_marker_path); the first process writes it.
                marker = _read_marker(resume_marker_path)
                run_id = marker.get("wandb_run_id")
                if run_id:
                    self._wandb = self._wandb_resume(
                        wandb, wandb_project, run_name, config or {}, run_id, step_offset
                    )
                else:
                    self._wandb = wandb.init(
                        project=wandb_project, name=run_name, config=config or {}
                    )
                    if resume_marker_path:
                        Path(resume_marker_path).parent.mkdir(parents=True, exist_ok=True)
                        with open(resume_marker_path, "w") as f:
                            json.dump({**marker, "wandb_run_id": self._wandb.id}, f)
            except Exception as e:  # missing package, no API key, offline, ...
                print(f"[metrics] wandb disabled ({e!r}); logging to jsonl only")

    @staticmethod
    def _wandb_resume(wandb, project, run_name, config, run_id, step_offset):
        """Reattach to `run_id`, rewound to `step_offset` when wandb allows it.

        `resume_from="<id>?_step=<n>"` (wandb's rewind) discards the run's
        history after step n, matching the jsonl rewind. Older wandb
        versions, or a server that rejects it, fall back to
        `resume="allow"`, which keeps the history and refuses steps that go
        backwards until the resumed run passes the crashed one.
        """
        if step_offset > 0:
            try:
                return wandb.init(
                    project=project, name=run_name, config=config,
                    resume_from=f"{run_id}?_step={step_offset}",
                )
            except Exception as e:
                print(f"[metrics] wandb rewind to step {step_offset} refused ({e!r}); "
                      "reattaching without rewind")
                # The failed init can leave wandb's service half set up, and
                # the next init then fails intermittently; tear it down so
                # the fallback starts clean.
                try:
                    wandb.teardown()
                except Exception:
                    pass
        return wandb.init(
            project=project, name=run_name, config=config, id=run_id, resume="allow"
        )

    def _rewind(self, step_offset: int) -> None:
        """Drop records and trajectory directories with step > step_offset.

        Best effort: a rewind that fails is printed, and the log is then
        appended to as it is.
        """
        try:
            dropped = 0
            if self.path.exists():
                kept = []
                for line in self.path.read_text().splitlines():
                    try:
                        step = json.loads(line).get("step")
                    except (ValueError, AttributeError):
                        step = None
                    if step is None or step <= step_offset:
                        kept.append(line)
                    else:
                        dropped += 1
                self.path.write_text("".join(f"{line}\n" for line in kept))
            trajectory_dir = self.path.parent / f"{self.path.stem}_trajectories"
            if trajectory_dir.is_dir():
                for step_dir in trajectory_dir.iterdir():
                    match = re.fullmatch(r"step_(\d+)", step_dir.name)
                    if match and step_dir.is_dir() and int(match.group(1)) > step_offset:
                        shutil.rmtree(step_dir)
                        dropped += 1
            if dropped:
                print(f"[resume] rewound {self.path} to step {step_offset}: "
                      f"{dropped} record(s)/transcript directories after it dropped")
        except Exception as e:
            print(f"[resume] could not rewind {self.path} (non-fatal): {e!r}")

    def _busy_seconds(self) -> tuple[float, float] | None:
        """(update, snapshot) seconds the session has spent so far, or None."""
        update = getattr(self.session, "update_seconds", None)
        snapshot = getattr(self.session, "snapshot_seconds", None)
        if not isinstance(update, (int, float)) or not isinstance(snapshot, (int, float)):
            return None
        return float(update), float(snapshot)

    def _timing_metrics(self, now: float) -> dict:
        """Timing metrics of the interval ending now; starts the next one."""
        from scottyrl.rollout import drain_episode_times

        metrics: dict = {}
        step_time = now - self._interval_start
        metrics["train/step_time_s"] = step_time
        busy = self._busy_seconds()
        if busy is not None and self._busy_at_start is not None:
            update = busy[0] - self._busy_at_start[0]
            snapshot = busy[1] - self._busy_at_start[1]
            wait = max(0.0, step_time - update - snapshot)
            metrics["train/update_time_s"] = update
            metrics["train/learner_wait_s"] = wait
            metrics["train/learner_wait_frac"] = wait / step_time if step_time > 0 else 0.0
        episodes = drain_episode_times("train")
        if episodes:
            metrics["train/rollout_time_s"] = (
                max(end for _, end in episodes) - min(start for start, _ in episodes)
            )
            metrics["train/episode_time_mean_s"] = (
                sum(end - start for start, end in episodes) / len(episodes)
            )
        self._interval_start = now
        self._busy_at_start = busy
        return metrics

    def log(self, step: int, metrics: dict) -> None:
        step += self.step_offset
        now = time.time()
        training_record = any(key.startswith("train/") for key in metrics)
        if not training_record and not self._seen_training:
            # Records before the first training one (the step-0 baseline)
            # move the start of the first timing interval past them.
            self._interval_start = now
            self._busy_at_start = self._busy_seconds()
        if training_record:
            self._seen_training = True
            # Training episodes that lost a sampling call and were counted as
            # failures since the last training record (rollout.run_episode).
            # Normally 0. Look into it if it is above 0 at most steps.
            from scottyrl.rollout import count_abandoned

            abandoned, total = count_abandoned("train")
            metrics = {
                **metrics,
                "train/abandoned_episodes": abandoned,
                **self._timing_metrics(now),
            }
            if 2 * abandoned > total:
                print(
                    f"[sanity] step {step}: {abandoned} of {total} training episodes were "
                    "abandoned (see the [rollout] WARNING lines): check the server and its "
                    "context window before spending more compute"
                )
        # "time" (epoch seconds) makes wall-clock-per-step analysis possible
        # from the logs alone; Part 3/4 of the assignment needs it.
        record = {"step": step, "time": now, **metrics}
        if self._f:
            self._f.write(json.dumps(record) + "\n")
            self._f.flush()
        if self._wandb is not None:
            self._wandb.log(metrics, step=step)
        self._write_trajectories(step, training_record)
        # The session may only point the resume marker at a checkpoint once
        # the iteration that took it is on record (see
        # TinkerSession.iteration_recorded).
        if self.session is not None and training_record:
            self.session.iteration_recorded(step)
        parts = [f"step {step}"]
        for key in sorted(metrics):
            value = metrics[key]
            parts.append(f"{key} {value:.4g}" if isinstance(value, float) else f"{key} {value}")
        print(" | ".join(parts))

    def _write_trajectories(self, step: int, training_record: bool) -> None:
        """Drain buffered episodes to `<trajectory_dir>/step_<n>/`.

        An episode tagged with a step (rollout.rollout_phase(step=...), used
        for asynchronous evaluations) goes to that step's directory; any
        other goes to `step`'s, the record being logged. The
        `trajectory_log_every` filter applies to the target step.

        A training record drains the whole buffer. An evaluation record
        (`training_record` False) drains only evaluation rollouts and leaves
        training rollouts buffered for the next training record: in an
        asynchronous run an evaluation finishes in the middle of a later
        iteration, and its record must not file that iteration's training
        rollouts under an earlier step. Training rollouts are therefore
        filed under the iteration during which they completed, exactly.
        Whatever is drained is written or discarded (steps that are not
        captured), never kept, so transcripts cannot accumulate in memory
        across a long run.
        """
        from scottyrl.rollout import PENDING_TRAJECTORIES

        if not PENDING_TRAJECTORIES:
            return
        if training_record:
            pending, PENDING_TRAJECTORIES[:] = list(PENDING_TRAJECTORIES), []
        else:
            pending = [e for e in PENDING_TRAJECTORIES if e[0] == "eval"]
            PENDING_TRAJECTORIES[:] = [e for e in PENDING_TRAJECTORIES if e[0] != "eval"]

        if not self.trajectory_dir:
            return

        try:
            # Rollouts of the same task are numbered in completion order;
            # a step directory written in several drains (an evaluation
            # whose rollouts finished across two records) continues the
            # numbering from the files already there.
            rollout_counts: dict[tuple, int] = {}
            for phase, step_tag, policy_version, task, tool_docs, reward, num_steps, turns in pending:
                target = step if step_tag is None else step_tag
                if target % self.trajectory_log_every != 0:
                    continue
                step_dir = self.trajectory_dir / f"step_{target:06d}"
                step_dir.mkdir(parents=True, exist_ok=True)
                # Task ids can contain path separators / other unsafe characters.
                safe_id = re.sub(r"[^A-Za-z0-9._-]", "_", str(task.id))
                key = (target, phase, safe_id)
                index = rollout_counts.get(key, 0)
                while (step_dir / f"{phase}_{safe_id}_rollout{index}.jsonl").exists():
                    index += 1
                rollout_counts[key] = index + 1
                out = step_dir / f"{phase}_{safe_id}_rollout{index}.jsonl"
                with open(out, "w") as f:
                    header = {
                        "type": "task",
                        "phase": phase,
                        "step": target,
                        # The policy version that generated this rollout
                        # (async runs; None when the trainer does not stamp it).
                        "policy_version": policy_version,
                        "task_id": task.id,
                        "goal": task.goal,
                        "max_steps": task.max_steps,
                        "info": task.info,
                        "reward": reward,
                        "num_steps": num_steps,
                        # What the agent was told it could do, needed to judge
                        # whether a malformed call was the model's fault.
                        "tool_docs": tool_docs,
                    }
                    f.write(json.dumps(header, default=str) + "\n")
                    for turn, record in enumerate(turns):
                        f.write(
                            json.dumps(
                                {"type": "step", "turn": turn, **record}, default=str
                            )
                            + "\n"
                        )
        except Exception as e:  # logging must never break training
            print(f"[metrics] trajectory logging failed (non-fatal): {e!r}")

    def close(self) -> None:
        """Close the log file and finish the wandb run. Never raises."""
        if self._f:
            try:
                self._f.close()
            except Exception as e:
                print(f"[metrics] could not close {self.path} (non-fatal): {e!r}")
        if self._wandb is not None:
            try:
                self._wandb.finish()
            except Exception as e:
                print(f"[metrics] wandb finish failed (non-fatal): {e!r}")

def sequence_batch_stats(seqs: list[TokenSequence]) -> dict:
    """Summary statistics of a training batch, for logging and sanity checks."""
    if not seqs:
        return {"num_sequences": 0, "num_action_tokens": 0}

    action_logprobs: list[float] = []
    action_advantages: list[float] = []
    for seq in seqs:
        for m, lp, adv in zip(seq.mask, seq.logprobs, seq.advantages):
            if m:
                action_logprobs.append(lp)
                action_advantages.append(adv)

    n = max(1, len(action_logprobs))
    mean_adv = sum(action_advantages) / n
    return {
        "num_sequences": len(seqs),
        "num_action_tokens": len(action_logprobs),
        "mean_seq_len": sum(len(s.tokens) for s in seqs) / len(seqs),
        "mean_advantage": mean_adv,
        "mean_abs_advantage": sum(abs(a) for a in action_advantages) / n,
        "adv_std": math.sqrt(max(0.0, sum((a - mean_adv) ** 2 for a in action_advantages) / n)),
        # Monte-Carlo entropy estimate: E[-log pi(a)] over sampled action tokens.
        # This includes predictable syntax/format tokens as well as semantic
        # choices, so a low value is a debugging signal rather than proof of
        # policy collapse.
        "entropy_proxy": -sum(action_logprobs) / n,
    }


def pass_at_k(
    reward_groups: list[list[float]], k: int, success_threshold: float = 1.0
) -> dict:
    """Success rate and pass@k of rollout groups, one reward list per group.

    This is the single definition used by both evaluate.evaluate_policy and
    the trainers' train-time records, so train/ and eval/ curves for the
    same quantity are computed by the same code:

      success_rate  fraction of all episodes with reward >= success_threshold
      pass@k        fraction of groups with at least one such episode

    `k` is explicit so the key name never depends on the shape of the data,
    and every group must hold exactly k rewards (ValueError otherwise).
    Train and eval normally use different k (cfg.group_size vs cfg.eval_k),
    so the keys are e.g. train/pass@8 and eval/pass@4. Those are different
    quantities and must not be compared as one curve; success_rate is the
    k-independent metric that does line up across train and eval.

    Returns {} when there are no groups.
    """
    if not reward_groups:
        return {}
    if any(len(group) != k for group in reward_groups):
        raise ValueError(f"pass_at_k: every group must hold exactly k={k} rewards")
    all_episodes = [r >= success_threshold for group in reward_groups for r in group]
    group_successes = [any(r >= success_threshold for r in group) for group in reward_groups]
    return {
        "success_rate": sum(all_episodes) / len(all_episodes),
        f"pass@{k}": sum(group_successes) / len(group_successes),
    }


def sanity_warnings(metrics: dict) -> list[str]:
    """Automated outlier checks. Print these prominently during training.

    Warnings are signals to investigate, not diagnoses: task structure and
    expected optimization behavior can also produce unusual-looking values.
    """
    warnings = []

    entropy = metrics.get("entropy_proxy")
    if entropy is not None and entropy < 0.005:
        warnings.append(
            f"entropy_proxy={entropy:.4f}: sampled action-token surprise is very low. "
            "This proxy includes predictable format tokens, so it is not by itself "
            "evidence of policy collapse. Inspect trajectory JSONL files and reward "
            "trends "
            "before changing the learning rate or sampling temperature."
        )

    iw_mean = metrics.get("importance_weight_mean")
    if iw_mean is not None and not 0.5 <= iw_mean <= 2.0:
        warnings.append(
            f"importance_weight_mean={iw_mean:.3f}: sampling and training policies have "
            "diverged a lot. Check staleness limits, or that you pass the correct "
            "sampling logprobs."
        )

    # An importance-weight mean near 1 can hide a rare, very large token-level
    # ratio, so check the tail independently. PPO uses a clipped surrogate;
    # importance_sampling is fully unclipped. Either way, the tail helps
    # diagnose staleness or sampler/trainer mismatch.
    iw_max = metrics.get("importance_weight_max")
    iw_std = metrics.get("importance_weight_std")
    max_is_unstable = iw_max is not None and (
        not math.isfinite(iw_max) or iw_max > 10.0
    )
    std_is_unstable = iw_std is not None and (
        not math.isfinite(iw_std) or iw_std > 1.0
    )
    if max_is_unstable or std_is_unstable:
        tail_values = []
        if iw_max is not None:
            tail_values.append(f"importance_weight_max={iw_max:.3g}")
        if iw_std is not None:
            tail_values.append(f"importance_weight_std={iw_std:.3g}")
        warnings.append(
            f"{', '.join(tail_values)}: importance-weight tail is unstable even if the "
            "mean is near 1. PPO uses a clipped surrogate; importance_sampling is "
            "fully unclipped. Tail ratios remain diagnostic: check staleness, "
            "sampler/trainer numerical agreement, and sampling logprob alignment."
        )

    grad_norm = metrics.get("grad_norm")
    if grad_norm is not None and grad_norm > 50.0:
        warnings.append(f"grad_norm={grad_norm:.1f}: gradient spike; check advantage scaling.")

    frac_degenerate = metrics.get("frac_degenerate_groups")
    if frac_degenerate is not None and frac_degenerate > 0.8:
        warnings.append(
            f"frac_degenerate_groups={frac_degenerate:.2f}: almost all groups have "
            "identical rewards (no learning signal). The task set may be too easy/hard "
            "for the current policy, or temperature too low."
        )

    return warnings

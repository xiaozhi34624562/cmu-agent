"""Everything that touches the Tinker SDK lives here (given).

If the Tinker API surface changes, this should be the only file that needs
updating. Everything here is given except :meth:`TinkerSession.submit_update`,
the one method students implement. See
https://tinker-docs.thinkingmachines.ai for the API reference.
"""

from __future__ import annotations

import json
import math
import os
import re
import time

from scottyrl.types import TokenSequence


def to_tinker_datum(seq: TokenSequence, loss_fn: str, advantage_scale: float = 1.0):
    """Convert a TokenSequence to a tinker.Datum for the given loss function.

    loss_fn choices used in this assignment:
      "ppo": clipped importance-weighted policy gradient. This is the
          default for GRPO experiments and requires sampling logprobs.
      "importance_sampling": token loss -(pi_theta / pi_sample) * A.
          This is the unclipped variant used for REINFORCE and also requires
          sampling logprobs.
      "cross_entropy": token loss -weight * log pi_theta with weight = A.
          This is REINFORCE with *no* importance weighting, exactly the
          "async without IW" ablation.

    `advantage_scale` multiplies every on-mask advantage (for
    `cross_entropy`, every weight) before it enters the datum; off-mask
    positions stay 0. Tinker sums the token losses over every action token
    of every datum in a batch, so with the default 1.0 the gradient of a
    batch grows with its token count and a long episode outweighs a short
    one. `train_step` passes 1 / T with T the batch's action-token count,
    which turns the sum into the mean token loss over the batch. The
    ratio-based losses are linear in the advantage, so the factor rescales
    the gradient and nothing else: the importance ratio pi_theta / pi_sample
    and the PPO clipping thresholds mean the same thing at any scale.
    `seq.advantages` is not modified.
    """
    import tinker
    from tinker import TensorData

    model_input = tinker.ModelInput.from_ints(seq.tokens[:-1])
    targets = seq.tokens[1:]
    # Zero out everything off-mask so no loss flows to env/prompt tokens.
    advantages = [
        a * advantage_scale if m else 0.0 for a, m in zip(seq.advantages, seq.mask)
    ]

    if loss_fn in {"importance_sampling", "ppo"}:
        loss_fn_inputs = {
            "target_tokens": TensorData(targets, dtype="int64"),
            "logprobs": TensorData(seq.logprobs, dtype="float32"),
            "advantages": TensorData(advantages, dtype="float32"),
        }
    elif loss_fn == "cross_entropy":
        loss_fn_inputs = {
            "target_tokens": TensorData(targets, dtype="int64"),
            "weights": TensorData(advantages, dtype="float32"),
        }
    else:
        raise ValueError(f"Unsupported loss_fn: {loss_fn}")

    return tinker.Datum(model_input=model_input, loss_fn_inputs=loss_fn_inputs)


def importance_weight_stats(
    seqs: list[TokenSequence], training_logprobs: list[list[float]]
) -> dict:
    """Compare training-time logprobs against sampling-time logprobs on action
    tokens. Near-1.0 means on-policy; drift indicates staleness."""
    ratios: list[float] = []
    for seq, train_lps in zip(seqs, training_logprobs):
        for m, lp_sample, lp_train in zip(seq.mask, seq.logprobs, train_lps):
            if m:
                ratios.append(math.exp(min(50.0, lp_train - lp_sample)))
    if not ratios:
        return {}
    mean = sum(ratios) / len(ratios)
    return {
        "importance_weight_mean": mean,
        "importance_weight_min": min(ratios),
        "importance_weight_max": max(ratios),
        "importance_weight_std": math.sqrt(
            sum((r - mean) ** 2 for r in ratios) / len(ratios)
        ),
    }


def _grad_norm_from(optimizer_metrics: dict) -> float | None:
    """The gradient norm among backend-defined optimizer metrics, if any.

    First present of `unclipped_grad_l2:mean` (hosted Tinker), `grad_norm`,
    or any key that ends with `grad_norm` (SkyRL: `skyrl.ai/grad_norm`).
    None when no such key holds a number.
    """
    candidates = ["unclipped_grad_l2:mean", "grad_norm"]
    candidates += sorted(k for k in optimizer_metrics if k.endswith("grad_norm") and k not in candidates)
    for key in candidates:
        value = optimizer_metrics.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def make_service_client():
    """The Tinker service client (given).

    `TINKER_BASE_URL` in the environment selects a self-hosted
    Tinker-compatible server; unset means the hosted Tinker service. The SDK
    refuses to start without an API key of the form `tml-...`, even for a
    self-hosted server that never checks it, so a placeholder is supplied
    there. A `TINKER_API_KEY` you set yourself is left alone.
    """
    import tinker

    base_url = os.environ.get("TINKER_BASE_URL")
    if not base_url:
        return tinker.ServiceClient()
    os.environ.setdefault("TINKER_API_KEY", "tml-self-hosted")
    return tinker.ServiceClient(base_url=base_url)


class TinkerSession:
    """Thin wrapper around the Tinker training + sampling clients.

    One session owns one training client for the whole run. It counts the
    optimizer steps it has taken (`completed_steps`), checkpoints resumable
    state every `resume_save_every` optimizer steps, and records every
    sampler snapshot in `snapshots` so the run can be packaged and
    re-evaluated.

    Two counters describe a run's progress. The trainers count ITERATIONS
    (1, 2, ...; a skipped iteration advances this count without an update)
    and the session counts OPTIMIZER STEPS (`completed_steps`). The log
    steps and the sync snapshot names follow iterations; the async version
    numbers follow optimizer steps.

    Resuming: pass `resume=True` and the path of a resume marker written by
    an earlier process (see config.resume_marker_path). `start()` then
    restores weights + optimizer state from the marker's `state_path` and
    sets

      step_offset      the marker's `step`: the absolute iteration whose
                       update produced the checkpoint. The trainers count
                       from 1 again; adding this makes their iteration
                       numbers absolute (log steps, `step_` snapshot names).
      completed_steps  the marker's `optimizer_steps`.
      version_offset   the same number; the async trainer's versions count
                       updates, so adding it makes `v` names and logged
                       policy versions absolute.
      resumes          how many times the run has been resumed (1 for the
                       first resumed process); every snapshot name of a
                       resumed process gets `_r{resumes}` appended.

    A checkpoint taken during an iteration is only usable once that
    iteration's training record is logged, so the marker is written by
    `iteration_recorded`, which MetricsLogger calls for every training
    record, not by `train_step` itself.
    """

    def __init__(
        self,
        base_model: str,
        lora_rank: int = 32,
        *,
        resume_marker_path: str | None = None,
        resume_save_every: int = 0,
        resume: bool = False,
    ):
        self.base_model = base_model
        self.lora_rank = lora_rank
        self.resume_marker_path = str(resume_marker_path) if resume_marker_path else None
        self.resume_save_every = int(resume_save_every or 0)
        self.resume = resume
        self.service_client = None
        self.training_client = None
        self.tokenizer = None
        # Optimizer steps taken by this run so far, across restarts.
        self.completed_steps = 0
        # Iterations a previous process finished before this one started (0
        # when fresh); see the class docstring.
        self.step_offset = 0
        # Optimizer steps a previous process finished (0 when fresh).
        self.version_offset = 0
        # How many times this run has been resumed (0 in a fresh process).
        self.resumes = 0
        # Every sampler snapshot of this session, oldest first:
        # {"name": ..., "path": "tinker://...", "completed_steps": N}.
        self.snapshots: list[dict] = []
        # Path of the last resumable state written by save_resumable_state.
        self.resumable_state_path: str | None = None
        # Wall-clock seconds this session has spent in `train_step` (updates,
        # including the periodic resumable checkpoint) and saving sampler
        # snapshots in `new_sampling_client`. MetricsLogger turns the change
        # between training records into train/update_time_s and
        # train/learner_wait_s (see "Timing Metrics" in ASSIGNMENT.md).
        self.update_seconds = 0.0
        self.snapshot_seconds = 0.0
        # A checkpoint saved by train_step whose iteration has not been
        # recorded yet: (state_path, completed_steps at the checkpoint).
        self._unmarked_checkpoint: tuple[str, int] | None = None

    async def start(self) -> TinkerSession:
        """Create the service and training clients (fresh or restored).

        `TINKER_BASE_URL` in the environment points the service client at a
        self-hosted Tinker-compatible server; unset means the hosted Tinker
        service. When resuming from a marker with a `state_path`, the
        training client is restored from that checkpoint, which carries its
        own base_model and lora_rank: the session adopts the marker's
        values and prints a warning if the config's differ. The marker's
        `resumes` count is incremented and written back at once, so a
        second crash resumes with a distinct snapshot suffix.
        """
        self.service_client = make_service_client()

        marker = self._read_marker() if self.resume else {}
        state_path = marker.get("state_path")
        if state_path:
            self.step_offset = int(marker.get("step", 0))
            self.completed_steps = int(marker.get("optimizer_steps", 0))
            self.version_offset = self.completed_steps
            self.resumes = int(marker.get("resumes", 0)) + 1
            self.resumable_state_path = state_path
            for key, expected in (("base_model", self.base_model), ("lora_rank", self.lora_rank)):
                recorded = marker.get(key)
                if recorded is not None and recorded != expected:
                    print(
                        f"[resume] WARNING: marker {key}={recorded!r} differs from the "
                        f"config's {expected!r}; the restored client uses the "
                        "checkpoint's value"
                    )
                    setattr(self, key, recorded)
            print(
                f"[resume] restoring from iteration {self.step_offset} "
                f"({self.completed_steps} optimizer steps, resume #{self.resumes}): {state_path}"
            )
            self._write_marker({**marker, "resumes": self.resumes})
            self.training_client = await self._with_adapter_retry(
                lambda: self.service_client.create_training_client_from_state_with_optimizer_async(
                    path=state_path
                )
            )
        else:
            self.training_client = await self._with_adapter_retry(
                lambda: self.service_client.create_lora_training_client_async(
                    base_model=self.base_model, rank=self.lora_rank
                )
            )
        self.tokenizer = self.training_client.get_tokenizer()
        return self

    def _read_marker(self) -> dict:
        """The resume marker's JSON object, or {} if missing or unreadable."""
        if not self.resume_marker_path:
            return {}
        try:
            with open(self.resume_marker_path) as f:
                data = json.load(f)
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def _write_marker(self, marker: dict) -> None:
        """Write the resume marker; errors are printed, not raised."""
        if not self.resume_marker_path:
            return
        try:
            os.makedirs(os.path.dirname(self.resume_marker_path) or ".", exist_ok=True)
            with open(self.resume_marker_path, "w") as f:
                json.dump(marker, f)
        except Exception as e:
            print(f"[resume] could not write {self.resume_marker_path} (non-fatal): {e!r}")

    async def _with_adapter_retry(self, make_client, attempts: int = 6, delay: float = 60.0):
        """Create a training client, retrying while the backend still holds one.

        Some backends (SkyRL's FSDP worker group) support a single LoRA
        adapter at a time and keep a crashed run's adapter registered until
        its session times out (SkyRL's default is 300s, swept every 60s).
        Resuming right after a crash races that cleanup, so wait it out.
        Only errors mentioning "register_adapter" or "single LoRA adapter"
        are retried; anything else propagates at once.
        """
        import asyncio

        for attempt in range(attempts):
            try:
                return await make_client()
            except Exception as e:
                stale_adapter = "register_adapter" in str(e) or "single LoRA adapter" in str(e)
                if not stale_adapter or attempt == attempts - 1:
                    raise
                print(
                    f"[resume] backend still holds a previous adapter; waiting "
                    f"{delay:.0f}s for its session to expire "
                    f"(attempt {attempt + 1}/{attempts})"
                )
                await asyncio.sleep(delay)

    async def submit_update(self, datums: list, loss_fn: str, lr: float, grad_clip_norm: float) -> tuple:
        """*** STUDENT IMPLEMENTATION *** Submit one forward/backward pass and
        one optimizer step to the Tinker training client and return both
        results.

        `datums` is the list of `tinker.Datum` built by `train_step`; pass it
        through unchanged. The two SDK calls are
        `self.training_client.forward_backward_async(datums, loss_fn=loss_fn)`
        and `self.training_client.optim_step_async(params)`, where `params`
        is a `tinker.AdamParams` whose `learning_rate` is `lr` and whose
        `grad_clip_norm` is `grad_clip_norm`. 

        Each call returns a future for work queued on the server. Submit
        BOTH before resolving either result: Tinker batches requests that
        arrive back to back into the same server cycle, so resolving the
        first result before submitting the second serializes the two
        operations and roughly doubles the latency of every step. A future
        is resolved with `await future.result_async()`.

        Returns: `(fwd_result, opt_result)`, the two resolved results.

        Do not catch SDK errors (RequestFailedError, APIStatusError,
        TimeoutError, ...): callers need submission and training failures
        to propagate. API reference:
        https://tinker-docs.thinkingmachines.ai/tinker/api-reference/trainingclient/
        """
        import tinker

        # TODO(student): implement this method.
        raise NotImplementedError

    async def train_step(
        self,
        seqs: list[TokenSequence],
        loss_fn: str,
        lr: float,
        grad_clip_norm: float,
    ) -> dict:
        """One optimizer update on `seqs`; returns the backend metrics.

        Converts the sequences to datums, hands them to `submit_update`,
        then extracts metrics from the two results:

          `loss_normalizer`, T = the number of action tokens in `seqs` (at
            least 1). Tinker sums token losses over the batch; every
            advantage is passed to `to_tinker_datum` scaled by 1 / T, so the
            objective is the mean token loss over the batch and a batch of
            long episodes gets the same gradient scale as a batch of short
            ones (Dr.GRPO's constant normalizer, set per batch; a
            per-sequence mean would down-weight the tokens of long
            episodes). The sequences' own `advantages` stay as the trainer
            built them, so the logged advantage statistics are unscaled;
          every key of `fwd_result.metrics`, as floats (loss, ...);
          importance_weight_{mean,min,max,std} from the training-time
            logprobs in `fwd_result.loss_fn_outputs`, when reported;
          every key of `opt_result.metrics` under an `optim/` prefix;
          `grad_norm`, an alias for the optimizer's gradient norm. The SDK
            does not name that key, the backend does: hosted Tinker reports
            `unclipped_grad_l2:mean` (only when clipping is on), SkyRL
            reports `skyrl.ai/grad_norm`. The alias takes the first present
            of `unclipped_grad_l2:mean`, `grad_norm`, or any optimizer key
            that ends with `grad_norm`.

        A finished step counts towards `completed_steps` and may save a
        resumable checkpoint (see `_maybe_checkpoint`). Errors from
        `submit_update` propagate; nothing is counted for a failed step.
        """
        started = time.monotonic()
        # Tinker sums token losses over the batch; 1 / T makes it a mean.
        loss_normalizer = max(1, sum(seq.num_action_tokens for seq in seqs))
        datums = [
            to_tinker_datum(seq, loss_fn, advantage_scale=1.0 / loss_normalizer)
            for seq in seqs
        ]
        fwd_result, opt_result = await self.submit_update(
            datums, loss_fn=loss_fn, lr=lr, grad_clip_norm=grad_clip_norm
        )

        metrics: dict = {"loss_normalizer": loss_normalizer}
        try:  # loss + per-token training logprobs, if the backend reports them
            metrics.update({k: float(v) for k, v in fwd_result.metrics.items()})
        except (AttributeError, TypeError, ValueError):
            pass
        try:
            training_logprobs = [
                out["logprobs"].tolist() for out in fwd_result.loss_fn_outputs
            ]
            metrics.update(importance_weight_stats(seqs, training_logprobs))
        except (AttributeError, KeyError, TypeError):
            pass
        try:
            optimizer_metrics = dict(opt_result.metrics)
        except (AttributeError, TypeError, ValueError):
            optimizer_metrics = {}
        for key, value in optimizer_metrics.items():
            try:
                metrics[f"optim/{key}"] = float(value)
            except (TypeError, ValueError):
                pass
        grad_norm = _grad_norm_from(optimizer_metrics)
        if grad_norm is not None:
            metrics["grad_norm"] = grad_norm

        # Both trainers take every optimizer step through this method, so
        # counting and checkpointing here covers sync and async alike.
        self.completed_steps += 1
        await self._maybe_checkpoint()
        self.update_seconds += time.monotonic() - started
        return metrics

    async def save_resumable_state(self, name: str) -> str:
        """Checkpoint full resumable state (weights + optimizer); returns its path.

        This is a different artifact from the sampler snapshots written by
        `new_sampling_client` (weights only). `overwrite=True` lets a
        resumed run rewrite a name it already used.
        """
        save_future = await self.training_client.save_state_async(name=name, overwrite=True)
        save_result = await save_future.result_async()
        self.resumable_state_path = save_result.path
        return save_result.path

    async def _maybe_checkpoint(self) -> None:
        """Every `resume_save_every` optimizer steps, save resumable state.

        The state is saved as `resume_{completed_steps:06d}` and remembered
        as pending; the marker is not written here. The iteration that took
        this step has not been recorded yet, and a marker that pointed at
        the checkpoint before the record exists would make a resumed run
        skip that iteration's record. `iteration_recorded` writes the
        marker once the record is logged. Never raises: losing a checkpoint
        must not take down a training run.
        """
        if not self.resume_save_every or not self.resume_marker_path:
            return
        if self.completed_steps % self.resume_save_every != 0:
            return
        try:
            state_path = await self.save_resumable_state(f"resume_{self.completed_steps:06d}")
            self._unmarked_checkpoint = (state_path, self.completed_steps)
            print(f"[resume] saved checkpoint after {self.completed_steps} optimizer steps")
        except Exception as e:
            print(f"[resume] checkpoint failed (non-fatal): {e!r}")

    def iteration_recorded(self, absolute_step: int) -> None:
        """Point the resume marker at the pending checkpoint, if there is one.

        MetricsLogger calls this with the absolute step of every training
        record it writes. When `train_step` saved a checkpoint during that
        iteration, the marker is (re)written as

          {"step": absolute_step, "optimizer_steps": N, "state_path": ...,
           "base_model": ..., "lora_rank": ..., "resumes": R, ...}

        keeping any other keys it already had (MetricsLogger stores the
        wandb run id there). A resumed run then continues from iteration
        `step + 1` with N optimizer steps done. Without a pending checkpoint
        this does nothing. Never raises.
        """
        if self._unmarked_checkpoint is None:
            return
        state_path, optimizer_steps = self._unmarked_checkpoint
        self._unmarked_checkpoint = None
        marker = {
            "base_model": self.base_model,
            "lora_rank": self.lora_rank,
            **self._read_marker(),
            "step": int(absolute_step),
            "optimizer_steps": optimizer_steps,
            "state_path": state_path,
            "resumes": self.resumes,
        }
        self._write_marker(marker)
        print(f"[resume] checkpointed at step {absolute_step} ({optimizer_steps} optimizer steps)")

    def _snapshot_name(self, name: str) -> str:
        """The name a sampler snapshot is saved under on the server.

        Trainers name snapshots relative to their own loop: the sync trainer
        `step_000000`, `step_000001`, ... (iterations) and the async trainer
        `v0`, `v1`, ... (updates). A resumed process counts from 0 again, so
        the offsets restore absolute numbers: `step_(\\d+)` gets `step_offset`
        added and `v(\\d+)` gets `version_offset` added. A run resumed at
        iteration 40 after 38 updates saves the trainer's `step_000001` as
        `step_000041` and its `v1` as `v39`.

        When `resumes > 0`, every name of the process then gets
        `_r{resumes}` appended (`step_000041_r1`, `v39_r1`, `baseline_r1`):
        the crashed process may already have saved the plain name on the
        server (its iterations after the checkpoint are redone), and
        sampler snapshots cannot be overwritten. As a fallback, any other
        name that repeats an earlier snapshot name of this session gets
        `_r{n}` appended as well (`x`, `x_r1`, `x_r2`, ...), so no two
        snapshots of one session share a name.
        """
        for pattern, prefix, offset in (
            (r"step_(\d+)", "step_", self.step_offset),
            (r"v(\d+)", "v", self.version_offset),
        ):
            match = re.fullmatch(pattern, name)
            if match and offset:
                digits = match.group(1)
                name = prefix + str(int(digits) + offset).zfill(len(digits))
                break
        if self.resumes:
            name = f"{name}_r{self.resumes}"
        used = {snapshot["name"] for snapshot in self.snapshots}
        if name not in used:
            return name
        repeat = 1
        while f"{name}_r{repeat}" in used:
            repeat += 1
        return f"{name}_r{repeat}"

    async def new_sampling_client(self, name: str):
        """Snapshot current weights and return a sampling client for them.

        The snapshot is saved under `_snapshot_name(name)` (the trainer's
        name, made absolute and unique when resuming) and recorded in
        `self.snapshots` as {"name", "path", "completed_steps"}, oldest
        first. The last entry's path is the run's `final_sampler_path`.
        """
        snapshot_name = self._snapshot_name(name)
        started = time.monotonic()
        save_future = await self.training_client.save_weights_for_sampler_async(
            name=snapshot_name
        )
        save_result = await save_future.result_async()
        self.snapshot_seconds += time.monotonic() - started
        self.snapshots.append(
            {
                "name": snapshot_name,
                "path": save_result.path,
                "completed_steps": self.completed_steps,
            }
        )
        return self.service_client.create_sampling_client(model_path=save_result.path)

    def checkpoints_manifest(self, run_name: str | None) -> dict:
        """What this session saved, for runs/{run_name}.checkpoints.json.

        `final_sampler_path` is the last sampler snapshot (what Part 5 is
        re-evaluated on); `resumable_state_path` is the last full state
        checkpoint. Either is null when nothing of that kind was saved.
        `write_checkpoints_manifest` merges this with what earlier
        processes of a resumed run saved.
        """
        return {
            "run_name": run_name,
            "base_model": self.base_model,
            "lora_rank": self.lora_rank,
            "completed_steps": self.completed_steps,
            "resumes": self.resumes,
            "snapshots": list(self.snapshots),
            "final_sampler_path": self.snapshots[-1]["path"] if self.snapshots else None,
            "resumable_state_path": self.resumable_state_path,
        }


def write_checkpoints_manifest(session: TinkerSession, run_name: str | None, path: str | None) -> None:
    """Write the run's checkpoints manifest to `path` as JSON.

    The entry scripts call this in their `finally` block so the manifest
    exists even after a crash. A resumed process (`session.resumes > 0`)
    merges with the manifest the earlier processes left: their snapshots
    come first, this session's follow, `final_sampler_path` is the last of
    the merged list, and `resumable_state_path` is this session's when it
    saved one, else the earlier one. `completed_steps`, `base_model`,
    `lora_rank` and `resumes` are the session's. A None path (no run_name)
    writes nothing; write errors are printed, not raised.
    """
    if not path:
        return
    try:
        manifest = session.checkpoints_manifest(run_name)
        prior: dict = {}
        if session.resumes:
            try:
                with open(path) as f:
                    loaded = json.load(f)
                prior = loaded if isinstance(loaded, dict) else {}
            except (OSError, ValueError):
                prior = {}
        if prior:
            snapshots = list(prior.get("snapshots") or []) + manifest["snapshots"]
            manifest["snapshots"] = snapshots
            manifest["final_sampler_path"] = snapshots[-1]["path"] if snapshots else None
            manifest["resumable_state_path"] = (
                manifest["resumable_state_path"] or prior.get("resumable_state_path")
            )
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"[checkpoints] wrote {path}")
    except Exception as e:
        print(f"[checkpoints] could not write {path} (non-fatal): {e!r}")

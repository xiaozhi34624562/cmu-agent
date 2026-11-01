"""Configuration system (given).

Experiments are defined by YAML files in `configs/` with two sections that
map onto the dataclasses below:

    model:
      base_model: Qwen/Qwen3.5-4B
      max_tokens: 256
      chat_template: scottyrl/chat_templates/qwen3_5.jinja
      enable_thinking: false
    train:
      env: number_search
      algo: grpo
      group_size: 8
      loss_fn: ppo
      grad_clip_norm: 1.0

Any field can be overridden from the command line:

    python scripts/train_sync.py --config configs/p2b_number_search_grpo.yaml \
        --set train.lr=2e-5 --set model.temperature=0.8

`train.run_name` identifies a run: its log is runs/{run_name}.jsonl, its
resume marker runs/{run_name}.resume.json, and its checkpoint manifest
runs/{run_name}.checkpoints.json. See check_run_name_available for how a
name that already has results is handled.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, fields
from pathlib import Path

import yaml

SUPPORTED_LOSS_FNS = frozenset({"cross_entropy", "importance_sampling", "ppo"})

# The directory that holds `scottyrl/`, `configs/`, `data/`, ... Relative
# paths in configs (e.g. `model.chat_template`) are resolved against it, so
# the scripts work from any working directory.
REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class ModelConfig:
    """Everything about the sampled model and how prompts are rendered for it.

    `chat_template` is a Jinja file (relative to the repo root, or absolute)
    that turns the agent's message list into the exact text the model was
    trained on. The shipped template is derived from the stock Qwen3.5
    template and understands two extra knobs:

      enable_thinking: when true, the assistant prefill is `<think>\\n` and the
        model samples its reasoning before the answer; when false the prefill
        is an empty think block and the model answers directly. Either way the
        prefill is part of the prompt, never of the sampled action.
      preserve_thinking_history: when true, earlier assistant turns are
        re-rendered verbatim, so every prompt in an episode is an extension of
        the previous prompt + completion (one training sequence per episode).
        When false, `<think>...</think>` blocks are dropped from earlier turns:
        shorter prompts, but each turn becomes its own training sequence.

    `stop_sequences` are token names the sampler stops on; the tokenizer maps
    them to ids (names it does not know are skipped). The template writes
    `<|im_end|>` back when it renders history, so a completion that stops on
    it keeps the sequence-extension property; a completion that stops on a
    token the template does not write back (`<|endoftext|>`) breaks it and
    starts a new training sequence at that turn (see `LLMCall`).
    """

    base_model: str = "Qwen/Qwen3.5-4B"
    lora_rank: int = 32
    max_tokens: int = 256
    temperature: float = 1.0
    chat_template: str = "scottyrl/chat_templates/qwen3_5.jinja"
    enable_thinking: bool = False
    preserve_thinking_history: bool = True
    stop_sequences: list[str] = field(
        default_factory=lambda: ["<|im_end|>", "<|endoftext|>"]
    )


def resolve_chat_template(path: str | Path) -> Path:
    """Absolute path of a chat template given relative to the repo root."""
    resolved = Path(path).expanduser()
    if not resolved.is_absolute():
        resolved = REPO_ROOT / resolved
    return resolved


@dataclass
class TrainConfig:
    env: str = "number_search"
    agent: str = "xml_toolcall"
    algo: str = "grpo"  # "reinforce" | "grpo"
    group_size: int = 8  # rollouts per task (1 for REINFORCE)
    tasks_per_batch: int = 8  # task groups per training step
    loss_fn: str = "ppo"  # "cross_entropy" | "importance_sampling" | "ppo"
    lr: float = 1e-5
    grad_clip_norm: float = 1.0
    num_steps: int = 100
    # Evaluate every N training steps. 0 disables evaluation entirely,
    # including the step-0 baseline; so does eval_tasks=0.
    eval_every: int = 10
    eval_k: int = 4
    eval_tasks: int = 50  # how many val tasks to evaluate on
    seed: int = 11768
    # Where the per-step JSON log goes: runs/{run_name}.jsonl, derived by
    # load_config from run_name. Not settable from a config file or --set
    # (load_config rejects it), so the log, the resume marker, the
    # checkpoints manifest, packaging and grading all follow run_name.
    log_path: str | None = None

    # Async-only settings (Part 3)
    num_workers: int = 8
    groups_per_batch: int = 8
    max_staleness: int = 2  # drop groups sampled > this many versions ago
    queue_capacity: int = 16

    # Identity of one experiment. A run_name that already has results under
    # runs/ is refused unless `resume` is set (see check_run_name_available),
    # so a changed experiment gets a changed run_name.
    run_name: str | None = None
    # Continue this run_name from its last resumable checkpoint instead of
    # starting fresh. Only meaningful when runs/{run_name}.resume.json exists.
    resume: bool = False
    # Save weights + optimizer state every N optimizer steps so the run can be
    # resumed after a crash (0 disables checkpointing and resuming). A
    # skipped step takes no optimizer step, so checkpoints are not evenly
    # spaced in log steps.
    resume_save_every: int = 10

    # Logging
    # Write full agent<->env transcripts every N training steps (0 disables).
    # Every rollout of a logged step is written; see metrics.MetricsLogger.
    trajectory_log_every: int = 1
    wandb_project: str | None = None  # set (or use --set) to enable wandb

    def __post_init__(self) -> None:
        _validate_train_config(self)


def _validate_train_config(config: TrainConfig) -> None:
    value = config.grad_clip_norm
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
        or value < 0
    ):
        raise ValueError("train.grad_clip_norm must be a finite nonnegative number")
    # Evaluating on zero tasks is meaningless, so treat it as "no evaluation"
    # and let everything downstream check eval_every alone.
    if config.eval_tasks == 0:
        config.eval_every = 0


@dataclass
class Config:
    model: ModelConfig = field(default_factory=ModelConfig)
    train: TrainConfig = field(default_factory=TrainConfig)

    def to_dict(self) -> dict:
        return {
            "model": {f.name: getattr(self.model, f.name) for f in fields(ModelConfig)},
            "train": {f.name: getattr(self.train, f.name) for f in fields(TrainConfig)},
        }


def resume_marker_path(train_cfg: TrainConfig) -> str | None:
    """Path of the run's resume marker, runs/{run_name}.resume.json.

    The marker records the last usable resumable checkpoint as JSON:

      {"step": S, "optimizer_steps": N, "state_path": "tinker://...",
       "base_model": ..., "lora_rank": ..., "resumes": R, "wandb_run_id": ...}

    S is the absolute iteration (log step) whose update produced the
    checkpoint, N the optimizer steps completed at that point (a skipped
    iteration takes none, so N <= S), R how many times the run has been
    resumed (0 in a fresh run). TinkerSession.iteration_recorded writes it
    once iteration S's training record is logged, TinkerSession.start bumps
    `resumes`, and MetricsLogger adds the wandb run id. Returns None when the
    run has no run_name or checkpointing is disabled (resume_save_every == 0).
    """
    if not train_cfg.run_name or not train_cfg.resume_save_every:
        return None
    return str(Path("runs") / f"{train_cfg.run_name}.resume.json")


def checkpoints_manifest_path(train_cfg: TrainConfig) -> str | None:
    """Path of runs/{run_name}.checkpoints.json, or None without a run_name.

    The entry scripts write this manifest when a run ends (see
    TinkerSession.checkpoints_manifest); packaging and grading read
    `final_sampler_path` from it.
    """
    if not train_cfg.run_name:
        return None
    return str(Path("runs") / f"{train_cfg.run_name}.checkpoints.json")


def _read_json(path: str | Path | None) -> dict:
    """Parse a JSON object file; {} when it is missing or unreadable."""
    if not path:
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def check_run_name_available(train_cfg: TrainConfig) -> None:
    """Decide whether this run_name starts fresh, resumes, or must stop.

    Called by both entry scripts before anything else. run_name names the
    graded log (runs/{run_name}.jsonl) and the checkpoint a resume continues
    from, so reusing it by accident would either append a second
    experiment's steps to that log or continue weights the new settings
    never produced. The rule:

      no prior results (no log file, no resume marker): start fresh, whatever
        `train.resume` says.
      prior results and `train.resume` is false: SystemExit with the three
        options (new run_name, --set train.resume=true, or delete the files).
      `train.resume` is true but `train.resume_save_every` is 0: SystemExit,
        that setting disables checkpointing and therefore resuming.
      `train.resume` is true but there is no readable marker with a
        `state_path`: SystemExit, there is nothing to resume from.
      `train.resume` is true, the marker is usable, but the log file is
        missing: a warning is printed and the run resumes; the rebuilt log
        starts at the marker's step + 1 (no baseline, no earlier records).
    """
    if not train_cfg.run_name:
        return
    marker_path = resume_marker_path(train_cfg)
    existing = [
        p for p in (train_cfg.log_path, marker_path) if p and Path(p).exists()
    ]
    if not existing:
        return
    if not train_cfg.resume:
        raise SystemExit(
            f"run_name '{train_cfg.run_name}' already has results "
            f"({', '.join(existing)}).\n"
            "Pick one:\n"
            "  - new experiment (different settings): choose a new run_name, "
            "e.g. --set train.run_name=<name>\n"
            "  - continue this run (same settings, e.g. after a crash): "
            "--set train.resume=true\n"
            "  - redo it from scratch: delete the files above first"
        )
    if not train_cfg.resume_save_every:
        raise SystemExit(
            f"train.resume is set for run_name '{train_cfg.run_name}' but "
            "resuming is disabled because train.resume_save_every=0 (no "
            "checkpoint is ever written). Set train.resume_save_every to a "
            "positive number, start over with a new run_name, or delete the "
            "files under runs/ for this one."
        )
    marker = _read_json(marker_path)
    if not marker.get("state_path"):
        where = marker_path or f"runs/{train_cfg.run_name}.resume.json"
        raise SystemExit(
            f"train.resume is set but run_name '{train_cfg.run_name}' has "
            f"nothing to resume from: no readable resume marker with a "
            f"state_path at {where}. A checkpoint is written every "
            "train.resume_save_every optimizer steps. Start over with a new "
            "run_name, or delete the files under runs/ for this one."
        )
    if train_cfg.log_path and not Path(train_cfg.log_path).exists():
        step = marker.get("step", "?")
        print(
            f"[resume] WARNING: {train_cfg.log_path} is missing; the resumed "
            f"log will start at step {step} + 1 with no baseline evaluation "
            "and no earlier records"
        )


def _apply(section, values: dict, source: str) -> None:
    valid = {f.name for f in fields(section)}
    for key, value in values.items():
        if key not in valid:
            raise ValueError(f"Unknown config key '{key}' in {source}")
        # YAML parses e.g. "2e-5" (no dot) as a string; coerce numeric fields.
        current = getattr(section, key)
        if isinstance(value, str) and not isinstance(current, bool):
            if isinstance(current, float):
                value = float(value)
            elif isinstance(current, int):
                value = int(value)
        setattr(section, key, value)


_LOG_PATH_MESSAGE = (
    "train.log_path is derived from run_name (runs/{{run_name}}.jsonl) and "
    "cannot be set in {source}; set train.run_name instead"
)


def load_config(path: str | Path | None = None, overrides: list[str] = ()) -> Config:
    """Build a Config from defaults <- yaml file <- --set overrides.

    `train.log_path` is derived from `train.run_name`; supplying it in the
    file or with --set raises ValueError.
    """
    config = Config()

    if path is not None:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        unknown = set(data) - {"model", "train"}
        if unknown:
            raise ValueError(f"Unknown config sections in {path}: {sorted(unknown)}")
        if "log_path" in (data.get("train") or {}):
            raise ValueError(_LOG_PATH_MESSAGE.format(source=str(path)))
        _apply(config.model, data.get("model") or {}, str(path))
        _apply(config.train, data.get("train") or {}, str(path))

    for override in overrides:
        if "=" not in override or "." not in override.split("=", 1)[0]:
            raise ValueError(f"Overrides look like section.key=value, got '{override}'")
        dotted, raw_value = override.split("=", 1)
        section_name, key = dotted.split(".", 1)
        if dotted == "train.log_path":
            raise ValueError(_LOG_PATH_MESSAGE.format(source=f"--set {override}"))
        if section_name not in ("model", "train"):
            raise ValueError(
                f"Unknown section '{section_name}' in override '{override}'"
            )
        section = config.model if section_name == "model" else config.train
        _apply(section, {key: yaml.safe_load(raw_value)}, f"--set {override}")

    if config.train.loss_fn not in SUPPORTED_LOSS_FNS:
        choices = ", ".join(sorted(SUPPORTED_LOSS_FNS))
        raise ValueError(
            f"Unsupported train.loss_fn '{config.train.loss_fn}'; choose one of: {choices}"
        )

    # Overrides are applied after TrainConfig.__post_init__, so validate the
    # final merged value as well as direct TrainConfig construction.
    _validate_train_config(config.train)

    template_path = resolve_chat_template(config.model.chat_template)
    if not template_path.is_file():
        raise FileNotFoundError(
            f"model.chat_template '{config.model.chat_template}' not found "
            f"(resolved to {template_path})"
        )
    config.model.chat_template = str(template_path)

    if not isinstance(config.model.stop_sequences, list) or not all(
        isinstance(s, str) for s in config.model.stop_sequences
    ):
        raise ValueError("model.stop_sequences must be a list of strings")

    # log_path follows run_name so the two cannot drift apart: the resume
    # marker, the checkpoints manifest, packaging and grading all look for
    # runs/{run_name}.jsonl. Without a run_name there is no log file.
    if config.train.run_name:
        config.train.log_path = f"runs/{config.train.run_name}.jsonl"

    return config

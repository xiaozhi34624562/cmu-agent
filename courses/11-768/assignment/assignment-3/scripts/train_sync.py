"""Entry point for synchronous training (Parts 2 and 4.1, given).

Examples:
  python scripts/train_sync.py --config configs/p2a_number_search_reinforce.yaml
  python scripts/train_sync.py --config configs/p2b_number_search_grpo.yaml \
      --set train.lr=2e-5
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from scottyrl.config import (
    check_run_name_available,
    checkpoints_manifest_path,
    load_config,
    resume_marker_path,
)
from scottyrl.envs import make_env_factory
from scottyrl.metrics import MetricsLogger
from scottyrl.tinker_adapter import TinkerSession, write_checkpoints_manifest
from scottyrl.train.sync import SyncTrainer
from scottyrl.types import load_tasks

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="YAML config (see configs/)")
    parser.add_argument("--set", dest="overrides", action="append", default=[],
                        metavar="SECTION.KEY=VALUE", help="override a config field")
    args = parser.parse_args()

    config = load_config(args.config, args.overrides)
    model_cfg, train_cfg = config.model, config.train
    # A run_name that already has results is only reused on purpose.
    check_run_name_available(train_cfg)

    train_tasks = load_tasks(DATA_DIR / f"{train_cfg.env}_train.jsonl")
    val_tasks = load_tasks(DATA_DIR / f"{train_cfg.env}_val.jsonl")

    session = await TinkerSession(
        model_cfg.base_model,
        model_cfg.lora_rank,
        resume_marker_path=resume_marker_path(train_cfg),
        resume_save_every=train_cfg.resume_save_every,
        resume=train_cfg.resume,
    ).start()
    # The logged config keeps the run's configured total, not the remainder.
    config_dict = config.to_dict()
    # A resumed run only trains the steps that are left. The trainer counts
    # from 1, so the logger re-adds the offset to keep step numbers absolute
    # (the trainer's eval_due reads the same offset to keep evaluations on
    # absolute multiples of eval_every).
    done = session.step_offset
    if done:
        remaining = max(0, train_cfg.num_steps - done)
        print(f"[resume] {done} step(s) already done; {remaining} to go")
    train_cfg.num_steps = max(0, train_cfg.num_steps - done)
    logger = MetricsLogger(
        path=train_cfg.log_path,
        wandb_project=train_cfg.wandb_project,
        run_name=train_cfg.run_name,
        config=config_dict,
        trajectory_log_every=train_cfg.trajectory_log_every,
        step_offset=done,
        resume_marker_path=resume_marker_path(train_cfg),
        session=session,
    )
    trainer = SyncTrainer(
        session, make_env_factory(train_cfg.env), train_tasks, val_tasks,
        model_cfg, train_cfg, logger,
    )
    try:
        # Step-0 baseline (given): evaluate the untrained policy before any
        # update, so the eval curve starts from a real baseline instead of
        # first appearing at cfg.eval_every. train() only handles the
        # periodic evaluations. A resumed run already has its baseline in
        # the log, so it skips this, as does a run
        # with evaluation disabled (eval_every=0 or eval_tasks=0).
        if done == 0 and train_cfg.eval_every:
            baseline_policy = trainer.make_policy(
                await session.new_sampling_client("baseline")
            )
            trainer.record_evaluation(0, await trainer.evaluate_now(baseline_policy))
        await trainer.train()
    finally:
        # What this run saved on the Tinker service (sampler snapshots and
        # resumable state); packaging and grading read final_sampler_path.
        write_checkpoints_manifest(
            session, train_cfg.run_name, checkpoints_manifest_path(train_cfg)
        )
        logger.close()


if __name__ == "__main__":
    asyncio.run(main())

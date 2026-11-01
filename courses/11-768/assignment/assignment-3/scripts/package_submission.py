"""Package your submission as a zip file (given).

Run it from the repo root once every required run has finished:

  python scripts/package_submission.py                  # writes submission.zip
  python scripts/package_submission.py --out a3.zip
  python scripts/package_submission.py --allow-missing  # package what is there

What goes into the zip, all at their repo-relative paths:

  - for every run named in configs/required_runs.yaml: its config,
    runs/<run_name>.jsonl (the per-step log), runs/<run_name>_trajectories/
    (the transcripts) and runs/<run_name>.checkpoints.json (what the run
    saved on the Tinker service);
  - the six source files you implement (STUDENT_FILES below);
  - report.pdf and AI_USAGE.md (your statement on AI assistance);
  - submission/manifest.json: the git commit, a timestamp, and per run the
    number of training and evaluation records, the last logged step, the
    checkpoint paths and the Hugging Face model id of the exported adapter
    (`hf_model_id`). The same file is also left on disk.

Tinker checkpoints stay on the Tinker service; the zip carries their
`tinker://` paths (in the checkpoints manifests), not the weights. Graders
re-evaluate your Part 5 adapter from the public Hugging Face repo that
scripts/export_checkpoint.py creates and records in
runs/p5_textcraft_grpo.checkpoints.json as `hf_model_id`, so export it
before packaging and keep the repo public until grades are released.

The script prints a checklist of present and missing items. A missing run
log, checkpoints file or AI_USAGE.md, or a missing `hf_model_id` for
p5_textcraft_grpo, is an error (exit code 1, no zip written) unless
--allow-missing is given;
a missing report.pdf is an error unless --allow-missing-report is given.
Missing trajectory directories are only reported: a run with
trajectory_log_every 0 has none.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

# The checkout this script lives in; nothing here imports scottyrl.
REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_RUNS_FILE = "configs/required_runs.yaml"
REPORT_FILE = "report.pdf"
AI_USAGE_FILE = "AI_USAGE.md"
MANIFEST_FILE = "submission/manifest.json"
# The run whose adapter must be exported to the Hub (scripts/export_checkpoint.py).
HF_EXPORT_RUN = "p5_textcraft_grpo"

# The files with student code; everything else is restored to the given
# version before grading, so nothing else from scottyrl/ is packaged.
STUDENT_FILES = [
    "scottyrl/advantages.py",
    "scottyrl/datagen.py",
    "scottyrl/tinker_adapter.py",
    "scottyrl/train/common.py",
    "scottyrl/train/sync.py",
    "scottyrl/train/async_grpo.py",
]


def load_required_runs(path: Path) -> dict[str, str]:
    """The run_name -> config path mapping of configs/required_runs.yaml."""
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in data.items()
    ):
        raise ValueError(f"{path} must map run names to config paths")
    return data


def summarize_log(path: Path) -> dict:
    """Count the records of a runs/<run_name>.jsonl log.

    A record is a training record when any key starts with `train/` and an
    evaluation record when any key starts with `eval/` (the trainers write
    one or the other). Lines that are not JSON objects are ignored.
    """
    train_records = eval_records = 0
    last_step = None
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if not isinstance(record, dict):
                continue
            if any(k.startswith("train/") for k in record):
                train_records += 1
            if any(k.startswith("eval/") for k in record):
                eval_records += 1
            step = record.get("step")
            if isinstance(step, int) and (last_step is None or step > last_step):
                last_step = step
    return {
        "train_records": train_records,
        "eval_records": eval_records,
        "last_step": last_step,
    }


def git_commit(root: Path) -> str | None:
    """The checked-out commit of `root`, or None when git is unavailable."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def hf_model_id_item(run_name: str) -> str:
    """The checklist name of a run's exported adapter."""
    return f"hf_model_id in runs/{run_name}.checkpoints.json"


def _files_under(directory: Path) -> list[Path]:
    return sorted(p for p in directory.rglob("*") if p.is_file())


def collect(root: Path, required_runs: dict[str, str]) -> tuple[list[Path], dict, list[str], list[str]]:
    """Gather what the zip holds.

    Returns (files, manifest, missing_required, missing_optional) where every
    file is an absolute path under `root`, the manifest is the JSON object
    written to submission/manifest.json (without the timestamp and commit),
    and the two lists name the items the checklist reports as missing. Each
    run's entry carries `hf_model_id` from its checkpoints file (None when
    not exported); for HF_EXPORT_RUN a missing one is a required item.
    """
    files: list[Path] = []
    missing_required: list[str] = []
    missing_optional: list[str] = []
    runs: dict[str, dict] = {}

    for run_name, config_path in required_runs.items():
        entry: dict = {"config": config_path}
        config = root / config_path
        if config.is_file():
            files.append(config)
        else:
            missing_required.append(config_path)

        log = root / "runs" / f"{run_name}.jsonl"
        entry["log"] = f"runs/{run_name}.jsonl"
        if log.is_file():
            files.append(log)
            entry.update(summarize_log(log))
        else:
            missing_required.append(entry["log"])
            entry.update({"train_records": 0, "eval_records": 0, "last_step": None})

        trajectories = root / "runs" / f"{run_name}_trajectories"
        entry["trajectories"] = f"runs/{run_name}_trajectories/"
        trajectory_files = _files_under(trajectories) if trajectories.is_dir() else []
        if trajectory_files:
            files.extend(trajectory_files)
        else:
            missing_optional.append(entry["trajectories"])
        entry["trajectory_files"] = len(trajectory_files)

        checkpoints = root / "runs" / f"{run_name}.checkpoints.json"
        entry["checkpoints"] = f"runs/{run_name}.checkpoints.json"
        entry["final_sampler_path"] = None
        entry["resumable_state_path"] = None
        entry["hf_model_id"] = None
        if checkpoints.is_file():
            files.append(checkpoints)
            try:
                with open(checkpoints) as f:
                    data = json.load(f)
            except ValueError:
                data = {}
            if isinstance(data, dict):
                entry["final_sampler_path"] = data.get("final_sampler_path")
                entry["resumable_state_path"] = data.get("resumable_state_path")
                entry["hf_model_id"] = data.get("hf_model_id") or None
        else:
            missing_required.append(entry["checkpoints"])
        if run_name == HF_EXPORT_RUN and not entry["hf_model_id"]:
            missing_required.append(hf_model_id_item(run_name))
        runs[run_name] = entry

    for relative in STUDENT_FILES:
        path = root / relative
        if path.is_file():
            files.append(path)
        else:
            missing_required.append(relative)

    ai_usage = root / AI_USAGE_FILE
    if ai_usage.is_file():
        files.append(ai_usage)
    else:
        missing_required.append(AI_USAGE_FILE)

    manifest = {
        "runs": runs,
        "student_files": list(STUDENT_FILES),
        "report": (root / REPORT_FILE).is_file(),
        "ai_usage": ai_usage.is_file(),
    }
    return files, manifest, missing_required, missing_optional


def write_zip(out: Path, root: Path, files: list[Path], manifest_path: Path) -> None:
    """Write `files` (and the manifest) to `out` at their paths under `root`."""
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            zf.write(path, arcname=path.relative_to(root).as_posix())
        zf.write(manifest_path, arcname=manifest_path.relative_to(root).as_posix())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", default="submission.zip", help="zip file to write")
    parser.add_argument(
        "--root", default=str(REPO_ROOT),
        help="repo root holding runs/, configs/ and scottyrl/ (default: this checkout)",
    )
    parser.add_argument(
        "--allow-missing", action="store_true",
        help="package even if a required run log, checkpoints file or AI_USAGE.md is missing",
    )
    parser.add_argument(
        "--allow-missing-report", action="store_true",
        help="package even if report.pdf is missing",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    required_runs = load_required_runs(root / REQUIRED_RUNS_FILE)
    files, manifest, missing_required, missing_optional = collect(root, required_runs)
    report = root / REPORT_FILE
    if report.is_file():
        files.append(report)

    print("Submission checklist")
    for run_name, entry in manifest["runs"].items():
        print(f"  {run_name}")
        for key in ("config", "log", "trajectories", "checkpoints"):
            item = entry[key]
            present = item not in missing_required and item not in missing_optional
            print(f"    [{'ok' if present else 'MISSING'}] {item}")
        if entry["last_step"] is not None:
            print(
                f"         {entry['train_records']} training record(s), "
                f"{entry['eval_records']} evaluation record(s), last step {entry['last_step']}"
            )
        if entry["final_sampler_path"]:
            print(f"         final_sampler_path {entry['final_sampler_path']}")
        if entry["hf_model_id"]:
            print(f"    [ok] hf_model_id {entry['hf_model_id']}")
        elif run_name == HF_EXPORT_RUN:
            print(
                f"    [MISSING] {hf_model_id_item(run_name)}: "
                f"run scripts/export_checkpoint.py --run {run_name} first"
            )
    for relative in STUDENT_FILES:
        print(f"  [{'MISSING' if relative in missing_required else 'ok'}] {relative}")
    print(f"  [{'ok' if manifest['report'] else 'MISSING'}] {REPORT_FILE}")
    print(f"  [{'ok' if manifest['ai_usage'] else 'MISSING'}] {AI_USAGE_FILE}")

    problems = []
    if missing_required and not args.allow_missing:
        problems.append(
            f"{len(missing_required)} required item(s) missing (see the checklist); "
            "finish the runs or pass --allow-missing"
        )
    if not manifest["report"] and not args.allow_missing_report:
        problems.append(f"{REPORT_FILE} missing; add it or pass --allow-missing-report")
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}")
        return 1

    manifest = {
        "git_commit": git_commit(root),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **manifest,
    }
    manifest_path = root / MANIFEST_FILE
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    out = Path(args.out)
    write_zip(out, root, files, manifest_path)
    print(f"wrote {out} ({len(files) + 1} files) and {MANIFEST_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

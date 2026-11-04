#!/usr/bin/env python3
"""Check that your Assignment 2 submission has every expected file and artifact.

Run from the repository root:

    uv run python check_submission.py

This only checks that files exist and that runs finished; it does not grade
your answers. Fix every line marked [MISSING] before you submit.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SECTION3 = Path("writeup/3_run_example_tasks")
SECTION3_ARTIFACTS = SECTION3 / "artifacts"

# Tasks that ship with the starter or are downloaded in Section 3.
EXAMPLE_TASKS = {"humaneval-0", "django__django-11099", "model-extraction-relu-logits"}

FIGURES = [
    "effort-distribution.png",
    "bash-command-usage.png",
    "exploration-to-implementation.png",
    "repeated-effort.png",
    "context-consulted.png",
    "failure-recovery.png",
    "custom-analysis.png",
]
FIGURES_REQUIRED = 3

# (job name from the handout, handout section, whether it is a model run)
SECTION3_JOBS = [
    ("humaneval-oracle", "3.1", False),
    ("humaneval-agent", "3.1", True),
    ("swebench-django-11099", "3.2", True),
    ("terminal-bench-model-extraction", "3.3", True),
]
MODEL_ATTEMPTS = 5

PLACEHOLDER = re.compile(r"<!--\s*(Your response here|Paste your [^>]*?)\.?\s*-->")

# Color the labels only in a terminal, and respect https://no-color.org.
USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ


def label(text: str, color: str) -> str:
    padded = f"{text:<9}"
    return f"\033[1;{color}m{padded}\033[0m" if USE_COLOR else padded


OK = label("[OK]", "32")  # green
WARN = label("[CHECK]", "33")  # yellow
MISSING = label("[MISSING]", "31")  # red


class Report:
    def __init__(self) -> None:
        self.missing = 0
        self.warnings = 0

    def section(self, title: str) -> None:
        print(f"\n{title}\n{'-' * len(title)}")

    def ok(self, message: str) -> None:
        print(f"  {OK} {message}")

    def miss(self, message: str, hint: str | None = None) -> None:
        self.missing += 1
        print(f"  {MISSING} {message}")
        if hint:
            print(f"              -> {hint}")

    def warn(self, message: str, hint: str | None = None) -> None:
        self.warnings += 1
        print(f"  {WARN} {message}")
        if hint:
            print(f"              -> {hint}")

    def require_file(self, path: Path, hint: str | None = None) -> bool:
        if (ROOT / path).is_file():
            self.ok(str(path))
            return True
        self.miss(f"{path} not found", hint)
        return False


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def trial_reward(trial: Path) -> float | None:
    result = read_json(trial / "result.json") or {}
    rewards = (result.get("verifier_result") or {}).get("rewards") or {}
    if "reward" in rewards:
        return rewards["reward"]
    try:
        return float((trial / "verifier" / "reward.txt").read_text().strip())
    except (OSError, ValueError):
        return None


def check_job(
    report: Report,
    job: Path,
    *,
    attempts: int,
    model_run: bool,
    rerun_hint: str,
) -> None:
    """Check one Harbor job folder (the folder named by --job-name)."""
    if not (ROOT / job).is_dir():
        report.miss(f"{job}/ not found", rerun_hint)
        return
    if not (ROOT / job / "result.json").is_file():
        report.miss(f"{job}/ has no result.json (the job did not finish)", rerun_hint)
        return

    trials = sorted(p for p in (ROOT / job).iterdir() if p.is_dir() and "__" in p.name)
    problems: list[str] = []
    if len(trials) != attempts:
        noun = "attempt" if attempts == 1 else "attempts"
        problems.append(f"expected {attempts} {noun}, found {len(trials)}")

    for trial in trials:
        name = trial.name
        result = read_json(trial / "result.json")
        if result is None:
            problems.append(f"{name}: no result.json (the attempt did not finish)")
            continue
        if not (trial / "verifier" / "reward.txt").is_file():
            problems.append(f"{name}: no verifier/reward.txt (the verifier did not run)")
        if model_run and not (trial / "agent" / "trajectory.json").is_file():
            problems.append(f"{name}: no agent/trajectory.json")
        if not model_run and trial_reward(trial) != 1:
            problems.append(f"{name}: oracle reward is {trial_reward(trial)}, expected 1")

    if problems:
        report.miss(f"{job}/ is incomplete:")
        for problem in problems:
            print(f"              - {problem}")
        print(f"              -> {rerun_hint}")
        return

    errored = [t.name for t in trials if (read_json(t / "result.json") or {}).get("exception_info")]
    count = f"{len(trials)} attempt" + ("" if len(trials) == 1 else "s")
    report.ok(f"{job}/ ({count})")
    if errored:
        report.warn(
            f"{job}/ has attempts that ended with an error: {', '.join(errored)}",
            "Open them with `uv run harbor view` and make sure this is a real agent failure, "
            "not a setup problem.",
        )


def check_placeholders(report: Report, path: Path) -> None:
    if not (ROOT / path).is_file():
        return
    lines = [
        number
        for number, line in enumerate((ROOT / path).read_text().splitlines(), start=1)
        if PLACEHOLDER.search(line)
    ]
    if lines:
        where = ", ".join(str(n) for n in lines)
        report.warn(
            f"{path} still has {len(lines)} unanswered placeholder(s) (line {where})",
            "Replace each `<!-- ... -->` placeholder with your answer.",
        )


def check_section2(report: Report) -> None:
    report.section("Section 2: Basics")
    path = Path("writeup/2_basics/responses.md")
    report.require_file(path)
    check_placeholders(report, path)


def check_section3(report: Report) -> None:
    report.section("Section 3: Run Example Tasks")
    responses = SECTION3 / "responses.md"
    report.require_file(responses)
    check_placeholders(report, responses)

    present = [f for f in FIGURES if (ROOT / SECTION3 / f).is_file()]
    if len(present) >= FIGURES_REQUIRED:
        report.ok(f"{len(present)} trajectory figures: {', '.join(present)}")
    else:
        found = ", ".join(present) if present else "none"
        report.miss(
            f"{len(present)} of {FIGURES_REQUIRED} trajectory figures in {SECTION3}/ (found: {found})",
            f"Save each figure with its filename from Section 3.4, e.g. {SECTION3 / FIGURES[0]}.",
        )

    if (ROOT / responses).is_file():
        text = (ROOT / responses).read_text()
        leftover = [f for f in FIGURES if f"### `{f}`" in text and f not in present]
        if leftover and len(present) >= FIGURES_REQUIRED:
            report.warn(
                f"responses.md still lists unanswered 3.4 questions: {', '.join(leftover)}",
                "Delete the questions you did not answer.",
            )

    for job_name, section, model_run in SECTION3_JOBS:
        check_job(
            report,
            SECTION3_ARTIFACTS / job_name,
            attempts=1,
            model_run=model_run,
            rerun_hint=f"Run the `--job-name {job_name}` command from Section {section}.",
        )


def find_student_tasks() -> list[Path]:
    tasks = ROOT / "tasks"
    if not tasks.is_dir():
        return []
    return sorted(
        p.relative_to(ROOT)
        for p in tasks.iterdir()
        if p.is_dir() and p.name not in EXAMPLE_TASKS and not p.name.startswith(".")
    )


def check_section4(report: Report) -> None:
    report.section("Section 4: Create Your Own Task")
    tasks = find_student_tasks()
    if not tasks:
        report.miss(
            "no task of your own found in tasks/",
            "Create your task at tasks/<task-id>/ (the example tasks do not count).",
        )
        return
    if len(tasks) > 1:
        names = ", ".join(t.name for t in tasks)
        report.miss(
            f"found {len(tasks)} tasks of your own in tasks/ ({names}); submit exactly one",
            "Remove or move the tasks you are not submitting.",
        )
        return

    task = tasks[0]
    report.ok(f"task folder {task}/")
    for name in ("instruction.md", "task.toml", "tests/test.sh", "solution/solve.sh"):
        report.require_file(task / name)

    task_toml = ROOT / task / "task.toml"
    uses_prebuilt_image = task_toml.is_file() and "docker_image" in task_toml.read_text()
    if not uses_prebuilt_image:
        report.require_file(
            task / "environment" / "Dockerfile",
            "Every task needs an environment/Dockerfile (or a docker_image in task.toml).",
        )

    report.require_file(
        task / "report.pdf",
        "Compile writeup/4_create_tasks/report.tex and save the PDF here.",
    )

    check_job(
        report,
        task / "artifacts" / f"{task.name}-oracle",
        attempts=1,
        model_run=False,
        rerun_hint="Run the oracle command from Section 4.2 with your task id.",
    )
    check_job(
        report,
        task / "artifacts" / f"{task.name}-gemini",
        attempts=MODEL_ATTEMPTS,
        model_run=True,
        rerun_hint=f"Run the {MODEL_ATTEMPTS}-attempt command from Section 4.3 with your task id.",
    )


def main() -> int:
    print("CS329Z Assignment 2: submission check")
    print(f"Repository: {ROOT}")

    report = Report()
    check_section2(report)
    check_section3(report)
    check_section4(report)

    report.section("Section 5: Peer Review")
    print("  Submitted separately on Gradescope as peer_review.pdf (not checked here).")

    print()
    if report.missing:
        print(
            f"{report.missing} item(s) missing and {report.warnings} to double-check. "
            "Fix every [MISSING] line before you submit."
        )
        return 1
    if report.warnings:
        print(f"All required files are present. {report.warnings} item(s) to double-check above.")
        return 0
    print("Everything is in place.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

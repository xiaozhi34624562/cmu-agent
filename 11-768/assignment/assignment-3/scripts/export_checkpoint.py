"""Export a run's final adapter to a public Hugging Face model repo (given).

Graders cannot sample from your `tinker://` checkpoints (they live on your
own server), so the Part 5 adapter is submitted as a public Hub repo. Run this once after the Part 5 run has finished:

  python scripts/export_checkpoint.py                       # p5_textcraft_grpo
  python scripts/export_checkpoint.py --run p5_textcraft_grpo --exist-ok

It reads `final_sampler_path` from runs/<run>.checkpoints.json, downloads
the checkpoint archive from the Tinker service (`TINKER_BASE_URL` selects a
self-hosted server), extracts the PEFT LoRA adapter, adds a model card,
uploads everything to `<hf-username>/scottyrl-a3-<run>` (public; graders
must be able to load it) and records the repo id in the checkpoints file as
`hf_model_id`, which scripts/package_submission.py puts in the manifest.
The repo must stay public until grades are released.

You need a Hugging Face account and a login (`hf auth login`, once). The
name template is fixed; `--repo-id` overrides it if you must (the manifest
carries whatever was used). Re-running against an existing repo needs
`--exist-ok`. `--model-path tinker://...` exports another checkpoint of the
run; `--from-dir <adapter_dir>` uploads an adapter directory that is
already on disk (course staff pulling checkpoints off a server volume, or
`tinker checkpoint download` output) and skips the download.

The export downloads the checkpoint through your server, so the deployment
that trained the run must be up. If you have stopped it, redeploy it with
the same command: checkpoints persist on its volume. Graders serve
the repo with vLLM and evaluate it with scripts/evaluate_checkpoint.py
--server; the model card shows the exact commands, so you can check your
export the same way.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import yaml

# The checkout this script lives in.
REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_RUNS_FILE = "configs/required_runs.yaml"
DEFAULT_RUN = "p5_textcraft_grpo"
DEFAULT_BASE_MODEL = "Qwen/Qwen3.5-4B"
REPO_ID_TEMPLATE = "{hf_user}/scottyrl-a3-{run_name}"
MODEL_CARD_TAGS = ["tinker", "peft", "lora", "scottyrl", "11-768"]
ADAPTER_CONFIG = "adapter_config.json"
ADAPTER_WEIGHTS = ("adapter_model.safetensors", "adapter_model.bin")
COMPLETE_MARKER = "checkpoint_complete"


class ExportError(Exception):
    """A problem the user can fix; printed without a traceback."""


# ------------------------------------------------------- service access --


def make_rest_client():
    """A Tinker REST client (`TINKER_BASE_URL` selects a self-hosted server)."""
    from scottyrl.tinker_adapter import make_service_client

    return make_service_client().create_rest_client()


def make_hf_api():
    """An `HfApi` using the login of `hf auth login`."""
    from huggingface_hub import HfApi

    return HfApi()


def download_archive(url: str, dest: Path, timeout: float = 600.0) -> None:
    """Stream the archive at `url` (the URL the archive endpoint returned) to `dest`."""
    import httpx

    with httpx.stream("GET", url, timeout=timeout, follow_redirects=True) as response:
        response.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)


def hf_username(api) -> str:
    """The logged-in user's name; an ExportError when there is no login."""
    try:
        return api.whoami()["name"]
    except Exception as e:  # LocalTokenNotFoundError, HfHubHTTPError, ...
        raise ExportError(
            f"not logged in to Hugging Face ({e.__class__.__name__}: {e}); "
            "run `hf auth login` once, then retry"
        ) from e


def default_repo_id(hf_user: str, run_name: str) -> str:
    return REPO_ID_TEMPLATE.format(hf_user=hf_user, run_name=run_name)


# ----------------------------------------------------------- local files --


def load_required_runs(root: Path) -> dict[str, str]:
    with open(root / REQUIRED_RUNS_FILE) as f:
        data = yaml.safe_load(f) or {}
    return {str(k): str(v) for k, v in data.items()}


def run_model_settings(root: Path, config_path: str) -> tuple[str, int | None]:
    """(base_model, lora_rank) of the run's config, with the repo defaults."""
    try:
        with open(root / config_path) as f:
            model = (yaml.safe_load(f) or {}).get("model") or {}
    except OSError:
        model = {}
    rank = model.get("lora_rank")
    return str(model.get("base_model") or DEFAULT_BASE_MODEL), int(rank) if rank else None


def checkpoints_path(root: Path, run_name: str) -> Path:
    return root / "runs" / f"{run_name}.checkpoints.json"


def read_checkpoints(path: Path) -> dict:
    """The run's checkpoints manifest, or {} when it does not exist."""
    try:
        with open(path) as f:
            data = json.load(f)
    except OSError:
        return {}
    except ValueError as e:
        raise ExportError(f"{path} is not valid JSON: {e}") from e
    return data if isinstance(data, dict) else {}


def update_checkpoints(path: Path, repo_id: str, exported_from: str) -> None:
    """Record the export in runs/<run>.checkpoints.json (created if absent)."""
    data = read_checkpoints(path)
    data["hf_model_id"] = repo_id
    data["hf_exported_from"] = exported_from
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def git_commit(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    return (result.stdout.strip() or None) if result.returncode == 0 else None


# --------------------------------------------------------------- archive --


def safe_extract(archive: Path, dest: Path) -> None:
    """Extract a tar archive, refusing links and paths outside `dest`."""
    dest.mkdir(parents=True, exist_ok=True)
    base = dest.resolve()
    with tarfile.open(archive, "r:*") as tar:
        for member in tar.getmembers():
            name = member.name
            if member.issym() or member.islnk():
                raise ExportError(f"archive holds a link ({name}); refusing to extract it")
            parts = Path(name).parts
            if Path(name).is_absolute() or ".." in parts:
                raise ExportError(f"archive holds an unsafe path ({name}); refusing to extract it")
            target = (dest / name).resolve()
            if target != base and base not in target.parents:
                raise ExportError(f"archive holds an unsafe path ({name}); refusing to extract it")
        if hasattr(tarfile, "data_filter"):
            tar.extractall(dest, filter="data")
        else:
            tar.extractall(dest)


def validate_adapter(adapter_dir: Path, *, from_archive: bool) -> None:
    """The directory must hold a PEFT adapter (config + weights); an archive
    must also carry the `checkpoint_complete` marker."""
    if not (adapter_dir / ADAPTER_CONFIG).is_file():
        raise ExportError(f"{adapter_dir} has no {ADAPTER_CONFIG}: not a PEFT adapter")
    if not any((adapter_dir / name).is_file() for name in ADAPTER_WEIGHTS):
        raise ExportError(f"{adapter_dir} has none of {', '.join(ADAPTER_WEIGHTS)}")
    if from_archive and not (adapter_dir / COMPLETE_MARKER).is_file():
        raise ExportError(
            f"archive is missing {COMPLETE_MARKER}: the checkpoint is incomplete; "
            "wait for the save to finish or export another snapshot"
        )


def ensure_base_model(adapter_dir: Path, base_model: str) -> str:
    """Make sure adapter_config.json names its base model; returns the name."""
    path = adapter_dir / ADAPTER_CONFIG
    try:
        config = json.loads(path.read_text())
    except ValueError as e:
        raise ExportError(f"{path} is not valid JSON: {e}") from e
    if not isinstance(config, dict):
        raise ExportError(f"{path} must hold a JSON object")
    recorded = config.get("base_model_name_or_path")
    if isinstance(recorded, str) and recorded:
        return recorded
    config["base_model_name_or_path"] = base_model
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")
    return base_model


def model_card(
    *,
    repo_id: str,
    base_model: str,
    lora_rank: int | None,
    run_name: str,
    exported_from: str,
    config_path: str,
    commit: str | None,
) -> str:
    rank = f"rank {lora_rank}" if lora_rank else "unknown rank"
    tags = "\n".join(f"- {tag}" for tag in MODEL_CARD_TAGS)
    return f"""---
base_model: {base_model}
library_name: peft
tags:
{tags}
---

# scottyrl A3 adapter: {run_name}

LoRA adapter ({rank}) on `{base_model}`, trained with the scottyrl
framework for 11-768 (AI Agents, CMU), Assignment 3.

- run_name: `{run_name}`
- exported from: `{exported_from}`
- config: `{config_path}`
- git commit: `{commit or "unknown"}`

## How it is evaluated

Graders serve the adapter with vLLM and run the course evaluation script
against the server, on the medium and hard TextCraft-Synth validation
splits:

```bash
vllm serve {base_model} --enable-lora --max-lora-rank {lora_rank or 32} \\
    --lora-modules a3={repo_id}
python scripts/evaluate_checkpoint.py --config {config_path} \\
    --server http://localhost:8000/v1 --model a3 --k 4
python scripts/evaluate_checkpoint.py --config {config_path} \\
    --server http://localhost:8000/v1 --model a3 --k 4 \\
    --tasks data/textcraft_val_hard.jsonl
```
"""


def prepare_adapter(
    adapter_dir: Path,
    *,
    from_archive: bool,
    base_model: str,
    lora_rank: int | None,
    repo_id: str,
    run_name: str,
    exported_from: str,
    config_path: str,
    commit: str | None,
) -> str:
    """Validate the adapter, fix its base model, write the model card.
    Returns the base model recorded in adapter_config.json."""
    validate_adapter(adapter_dir, from_archive=from_archive)
    base_model = ensure_base_model(adapter_dir, base_model)
    (adapter_dir / "README.md").write_text(
        model_card(
            repo_id=repo_id,
            base_model=base_model,
            lora_rank=lora_rank,
            run_name=run_name,
            exported_from=exported_from,
            config_path=config_path,
            commit=commit,
        )
    )
    return base_model


# ------------------------------------------------------------------ main --


def split_sampler_path(tinker_path: str) -> tuple[str, str]:
    """(run id, checkpoint id) of a sampler snapshot path.

    The SkyRL server records snapshots as `tinker://<run>/<id>` but also
    accepts `tinker://<run>/sampler_weights/<id>`. Its archive endpoint wants
    the bare `<id>`, so the Tinker client's `..._from_tinker_path` helpers
    cannot be used: they reject the first form and send the second as two
    path segments, which the server answers with 405 Method Not Allowed.
    """
    parts = []
    if tinker_path.startswith("tinker://"):
        parts = tinker_path.removeprefix("tinker://").split("/")
    if len(parts) == 3 and parts[1] == "sampler_weights":
        parts = [parts[0], parts[2]]
    if len(parts) != 2 or not all(parts):
        raise ExportError(
            f"not a sampler snapshot path: {tinker_path}; expected "
            "tinker://<run>/<id> or tinker://<run>/sampler_weights/<id>"
        )
    return parts[0], parts[1]


def fetch_archive(rest_client, tinker_path: str, archive: Path) -> None:
    """Download the checkpoint archive of `tinker_path` to `archive`."""
    run_id, checkpoint_id = split_sampler_path(tinker_path)
    try:
        url = rest_client.get_checkpoint_archive_url(run_id, checkpoint_id).result().url
    except Exception as e:
        raise ExportError(
            f"could not get the archive of {tinker_path} from the server "
            f"({e.__class__.__name__}: {e}). Check that TINKER_BASE_URL points at "
            "the deployment that trained this run and that it is deployed: if you "
            "stopped it, redeploy it with the same command (checkpoints persist on "
            "its volume) and retry"
        ) from e
    download_archive(url, archive)


def weights_info(rest_client, tinker_path: str) -> tuple[str | None, int | None]:
    """(base_model, lora_rank) as the server records them, or Nones."""
    try:
        info = rest_client.get_weights_info_by_tinker_path(tinker_path).result()
        return getattr(info, "base_model", None), getattr(info, "lora_rank", None)
    except Exception:
        return None, None


def upload(api, adapter_dir: Path, repo_id: str, *, exist_ok: bool, message: str) -> str:
    """Create the public repo and upload the adapter directory; returns its URL."""
    try:
        repo_url = api.create_repo(repo_id, repo_type="model", private=False, exist_ok=exist_ok)
    except Exception as e:
        raise ExportError(
            f"could not create {repo_id} ({e.__class__.__name__}: {e}); "
            "if the repo already exists, pass --exist-ok to update it"
        ) from e
    api.upload_folder(
        repo_id=repo_id,
        folder_path=str(adapter_dir),
        repo_type="model",
        commit_message=message,
        ignore_patterns=[COMPLETE_MARKER],
    )
    return str(repo_url)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--run", default=DEFAULT_RUN,
                        help=f"run name, a key of {REQUIRED_RUNS_FILE} (default: {DEFAULT_RUN})")
    parser.add_argument("--model-path", default=None, metavar="tinker://...",
                        help="checkpoint to export (default: the run's final_sampler_path)")
    parser.add_argument("--from-dir", default=None, metavar="ADAPTER_DIR",
                        help="upload this adapter directory instead of downloading")
    parser.add_argument("--repo-id", default=None,
                        help="Hub repo id (default: <hf-username>/scottyrl-a3-<run>)")
    parser.add_argument("--exist-ok", action="store_true", help="update an existing repo")
    parser.add_argument("--root", default=str(REPO_ROOT),
                        help="repo root holding runs/ and configs/ (default: this checkout)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    try:
        required_runs = load_required_runs(root)
        if args.run not in required_runs:
            raise ExportError(
                f"unknown run {args.run!r}; {REQUIRED_RUNS_FILE} names "
                f"{', '.join(required_runs)}"
            )
        config_path = required_runs[args.run]
        base_model, lora_rank = run_model_settings(root, config_path)
        manifest_path = checkpoints_path(root, args.run)

        api = make_hf_api()
        repo_id = args.repo_id or default_repo_id(hf_username(api), args.run)
        print(f"[export] repo id: {repo_id} (template {REPO_ID_TEMPLATE})")

        tinker_path = args.model_path
        if not args.from_dir and not tinker_path:
            manifest = read_checkpoints(manifest_path)
            if not manifest:
                raise ExportError(
                    f"{manifest_path} does not exist: run the training first "
                    f"(see ASSIGNMENT.md for the command; the config is {config_path})"
                )
            tinker_path = manifest.get("final_sampler_path")
            if not tinker_path:
                raise ExportError(
                    f"{manifest_path} has no final_sampler_path: the run saved no "
                    "sampler snapshot; finish (or resume) the run first"
                )
        exported_from = tinker_path or str(Path(args.from_dir).resolve())
        commit = git_commit(root)

        with tempfile.TemporaryDirectory() as tmp:
            if args.from_dir:
                adapter_dir = Path(args.from_dir)
                if not adapter_dir.is_dir():
                    raise ExportError(f"--from-dir {adapter_dir} is not a directory")
                from_archive = False
            else:
                rest_client = make_rest_client()
                archive = Path(tmp) / "checkpoint.tar"
                print(f"[export] downloading {tinker_path}")
                fetch_archive(rest_client, tinker_path, archive)
                adapter_dir = Path(tmp) / "adapter"
                safe_extract(archive, adapter_dir)
                from_archive = True
                server_base, server_rank = weights_info(rest_client, tinker_path)
                base_model = server_base or base_model
                lora_rank = server_rank or lora_rank

            base_model = prepare_adapter(
                adapter_dir,
                from_archive=from_archive,
                base_model=base_model,
                lora_rank=lora_rank,
                repo_id=repo_id,
                run_name=args.run,
                exported_from=exported_from,
                config_path=config_path,
                commit=commit,
            )
            print(f"[export] adapter on {base_model}; uploading to {repo_id} (public)")
            url = upload(
                api, adapter_dir, repo_id,
                exist_ok=args.exist_ok,
                message=f"scottyrl A3 {args.run} from {exported_from}",
            )

        update_checkpoints(manifest_path, repo_id, exported_from)
        print(f"[export] recorded hf_model_id in {manifest_path}")
        print(f"[export] done: {url}")
        return 0
    except ExportError as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

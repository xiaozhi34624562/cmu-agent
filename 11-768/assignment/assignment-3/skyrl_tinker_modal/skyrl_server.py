"""Shared pieces of the SkyRL Tinker servers on Modal (given).

The three launch scripts in this directory (`serve_number_search_sync.py`,
`serve_number_search_async.py`, `serve_textcraft.py`) set their GPU placement
and inference capacity.
Everything else lives here: the container image, the persistent volumes, the
backend settings every deployment shares, and the command that starts SkyRL's
Tinker API server.

All deployments train with SkyRL's Megatron backend, which is the one SkyRL
supports Qwen3.5 on (through Megatron-Bridge), and sample with vLLM.

The image fetches the exact SkyRL revision during its build, so the host only
needs this directory, the Modal CLI, and Modal credentials.
"""

from __future__ import annotations

import json
import os
import subprocess

import modal

# Base model the server trains and samples from. Read from SKYRL_BASE_MODEL at
# deploy time; the default is the value every config in ../configs/ uses. A
# SkyRL Tinker server serves exactly one model, so the client config's
# `model.base_model` must equal this string or creating the training client
# fails. The value is forwarded into the container as a Modal secret so the
# module evaluates to the same name locally and remotely.
MODEL_NAME = os.environ.get("SKYRL_BASE_MODEL", "Qwen/Qwen3.5-4B")
# Upstream 125cb814 plus Megatron output ordering and adapter-only sampler saves.
SKYRL_GIT_URL = "https://github.com/adityasoni9998/SkyRL.git"
SKYRL_COMMIT = "491e1329c314ef43818fb6824d9f2ae61883416c"
# Training backend. This one string is both the `uv` extra and the --backend
# flag, and the two must agree: SkyRL's API server starts its engine with
# `--extra <backend>` appended to our flags, and SkyRL declares its `fsdp` and
# `megatron` extras as conflicting.
BACKEND = "megatron"
REMOTE_REPO = "/opt/SkyRL"
# The pinned fork includes adapter-only sampler checkpoints. A named sampler
# snapshot is what `TinkerSession.new_sampling_client` saves after every
# update, and what scripts/export_checkpoint.py downloads for Part 5. Stock
# SkyRL answers it by exporting the full merged model: several GB per step on
# Megatron, and not an adapter. The fork archives the LoRA adapter it
# has just handed to vLLM, in the layout the export script expects.
VENV = "/opt/skyrl-venv"
HF_CACHE = "/cache/huggingface"
STATE_DIR = "/state"
PORT = 9000

# How long an idle container stays up (and keeps billing) after the last
# request. Short on purpose: `modal app stop <app-name>` ends it at once.
SCALEDOWN_WINDOW = 5 * 60

BASE_BACKEND_CONFIG = {
    "trainer.placement.policy_num_nodes": 1,
    "trainer.policy.megatron_config.tensor_model_parallel_size": 1,
    "trainer.policy.megatron_config.pipeline_model_parallel_size": 1,
    "trainer.policy.megatron_config.context_parallel_size": 1,
    "trainer.policy.language_model_only": True,
    "generator.inference_engine.language_model_only": True,
    "trainer.policy.megatron_config.lora_config.merge_lora": False,
    "trainer.policy.optimizer_config.max_grad_norm": 1.0,
    "trainer.policy.optimizer_config.adam_betas": [0.9, 0.95],
    "trainer.policy.optimizer_config.weight_decay": 0.0,
    "trainer.use_expandable_segments": True,
    "trainer.max_tokens_per_microbatch": 32768,
    "generator.inference_engine.max_num_batched_tokens": 50000,
    "generator.inference_engine.max_num_seqs": 256,
    "generator.inference_engine.enable_prefix_caching": True,
    "generator.inference_engine.enforce_eager": False,
    "generator.inference_engine.engine_init_kwargs.gdn_prefill_backend": "triton",
    "generator.inference_engine.engine_init_kwargs.compilation_config": {
        "cudagraph_mode": "FULL_DECODE_ONLY"
    },
    "generator.inference_engine.use_expandable_segments": False,
    "generator.inference_engine.enable_ray_prometheus_stats": True,
    "generator.inference_engine.engine_init_kwargs.enable_mfu_metrics": True,
}

def colocated(num_gpus: int) -> dict:
    """Placement keys for training and sampling SHARING the same `num_gpus`.

    SkyRL puts the vLLM engines to sleep while a training request runs and
    wakes them when new weights are published, so every GPU works in both
    phases. This suits synchronous training, where the two phases never
    overlap. SkyRL requires the training and inference GPU counts to match.
    """
    return {
        "trainer.placement.colocate_all": True,
        "trainer.placement.policy_num_gpus_per_node": num_gpus,
        "generator.inference_engine.num_engines": num_gpus,
    }


def split(train_gpus: int, inference_gpus: int) -> dict:
    """Placement keys for training and sampling on SEPARATE GPUs.

    Sampling requests go straight to the vLLM engines while training runs, so
    rollouts and updates overlap. Asynchronous training needs this; it also
    suits workloads dominated by long rollouts.
    """
    return {
        "trainer.placement.colocate_all": False,
        "trainer.placement.policy_num_gpus_per_node": train_gpus,
        "generator.inference_engine.num_engines": inference_gpus,
    }


# Fetch only the pinned commit. Verifying HEAD makes a moved/ref-substitution or
# an accidental edit to the fetch command fail the image build immediately.
_clone_skyrl = (
    f"git init {REMOTE_REPO}"
    f" && git -C {REMOTE_REPO} remote add origin {SKYRL_GIT_URL}"
    f" && git -C {REMOTE_REPO} fetch --depth=1 origin {SKYRL_COMMIT}"
    f" && git -C {REMOTE_REPO} checkout --detach FETCH_HEAD"
    f' && test "$(git -C {REMOTE_REPO} rev-parse HEAD)" = "{SKYRL_COMMIT}"'
)

_IMPORT_CHECK = (
    "import skyrl; import torch, vllm, flash_attn, transformer_engine.pytorch, "
    "megatron.core, megatron.bridge; "
    "assert torch.cuda.is_available(); "
    "print(torch.__version__, vllm.__version__, transformer_engine.__version__)"
)

image = (
    modal.Image.from_registry("nvidia/cuda:12.8.1-devel-ubuntu22.04", add_python="3.12")
    .apt_install(
        "build-essential",
        "ca-certificates",
        "curl",
        "git",
        "libnuma-dev",
        "numactl",
    )
    .run_commands("curl -LsSf https://astral.sh/uv/0.9.4/install.sh | sh")
    .env(
        {
            "PATH": (
                f"{VENV}/bin:/root/.local/bin:/usr/local/cuda/bin:"
                "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            ),
            "CUDA_HOME": "/usr/local/cuda",
            "HF_HOME": HF_CACHE,
            "HF_HUB_ENABLE_HF_TRANSFER": "1",
            "RAY_RUNTIME_ENV_HOOK": "ray._private.runtime_env.uv_runtime_env_hook.hook",
            "SKYRL_REPO_ROOT": REMOTE_REPO,
            "UV_LINK_MODE": "copy",
            # Keep the environment outside the repository so Ray can safely
            # propagate the repository as its working directory.
            "UV_PROJECT_ENVIRONMENT": VENV,
        }
    )
    .run_commands(_clone_skyrl)
    .workdir(REMOTE_REPO)
    # Nothing is compiled for the GPU here (Transformer Engine, flash-attn and
    # the Mamba kernels come as prebuilt wheels; Megatron-LM and Megatron-Bridge
    # are installed from their pinned git revisions). The build still runs on a
    # GPU so that the import check can load the CUDA libraries: a broken
    # install then fails the build instead of your first training run.
    .run_commands(
        f"uv sync --extra tinker --extra {BACKEND}",
        f"python -c '{_IMPORT_CHECK}'",
        gpu="H100",
    )
    # The launch scripts import this module inside the container too. Every
    # layer above is shared by the three deployments, so the image is built
    # once and reused.
    .add_local_python_source("skyrl_server")
)

# Model downloads are shared by all deployments. Service state (checkpoints and
# SkyRL's model registry) is kept per deployment, so two servers running at the
# same time never write to the same database.
hf_cache = modal.Volume.from_name("scottyrl-hf-cache", create_if_missing=True)


def server_options(app_name: str, gpu: str) -> dict:
    """Keyword arguments for the `@app.function` that runs a Tinker server.

    `gpu` is a Modal GPU string such as "H100:2". The container scales to zero
    when idle and never runs more than one replica, because a SkyRL server
    holds the training state of a run in memory.
    """
    state = modal.Volume.from_name(f"{app_name}-state", create_if_missing=True)
    return {
        "image": image,
        "gpu": gpu,
        "cpu": 8,
        "memory": 32 * 1024,
        "timeout": 12 * 60 * 60,
        "min_containers": 0,
        "max_containers": 1,
        "scaledown_window": SCALEDOWN_WINDOW,
        "volumes": {HF_CACHE: hf_cache, STATE_DIR: state},
        "secrets": [modal.Secret.from_dict({"SKYRL_BASE_MODEL": MODEL_NAME})],
    }


def launch_tinker_server(backend_config: dict) -> None:
    """Start SkyRL's Tinker API server on PORT inside the container.

    Checkpoints and SkyRL's model registry live on the state volume, so a run
    can be resumed (`--set train.resume=true`) from a fresh container after the
    deployment has scaled down or been redeployed.
    """
    os.makedirs(f"{STATE_DIR}/checkpoints", exist_ok=True)
    os.makedirs(f"{STATE_DIR}/database", exist_ok=True)

    env = os.environ.copy()
    # HF_HOME remains on its persistent Volume even though SkyRL/Ray use /tmp
    # as HOME, matching the known-good bare-metal launch configuration.
    env["HOME"] = "/tmp"

    # Prefer the injected secret over the module constant so the served model is
    # the one chosen at deploy time.
    base_model = os.environ.get("SKYRL_BASE_MODEL", MODEL_NAME)
    print(f">>> serving base model: {base_model}", flush=True)

    command = [
        "uv", "run", "--active", "--no-sync", "--extra", "tinker", "--extra", BACKEND,
        "-m", "skyrl.tinker.api",
        "--base-model", base_model,
        "--backend", BACKEND,
        "--port", str(PORT),
        "--checkpoints-base", f"{STATE_DIR}/checkpoints",
        "--database-url", f"sqlite:///{STATE_DIR}/database/tinker.db",
        "--backend-config", json.dumps(backend_config),
    ]
    print(">>> launching:", " ".join(command), flush=True)
    subprocess.Popen(command, cwd=REMOTE_REPO, env=env)


def run_smoke_install() -> None:
    """Check the installed SkyRL revision, CUDA stack and Megatron on one GPU."""
    code = f"""
import skyrl
import pathlib
import ray
import subprocess
import torch
import transformer_engine.pytorch
import megatron.core
import megatron.bridge
import vllm

assert pathlib.Path({REMOTE_REPO!r}, "pyproject.toml").is_file()
installed_commit = subprocess.check_output(
    ["git", "-C", {REMOTE_REPO!r}, "rev-parse", "HEAD"], text=True
).strip()
assert installed_commit == {SKYRL_COMMIT!r}, installed_commit
assert torch.cuda.is_available()
print({{
    "skyrl_commit": installed_commit,
    "skyrl": skyrl.__version__,
    "torch": torch.__version__,
    "torch_cuda": torch.version.cuda,
    "vllm": vllm.__version__,
    "transformer_engine": transformer_engine.__version__,
    "ray": ray.__version__,
    "gpu": torch.cuda.get_device_name(0),
}})
"""
    subprocess.run(["python", "-c", code], check=True)

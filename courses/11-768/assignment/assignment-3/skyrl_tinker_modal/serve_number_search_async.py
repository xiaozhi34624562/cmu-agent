"""SkyRL Tinker server for the ASYNCHRONOUS Number Search runs (given).

Use it for:  Part 3 (`p3`) and Part 4.3 (`p43_*_iw`, `p43_*_noiw`).
Hardware:    2x H100, split: 1 for training, 1 for sampling.

See README.md for the trainer and inference settings.

Run from this directory:

    uv run modal run serve_number_search_async.py::smoke_install   # optional, builds the image
    uv run modal deploy serve_number_search_async.py
    uv run modal app stop scottyrl-ns-async                        # when you are done
"""

from __future__ import annotations

import os

import modal
from skyrl_server import (
    BASE_BACKEND_CONFIG,
    PORT,
    image,
    launch_tinker_server,
    run_smoke_install,
    server_options,
    split,
)

APP_NAME = os.environ.get("SKYRL_APP_NAME", "scottyrl-ns-async")

backend_config = {
    **BASE_BACKEND_CONFIG,
    **split(train_gpus=1, inference_gpus=1),
    "trainer.logprobs_chunk_size": 1024,
    "trainer.fused_lm_head_logprob": True,
    "generator.inference_engine.gpu_memory_utilization": 0.85,
    "generator.inference_engine.engine_init_kwargs.max_model_len": 32768,
}

app = modal.App(APP_NAME)


@app.function(image=image, gpu="H100", timeout=20 * 60)
def smoke_install() -> None:
    run_smoke_install()


@app.function(**server_options(APP_NAME, gpu="H100:2"))
@modal.concurrent(max_inputs=1_000)
@modal.web_server(PORT, startup_timeout=45 * 60)
def tinker_server() -> None:
    """Expose a scale-to-zero Tinker-compatible endpoint."""
    launch_tinker_server(backend_config)

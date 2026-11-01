#!/bin/bash
# Starts your server when the leaderboard grades your submission.
#
# The leaderboard runs this file with bash on a fresh RTX PRO 4500 node, in place of serve.sh or your own batch script,
# so #SBATCH lines here have no effect. It runs inside the course's sandbox, which has no network and hides /shared,
# /scratch and every home folder. Nothing under $A4 or ~/a4 is there, so a launch.sh that calls $A4/bin/serve.sh or
# reads ~/a4 fails on the leaderboard.
#
# For engine sglang, the sandbox gives this script:
#   PATH                  the course environment's programs (python and the CUDA toolchain) and the course's helpers,
#                         among them a4-serve
#   PYTHONPATH            the python/ folder of SGLang v0.5.20 with your engine/sglang.patch applied, if you have one
#   HOME                  a fresh folder on the node's local disk, for caches
#   HF_HOME               the model's local copy, with HF_HUB_OFFLINE=1, so nothing is downloaded
#   A4_ENGINE             the engine engine.json names (sglang)
#   A4_ENGINE_DIR         this folder, read-only
#   A4_SRC                the SGLang source tree that PYTHONPATH points into, read-only
#   A4_MODEL_PATH         the model to load
#   A4_SERVED_MODEL_NAME  the name to serve it under (qwen3.6-35b-a3b-fp4)
#   A4_HOST, A4_PORT      the address to listen on: 127.0.0.1 and a port the leaderboard picks
#   A4_KEY_FILE           a file holding the key your server must require
# For engine other, this script runs from the node's own shell, without a4-serve, PYTHONPATH or A4_SRC, and gets
# A4_ENV_DIR, your environment folder: see Your own engine on the leaderboard's engine conventions page.
#
# The server must listen on 127.0.0.1:$A4_PORT, require the key in $A4_KEY_FILE on every request (only /health and
# /metrics may answer without it), serve exactly one model, named $A4_SERVED_MODEL_NAME, and be ready within 45 minutes
# of the start of the grading job, which includes the course's own setup of the node.
#
# a4-serve starts SGLang with the flags in the file, then adds the ones the course sets from the variables above:
# --model-path, --served-model-name, --host, --port and --api-key. Put the flags you choose in flags.txt.
#
# Test this file as the leaderboard runs it, in a job on a GPU node after setup.sh, with engine/ at ~/a4/engine:
#   bash $A4/bin/check-submission.sh --launch
set -euo pipefail
exec a4-serve --flags-file "$A4_ENGINE_DIR/flags.txt"

# Assignment 4 starter code

This is the Assignment 3 framework with six changes for Assignment 4. The assignment itself is on the course website.

- **Tasks.** `evaluation_scripts/agent_task_input.json` and `task_test.json` hold 25 SWE-bench Pro tasks, different from Assignment 3's and from the leaderboard's.
- **Every task live at once.** The dispatcher lets your agent keep all 25 tasks open (Assignment 3 allowed 5). Do not change the harness's settings: the leaderboard runs the harness as it is shipped, with its 26 tasks.
- **The 4-hour clock starts with the run**, as on the leaderboard, not when the first task is opened as in Assignment 3. The run's end-to-end time is from its start to the last task done.
- **Your server instead of the course API.** The egress proxy forwards your agent's model calls to `A3_API_UPSTREAM`, your server, and to nothing else. There is no default.
- **Your server's folder.** `engine/` tells the leaderboard how to start your server, and the submission holds it next to `src/`. See [engine/ and launch.sh](#engine-and-launchsh).
- **New names.** The driver is `madsServe.py` (Assignment 3's `madsOpt.py`), and it writes your agent's traces to `madsServe_logs/`. The session packager is `package_agent_sessions.py` (Assignment 3's `package_claude_sessions.py`), and the session archive Claude Code commits with every turn is `agent-sessions.tar.gz` (Assignment 3's `claude-sessions.tar.gz`). If your agent reads `MADSOPT_MAX_ITERATIONS`, make it read `MADSSERVE_MAX_ITERATIONS`, since only the new name reaches the agent container.

## Prerequisites

As in Assignment 3, a Linux x86_64 machine with Docker. In addition:

- **Disk.** The task images take about 40 GB to download and about 105 GB on disk, or about 145 GB if your Docker uses the containerd image store (`docker info` shows `io.containerd.snapshotter.v1`).
- **CPU and memory.** Each task container may use 1 CPU and 4 GB of memory, and with 25 tasks open they all run at once, next to up to 3 gradings.
- **Network.** The machine must reach the cluster's login node, which answers only on the Harvard network and the Harvard University VPN. A CloudLab or AWS machine either joins the VPN or reaches your server through a laptop that is on it, as the [HPC page](https://cs2680.com/computing/cluster.html#cloudlab-aws) describes. With the laptop, every `ssh` or `scp` to `cs2680` below runs on the laptop instead, as that page shows.

## Pointing the harness at your server

The egress proxy runs in a container, and a container cannot reach the `localhost` of the machine it runs on. Open the [SSH tunnel](https://cs2680.com/computing/cluster.html#tunnel) to your server's node on the Docker bridge address instead, which the containers can reach. It is usually `172.17.0.1`; `docker network inspect bridge -f '{{(index .IPAM.Config 0).Gateway}}'` prints it.

```bash
ssh -f -N -o ExitOnForwardFailure=yes -L 172.17.0.1:30000:<node>:30000 cs2680   # <node>: your server's node
export A3_API_UPSTREAM=http://172.17.0.1:30000          # an origin: no /v1
export CS2680_API_KEY=$(ssh cs2680 cat a4/serve.key)    # the same key as your server
export CS2680_MODEL_EXPERT=qwen3.6-35b-a3b-fp4 CS2680_MODEL_STANDARD=qwen3.6-35b-a3b-fp4 CS2680_MODEL_STARTER=qwen3.6-35b-a3b-fp4
curl -s -H "Authorization: Bearer $CS2680_API_KEY" $A3_API_UPSTREAM/v1/models   # should list qwen3.6-35b-a3b-fp4
bash evaluation_scripts/prepare_images.sh             # once
python3 evaluation_scripts/run_all.py --limit 0       # preflight
python3 evaluation_scripts/run_all.py
```

A passing preflight prints `egress: your server via ... -> 200, serving ['qwen3.6-35b-a3b-fp4']`, then `EGRESS OK`, then `preflight k: k ok` for every task from 0 to 24. `HTTP 502` means the proxy cannot reach `A3_API_UPSTREAM`: the tunnel is down, the address is wrong, or a firewall blocks the Docker bridge. `HTTP 401` means your server refused the key. When your server's job ends, stop its tunnel before you open one to the next job's node.

All three model ids name the one model your server serves, so an Assignment 3 agent needs no change to call it. Copy your Assignment 3 `src/` over this folder's `src/`.

## engine/ and launch.sh

`engine/` is the part of your submission that starts your server. This folder's copy is the basic SGLang setup:

- `engine.json` names the framework, `sglang`, and the model, `nvidia/Qwen3.6-35B-A3B-NVFP4` at the revision the leaderboard's catalog lists. Do not change the model; changing it is part of Assignment 5.
- `flags.txt` is a copy of `$A4/basic-sglang-flags.txt`, the basic setup's flags.
- `launch.sh` starts the server. Its one working line is `exec a4-serve --flags-file "$A4_ENGINE_DIR/flags.txt"`.

If you change SGLang, your changes go in `engine/sglang.patch` too, as Part 4 of the assignment page says. The template is for SGLang; the leaderboard's [engine conventions page](https://leaderboard.cs2680.com/a4/engines.html) gives the conventions for vLLM.

To use another framework, build it into an environment folder under `/shared/courseSharedFolders/176914outer/176914/a4-models/<your cluster username>/`, set `"engine"` to `"other"` in `engine.json`, and add an `"env"` key with the folder's path. Your `launch.sh` then starts the server from that folder. [Your own engine](https://leaderboard.cs2680.com/a4/engines.html#own-engine) on the engine conventions page has the folder's rules, a tested example, and how to test it. The course does not fix problems inside your own engine.

The leaderboard runs `launch.sh` with bash on a fresh RTX PRO 4500 node, in place of `serve.sh` or your own batch script, so `#SBATCH` lines in it have no effect. It runs inside the course's sandbox, which has no network and hides `/shared`, `/scratch` and every home folder. Nothing under `$A4` or `~/a4` is there, so a `launch.sh` that calls `$A4/bin/serve.sh` fails on the leaderboard. For `sglang`, the sandbox gives `launch.sh` the course environment, the course's helper `a4-serve` on `PATH`, SGLang v0.5.20 with your patch on `PYTHONPATH`, the model's local copy in `HF_HOME` with downloads turned off, and the variables `A4_ENGINE_DIR` (this folder), `A4_MODEL_PATH`, `A4_SERVED_MODEL_NAME`, `A4_HOST`, `A4_PORT` and `A4_KEY_FILE`. The comments in `launch.sh` list every variable it gets. For `other`, `launch.sh` runs from the node's own shell, without `a4-serve` or `PYTHONPATH`, and gets `A4_ENV_DIR`, the path of your environment folder, which is the one part of `/shared` it can read. [Your own engine](https://leaderboard.cs2680.com/a4/engines.html#own-engine) lists what it gets.

The server must listen on `127.0.0.1:$A4_PORT`, require the key in `$A4_KEY_FILE` on every request (only `/health` and `/metrics` may answer without it), serve exactly one model, named `$A4_SERVED_MODEL_NAME`, and be ready within 45 minutes of the start of the grading job. `a4-serve` does this for SGLang and vLLM: it starts the engine with the flags in the file and then adds `--model-path`, `--served-model-name`, `--host`, `--port` and `--api-key` from those variables.

To test `launch.sh` as the leaderboard runs it, first copy this folder's `engine/` to `~/a4/engine` on the cluster (from this folder: `scp -r engine cs2680:a4/`, which also replaces the cluster's `flags.txt` with this folder's). Then, in a job on a GPU node after `setup.sh` (`setup.sh --vllm` for `vllm`, `setup.sh --weights-only` for `other`), run:

```bash
bash $A4/bin/check-submission.sh --launch      # tests ~/a4/engine; --launch DIR tests DIR/engine
```

Before you zip your submission, copy `~/a4/engine` back over this folder's `engine/` (from this folder: `scp -r 'cs2680:a4/engine/*' engine/`), so that the leaderboard runs what you tested.

## Session logs

Before you start work with Claude Code, run `bash init.sh` once from this folder. It copies `package_agent_sessions.py` to the root of your course repository and writes `CLAUDE.local.md` there, replacing Assignment 3's, so that Claude Code commits the repository's session logs with every turn, in `agent-sessions.tar.gz` at the repository root. For the submission, run `python3 package_agent_sessions.py` from the repository root, which writes `assignment4/a4-sessions.tar.gz`.

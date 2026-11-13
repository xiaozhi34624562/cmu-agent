# Assignment 5 starter code

This is the Assignment 4 framework with these changes for Assignment 5. The assignment itself is on the course website.

- **Two task sets.** `run_all.py --tasks tb2` (the default) runs the 89 tasks of Terminal-Bench 2.0. `run_all.py --tasks a4` runs the 25 tasks of Assignment 4's starter. The leaderboard runs Terminal-Bench 2.0 and the 26 tasks of Assignment 4's leaderboard with the same dispatcher.
- **A generic dispatcher.** `next_task()` returns `task` (the index *k*), `instruction` (the whole task as text), `sandbox_url`, `workdir` and `time_limit_s`. `done(k)` ends task *k*, and the course grades the task's final state. It returns at once and does not report the result. `extract_patch`, `submit_patch`, `evaluate` and `continue_task` are removed: a task's tests run once, after `done(k)`. `madsServe.py` lists the calls. An Assignment 4 task's final state is the changes in its repository since the task's base commit, whether staged, committed or neither, binary files included. One gap remains from Assignment 4: when nothing is staged or committed, a file deleted from the working tree alone (with `rm` rather than `git rm`) does not count. Delete files with `git rm` so that the deletion always counts.
- **Time limits.** A Terminal-Bench 2.0 run has 6 hours from its start, and each task also has its own limit from its `task.toml` (10-200 minutes), counted from when `next_task()` returned it. A run on Assignment 4's tasks is set up as in Assignment 4: 4 hours from its start, no limit per task, and every task may be open at once. `time_limit_s` is the most seconds the task may stay open: its own limit or what is left of the run's, whichever is less. For Assignment 4's tasks it is what is left of the run. A task still open at either limit is graded as it is at that moment. After a task's own limit, a later `done(k)` returns `{"ok": true, "timed_out": true}`. At the run's limit the run stops: the agent's next dispatcher call raises `DispatcherShutdown`, and tasks never opened count as not solved. `run_all.py` uses the leaderboard's limits by default; `A3_RUN_LIMIT_S` sets another limit on the whole run in seconds, and `A3_RUN_LIMIT_S=0` removes it for local experiments. Then an Assignment 4 task's `time_limit_s` is `None`.
- **Task order.** `A3_TASK_ORDER=random` hands the tasks out in a new random order every run, so the index *k* does not identify a task. The leaderboard sets it for both task sets. The default, `fixed`, keeps the task list's order. The results name each task by its key in either order: a Terminal-Bench task's name, or an Assignment 4 task's key in `agent_task_input.json`. That key is a number (`"0"` to `"24"`), but it is not the index *k*, so the results give the task's instance id beside it.
- **The sandbox.** `src/sandbox_server.py` reads and writes any path in the task's container (Assignment 4's copy refused paths outside the repository and `/work`). A Terminal-Bench task's container has internet access on a network of its own and the task's own CPUs and memory, as in Terminal-Bench's own harness, Harbor. Once a task ends, your agent cannot reach its container, from another task's container either. Assignment 4's tasks have no network, as before. If you rewrite the server, it must listen on the `--port` that `run_all.py` gives it, since a task may use other ports itself. One `/exec` call runs for at most 900 seconds: that is `MAX_TIMEOUT_S` in your own `src/sandbox_server.py`, and you may change it. A command that starts a background process must redirect the process's output and input, as in `cmd > /tmp/cmd.log 2>&1 < /dev/null &`. Otherwise `/exec` waits 10 seconds for the process to close its output, then returns only the output printed so far.
- **Git history.** In an Assignment 4 task, the repository holds only the task's base commit, as after `git clone --depth 1`, so `git log` shows one commit. `prepare_images.sh` builds these images, `cs2680-a5-nohist:<instance id>`, from the task images, offline and in a few seconds each. The tests still run on the original images. The leaderboard does the same.
- **Results.** After a run, `run_all_results.md` and `results.json` list each task's result, and `gradings/<task>/` holds its test output. `run_all.py` prints the run's end-to-end time, and `run_all_results.md` records it: from the run's start to the end of its last task, at most the run's limit, as the leaderboard measures it. With `--limit N`, the results list only the N tasks the run could open. A task whose container fails to start, such as one that asks for more CPUs than the machine has, is listed as failed to start, with Docker's error, and the run goes on. If your agent crashes, `run_all.py` says so, shows the end of `run_logs/agent.log` and exits with status 1.
- **New names.** The session packager writes `assignment5/a5-sessions.tar.gz`.

## Prerequisites

As in Assignment 4, a Linux x86_64 machine with Docker. In addition:

- **Disk.** Terminal-Bench 2.0's images take about 49 GB to download and about 80 GB on disk, or about 130 GB with the containerd image store (`docker info` shows `io.containerd.snapshotter.v1`). Assignment 4's take about 40 GB to download and about 105 GB on disk, or about 145 GB with the containerd image store.
- **CPU and memory.** Each Terminal-Bench task's container gets the task's CPUs (1-4) and memory (2-8 GB). The machine needs at least 4 CPUs: Docker refuses a container that asks for more CPUs than the machine has, and two tasks ask for 4. All 89 tasks at once reserve 98 CPUs and 222 GB, so on a smaller machine keep fewer tasks open (`A3_MAX_LIVE` caps them). Each of Assignment 4's tasks gets 1 CPU and 4 GB.
- **Network.** The machine must reach the cluster's login node, as in Assignment 4, and Terminal-Bench's task containers must reach the internet.

## Pointing the harness at your server

Start your server on the cluster as in Assignment 4, but from Assignment 5's course environment, `$A5`, which serves the model as `cs2680-model`. Set it in every shell on the cluster, and use `$A5` wherever Assignment 4 uses `$A4`:

```bash
export A5=/shared/courseSharedFolders/176914outer/176914/a5   # the course environment
```

The `A4_*` variables that `launch.sh` gets, such as `$A4_PORT`, keep their names, and so does the folder `~/a4`.

As in Assignment 4: open the [SSH tunnel](https://cs2680.com/computing/cluster.html#tunnel) to your server's node on the Docker bridge address, then:

```bash
ssh -f -N -o ExitOnForwardFailure=yes -L 172.17.0.1:30000:<node>:30000 cs2680   # <node>: your server's node
export A3_API_UPSTREAM=http://172.17.0.1:30000          # an origin: no /v1
export CS2680_API_KEY=$(ssh cs2680 cat a4/serve.key)    # the same key as your server
export CS2680_MODEL_EXPERT=cs2680-model CS2680_MODEL_STANDARD=cs2680-model CS2680_MODEL_STARTER=cs2680-model
curl -s -H "Authorization: Bearer $CS2680_API_KEY" $A3_API_UPSTREAM/v1/models   # should list cs2680-model
bash evaluation_scripts/prepare_images.sh             # once; --tasks tb2 or --tasks a4 prepares one set
python3 evaluation_scripts/run_all.py --limit 0       # preflight (add --tasks a4 for Assignment 4's tasks)
python3 evaluation_scripts/run_all.py                 # Terminal-Bench 2.0
python3 evaluation_scripts/run_all.py --tasks a4      # the 25 tasks of Assignment 4's starter
```

A passing preflight prints `EGRESS OK`, then `preflight k: ... ok` for every task. Its sandbox check expects internet access in a Terminal-Bench task's container and none in an Assignment 4 task's. Your server serves the model under the name `cs2680-model` even if you change the model, so the model ids above do not change. Your agent must take the name from these `CS2680_MODEL_*` variables. Do not hard-code Assignment 4's name. Your server no longer lists it, and some engines, such as vLLM, reject a request for it. Copy your Assignment 4 `src/` over this folder's `src/`, but keep this folder's `src/sandbox_server.py` or remove the path limit from yours.

## engine/ and launch.sh

`engine/` is the part of your submission that starts your server. This folder's copy is the basic SGLang setup:

- `engine.json` names the framework, `sglang`, and the model, `nvidia/Qwen3.6-35B-A3B-NVFP4` at the revision the leaderboard's catalog lists. You may change the model; the assignment page says how.
- `flags.txt` is a copy of `$A5/basic-sglang-flags.txt`, the basic setup's flags.
- `launch.sh` starts the server. Its one working line is `exec a4-serve --flags-file "$A4_ENGINE_DIR/flags.txt"`.

If you change SGLang, your changes go in `engine/sglang.patch` too, as Part 4 of Assignment 4 says. The template is for SGLang; the leaderboard's [engine conventions page](https://leaderboard.cs2680.com/a5/engines.html) gives the conventions for vLLM.

To use another framework, build it into an environment folder under `/shared/courseSharedFolders/176914outer/176914/a4-models/<your cluster username>/`, set `"engine"` to `"other"` in `engine.json`, and add an `"env"` key with the folder's path. Your `launch.sh` then starts the server from that folder. [Your own engine](https://leaderboard.cs2680.com/a5/engines.html#own-engine) on the engine conventions page has the folder's rules, a tested example, and how to test it. The course does not fix problems inside your own engine.

The leaderboard runs `launch.sh` with bash on a fresh RTX PRO 4500 node, in place of `serve.sh` or your own batch script, so `#SBATCH` lines in it have no effect. It runs inside the course's sandbox, which has no network and hides `/shared`, `/scratch` and every home folder. Nothing under `$A5` or `~/a4` is there, so a `launch.sh` that calls `$A5/bin/serve.sh` fails on the leaderboard. For `sglang`, the sandbox gives `launch.sh` the course environment, the course's helper `a4-serve` on `PATH`, SGLang v0.5.20 with your patch on `PYTHONPATH`, the model's local copy in `HF_HOME` with downloads turned off, and the variables `A4_ENGINE_DIR` (this folder), `A4_MODEL_PATH`, `A4_SERVED_MODEL_NAME`, `A4_HOST`, `A4_PORT` and `A4_KEY_FILE`. The comments in `launch.sh` list every variable it gets. For `other`, `launch.sh` runs from the node's own shell, without `a4-serve` or `PYTHONPATH`, and gets `A4_ENV_DIR`, the path of your environment folder, which is the one part of `/shared` it can read. [Your own engine](https://leaderboard.cs2680.com/a5/engines.html#own-engine) lists what it gets.

The server must listen on `127.0.0.1:$A4_PORT`, require the key in `$A4_KEY_FILE` on every request (only `/health` and `/metrics` may answer without it), serve exactly one model, named `$A4_SERVED_MODEL_NAME`, and be ready within 45 minutes of the start of the grading job. `a4-serve` does this for SGLang and vLLM: it starts the engine with the flags in the file and then adds `--model-path`, `--served-model-name`, `--host`, `--port` and `--api-key` from those variables.

To test `launch.sh` as the leaderboard runs it, first copy this folder's `engine/` to `~/a4/engine` on the cluster (from this folder: `scp -r engine cs2680:a4/`, which also replaces the cluster's `flags.txt` with this folder's). Then, in a job on a GPU node after `setup.sh` (`setup.sh --vllm` for `vllm`, `setup.sh --weights-only` for `other`), run:

```bash
bash $A5/bin/check-submission.sh --launch      # tests ~/a4/engine; --launch DIR tests DIR/engine
```

Before you zip your submission, copy `~/a4/engine` back over this folder's `engine/` (from this folder: `scp -r 'cs2680:a4/engine/*' engine/`), so that the leaderboard runs what you tested.

## Session logs

Before you start work with Claude Code, run `bash init.sh` once from this folder. It copies `package_agent_sessions.py` to the root of your course repository and writes `CLAUDE.local.md` there, replacing Assignment 4's, so that Claude Code commits the repository's session logs with every turn, in `agent-sessions.tar.gz` at the repository root. For the submission, run `python3 package_agent_sessions.py` from the repository root, which writes `assignment5/a5-sessions.tar.gz`. Commit that file to your course repository with your code: it is part of your submission. The packager replaces the course server key with `REDACTED` in the files it archives: the value of `CS2680_API_KEY` when it is set, the contents of `~/a4/serve.key` when that file exists, and a 32-hex-digit key after `Bearer` or `api_key`.

`assignment5/.gitignore` keeps the harness's cache, `assignment5/.cache/`, out of your commits. The cache holds Terminal-Bench's tests and solutions and SWE-bench Pro's reference patches. `starter_code/.gitignore` covers what `run_all.py` writes in this folder.

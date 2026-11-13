#!/usr/bin/env python3
"""run_all.py — DISPATCHER runner of the CS2680 Assignment 5 harness (host side).

    export A3_API_UPSTREAM=http://<address>:<port>   # your server (../README.md)
    export CS2680_API_KEY=...         # your server's key, and the model ids (../README.md)
    python3 evaluation_scripts/run_all.py [--tasks tb2|a4] [--limit N]

  --tasks tb2     Terminal-Bench 2.0's 89 tasks (default), from $TERMINAL_BENCH_DIR
  --tasks a4      the 25 tasks of Assignment 4's starter (agent_task_input.json)
  --limit N       only the first N tasks (of the run's order) can be opened, and the results list those N alone
                  (0 = preflight: start the agent, start and health-check every task's sandbox, check egress, stop)

  CS2680_*        every CS2680_* variable is passed into the agent container as is, except
                  CS2680_BASE_URL: the agent gets http://a3proxy_<run>:3128/v1 (the egress proxy)
  A3_API_UPSTREAM your server, which the egress proxy forwards to (required)

  Session id: every model request of a run carries <First>_<Last>_<UTC start time> (the egress
  proxy adds it; dispatcher/session.py), with your name from dispatcher/student_name.json: fill it
  in, or run this once in a terminal and answer. The id is printed and kept in run_logs/session_id.
  A3_SESSION_ID   the grader's id for a grading (sub_<n>_<UTC>[_c<k>]), used instead of the name

  A3_TASK_ORDER   fixed (default) or random: the order next_task hands the tasks out in. fixed: the task
                  list's own order, k = the task's place in it; random (the leaderboard's grader sets it, for
                  both task sets): a new order for every run (random.SystemRandom, from os.urandom), so the
                  index k a task is handed out under says nothing about which task it is. Either way the
                  order is recorded in $A3_HOSTLOG/task_order.json, and the results (results.json,
                  run_all_results.md, results.tsv, gradings/<key>/) name each task by its key
  A3_MAX_LIVE     tasks (sandboxes) live at once, default 0: no limit (every task may be live)
  A3_MAX_GRADING  gradings running at once, default 4
  A3_TB_SUBNETS   the addresses of the Terminal-Bench tasks' own networks, a /28 of it per task, default
                  10.213.0.0/16; set another private range if your machine already uses those addresses
  A3_EVAL_TIMEOUT seconds per grading of an Assignment 4 task, default 2100 (a hung test suite = failed);
                  a Terminal-Bench task's grading has its own task.toml limit ([verifier] timeout_sec)
  A3_RUN_LIMIT_S  seconds for the whole run, counted from its start (A3_CLOCK_FROM); default the
                  leaderboard's: 21600 (6 h) for --tasks tb2, 14400 (4 h) for --tasks a4; 0 = no limit on
                  the whole run, for local experiments (see "time limits" below)
  A3_CLOCK_FROM   start (default) or first_task: when the whole-run clock starts
  A3_DOCKER       docker command; default: `docker` if it works, else `sudo -n -E docker` (asks
                  for the sudo password once at the start and keeps sudo alive during the run)
  A3_CACHE        host-only cache dir, default <dir holding this harness>/.cache/cs2680_a3 — OUTSIDE
                  the harness, so the agent container (which mounts the harness) never sees it:
  A3_ASSETS         portable_python/, portable_python_musl/, wheels/, images/ (prepare_images.sh),
                    default $A3_CACHE/assets
  A3_HOSTLOG        host-only records (results, task entries, patch snapshots), default $A3_CACHE/hostlogs;
                    clock_start (epoch: when the whole-run clock started) and agent_over (`<epoch> <why>`, why
                    end | limit | agent_died: when the agent's request loop ended) are written there for the grader
  TERMINAL_BENCH_DIR  Terminal-Bench 2.0's tasks (instruction.md, task.toml, tests/ per task; prepare_images.sh
                    fetches them), default $A3_CACHE/terminal-bench-2
  SWEBENCH_PRO_OS   the checkout with Assignment 4's tasks' tests (prepare_images.sh fetches it),
                    default $A3_CACHE/SWE-bench_Pro-os

The AGENT drives the task flow (see madsServe.py / dispatcher.py). This script starts the
infrastructure, then serves the agent's requests one at a time and enforces the rules:

  next_task   start sandbox k (next index: 0, 1, 2, ... in the run's order, A3_TASK_ORDER), answer
              {task=k, instruction, sandbox_url, workdir, time_limit_s}; error when A3_MAX_LIVE are
              live; task=null at the end. time_limit_s is the most seconds the task may stay open from
              this answer: min(its own limit, what is left of A3_RUN_LIMIT_S); an Assignment 4 task has
              no limit of its own, so it gets what is left of the run; null only when no limit applies
              (an Assignment 4 task with A3_RUN_LIMIT_S=0)
  done k      task k ends at once: the agent can no longer reach its sandbox, and its final state is
              graded IN THE BACKGROUND, never reported to the agent. A Terminal-Bench task: its
              tests run in its own container (grade_tb.sh), as in Harbor. An Assignment 4 task: the
              repository's changes since the task's base commit, staged, committed or neither
              (snapshot_diff: Assignment 4's `git add -N . && git diff` when nothing was staged or
              committed, `git diff <base commit>` when something was; --binary when a file is binary)
              are graded on a pristine container with no network (evaluate_one.sh; the verdict is
              decided on the host, verdict.py).
  time limits by default the leaderboard's. Terminal-Bench 2.0: 6 h for the whole run, and each task
              its own limit (task.toml [agent] timeout_sec, 10-200 min) from when it was opened.
              Assignment 4's tasks, as in Assignment 4: 4 h for the whole run and no limit per task;
              every task may be open at once. A task still open at its own limit ends as if done(k)
              had been called. A3_RUN_LIMIT_S after the run started, the run is stopped: `shutdown`
              is published (the agent's next dispatcher call raises DispatcherShutdown), every task
              still open ends as by done(k), tasks never opened count as not solved. Either way the
              task is graded on its state at that moment (a Terminal-Bench task that waits for a
              grading slot is paused until its grading starts). After a task's own limit a later
              done(k) answers {ok, timed_out: true}; after the run's limit no call is answered.
              Gradings are not the agent's time: they finish after the limit.

Results live in this process's memory (Task.result) and in $A3_HOSTLOG, never in files the agent
container can reach; the repo-root copies (results.json, run_all_results.md, gradings/,
model_patch_<key>.diff for Assignment 4's tasks) are written after the agent container is gone.
run_all_results.md also gives the run's end-to-end time as the leaderboard computes it (end_to_end),
and why a task's sandbox did not start (Docker's error). Exit status: 0; 1 when the preflight failed
or the agent crashed (madsServe.py exited non-zero: the end of run_logs/agent.log is printed); 130
when the run was interrupted.
Never handed to the agent: the task's name or instance id, its image, its tests.

Infrastructure: egress proxy a3proxy_<run> (the only container with internet besides Terminal-Bench
task containers; a reverse proxy that forwards /v1/... to A3_API_UPSTREAM itself, no tunnels), agent
container a3agent_<run> on two --internal networks with CS2680_BASE_URL=http://a3proxy_<run>:3128/v1
(its only way out), sandbox a3sbx_<run>_<k> per live task on the private network, running
src/sandbox_server.py with a bind-mounted portable CPython. Both internal networks are created with
no address of this host on them (create_internal_network). A Terminal-Bench task's container is also
on a network of its own, a3inet_<run>_<k>, a plain bridge network with internet access, as
Terminal-Bench requires and as Harbor gives each task. No other task's container is on it, so once
task k has ended and left the private network, nothing the agent runs can reach it, from another
task's container included. Its subnet is a /28 of A3_TB_SUBNETS, and its bridge interface is named
a3i<9 hex digits of sha1(<run>)><k in 3 digits> (tb_bridge), so that a grading machine's firewall can
filter these networks alone, by name, and leave docker0 and the --internal networks as they are. An
Assignment 4 task's container has no internet, and its gradings run with no network.

Boundary with the agent container: it mounts this folder READ-ONLY at /madsServe; only .tasks/ and
madsServe_logs/ are writable mounts. run_logs/ reads as an empty folder there, and the grader's
grader_run.log (this script's output) as an empty file: sequence.log, task_opened.tsv and that output
name the task behind each k, which would undo a random order (A3_TASK_ORDER); the task lists read as
{} (hidden.json). The host never runs a file from that folder during or after the
run (the grading scripts and the task list they read are copied to $A3_HOSTLOG before the agent
starts and run from there), touches .tasks/ only through a directory fd without following symlinks,
and removes symlinks and special files from both writable folders afterwards.
"""

import argparse
import ast
import hashlib
import ipaddress
import json
import os
import random
import re
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
import urllib.parse
from dataclasses import dataclass
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
TASKS_JSON = "evaluation_scripts/agent_task_input.json"
SEQ = ".tasks/seq"
CACHE = os.environ.get("A3_CACHE", os.path.join(os.path.dirname(ROOT), ".cache", "cs2680_a3"))
PRO_OS = os.environ.get("SWEBENCH_PRO_OS", os.path.join(CACHE, "SWE-bench_Pro-os"))
V2 = PRO_OS + "/v2/tasks"
TB_DIR = os.environ.get("TERMINAL_BENCH_DIR", os.path.join(CACHE, "terminal-bench-2"))

ASSETS = os.environ.get("A3_ASSETS", os.path.join(CACHE, "assets"))
PORTABLE_PY = os.environ.get("A3_PORTABLE_PY", f"{ASSETS}/portable_python")
PORTABLE_PY_MUSL = os.environ.get("A3_PORTABLE_PY_MUSL", f"{ASSETS}/portable_python_musl")
AGENT_IMAGE = os.environ.get("A3_AGENT_IMAGE", "cs2680-a3-agent")
NOHIST = "cs2680-a5-nohist"   # an Assignment 4 task's image with only its base commit left in .git: prepare_images.sh, step 6
SBX_CPUS = os.environ.get("A3_SBX_CPUS", "1"); SBX_MEM = os.environ.get("A3_SBX_MEM", "4g")   # Assignment 4's tasks
SBX_PORT = 19473; PROXY_PORT = 3128   # SBX_PORT: the sandbox server's port in every task container, away from the
                                      # ports tasks use themselves (headless-terminal's tests serve on 8000)
API_UPSTREAM = os.environ.get("A3_API_UPSTREAM", "")
MAX_LIVE = int(os.environ.get("A3_MAX_LIVE", "0"))    # 0: no limit
MAX_GRADING = int(os.environ.get("A3_MAX_GRADING", "4"))
EVAL_TIMEOUT = int(os.environ.get("A3_EVAL_TIMEOUT", "2100"))
RUN_LIMITS = {"tb2": 21600, "a4": 14400}   # the leaderboard's limit on the whole run: 6 h (tb2), 4 h (a4)
RUN_LIMIT_S = 0                     # the whole run, from CLOCK_FROM; 0: none. Set by main(): A3_RUN_LIMIT_S or RUN_LIMITS
CLOCK_FROM = os.environ.get("A3_CLOCK_FROM", "start")               # from the run's start (or first_task)
if CLOCK_FROM not in ("first_task", "start"):
    sys.exit(f"error: A3_CLOCK_FROM must be first_task or start, not {CLOCK_FROM!r}")
TASK_ORDER = os.environ.get("A3_TASK_ORDER", "fixed")               # the order next_task hands the tasks out in
if TASK_ORDER not in ("random", "fixed"):
    sys.exit(f"error: A3_TASK_ORDER must be random or fixed, not {TASK_ORDER!r}")
T0 = None                                                           # when the run started (main, before the agent)

RUN = f"{int(time.time())}_{os.getpid()}"
NET, EGRESS = f"a3sbx_{RUN}", f"a3egress_{RUN}"
# Each Terminal-Bench task's container has a network of its own with internet access, a3inet_<run>_<k> (tb_net), whose
# subnet is a /28 of TB_SUBNETS (create_task_network)
TB_SUBNETS = os.environ.get("A3_TB_SUBNETS", "10.213.0.0/16")
try:
    if ipaddress.ip_network(TB_SUBNETS).version != 4 or ipaddress.ip_network(TB_SUBNETS).prefixlen > 28:
        raise ValueError
except ValueError:
    sys.exit(f"error: A3_TB_SUBNETS must be an IPv4 network of /28 or more addresses, such as 10.213.0.0/16, not {TB_SUBNETS!r}")


def tb_net(k: int) -> str:
    return f"a3inet_{RUN}_{k}"


def tb_bridge(k: int) -> str:
    """Task k's bridge interface: a3i + 9 hex digits of sha1(<run>) + k in 3 digits (15 characters, the most a Linux
    interface name may have), named so that a grading machine's firewall matches Terminal-Bench's internet networks
    alone (-i a3i+) and leaves docker0 (where the egress proxy reaches A3_API_UPSTREAM) and the --internal networks
    (br-<id>) as they are."""
    return "a3i" + hashlib.sha1(RUN.encode()).hexdigest()[:9] + f"{k:03d}"


AGENT, PROXY = f"a3agent_{RUN}", f"a3proxy_{RUN}"
API_BASE_URL = f"http://{PROXY}:{PROXY_PORT}/v1"   # the agent's CS2680_BASE_URL
HOSTLOG = os.path.join(os.environ.get("A3_HOSTLOG", os.path.join(CACHE, "hostlogs")), f"{os.path.basename(ROOT)}_{RUN}")
SCRIPTS = f"{HOSTLOG}/evaluation_scripts"   # host-only copies of the course scripts the host runs (snapshot_scripts)
GRADINGS = f"{HOSTLOG}/gradings"            # each task's grading while the run lasts (move_gradings)

# An Assignment 4 task's instruction, worded as SWE-bench Pro V2's instruction.md.
A4_INSTRUCTION = ("A code repository is available in the `{wd}` directory. Your task is to implement the changes "
                  "necessary to satisfy the following Pull Request (PR) description:\n\n<pr_description>\n{body}\n"
                  "</pr_description>\n\nConstraints:\n\n* Do not reference, look up, or copy existing solutions, "
                  "external PRs, or online workarounds. The implementation must be entirely your own independent work.\n")


# --- helpers -------------------------------------------------------------------------

def log(msg: str):
    line = f"== {msg}"
    try:
        print(line, file=sys.stderr, flush=True)
    except OSError:      # the terminal is gone (closed window = SIGHUP): keep going, the log file still gets it
        pass
    with open("run_logs/sequence.log", "a") as f:
        f.write(line + "\n")


DOCKER = ["docker"]   # set by resolve_docker(); every sh("docker", ...) goes through it
SESSION = None        # set by main(): this run's session id (dispatcher/session.py)
AGENT_EXIT = None     # set by cleanup(): the agent container's exit status, madsServe.py's (None: still running then)


def resolve_docker():
    """Plain `docker` if this user may use it; else `sudo -n -E docker`: the password is asked
    once here, sudo is kept alive by a background thread (a later prompt would stall a run whose
    output is captured), and -E keeps the environment (`docker run -e CS2680_...` reads it).
    The choice is exported as A3_DOCKER for evaluate_one.sh."""
    global DOCKER
    if os.environ.get("A3_DOCKER"):
        DOCKER = os.environ["A3_DOCKER"].split()
    elif not shutil.which("docker"):
        sys.exit("error: docker not found on PATH (see Step 0 of the project description)")
    elif subprocess.run(["docker", "info"], capture_output=True).returncode == 0:
        DOCKER = ["docker"]
    elif shutil.which("sudo"):
        log("docker is not usable without root here: using sudo (asks for your password once)")
        if subprocess.run(["sudo", "-v"]).returncode != 0:
            sys.exit("error: sudo failed; add yourself to the docker group instead: sudo usermod -aG docker $USER")
        if subprocess.run(["sudo", "-n", "-E", "docker", "info"], capture_output=True).returncode != 0:
            sys.exit("error: `sudo -E docker info` failed; add yourself to the docker group: sudo usermod -aG docker $USER")
        DOCKER = ["sudo", "-n", "-E", "docker"]
        def keep_sudo_alive():
            while True:
                time.sleep(60)
                subprocess.run(["sudo", "-n", "-v"], capture_output=True)
        threading.Thread(target=keep_sudo_alive, daemon=True).start()
    else:
        sys.exit("error: docker is not usable by this user and there is no sudo: sudo usermod -aG docker $USER")
    os.environ["A3_DOCKER"] = " ".join(DOCKER)


def sh(*cmd, check=True, capture=True, text=True, **kw) -> subprocess.CompletedProcess:
    if cmd and cmd[0] == "docker":
        cmd = (*DOCKER, *cmd[1:])
    return subprocess.run(list(cmd), check=check, text=text,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None, **kw)


def running(name: str) -> bool:
    r = sh("docker", "inspect", "-f", "{{.State.Running}}", name, check=False)
    return r.returncode == 0 and r.stdout.strip() == "true"


def span(s: int) -> str:
    """A limit in seconds as people read it: hours when it is a whole tenth of an hour (6 h, 1.5 h), else seconds."""
    return f"{s / 3600:g} h" if s % 360 == 0 else f"{s} s"


def have_image(img: str) -> bool:
    return sh("docker", "image", "inspect", img, check=False).returncode == 0


# --- the agent-writable folders ----------------------------------------------------------
# .tasks/ and madsServe_logs/ are the only host folders the (root) agent container can write. Any
# entry in them may be a symlink to a host path or a device node, so the host never opens a path
# there: it works relative to the fd of .tasks/seq (opened before the agent starts), with
# O_NOFOLLOW, and reads plain files only. madsServe_logs/ is not read during the run.

SEQ_FD = -1


def open_task_dirs():
    global SEQ_FD
    SEQ_FD = os.open(SEQ, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)


def exists_at(dir_fd: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
        return True
    except OSError:
        return False


def open_plain(dir_fd: int, name: str):
    """`name` in dir_fd opened for binary reading; None if missing, a symlink or not a plain file."""
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dir_fd)
    except OSError:
        return None
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        return None
    return os.fdopen(fd, "rb")


def write_at(dir_fd: int, name: str, data: bytes):
    """Atomically replace `name` in dir_fd (a symlink there is replaced, never followed)."""
    tmp = f".{name}.{os.urandom(6).hex()}.tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644, dir_fd=dir_fd)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    os.replace(tmp, name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)


def seq_json(name: str, obj):
    write_at(SEQ_FD, name, json.dumps(obj).encode())


def drop_links():
    """After the agent container is gone: remove every symlink and special file (fifo, socket,
    device node) it left in its writable folders, so whatever reads or uploads them later only
    finds plain files."""
    for top in (".tasks", "madsServe_logs"):
        for root, dirs, files in os.walk(top):
            for name in dirs + files:
                p = os.path.join(root, name)
                try:
                    m = os.lstat(p).st_mode
                    if not (stat.S_ISREG(m) or stat.S_ISDIR(m)):
                        os.unlink(p)
                except OSError:
                    pass


def move_gradings():
    """After the agent container is gone, also when the run was stopped: each task's grading
    (test logs, test names, expected values) from GRADINGS, which the agent container never mounts,
    to gradings/<key>/ in this folder."""
    if not os.path.isdir(GRADINGS):
        return
    os.makedirs("gradings", exist_ok=True)
    for key in sorted(os.listdir(GRADINGS)):
        src, dst = os.path.join(GRADINGS, key), os.path.join("gradings", key)
        try:
            if os.path.islink(src) or not os.path.isdir(src):
                continue
            if os.path.lexists(dst):
                log(f"gradings/{key} already exists; that task's grading stays in {src}")
                continue
            shutil.move(src, dst)
        except OSError as e:
            log(f"grading of task {key} not moved to gradings/ ({e}); it stays in {src}")
    try:
        os.rmdir(GRADINGS)
    except OSError:
        pass


def snapshot_scripts():
    """Copy the course scripts the host runs (evaluate_one.sh with its verdict.py, grade_tb.sh) and the
    task list they read to the host-only $A3_HOSTLOG before the agent starts; they run from there,
    never from the folder the agent container mounts."""
    os.makedirs(SCRIPTS, exist_ok=True)
    for f in ("evaluate_one.sh", "verdict.py", "grade_tb.sh", "agent_task_input.json"):
        shutil.copy(f"evaluation_scripts/{f}", f"{SCRIPTS}/{f}")


def sbx(k: int) -> str:
    return f"a3sbx_{RUN}_{k}"


def read_toml(path: str) -> dict:
    """task.toml as nested dicts: tomllib when there is one (Python 3.11+), else the subset the task
    files use ([section] headers; key = number, string or boolean)."""
    try:
        import tomllib
        with open(path, "rb") as f:
            return tomllib.load(f)
    except ImportError:
        pass
    data, cur = {}, None
    for line in open(path):
        line = line.split("#", 1)[0].strip() if not line.lstrip().startswith(("'", '"')) else line.strip()
        m = re.fullmatch(r"\[([A-Za-z0-9_.-]+)\]", line)
        if m:
            cur = data
            for part in m.group(1).split("."):
                cur = cur.setdefault(part, {})
            continue
        m = re.fullmatch(r"([A-Za-z0-9_-]+)\s*=\s*(.+)", line)
        if m and cur is not None:
            v = m.group(2).strip()
            if v[:1] in "\"'":
                v = v[1:-1]
            elif v in ("true", "false"):
                v = v == "true"
            else:
                try:
                    v = float(v) if "." in v else int(v)
                except ValueError:
                    continue
            cur[m.group(1)] = v
    return data


@dataclass
class Task:
    k: int
    key: str
    kind: str                        # "tb2" (Terminal-Bench 2.0) or "a4" (Assignment 4's tasks)
    entry: dict                      # a4: the agent_task_input.json entry; tb2: the task's task.toml
    instruction: str = ""            # tb2: instruction.md; a4: built from the entry when the task opens
    time_limit_s: Optional[int] = None   # tb2: the task's own limit (task.toml); a4: None, no limit per task
    place: int = 0                   # the task's place in the task list's own order (k is its place in the run's)
    image: str = ""                  # the sandbox's image
    cpus: str = SBX_CPUS
    memory: str = SBX_MEM
    tests_dir: str = ""              # tb2: the task's tests/ folder (host only)
    verifier_timeout: int = EVAL_TIMEOUT
    live: bool = False
    ended: bool = False
    how: str = ""                    # done | time limit | run limit | end of run
    wd: str = "/app"
    t_start: float = 0.0
    t_end: float = 0.0
    result: Optional[int] = None     # 1 solved, 0 not
    detail: str = ""                 # a4: "<failed>/<total> tests failing"
    grading: Optional[subprocess.Popen] = None
    grading_t0: float = 0.0
    queued: bool = False             # waiting for a grading slot
    patch: str = ""                  # a4: the host-only snapshot of the final diff
    start_error: str = ""            # why its sandbox did not start (Docker's error): host only, in the results

    @property
    def iid(self): return self.entry.get("instance_id", self.key)


# --- setup ----------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--tasks", choices=("tb2", "a4"), default="tb2",
                   help="tb2: Terminal-Bench 2.0 (default); a4: the 25 tasks of Assignment 4's starter")
    p.add_argument("--limit", type=int, default=-1)
    return p.parse_args()


def preconditions():
    if not API_UPSTREAM:
        sys.exit("error: export A3_API_UPSTREAM first, the address of your server as the agent machine's containers reach it (README.md)")
    u = urllib.parse.urlsplit(API_UPSTREAM)
    if u.scheme not in ("http", "https") or not u.hostname or u.path not in ("", "/") or u.query or u.fragment:
        sys.exit(f"error: A3_API_UPSTREAM must be an origin like http://172.17.0.1:30000, with no path such as /v1, not {API_UPSTREAM!r}")
    if u.hostname in ("localhost", "::1") or u.hostname.startswith("127."):
        sys.exit("error: A3_API_UPSTREAM cannot be localhost: the egress proxy runs in a container, whose localhost is its own; "
                 "use the address your tunnel listens on for the containers (README.md)")
    if not os.environ.get("CS2680_API_KEY"):
        sys.exit("error: export CS2680_API_KEY first")
    for d in (PORTABLE_PY, PORTABLE_PY_MUSL):
        if not os.access(f"{d}/bin/python3", os.X_OK):
            sys.exit(f"error: no portable python at {d} (set A3_ASSETS / A3_PORTABLE_PY / A3_PORTABLE_PY_MUSL)")
    if os.path.realpath(HOSTLOG).startswith(os.path.realpath(ROOT) + os.sep):
        sys.exit("error: A3_HOSTLOG must be outside this folder (the agent container mounts it)")
    old = [p for p in os.listdir(".") if p.startswith("model_patch_") or p in ("madsServe_logs", "results.json", "gradings", "run_all_results.md")]
    old = [p for p in old if not (p == "madsServe_logs" and os.path.isdir(p) and not os.listdir(p))]   # every run makes one
    if old:
        sys.exit(f"error: outputs of a previous run are still here ({', '.join(old[:3])}...); move them first")


def load_tb2() -> list:
    if not os.path.isdir(TB_DIR):
        sys.exit(f"error: no Terminal-Bench tasks at {TB_DIR}: run evaluation_scripts/prepare_images.sh (or set TERMINAL_BENCH_DIR)")
    tasks = []
    for name in sorted(os.listdir(TB_DIR)):
        d = os.path.join(TB_DIR, name)
        if not os.path.isfile(f"{d}/task.toml") or not os.path.isfile(f"{d}/tests/test.sh"):
            continue
        cfg = read_toml(f"{d}/task.toml")
        env, agent, verifier = cfg.get("environment", {}), cfg.get("agent", {}), cfg.get("verifier", {})
        if not env.get("docker_image"):
            sys.exit(f"error: {d}/task.toml names no docker_image")
        mem = env.get("memory") or (f"{int(env['memory_mb'])}m" if env.get("memory_mb") else "2g")
        tasks.append(Task(len(tasks), name, "tb2", cfg, place=len(tasks), instruction=open(f"{d}/instruction.md").read(),
                          time_limit_s=int(agent.get("timeout_sec", 900)), image=env["docker_image"],
                          cpus=str(env.get("cpus", 1)), memory=str(mem), tests_dir=f"{d}/tests",
                          verifier_timeout=int(verifier.get("timeout_sec", 900))))
    if not tasks:
        sys.exit(f"error: no Terminal-Bench tasks found in {TB_DIR}")
    return tasks


def load_a4() -> list:
    """Assignment 4's tasks as Assignment 4 ran them: no time limit per task, only the run's (A3_RUN_LIMIT_S). The agent
    works in the task's NOHIST image; the grading uses the image it was made from (evaluate_one.sh)."""
    return [Task(k, key, "a4", entry, place=k, image=f"{NOHIST}:{entry['instance_id']}")
            for k, (key, entry) in enumerate(json.load(open(TASKS_JSON)).items())]


def a4_instruction(t: Task) -> str:
    parts = [t.entry.get("problem_statement", "").strip()]
    for title, field in (("Requirements", "requirements"), ("New Interfaces", "interface")):
        if t.entry.get(field, "").strip():
            parts.append(f"## {title}\n{t.entry[field].strip()}")
    return A4_INSTRUCTION.format(wd=t.wd, body="\n\n".join(parts))


def load_tasks(kind: str, limit: int):
    """The tasks in the order next_task hands them out, k = 0, 1, ... (A3_TASK_ORDER): the list's own, or random, a new
    order for every run. The order goes to the host-only task_order.json ({k, key} per task, in it)."""
    tasks = load_tb2() if kind == "tb2" else load_a4()
    if TASK_ORDER == "random":
        random.SystemRandom().shuffle(tasks)
        for k, t in enumerate(tasks):
            t.k = k
    os.makedirs(f"{HOSTLOG}/tasks", exist_ok=True)
    for t in tasks:
        json.dump({"key": t.key, "kind": t.kind, "image": t.image, "time_limit_s": t.time_limit_s, "entry": t.entry},
                  open(f"{HOSTLOG}/tasks/{t.k}.json", "w"))
    with open(f"{HOSTLOG}/task_order.json", "w") as f:
        json.dump({"order": TASK_ORDER, "tasks": [{"k": t.k, "key": t.key} for t in tasks]}, f, indent=1)
    n = len(tasks) if limit < 0 else min(limit, len(tasks))
    return tasks, n


def ensure_image(img: str, tarbase: str):
    if have_image(img):
        return
    tar = f"{ASSETS}/images/{tarbase}.tar"
    if os.path.isfile(tar):
        log(f"loading {img} from {tar}")
        if sh("docker", "load", "-q", "-i", tar, check=False).returncode == 0 and have_image(img):
            return
    log(f"pulling {img}")
    if sh("docker", "pull", "-q", img, check=False).returncode != 0:
        sys.exit(f"cannot get {img} — run evaluation_scripts/prepare_images.sh (with internet) or set A3_ASSETS to a dir with images/")


def ensure_images(tasks):
    for t in tasks:
        if t.kind == "a4":
            ensure_image(t.entry["docker_image"], t.iid)                  # gradings
            if t.entry.get("sandbox_image"):
                ensure_image(t.entry["sandbox_image"], f"{t.iid}.sandbox")   # the pre-warmed sandbox (gradings too)
            if not have_image(t.image):                                   # the agent's: built, never pulled
                sys.exit(f"no {t.image} — run evaluation_scripts/prepare_images.sh --tasks a4 (it builds it offline "
                         "from the task's image)")
        else:
            ensure_image(t.image, f"tb_{t.key}")
    if not have_image(AGENT_IMAGE):
        tar = f"{ASSETS}/images/{AGENT_IMAGE}.tar"
        if os.path.isfile(tar):
            log(f"loading {AGENT_IMAGE} from {tar}"); sh("docker", "load", "-q", "-i", tar)
        else:
            if not os.path.isdir(f"{ASSETS}/wheels"):
                sys.exit(f"no {ASSETS}/wheels to build {AGENT_IMAGE} (pip download openai -d wheels)")
            log(f"building {AGENT_IMAGE} from dispatcher/agent.Dockerfile (context {ASSETS})")
            sh("docker", "build", "-q", "-f", "dispatcher/agent.Dockerfile", "-t", AGENT_IMAGE, ASSETS)


def docker_major() -> Optional[int]:
    """The Docker server's major version (28 for 28.0.1), or None when `docker version` does not say."""
    r = sh("docker", "version", "-f", "{{.Server.Version}}", check=False)
    m = re.match(r"(\d+)\.", (r.stdout or "").strip())
    return int(m.group(1)) if r.returncode == 0 and m else None


def network_failed(name: str, r: subprocess.CompletedProcess):
    """Stop the run: `docker network create <name>` failed, for the reason Docker gives (main removes what was
    started). Docker's message for exhausted address pools gets the usual remedy added."""
    why = (r.stderr or r.stdout or "").strip()[-500:] or f"exit status {r.returncode}"
    if "address pool" in why.lower():
        why += " (Docker has no address range left for another network: `docker network prune` removes the networks no container uses)"
    log(f"error: docker network create {name} failed: {why}")
    sys.exit(1)


def create_internal_network(name: str):
    """An --internal network with no address of this host on it (gateway mode "isolated", Docker 28+):
    its containers reach each other, but not this host's own services (sshd, rpcbind, ...) through a
    gateway address. The host itself only ever reaches them with `docker exec`. When that fails on a Docker older
    than 28, the network is made without it, with a warning; any other failure stops the run with Docker's error."""
    r = sh("docker", "network", "create", "--internal", "-o", "com.docker.network.bridge.gateway_mode_ipv4=isolated",
           name, check=False)
    if r.returncode == 0:
        return
    major = docker_major()
    if major is None or major >= 28:
        network_failed(name, r)
    log(f"warning: Docker {major} cannot isolate {name} from the host (that needs Docker 28+); "
        f"its containers can reach this host's own services")
    r = sh("docker", "network", "create", "--internal", name, check=False)
    if r.returncode != 0:
        network_failed(name, r)


def create_task_network(k: int) -> subprocess.CompletedProcess:
    """Terminal-Bench task k's own network, with internet access, as Harbor gives each task one: no other task's
    container is on it, so once k has ended and left the private network NET, nothing the agent runs (in another
    task's container included) can reach it. Its subnet is a /28 of TB_SUBNETS, the first one free from a place that
    depends on the run and k: a run's 89 task networks, and another run's on the same machine, would use up Docker's
    default address pools (about 30 networks). A /28 that Docker already holds is skipped."""
    subnets = list(ipaddress.ip_network(TB_SUBNETS).subnets(new_prefix=28))
    first = int(hashlib.sha1(tb_net(k).encode()).hexdigest(), 16) % len(subnets)
    for i in range(min(len(subnets), 64)):
        r = sh("docker", "network", "create", "--subnet", str(subnets[(first + i) % len(subnets)]),
               "-o", f"com.docker.network.bridge.name={tb_bridge(k)}", tb_net(k), check=False)
        if r.returncode == 0 or "overlap" not in (r.stderr or "").lower():
            break
    return r


def start_infra(kind: str):
    create_internal_network(NET)
    create_internal_network(EGRESS)
    log(f"agent {AGENT} ({AGENT_IMAGE}); networks {NET}, {EGRESS}{', and a3inet_' + RUN + '_<k> per task' if kind == 'tb2' else ''}; "
        f"API {API_BASE_URL} -> {API_UPSTREAM}; max live {MAX_LIVE or 'all'}, max grading {MAX_GRADING}")
    sh("docker", "run", "-d", "--name", PROXY, "--network", "bridge", "-v", f"{ROOT}/dispatcher:/dispatcher:ro",
       AGENT_IMAGE, "python3", "-B", "/dispatcher/egress_proxy.py", "--port", str(PROXY_PORT), "--upstream", API_UPSTREAM,
       "--session", SESSION)
    sh("docker", "network", "connect", EGRESS, PROXY)
    host_id = f"{os.getuid()}:{os.getgid()}"
    script = (
        'trap "chown -R $HOST_ID /madsServe/.tasks /madsServe/madsServe_logs 2>/dev/null" EXIT\n'
        'touch /madsServe/.tasks/seq/ready\n'
        'cd /madsServe/.tasks/trace\n'
        'python3 /madsServe/madsServe.py --log; rc=$?\n'
        'mkdir -p /madsServe/madsServe_logs && cp -r madsServe_logs/. /madsServe/madsServe_logs/ 2>/dev/null || true\n'
        'exit $rc\n')                                   # madsServe.py's exit status: 1 when Agent.run raised
    env = [*[x for v in sorted(os.environ) if v.startswith("CS2680_") and v != "CS2680_BASE_URL"
             for x in ("-e", v)],                                                            # key + model ids
           "-e", "MADSSERVE_MAX_ITERATIONS",
           "-e", f"CS2680_BASE_URL={API_BASE_URL}",     # the egress proxy: the agent's only way out
           "-e", f"HOST_ID={host_id}", "-e", "PYTHONDONTWRITEBYTECODE=1"]
    hidden = f"{HOSTLOG}/hidden.json"     # the task lists (instance ids, hidden test names) read as {} in the agent
    with open(hidden, "w") as f:
        f.write("{}\n")
    no_logs = f"{HOSTLOG}/hidden_run_logs"  # run_logs/ reads as this empty folder in the agent, and the grader's
    os.makedirs(no_logs, exist_ok=True)     # grader_run.log (this script's output) as an empty file: sequence.log,
    no_log = f"{HOSTLOG}/hidden_log"        # task_opened.tsv and that output name the task behind each k (A3_TASK_ORDER)
    open(no_log, "w").close()
    mounts = ["-v", f"{ROOT}:/madsServe:ro",                      # read-only: the agent cannot touch the course files
              "-v", f"{ROOT}/.tasks:/madsServe/.tasks", "-v", f"{ROOT}/madsServe_logs:/madsServe/madsServe_logs",
              "-v", f"{no_logs}:/madsServe/run_logs:ro",
              *(["-v", f"{no_log}:/madsServe/grader_run.log:ro"] if os.path.isfile("grader_run.log") else []),
              *[x for f in ("agent_task_input.json", "task_test.json")
                for x in ("-v", f"{hidden}:/madsServe/evaluation_scripts/{f}:ro")]]
    sh("docker", "run", "-d", "--name", AGENT, "--network", EGRESS, *mounts, *env, AGENT_IMAGE, "bash", "-c", script)
    sh("docker", "network", "connect", NET, AGENT)
    while not exists_at(SEQ_FD, "ready"):
        if not running(AGENT):
            sys.exit("agent container died during setup (run_logs/agent.log)")
        time.sleep(1)


def cleanup():
    global AGENT_EXIT
    r = sh("docker", "inspect", "-f", "{{.State.Running}} {{.State.ExitCode}}", AGENT, check=False)
    state = (r.stdout or "").split() if r.returncode == 0 else []
    if state[:1] == ["false"] and state[1:] and state[1].lstrip("-").isdigit():
        AGENT_EXIT = int(state[1])
    sh("docker", "exec", AGENT, "chown", "-R", f"{os.getuid()}:{os.getgid()}", "/madsServe/.tasks", "/madsServe/madsServe_logs", check=False)
    for name, out in ((AGENT, "agent.log"), (PROXY, "proxy.log")):
        r = sh("docker", "logs", name, check=False)
        open(f"run_logs/{out}", "w").write((r.stdout or "") + (r.stderr or ""))
    ids = sh("docker", "ps", "-aq", "--filter", f"name=^a3sbx_{RUN}_", check=False).stdout.split()
    for c in ids + [AGENT, PROXY]:
        sh("docker", "rm", "-f", c, check=False)
    names = sh("docker", "network", "ls", "--format", "{{.Name}}", check=False).stdout.split()
    for net in [NET, EGRESS] + [n for n in names if n.startswith(f"a3inet_{RUN}_")]:   # and the tasks' own (tb_net)
        sh("docker", "network", "rm", net, check=False)
    drop_links()


# --- sandboxes --------------------------------------------------------------------------

def start_sandbox(t: Task) -> str:
    """Start sandbox k; returns its working directory or '' on failure."""
    py = 'PY=/opt/agentpy/bin/python3; [ -e /lib/ld-musl-x86_64.so.1 ] && PY=/opt/agentpy_musl/bin/python3\n'
    mounts = ["-v", f"{ROOT}/src/sandbox_server.py:/sandbox/sandbox_server.py:ro",
              "-v", f"{PORTABLE_PY}:/opt/agentpy:ro", "-v", f"{PORTABLE_PY_MUSL}:/opt/agentpy_musl:ro"]
    if t.kind == "a4":
        inner = ('WD=/testbed; [ -d /testbed/.git ] || WD=/app\n' + py +
                 f'exec "$PY" -B /sandbox/sandbox_server.py --root "$WD" --port {SBX_PORT}')
        what, r = "docker run", sh("docker", "run", "-d", "--name", sbx(t.k), "--network", NET, "--cpus", t.cpus,
                                   "--memory", t.memory, "-e", "GOPROXY=off", "-e", "GOSUMDB=off", "-e", "GOTOOLCHAIN=local",
                                   *mounts, "--entrypoint", "sh", t.image, "-c", inner, check=False)
    else:   # Terminal-Bench: the image's own working directory, the task's CPUs and memory, internet access on a network
        # of its own (create_task_network), and an init as PID 1 that reaps orphaned processes, as Harbor's
        # `sh -c 'sleep infinity'` does (otherwise a daemon's exited parent stays a zombie that pgrep lists)
        wd = sh("docker", "image", "inspect", "-f", "{{.Config.WorkingDir}}", t.image, check=False).stdout.strip() or "/"
        inner = py + f'exec "$PY" -B /sandbox/sandbox_server.py --root "{wd}" --port {SBX_PORT}'
        what, r = "docker network create", create_task_network(t.k)
        if r.returncode == 0:
            what, r = "docker run", sh("docker", "run", "-d", "--init", "--name", sbx(t.k), "--network", tb_net(t.k),
                                       "--cpus", t.cpus, "--memory", t.memory, *mounts, "--entrypoint", "sh", t.image,
                                       "-c", inner, check=False)
        if r.returncode == 0:
            what, r = "docker network connect", sh("docker", "network", "connect", NET, sbx(t.k), check=False)
    if r.returncode != 0:     # the task goes out without a sandbox; why (the image names the task) stays in the host's
        t.start_error = f"{what} failed: {(r.stderr or '').strip()[-500:]}"   # log and the results
        log(f"task {t.k}: {t.start_error}")
        sh("docker", "rm", "-f", sbx(t.k), check=False)
        if t.kind != "a4":
            sh("docker", "network", "rm", tb_net(t.k), check=False)
        return ""
    probe = f"import json,urllib.request as u;print(json.load(u.urlopen('http://{sbx(t.k)}:{SBX_PORT}/health',timeout=5))['root'])"
    for _ in range(30):   # health from INSIDE the agent container: the exact path the tools use
        r = sh("docker", "exec", AGENT, "python3", "-c", probe, check=False)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
        if not running(sbx(t.k)):
            break
        time.sleep(2)
    t.start_error = f"its sandbox server did not answer /health (run_logs/sandbox_{t.k}.log)"
    return ""


def stop_sandbox(t: Task):
    r = sh("docker", "logs", sbx(t.k), check=False)
    open(f"run_logs/sandbox_{t.k}.log", "w").write((r.stdout or "") + (r.stderr or ""))
    sh("docker", "rm", "-f", sbx(t.k), check=False)
    if t.kind != "a4":      # and its own network (create_task_network)
        sh("docker", "network", "rm", tb_net(t.k), check=False)


# Run in an Assignment 4 task's container as `sh -c SNAPSHOT_SH <workdir> <base commit>`: after `git add -N .` (so new
# files count, as in Assignment 4) it prints what the task's final diff is taken against, `index` or the base commit.
# `index`: HEAD is still the task's base commit and nothing is staged, so the diff is Assignment 4's `git diff` (the
# working tree against the index), byte for byte. The base commit: the agent staged or committed changes, so the
# diff is `git diff <base>`, the working tree against the task's base commit, and those changes count too. `index`
# also when the base commit is not in the repository (the agent rewrote its history and pruned the old commits): the
# diff is then Assignment 4's, which leaves staged and committed changes out. Assignment 4's diff also leaves out a
# tracked file deleted from the working tree alone, since `git add -N .` stages its deletion; a deletion staged with
# `git rm` counts.
SNAPSHOT_SH = r'''g() { git -C "$0" -c safe.directory='*' "$@"; }
from=index
if [ -n "$1" ] && g cat-file -e "$1^{commit}" 2>/dev/null &&
   { [ "$(g rev-parse -q --verify HEAD)" != "$1" ] || ! g diff --cached --quiet; }; then from=$1; fi
g add -N . && echo "$from"'''


def snapshot_diff(t: Task) -> str:
    """An Assignment 4 task's final state: the changes in its repository since the task's base commit (the entry's
    base_commit, which every task's image has checked out), staged, committed or neither (SNAPSHOT_SH), written to a
    host-only file (never a folder the agent container mounts). Returns the file's path. The diff is taken again with
    --binary when it has a binary file (a `Binary files ... differ` line, which would apply as an empty file), so a new
    or changed binary file is graded with its content: evaluate_one.sh's `git apply` applies such a patch."""
    r = sh("docker", "exec", sbx(t.k), "sh", "-c", SNAPSHOT_SH, t.wd, t.entry.get("base_commit") or "", check=False)
    since = r.stdout.strip() if r.returncode == 0 else ""
    patch = b""
    if since:
        diff = ["docker", "exec", sbx(t.k), "git", "-C", t.wd, "-c", "safe.directory=*", "diff",
                *([] if since == "index" else [since])]
        r = sh(*diff, check=False, text=False)
        patch = r.stdout if r.returncode == 0 else b""
        if re.search(rb"^Binary files .* differ$", patch, re.M):
            r = sh(*diff[:9], "--binary", *diff[9:], check=False, text=False)
            patch = r.stdout if r.returncode == 0 else patch
    os.makedirs(f"{HOSTLOG}/patches", exist_ok=True)
    path = f"{HOSTLOG}/patches/{t.k}.diff"
    with open(path, "wb") as f:
        f.write(patch)
    return path


# --- grading (background) -----------------------------------------------------------------

def total_tests(t: Task) -> int:
    c = json.load(open(f"{V2}/{t.iid}/tests/config.json"))
    n = 0
    for f in ("fail_to_pass", "pass_to_pass"):
        v = c.get(f, "[]"); v = ast.literal_eval(v) if isinstance(v, str) else v; n += len(v)
    return n


def start_grading(t: Task):
    outdir = f"{GRADINGS}/{t.key}"     # not under ROOT: the agent container mounts it, and reads it live
    if t.kind == "a4":
        env = dict(os.environ, A3_EVAL_TIMEOUT=str(EVAL_TIMEOUT), SWEBENCH_PRO_OS=PRO_OS)   # the copy cannot find it relative to itself
        cmd = ["bash", f"{SCRIPTS}/evaluate_one.sh", t.key, t.patch, outdir]
    else:
        env = dict(os.environ)
        cmd = ["bash", f"{SCRIPTS}/grade_tb.sh", sbx(t.k), t.tests_dir, t.wd, str(t.verifier_timeout), outdir]
        if t.queued:   # paused while it waited for a grading slot (end_task)
            sh("docker", "unpause", sbx(t.k), check=False)
    t.grading = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=open("run_logs/sequence.log", "a"), text=True, env=env)
    t.grading_t0 = time.time(); t.queued = False
    log(f"task {t.k}: grading started")


def finish_grading(t: Task):
    """Called when t.grading has exited: record the result (host only, never published to the agent)."""
    out = (t.grading.stdout.read() or "").strip()
    t.result = 1 if out.endswith("1") else 0
    if t.kind == "a4":
        try:                        # the host's verdict (verdict.py), never the grading container's own lines
            v = json.load(open(f"{GRADINGS}/{t.key}/verdict.json"))
            total, passed = int(v["required"]), int(v["passed_required"])
        except (OSError, ValueError, KeyError, TypeError):   # evaluate_one.sh stopped before deciding
            total, passed = total_tests(t), 0
        if t.result == 1:
            passed = total
        t.detail = f"{total - passed}/{total} tests failing"
    else:
        stop_sandbox(t)             # graded in its own container: only now is it removed
    secs = int(time.time() - t.grading_t0)
    timed_out = os.path.exists(f"{GRADINGS}/{t.key}/TIMEOUT")
    with open(f"{HOSTLOG}/results.tsv", "a") as f:
        f.write(f"{t.k}\t{t.key}\t{t.result}\t{t.how}\t{int(t.t_end - t.t_start)}\t{secs}\n")
    log(f"task {t.k}: {'SOLVED' if t.result else 'not solved'}{' (' + t.detail + ')' if t.detail else ''} "
        f"(grading {secs}s{', TIMEOUT' if timed_out else ''})")
    t.grading = None


# --- the request loop ---------------------------------------------------------------------

class Server:
    def __init__(self, tasks, n_available):
        self.tasks = tasks; self.n_available = n_available
        self.next_k = 0; self.n = 0
        self.grade_queue = []          # tasks waiting for a grading slot
        self.t_first = None            # when the whole-run clock started: the run's start, or the first task opened
        self.limit_note = ""           # set when A3_RUN_LIMIT_S stopped the run (goes into run_all_results.md)
        open(f"{HOSTLOG}/results.tsv", "w").close()
        if CLOCK_FROM == "start":      # the clock started with the run, whether or not a task is opened
            self.t_first = T0
            if RUN_LIMIT_S > 0:
                log(f"time limit: the whole run must end within {span(RUN_LIMIT_S)} of its start, by "
                    f"{time.strftime('%H:%M:%S UTC', time.gmtime(self.t_first + RUN_LIMIT_S))}")

    # -- state helpers
    def live(self): return [t for t in self.tasks if t.live]
    def grading_now(self): return sum(1 for t in self.tasks if t.grading is not None)

    def respond(self, n: int, payload: dict):
        payload["n"] = n
        seq_json(f"resp_{n}.json", payload)

    def end_task(self, t: Task, how: str):
        """Task t ends (done(k), its time limit, the run's limit or the end of the run): the agent can
        no longer reach its sandbox, and its final state is graded in the background."""
        t.live = False; t.ended = True; t.how = how; t.t_end = time.time()
        if t.kind == "a4":
            t.patch = snapshot_diff(t)
            stop_sandbox(t)
        else:
            sh("docker", "network", "disconnect", "-f", NET, sbx(t.k), check=False)   # cut the agent off
        with open("run_logs/task_times.tsv", "a") as f:
            f.write(f"{t.k}\t{t.key}\t{t.t_start}\t{t.t_end}\t{how}\n")
        log(f"task {t.k}: ended ({how}) after {int(t.t_end - t.t_start)}s; live={len(self.live())}")
        if self.grading_now() < MAX_GRADING:
            start_grading(t)
        else:
            if t.kind != "a4":   # frozen until its grading starts, so it is graded on its state at this moment
                sh("docker", "pause", sbx(t.k), check=False)
            t.queued = True; self.grade_queue.append(t)

    # -- time limits
    def task_limits(self):
        for t in self.live():
            if t.time_limit_s is not None and time.time() - t.t_start >= t.time_limit_s:
                self.end_task(t, "time limit")

    def time_limit(self, t: Task) -> Optional[int]:
        """next_task's time_limit_s for t, just opened: the most seconds it may stay open from now, its own
        limit or what is left of A3_RUN_LIMIT_S, whichever is less; None when neither applies."""
        left = None
        if RUN_LIMIT_S > 0 and self.t_first is not None:
            left = max(0, int(self.t_first + RUN_LIMIT_S - time.time()))
        limits = [s for s in (t.time_limit_s, left) if s is not None]
        return min(limits) if limits else None

    def over_time(self) -> bool:
        """True once A3_RUN_LIMIT_S has passed since the clock started (t_first); then publishes
        `shutdown` so the agent stops (its next dispatcher call raises DispatcherShutdown)."""
        if RUN_LIMIT_S <= 0 or self.t_first is None or time.time() - self.t_first < RUN_LIMIT_S:
            return False
        open_now = [t.k for t in self.live()]
        unopened = [t.k for t in self.tasks[:self.n_available] if t.t_start == 0.0]
        since = "it started" if CLOCK_FROM == "start" else "the first task was opened"
        self.limit_note = (f"Time limit reached: the run was stopped {span(RUN_LIMIT_S)} after {since}. Tasks still open "
                           f"({', '.join(map(str, open_now)) or 'none'}) ended as if done() had been called; tasks never opened "
                           f"({', '.join(map(str, unopened)) or 'none'}) count as not solved.")
        log(self.limit_note)
        write_at(SEQ_FD, "shutdown", b"")
        for t in self.live():
            self.end_task(t, "run limit")
        return True

    # -- background gradings
    def pump_gradings(self):
        for t in self.tasks:
            if t.grading is not None and t.grading.poll() is not None:
                finish_grading(t)
        while self.grade_queue and self.grading_now() < MAX_GRADING:
            start_grading(self.grade_queue.pop(0))

    # -- requests
    def handle(self, n: int, req: dict):
        op = req.get("op"); k = req.get("k")
        t = self.tasks[int(k)] if isinstance(k, int) and 0 <= int(k) < len(self.tasks) else None
        if op == "next_task":
            if MAX_LIVE and len(self.live()) >= MAX_LIVE:
                return self.respond(n, {"ok": False, "error": f"too many live tasks ({len(self.live())}): call done(k) on one first"})
            if self.next_k >= self.n_available:
                return self.respond(n, {"ok": True, "task": None})
            t = self.tasks[self.next_k]; self.next_k += 1
            log(f"task {t.k}: {t.key} — starting sandbox from {t.image}")
            wd = start_sandbox(t)
            if not wd:
                log(f"task {t.k}: sandbox failed to start; handed over without one")
            t.live = True; t.wd = wd or "/app"; t.t_start = time.time()
            if t.kind == "a4":
                t.instruction = a4_instruction(t)
            with open("run_logs/task_opened.tsv", "a") as f:   # host-only (the agent cannot write run_logs/):
                f.write(f"{t.k}\t{t.key}\t{t.t_start}\n")      # when each task was handed out (request_log.py)
            if self.t_first is None:
                self.t_first = t.t_start
                if RUN_LIMIT_S > 0:
                    log(f"time limit: the whole run must end within {span(RUN_LIMIT_S)}, by "
                        f"{time.strftime('%H:%M:%S UTC', time.gmtime(self.t_first + RUN_LIMIT_S))}")
            handed = {"task": t.k, "instruction": t.instruction, "sandbox_url": f"http://{sbx(t.k)}:{SBX_PORT}" if wd else "",
                      "workdir": t.wd, "time_limit_s": self.time_limit(t)}
            log(f"task {t.k}: handed out with time_limit_s {handed['time_limit_s']} (own limit {t.time_limit_s})")
            return self.respond(n, {"ok": True, "task": handed})
        if op == "done":
            if t is None or t.t_start == 0.0:
                return self.respond(n, {"ok": False, "error": f"task {k} was never opened"})
            if t.ended:
                return self.respond(n, {"ok": True, "timed_out": t.how in ("time limit", "run limit")})
            self.end_task(t, "done")
            return self.respond(n, {"ok": True})
        if op in ("extract", "evaluate", "continue"):
            return self.respond(n, {"ok": False, "error": f"'{op}' is not part of Assignment 5: a task's tests run once, after done(k)"})
        return self.respond(n, {"ok": False, "error": f"unknown op '{op}'"})

    def serve(self):
        log(f"{self.n_available} task(s) available, at most {MAX_LIVE or 'all'} live at once; waiting for the agent's requests")
        while True:
            self.pump_gradings()
            self.task_limits()
            if self.over_time():
                why = "limit"; break
            if exists_at(SEQ_FD, "end"):
                why = "end"; break
            if not running(AGENT):
                log("agent container died"); why = "agent_died"; break
            f = open_plain(SEQ_FD, f"req_{self.n}.json")
            if f is None:
                time.sleep(0.5); continue
            try:
                with f:
                    req = json.loads(f.read(1 << 20))
                self.handle(self.n, req)
            except Exception as e:   # never let one bad request kill the run
                log(f"request {self.n} failed: {type(e).__name__}: {e}")
                self.respond(self.n, {"ok": False, "error": f"dispatcher error: {type(e).__name__}: {e}"})
            self.n += 1
        # the agent is over: the grader can stop the model server now (gradings need no model)
        with open(f"{HOSTLOG}/agent_over.tmp", "w") as f:
            f.write(f"{time.time()} {why}\n")
        os.replace(f"{HOSTLOG}/agent_over.tmp", f"{HOSTLOG}/agent_over")
        for t in self.live():   # what the agent left open ends now
            self.end_task(t, "end of run")
        while any(t.grading is not None for t in self.tasks) or self.grade_queue:
            self.pump_gradings(); time.sleep(1)


# --- preflight ------------------------------------------------------------------------------

def preflight(tasks) -> int:
    bad = 0
    host = urllib.parse.urlsplit(API_UPSTREAM).hostname
    probe = f'''
import os, socket
base = os.environ.get("CS2680_BASE_URL", ""); proxy = ("{PROXY}", {PROXY_PORT}); host = "{host}"; ok = True
def status(req):   # the status code the proxy answers a raw request with
    s = socket.create_connection(proxy, timeout=20)
    try:
        s.sendall(req.encode()); line = s.recv(4096).split(b"\\r\\n", 1)[0].split()
        return int(line[1]) if len(line) > 1 and line[1].isdigit() else None
    finally: s.close()
try:
    import openai
    try:   # your server, with your key: it must answer and serve every model id the agent is given
        ids = [m.id for m in openai.OpenAI(base_url=base, api_key=os.environ.get("CS2680_API_KEY", ""), max_retries=0).models.list()]
        missing = sorted({{v for k, v in os.environ.items() if k.startswith("CS2680_MODEL_") and v and v not in ids}})
        print(f'egress: your server via {{base}} -> 200, serving {{ids}}' + (f'; NOT SERVED: {{missing}}' if missing else ''))
        ok = not missing
    except openai.APIStatusError as e:
        why = {{401: "your server refused CS2680_API_KEY", 403: "your server refused CS2680_API_KEY",
               502: "the proxy cannot reach A3_API_UPSTREAM", 504: "the proxy cannot reach A3_API_UPSTREAM"}}.get(e.status_code, "")
        print(f'egress: your server via {{base}} -> HTTP {{e.status_code}} FAILED: {{why or e.message}}'); ok = False
    except openai.APIConnectionError as e: print(f'egress: OpenAI SDK via {{base}} FAILED: {{e}}'); ok = False
except ImportError: print('egress: openai not importable'); ok = False
for what, req, want in (("CONNECT github.com:443", "CONNECT github.com:443 HTTP/1.1\\r\\nHost: github.com:443\\r\\n\\r\\n", 405),
                        ("CONNECT {host}:443", "CONNECT {host}:443 HTTP/1.1\\r\\nHost: {host}:443\\r\\n\\r\\n", 405),
                        ("GET http://github.com/", "GET http://github.com/ HTTP/1.1\\r\\nHost: github.com\\r\\n\\r\\n", 403),
                        ("GET /admin", "GET /admin HTTP/1.1\\r\\nHost: {PROXY}\\r\\n\\r\\n", 403)):
    try: c = status(req)
    except OSError as e: c = type(e).__name__
    print(f'egress: {{what}} via proxy -> {{c}}', '(refused, good)' if c == want else 'NOT REFUSED'); ok &= c == want
for addr in ((host, 443), ('1.1.1.1', 443)):
    try: socket.create_connection(addr, timeout=5); print(f'egress: direct {{addr[0]}}:443 CONNECTED - agent is NOT isolated'); ok = False
    except OSError as e: print(f'egress: direct {{addr[0]}}:443 -> {{type(e).__name__}} (no route, good)')
print('EGRESS OK' if ok else 'EGRESS CHECK FAILED')
'''
    r = sh("docker", "exec", "-i", AGENT, "python3", "-", input=probe, check=False)
    open("run_logs/egress_check.log", "w").write(r.stdout + r.stderr)
    for line in r.stdout.splitlines():
        log(line)
    if "EGRESS OK" not in r.stdout:
        bad = 1
    for t in tasks:
        wd = start_sandbox(t)
        log(f"preflight {t.k}: {t.key} {'ok (working directory ' + wd + ')' if wd else 'FAILED: ' + t.start_error}")
        bad |= 0 if wd else 1
        if t.k == 0 and wd:   # an Assignment 4 task has no internet; a Terminal-Bench task has it
            chk = (f"import socket\nfor a in (('{PROXY}', {PROXY_PORT}), ('1.1.1.1', 443)):\n"
                   "    try: socket.create_connection(a, timeout=5); print('REACHABLE', a[0])\n"
                   "    except OSError: print('unreachable', a[0])\n")
            py = 'PY=/opt/agentpy/bin/python3; [ -e /lib/ld-musl-x86_64.so.1 ] && PY=/opt/agentpy_musl/bin/python3; exec "$PY" -c "$0"'
            out = sh("docker", "exec", sbx(t.k), "sh", "-c", py, chk, check=False).stdout
            proxy_seen, internet = f"REACHABLE {PROXY}" in out, "REACHABLE 1.1.1.1" in out
            if proxy_seen or internet != (t.kind == "tb2"):
                log(f"preflight: sandbox network NOT as expected: {' '.join(out.split())}"); bad = 1
            else:
                log(f"preflight: sandbox network as expected (proxy unreachable, internet {'reachable' if internet else 'unreachable'})")
        stop_sandbox(t)
    return bad


# --- results ----------------------------------------------------------------------------------

def end_to_end(t0: Optional[float], tasks) -> Optional[float]:
    """The run's end-to-end time as the leaderboard computes it: from the start of its clock (t0: the run's start by
    default, which $A3_HOSTLOG/clock_start records) to the end of its last task, at most A3_RUN_LIMIT_S (tasks still
    open at the run's limit end then, and their gradings do not count). None when no task ended."""
    ends = [t.t_end for t in tasks if t.ended]
    if t0 is None or not ends:
        return None
    end = max(ends) if RUN_LIMIT_S <= 0 else min(max(ends), t0 + RUN_LIMIT_S)
    return round(max(0.0, end - t0), 1)


def cell(text: str) -> str:
    """text as one cell of a Markdown table: on one line, with | escaped."""
    return " ".join(str(text).split()).replace("|", "\\|")


def write_results(tasks, n_available: int, note: str = "", t0: Optional[float] = None):
    """From this process's memory only, after the agent container is gone. Only the tasks this run could open are
    listed and counted: with --limit N, the first N of the run's order (k < N)."""
    shutil.copy(f"{HOSTLOG}/results.tsv", "run_logs/results.tsv")
    left_out = len(tasks) - n_available
    tasks = sorted((t for t in tasks if t.k < n_available), key=lambda t: t.place)   # in the list's order, whatever
    res = {t.key: bool(t.result) for t in tasks}                                      # the run's was
    json.dump(res, open("results.json", "w"), indent=2)
    for t in tasks:
        if t.kind == "a4" and t.patch and os.path.exists(t.patch):
            shutil.copy(t.patch, f"model_patch_{t.key}.diff")
    solved = sum(res.values())
    e2e = end_to_end(t0, tasks)
    a4 = bool(tasks) and tasks[0].kind == "a4"
    rows = []
    for t in tasks:     # k: the index the task was handed out under in this run; key: its name in the task list
        notes = ([t.detail] if t.detail else []) + (["failed to start: " + t.start_error] if t.start_error else [])
        rows.append(f"| {t.k} | {t.key} |{' ' + t.iid + ' |' if a4 else ''} {'PASS' if res[t.key] else 'FAIL'} | "
                    f"{t.how or 'never opened'} | {int(t.t_end - t.t_start) if t.ended else '-'} | {cell('; '.join(notes))} |")
    head = ("| k | task key | instance | result | ended by | seconds open | notes |" if a4 else
            "| k | task | result | ended by | seconds open | notes |")
    limit = ([f"--limit {n_available}: this run could open the first {n_available} tasks of its order. The other {left_out} "
              f"were not part of it and are not listed.", ""] if left_out else [])
    took = (f"End-to-end time: {e2e:.0f} s ({e2e / 60:.1f} min), from the run's start to the end of its last task, at most "
            f"the run's limit: the time the leaderboard ranks." if e2e is not None else
            "End-to-end time: none (no task ended).")
    open("run_all_results.md", "w").write("\n".join(
        ["# Results", "", f"{solved}/{len(tasks)} solved", "", took, "", *limit, *([note, ""] if note else []),
         head, "|" + " --- |" * head.count(" | ") + " --- |", *rows]) + "\n")
    log(f"wrote run_all_results.md ({solved}/{len(tasks)} solved"
        f"{f', end to end {e2e:.0f} s ({e2e / 60:.1f} min)' if e2e is not None else ''}); host-only records in {HOSTLOG}")


def agent_crashed() -> bool:
    """After cleanup(): whether the agent ended with an error (madsServe.py's exit status, AGENT_EXIT: Agent.run
    raised, src/ did not import, or the container was killed); if so, says so with the end of run_logs/agent.log."""
    if AGENT_EXIT in (None, 0):
        return False
    log(f"error: the agent crashed: madsServe.py exited with status {AGENT_EXIT}. The end of run_logs/agent.log:")
    try:
        lines = open("run_logs/agent.log", errors="replace").read().splitlines()[-15:]
    except OSError:
        lines = []
    for line in lines:
        log("  " + line)
    return True


def _stop_signal(signum, frame):
    raise KeyboardInterrupt   # SIGTERM / SIGHUP: handled exactly like Ctrl-C (see main)


def session_id() -> str:
    """dispatcher/session.py's id for this run, run from its source before anything is started (the
    agent container, which could only read that folder anyway, does not exist yet; no __pycache__)."""
    path = os.path.join(ROOT, "dispatcher", "session.py")
    ns = {"__name__": "a3_session", "__file__": path}
    exec(compile(open(path).read(), path, "exec"), ns)
    return ns["session_id"]()


def main() -> int:
    global SESSION, T0, RUN_LIMIT_S
    args = parse_args()
    try:
        RUN_LIMIT_S = int(os.environ.get("A3_RUN_LIMIT_S") or RUN_LIMITS[args.tasks])
    except ValueError:
        sys.exit(f"error: A3_RUN_LIMIT_S must be a number of seconds, not {os.environ['A3_RUN_LIMIT_S']!r}")
    SESSION = session_id()                         # first: without a name, nothing is started
    preconditions()
    shutil.rmtree(".tasks", ignore_errors=True); shutil.rmtree("run_logs", ignore_errors=True)
    for d in (SEQ, ".tasks/trace", "run_logs", "madsServe_logs"):
        os.makedirs(d, exist_ok=True)              # host-owned before the (root) agent container starts
    with open("run_logs/session_id", "w") as f:
        f.write(SESSION + "\n")
    log(f"session {SESSION} (sent with every model request of this run)")
    resolve_docker()                               # after run_logs/ exists: its sudo fallback logs there
    os.makedirs(HOSTLOG, exist_ok=True)
    snapshot_scripts()
    open_task_dirs()
    tasks, n_available = load_tasks(args.tasks, args.limit)
    log(f"tasks: {'Terminal-Bench 2.0' if args.tasks == 'tb2' else 'Assignment 4'}, {len(tasks)} ({n_available} may be opened), "
        f"order {TASK_ORDER}")
    log("time limits: " + (f"{span(RUN_LIMIT_S)} for the whole run from its "
                             f"{'start' if CLOCK_FROM == 'start' else 'first task'}" if RUN_LIMIT_S > 0 else
                             "none for the whole run (A3_RUN_LIMIT_S=0)") +
        ("; each task its own (task.toml [agent] timeout_sec)" if args.tasks == "tb2" else "; none per task"))
    ensure_images(tasks[:n_available] if args.limit > 0 else tasks)
    rc = 0
    # Stopping the run must remove what it started (agent, proxy, task containers, networks):
    # SIGTERM (kill, an IDE's stop button) and SIGHUP (closing the terminal) take the same path
    # as Ctrl-C, and once the cleanup has begun further signals are ignored, so a second Ctrl-C
    # cannot cut it short and leave an agent running (and calling the model) with nobody watching.
    for s in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(s, _stop_signal)
    interrupted = False
    server = None
    try:
        T0 = time.time()                           # the run starts: the agent container is next
        with open(f"{HOSTLOG}/clock_start.tmp", "w") as f:
            f.write(f"{T0}\n")
        os.replace(f"{HOSTLOG}/clock_start.tmp", f"{HOSTLOG}/clock_start")
        start_infra(args.tasks)
        if args.limit == 0:
            rc = preflight(tasks)
            write_at(SEQ_FD, "shutdown", b"")
            while running(AGENT):
                time.sleep(1)
        else:
            server = Server(tasks, n_available)
            server.serve()
            write_at(SEQ_FD, "shutdown", b"")
            for _ in range(60):
                if not running(AGENT):
                    break
                time.sleep(1)
    except KeyboardInterrupt:
        interrupted = True
        log("interrupted: stopping the agent and removing its containers and networks (please wait)")
    finally:
        for s in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            signal.signal(s, signal.SIG_IGN)
        cleanup()
        move_gradings()     # only now: the agent container, which mounts this folder, is gone
    if interrupted:
        log("stopped: containers and networks removed; no results written")
        return 130
    if n_available > 0:
        write_results(tasks, n_available, server.limit_note if server else "",
                      server.t_first if server and server.t_first is not None else T0)
    if agent_crashed():   # a run whose agent crashed exits 1 (its results above are still what it did)
        rc = rc or 1
    return rc


if __name__ == "__main__":
    sys.exit(main())

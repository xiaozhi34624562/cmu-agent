"""Course-provided terminal sandbox.

``run_terminal(cmd)`` runs one shell command written by the model and returns
a ``TerminalResult``. It applies four layers. Each is listed with what it
stops and what it does not.

1. Allowlist check (``check_command``). The command is split into simple
   commands at unquoted ``|``, ``&``, ``;``, parentheses and newlines. Each
   one must start with a name in ``ALLOWED_PROGRAMS`` or ``SHELL_BUILTINS``.
   Rejected: a program given as a path (``/bin/rm``, ``./x.py``), a variable
   assignment (``X=1 cmd``), command substitution (``$(...)``, backticks),
   ``$'...'`` strings and here-documents (``<<``). A rejected command is
   never started.
   Not covered: the arguments. ``python3``, ``awk`` (``system()``),
   ``find -exec`` and ``xargs`` can start other programs or open any path,
   and a redirection such as ``> ~/notes.txt`` passes the check.

2. Restricted environment. The command runs under bash in the workspace,
   with none of your process's environment variables (so no API keys) and
   with PATH set to one directory that holds only links to the allowed
   programs. ``python3`` is the base interpreter, without the project's
   packages.
   Not covered: a program started by its absolute path.

3. Timeout and output cap. The command runs in its own process group. When
   the timeout expires, or the command exits, every process still in the
   group is killed. Up to ``MAX_OUTPUT_BYTES`` of stdout and of stderr are
   kept; shorter output is returned in full.
   Not covered: a process that leaves the group (``os.setsid()``); memory,
   CPU and disk use.

4. Operating-system jail, if one is available (``jail()`` says which). Only
   this layer also constrains ``python3`` and absolute paths.
   * macOS, ``sandbox-exec``: no network; no writes outside the workspace; no
     reads of your home directory or this repository (so not of ``.env``),
     except the workspace and the Python installation. Other files on the
     machine stay readable.
   * Linux, ``bwrap`` (bubblewrap), if installed and permitted: the same
     rules, and the command cannot see other processes.
   * Otherwise "none": layers 1 to 3 still apply, but a command that runs
     ``python3`` can use the network and read or write any file you can.

The workspace holds the corpus: ``docs/`` is a copy, and ``emails.jsonl`` is
a copy-on-write clone where the file system supports one (macOS APFS; Linux
btrfs and XFS). Elsewhere it is a symlink to the real archive, which is then
made read-only.

On Windows (without WSL), layers 1 to 3 apply with these differences, and
there is no layer 4: ``jail()`` is "none", so a command that runs
``python3`` can use the network and read or write any file you can.
* The shell is the ``bash.exe`` of Git for Windows, and the allowed
  programs are the ones in its ``usr/bin``. If Git for Windows is not
  installed, every command is rejected with a message that says so.
* The PATH directory holds one small script per allowed program instead of
  a link (a plain Windows user cannot create symlinks).
* The command runs in a job object, which is what is killed at the timeout.
* Windows line endings (``\\r\\n``) in the output are turned into ``\\n``.
* ``emails.jsonl`` is a hard link to the real archive, which is made
  read-only until this process exits (a copy, if the link cannot be made).
The details are in ``sandbox_windows.py``.
"""

from __future__ import annotations

import atexit
import functools
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path

from cs329z_hw1 import data, sandbox_windows

ALLOWED_PROGRAMS = (
    "python3", "python", "cat", "head", "tail", "grep", "wc", "sort", "uniq", "cut",
    "sed", "awk", "tr", "ls", "find", "jq", "diff", "comm", "paste", "join", "nl",
    "tee", "xargs", "basename", "dirname", "date", "seq", "mkdir",
)  # fmt: skip
SHELL_BUILTINS = ("cd", "echo", "printf", "pwd", "read", "test", "[", "true", "false")
MAX_OUTPUT_BYTES = 4_000_000  # per stream

_KEYWORDS = {"if", "then", "elif", "else", "fi", "while", "until", "do", "done", "!", "{", "}"}
_WINDOWS = sys.platform == "win32"
if _WINDOWS:  # the programs and the shell come from Git for Windows; None if it is not installed
    _SYSTEM_PATH = str(sandbox_windows.git_usr_bin() or "")
    _SHELL = os.path.join(_SYSTEM_PATH, "bash.exe") if _SYSTEM_PATH else None
else:
    _SYSTEM_PATH = "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"
    _SHELL = "/bin/bash" if os.path.exists("/bin/bash") else "/bin/sh"


@dataclass
class TerminalResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None  # None if the command was rejected or timed out
    timed_out: bool = False
    rejected: bool = False  # True if the allowlist check refused the command, or there is no shell
    reason: str = ""  # why it was rejected or killed; "" otherwise


def _simple_commands(cmd: str) -> list[str]:
    """Split ``cmd`` at unquoted | & ; ( ) and newlines, dropping comments."""
    parts, cur, quote, i = [], [], "", 0
    while i < len(cmd):
        c = cmd[i]
        if quote == "'":  # inside single quotes nothing is special
            quote = "" if c == "'" else quote
        elif c == "\\":  # keep the backslash and the character it escapes together
            c = cmd[i : i + 2]
        elif c == "`" or cmd.startswith(("$(", "$'"), i):
            raise ValueError("command substitution ($(...) or backticks) and $'...' are not supported")
        elif quote == '"':
            quote = "" if c == '"' else quote
        elif c in "'\"":
            quote = c
        elif cmd.startswith("<<", i):
            raise ValueError("here-documents (<<) are not supported; use python3 -c '...' instead")
        elif c == "#" and (i == 0 or cmd[i - 1] in " \t\n;|&()"):  # comment: skip to end of line
            i = cmd.find("\n", i) if "\n" in cmd[i:] else len(cmd)
            continue
        elif c in "|;()\n" or (c == "&" and cmd[i - 1 : i] not in ("<", ">") and cmd[i + 1 : i + 2] != ">"):
            parts.append("".join(cur))  # "&" in 2>&1 and &> is a redirection, not a separator
            cur, c = [], " "
        cur.append(c)
        i += len(c)
    if quote:
        raise ValueError("unbalanced quote")
    return parts + ["".join(cur)]


def _program(simple_command: str) -> str | None:
    """The word the shell would run as the program, or None if there is none."""
    words = shlex.split(simple_command)
    while words:
        word = words.pop(0)
        if word == "for":  # "for x in a b c": the remaining words are not commands
            return None
        if re.match(r"\d*[<>]|&>", word):  # a redirection
            if word[-1] in "<>&":  # operator and target are separate words
                words = words[1:]
        elif word not in _KEYWORDS:
            return word
    return None


def check_command(cmd: str) -> str:
    """Return "" if ``cmd`` passes the allowlist check, else the reason it does not."""
    allowed = ALLOWED_PROGRAMS + SHELL_BUILTINS
    try:
        programs = [_program(part) for part in _simple_commands(cmd)]
    except ValueError as e:
        return f"Command rejected: {e}."
    for program in programs:
        if program is not None and program not in allowed:
            return f"Command rejected: {program!r} is not an allowed program. Allowed: {', '.join(allowed)}."
    if not any(programs):
        return "Command rejected: it contains no program to run."
    return ""


@functools.cache
def _state_dir() -> Path:
    """A temporary directory for this process, removed when the process exits."""
    path = Path(tempfile.mkdtemp(prefix="cs329z_hw1_sandbox_")).resolve()
    atexit.register(_remove_tree, path)
    return path


def _remove_tree(path: Path) -> None:
    if _WINDOWS:  # a read-only file (the archive's hard link) cannot be deleted as it is
        for file in path.rglob("*"):
            file.chmod(0o666)
    shutil.rmtree(path, ignore_errors=True)


@functools.cache
def _bin_dir() -> Path:
    """The directory used as PATH: one symlink per allowed program found on this
    machine (on Windows, a script that runs the program)."""
    bin_dir = _state_dir() / "bin"
    bin_dir.mkdir()
    python = os.path.realpath(getattr(sys, "_base_executable", "") or sys.executable)
    for name in ALLOWED_PROGRAMS:
        target = python if name.startswith("python") else shutil.which(name, path=_SYSTEM_PATH)
        if target and _WINDOWS:
            sandbox_windows.write_shim(bin_dir / name, target)
        elif target:
            (bin_dir / name).symlink_to(target)
    return bin_dir


def make_workspace(path: str | Path | None = None) -> Path:
    """Create the directory ``path`` (a new temporary directory if None), put
    the corpus in it as ``emails.jsonl`` and ``docs/`` unless they are already
    there, and return it. ``emails.jsonl`` is left out if the archive has not
    been downloaded."""
    ws = Path(path).resolve() if path is not None else Path(tempfile.mkdtemp(prefix="cs329z_hw1_ws_"))
    ws.mkdir(parents=True, exist_ok=True)
    emails, docs = ws / "emails.jsonl", ws / "docs"
    if data.EMAILS_PATH.exists() and not os.path.lexists(emails):
        if _WINDOWS:  # no clone: a hard link to the real file, made read-only; else a copy
            try:
                os.link(data.EMAILS_PATH, emails)
            except OSError:
                shutil.copyfile(data.EMAILS_PATH, emails)
            else:
                _read_only_until_exit(data.EMAILS_PATH)
        else:
            clone = ["cp", "-c"] if sys.platform == "darwin" else ["cp", "--reflink=always"]
            if subprocess.run([*clone, data.EMAILS_PATH, emails], capture_output=True).returncode != 0:
                emails.unlink(missing_ok=True)  # no clone: link to the real file, made read-only
                os.chmod(data.EMAILS_PATH, 0o444)
                emails.symlink_to(data.EMAILS_PATH.resolve())
    if data.DOCS_DIR.is_dir() and not docs.exists():
        shutil.copytree(data.DOCS_DIR, docs)
    return ws


@functools.cache
def _read_only_until_exit(path: Path) -> None:
    """Make ``path`` read-only, and writable again when this process exits
    (so that ``data/download.py`` can replace the archive)."""
    os.chmod(path, 0o444)
    atexit.register(lambda: path.exists() and os.chmod(path, 0o666))


def default_workspace() -> Path:
    """The workspace ``run_terminal`` uses when it is not given one: a
    temporary directory created for this process and removed when it exits."""
    return make_workspace(_state_dir() / "workspace")


def _jail_argv(workspace: Path) -> list[str]:
    """The command prefix that starts the OS jail for ``workspace`` ([] if there is none)."""
    ws, home, repo, py, bin_dir, emails = (
        str(Path(p).resolve())
        for p in (workspace, Path.home(), data.REPO_ROOT, sys.base_prefix, _bin_dir(), data.EMAILS_PATH)
    )
    if sys.platform == "darwin" and os.path.exists("/usr/bin/sandbox-exec"):
        q = json.dumps  # quotes a path for the profile
        profile = (
            "(version 1)(allow default)(deny network*)"
            f'(deny file-write*)(allow file-write* (subpath {q(ws)}) (subpath "/dev/fd")'
            '(literal "/dev/null") (literal "/dev/stdout") (literal "/dev/stderr"))'
            f"(deny file-read* (subpath {q(home)}) (subpath {q(repo)}))"
            f"(allow file-read* (subpath {q(ws)}) (subpath {q(py)}) (literal {q(emails)}))"
        )
        return ["/usr/bin/sandbox-exec", "-p", profile]
    if sys.platform == "linux" and shutil.which("bwrap"):
        return [
            shutil.which("bwrap"), "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc",
            "--tmpfs", home, "--tmpfs", repo, "--ro-bind", py, py, "--ro-bind", bin_dir, bin_dir,
            "--ro-bind-try", emails, emails, "--bind", ws, ws,
            "--unshare-net", "--unshare-pid", "--die-with-parent",
        ]  # fmt: skip
    return []


@functools.cache
def jail() -> str:
    """Which OS jail is in use: "sandbox-exec", "bwrap" or "none". The jail
    is tried once on a trivial command. If that fails (for example because
    this process is itself sandboxed), no jail is used. Windows has none."""
    if _WINDOWS:
        return "none"
    argv = _jail_argv(_state_dir())
    try:
        if argv and subprocess.run([*argv, _SHELL, "-c", "true"], capture_output=True, timeout=10).returncode == 0:
            return Path(argv[0]).name
    except (OSError, subprocess.SubprocessError):
        pass
    return "none"


def _drain(pipe, buf: bytearray) -> None:
    """Read ``pipe`` to the end, keeping at most MAX_OUTPUT_BYTES in ``buf``."""
    while chunk := os.read(pipe.fileno(), 65536):
        buf += chunk[: MAX_OUTPUT_BYTES - len(buf)]


def _text(buf: bytearray) -> str:
    note = f"\n[sandbox: output cut off after {MAX_OUTPUT_BYTES} bytes]" if len(buf) >= MAX_OUTPUT_BYTES else ""
    text = bytes(buf).decode("utf-8", errors="replace")
    return (text.replace("\r\n", "\n") if _WINDOWS else text) + note


def run_terminal(cmd: str, *, workspace: str | Path | None = None, timeout: float = 10.0) -> TerminalResult:
    """Run ``cmd`` in the sandbox and return what happened.

    ``workspace`` is the working directory; ``make_workspace`` is applied to
    it, so a new or empty directory gets the corpus. ``None`` means
    ``default_workspace()``. A timeout or an allowlist rejection is reported
    in the result, not raised.
    """
    reason = check_command(cmd)
    if reason:
        return TerminalResult(rejected=True, reason=reason)
    if _SHELL is None:  # Windows without Git for Windows
        return TerminalResult(rejected=True, reason=sandbox_windows.INSTALL_HINT)
    ws = make_workspace(workspace) if workspace is not None else default_workspace()
    env = {
        "PATH": str(_bin_dir()), "HOME": str(ws), "TMPDIR": str(ws),
        "LC_ALL": "C", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1",
        **(sandbox_windows.child_env(ws) if _WINDOWS else {}),
    }  # fmt: skip
    argv = (_jail_argv(ws) if jail() != "none" else []) + [_SHELL, "-c", cmd]
    job = sandbox_windows.Job() if _WINDOWS else None  # Windows: a job object stands in for the process group
    proc = subprocess.Popen(
        argv, cwd=ws, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        start_new_session=not _WINDOWS,  # new session = own process group
        creationflags=subprocess.CREATE_NO_WINDOW if _WINDOWS else 0,
    )  # fmt: skip
    if job:
        job.add(proc)
    out, err = bytearray(), bytearray()
    readers = [
        threading.Thread(target=_drain, args=(pipe, buf), daemon=True)
        for pipe, buf in ((proc.stdout, out), (proc.stderr, err))
    ]
    for reader in readers:
        reader.start()
    timed_out = False
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
    if job:  # kill whatever is left in the group: the command itself, or jobs it left behind
        job.kill()
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    proc.wait()
    for reader in readers:
        reader.join(timeout=1.0)
    return TerminalResult(
        stdout=_text(out),
        stderr=_text(err),
        exit_code=None if timed_out else proc.returncode,
        timed_out=timed_out,
        reason=f"Timed out after {timeout:g} seconds; the command was killed." if timed_out else "",
    )

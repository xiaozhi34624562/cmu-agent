"""The Windows parts of ``cs329z_hw1.sandbox``. Not used on macOS or Linux.

Three things differ on Windows and are kept here so that ``sandbox.py`` stays
short:

* The shell. Windows has no ``/bin/bash``. The sandbox uses the ``bash.exe``
  that ships with Git for Windows, and the allowed programs come from the
  same installation (its ``usr/bin`` directory, which holds ``grep``,
  ``sort``, ``awk`` and the rest). ``git_usr_bin()`` finds that directory.
* The PATH directory. A plain Windows user cannot create symlinks, and a
  copy of ``grep.exe`` would not find its DLLs, so the PATH directory holds
  one small shell script per allowed program that starts the real program
  by its full path (``write_shim``).
* Killing the command. Windows has no process groups that ``kill`` can
  target, so every command is started inside a job object; terminating the
  job kills every process the command started (``Job``).
"""

from __future__ import annotations

import ctypes
import os
import shutil
from pathlib import Path

INSTALL_HINT = (
    "Command rejected: no shell was found. The terminal sandbox needs the bash.exe that "
    "ships with Git for Windows. Install it from https://git-scm.com/download/win "
    "(the default options are fine) and start a new terminal."
)


def git_usr_bin() -> Path | None:
    """The ``usr/bin`` directory of Git for Windows, or None if it is not installed."""
    roots = []
    for name in ("git", "bash"):
        found = shutil.which(name)
        if found:
            roots += Path(found).resolve().parents[:3]  # Git/cmd/git.exe, Git/usr/bin/bash.exe, ...
    for var in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)", "LOCALAPPDATA"):
        if os.environ.get(var):
            roots.append(Path(os.environ[var]) / "Git")
            roots.append(Path(os.environ[var]) / "Programs" / "Git")
    for root in roots:
        if (root / "usr" / "bin" / "bash.exe").exists() and (root / "usr" / "bin" / "msys-2.0.dll").exists():
            return root / "usr" / "bin"
    return None


def posix_path(path: str | Path) -> str:
    """``C:\\Users\\x`` as bash sees it: ``/c/Users/x``."""
    drive, rest = os.path.splitdrive(str(path))
    return "/" + drive.rstrip(":").lower() + rest.replace("\\", "/")


def write_shim(shim: Path, target: str) -> None:
    """Write the script ``shim`` that runs ``target`` with the same arguments."""
    shim.write_text(f'#!/bin/sh\nexec "{posix_path(target)}" "$@"\n', newline="\n")


def child_env(workspace: Path) -> dict[str, str]:
    """Variables a Windows process needs on top of the sandbox's own."""
    return {
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows"),  # without it, Python cannot start
        "TEMP": str(workspace), "TMP": str(workspace), "USERPROFILE": str(workspace),
    }  # fmt: skip


# ----------------------------------------------------------- job objects ---

_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
_JobObjectExtendedLimitInformation = 9


class _BasicLimits(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", ctypes.c_uint32), ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", ctypes.c_uint32),
        ("Affinity", ctypes.c_size_t), ("PriorityClass", ctypes.c_uint32), ("SchedulingClass", ctypes.c_uint32),
    ]  # fmt: skip


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimits), ("IoInfo", ctypes.c_uint64 * 6),
        ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]  # fmt: skip


class Job:
    """A Windows job object. ``add(proc)`` puts a process and everything it
    will start into the job; ``kill()`` terminates all of them. The job is
    also set to kill its processes if this process exits without calling
    ``kill``."""

    def __init__(self) -> None:
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)  # only exists on Windows
        k32.CreateJobObjectW.restype = ctypes.c_void_p
        k32.SetInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
        k32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        k32.TerminateJobObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        k32.CloseHandle.argtypes = [ctypes.c_void_p]
        self._k32 = k32
        self._handle = k32.CreateJobObjectW(None, None)
        if not self._handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = _ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not k32.SetInformationJobObject(
            self._handle, _JobObjectExtendedLimitInformation, ctypes.byref(limits), ctypes.sizeof(limits)
        ):
            raise ctypes.WinError(ctypes.get_last_error())

    def add(self, proc) -> None:
        """Put a ``subprocess.Popen`` process into the job."""
        if not self._k32.AssignProcessToJobObject(self._handle, int(proc._handle)):
            raise ctypes.WinError(ctypes.get_last_error())

    def kill(self) -> None:
        """Terminate every process in the job and release it."""
        self._k32.TerminateJobObject(self._handle, 1)
        self._k32.CloseHandle(self._handle)

#!/usr/bin/env python3
"""Package Claude Code, Cursor, and Codex sessions into one archive.

Assignment 3 shipped this script as package_claude_sessions.py, for assignment3/.

Claude Code stores one project directory per working directory under
~/.claude/projects. The directory name is the absolute path with every
non-alphanumeric character replaced by a hyphen.

Cursor Agent stores the same kind of project directory under
~/.cursor/projects (the leading slash is often omitted) and session
metadata under ~/.cursor/chats/<md5(path)>. Codex stores one rollout
per session under ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl, plus
archived copies under ~/.codex/archived_sessions.

Included by default:
  - sessions started in assignment5/ or any directory under it
  - sessions started in the git repository root
  - other Claude or Cursor project folders, including ssh-* folders,
    whose transcript cwd is in one of those places
  - Codex rollouts, including archived ones, whose cwd is in one of
    those places

A project folder is taken by its name only when the name is exactly
that of one of those places. A folder of a subdirectory is taken by the
cwd its transcripts record: names alone cannot tell ~/repo/notes from
~/repo-notes or ~/repo_notes, which all become -home-me-repo-notes.

The course server's key is scrubbed from every file as it is archived:
the value of CS2680_API_KEY when it is set, the contents of
~/a4/serve.key when that file is readable, and any 32-hex-digit token
after "Bearer" or "api_key" (in any of its spellings, such as
CS2680_API_KEY=, "api_key": or --api-key). Each is replaced by
"REDACTED" repeated to the same length, so a binary file such as an
SQLite database stays valid. Other 32-hex-digit strings, such as
hashes, are kept. A compressed file, such as a Codex rollout ending in
.zst, is archived as it is, and the script lists it.

The archive layout is:

  <claude-project>/
  cursor/projects/<project>/
  cursor/chats/<workspace-hash>/...
  codex/sessions/YYYY/MM/DD/rollout-*.jsonl
  codex/archived_sessions/YYYY/MM/DD/rollout-*.jsonl

Claude Code project directories stay at the archive root. Cursor and Codex
are stored under their own prefixes.

Run it from anywhere:

  python3 package_agent_sessions.py
  python3 package_agent_sessions.py --path ~/other/checkout
  python3 package_agent_sessions.py --no-repo-root
  python3 package_agent_sessions.py --dry-run
  python3 package_agent_sessions.py --path . --output agent-sessions.tar.gz
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ASSIGNMENT_DIR = (
    SCRIPT_DIR.parent if SCRIPT_DIR.name == "starter_code" else SCRIPT_DIR / "assignment5"
)
ARCHIVE_NAME = "a5-sessions.tar.gz"
# Same shapes the course page asks you to scan for before archiving.
SECRET_RE = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}"
    r"|ghp_[A-Za-z0-9]{36}"
    r"|AKIA[0-9A-Z]{16}"
    r"|BEGIN [A-Z ]*PRIVATE KEY"
)
CODEX_ROLLOUT_RE = re.compile(
    r"^rollout-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-"
    r"[0-9a-fA-F-]{36}\.jsonl(?:\.zst)?$"
)
CHUNK = 1024 * 1024
SECRET_OVERLAP = 128
HEAD_BYTES = 1024 * 1024
# The course server key (32 hex digits) where a transcript names it as a key. The separators allow the
# JSON-escaped forms a transcript holds, such as \"api_key\": \"...\", and the same escaped twice (a tool's
# output that is itself JSON text), \\\"api_key\\\": \\\"...
KEY_CONTEXT = rb"(?:(?i:bearer)[ \t]{1,8}|(?i:api[_-]?key)[\"'\\ \t:=]{1,16})"
KEY_TOKEN = rb"[0-9A-Fa-f]{32}(?![0-9A-Za-z])"
MIN_KEY_CHARS = 16                    # a shorter CS2680_API_KEY or serve.key is not scrubbed as text
SERVE_KEY = Path("~/a4/serve.key")
COMPRESSED = (".zst", ".gz", ".xz", ".bz2", ".zip")


class Archived:
    def __init__(self, tool: str, path: Path, arcname: str):
        self.tool = tool
        self.path = path
        self.arcname = arcname


def encode_path(path: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "-", path)


def path_forms(path: Path) -> list[Path]:
    """Absolute path as given, and the symlink-resolved path."""
    absolute = Path(os.path.abspath(path.expanduser()))
    resolved = absolute.resolve()
    if resolved == absolute:
        return [absolute]
    return [absolute, resolved]


def path_slugs(path: Path) -> set[str]:
    return {encode_path(str(form)) for form in path_forms(path)}


def cursor_slugs(path: Path) -> set[str]:
    """Claude's encoding, plus the forms Cursor uses on disk.

    Cursor replaces path separators and dots with hyphens and usually drops
    the leading slash, so /Users/me/cs_proj can be Users-me-cs_proj. Some
    builds use Claude's encoding instead. Keep underscores in the
    separator-only form so both layouts match.
    """
    slugs: set[str] = set()
    for form in path_forms(path):
        text = str(form)
        for slug in (encode_path(text), re.sub(r"[/\\.:]", "-", text)):
            if not slug:
                continue
            slugs.add(slug)
            if slug.startswith("-"):
                slugs.add(slug[1:])
    return slugs


def is_under(cwd: str, root: Path) -> bool:
    cwd_forms = path_forms(Path(cwd))
    root_forms = path_forms(root)
    for cwd_form in cwd_forms:
        for root_form in root_forms:
            try:
                cwd_form.relative_to(root_form)
                return True
            except ValueError:
                continue
    return False


def same_dir(cwd: str, root: Path) -> bool:
    return any(form == root_form for form in path_forms(Path(cwd)) for root_form in path_forms(root))


def cwd_selected(cwd: str | None, tree_roots: list[Path], exact_roots: list[Path]) -> bool:
    if not cwd:
        return False
    if any(is_under(cwd, root) for root in tree_roots):
        return True
    return any(same_dir(cwd, root) for root in exact_roots)


def git_root(start: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    text = result.stdout.strip()
    if not text:
        return None
    root = Path(text)
    # A repo rooted at $HOME or / would sweep in unrelated sessions.
    if root.resolve() in {Path.home().resolve(), Path(root.anchor).resolve()}:
        return None
    return root


def claude_projects_dir(override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    config = os.environ.get("CLAUDE_CONFIG_DIR")
    base = Path(config).expanduser() if config else Path.home() / ".claude"
    return base / "projects"


def cursor_home_dir(override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".cursor"


def codex_home_dir(override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    config = os.environ.get("CODEX_HOME")
    return Path(config).expanduser() if config else Path.home() / ".codex"


def exact_slug_matches(name: str, roots: list[Path], slugs_for=path_slugs) -> bool:
    slugs = set()
    for root in roots:
        slugs.update(slugs_for(root))
    return name in slugs


def project_cwd(project_dir: Path) -> str | None:
    """Return the cwd recorded in this project, from the first transcript that has one."""
    try:
        files = sorted(project_dir.glob("*.jsonl"))
    except OSError:
        return None
    for path in files:
        try:
            with path.open(encoding="utf-8", errors="replace") as handle:
                for count, line in enumerate(handle):
                    if count >= 40 or '"cwd"' not in line:
                        if count >= 40:
                            break
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    cwd = record.get("cwd")
                    if isinstance(cwd, str) and cwd:
                        return cwd
        except OSError:
            continue
    return None


def select_projects(
    projects_dir: Path,
    tree_roots: list[Path],
    exact_roots: list[Path],
    slugs_for=path_slugs,
) -> list[Path]:
    selected: dict[Path, Path] = {}
    try:
        entries = sorted(
            (entry for entry in projects_dir.iterdir() if entry.is_dir() and not entry.is_symlink()),
            key=lambda entry: entry.name,
        )
    except OSError:
        return []
    for entry in entries:
        # The folder of a root itself. A folder whose name only starts with a root's is not taken by its
        # name: ~/repo-old, ~/repo_notes and ~/repo/notes all start with ~/repo's. The cwd check below
        # takes it when it is a subdirectory of a tree root.
        if exact_slug_matches(entry.name, tree_roots + exact_roots, slugs_for):
            selected[entry.resolve()] = entry
    for entry in entries:
        if entry.resolve() in selected:
            continue
        cwd = project_cwd(entry)
        if cwd_selected(cwd, tree_roots, exact_roots):
            selected[entry.resolve()] = entry
    return [selected[key] for key in sorted(selected)]


def json_cwd(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    try:
        record = json.loads(text[:HEAD_BYTES])
    except json.JSONDecodeError:
        return None
    if not isinstance(record, dict):
        return None
    for key in ("cwd", "workspacePath", "workspace_path"):
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def cursor_project_cwd(project_dir: Path) -> str | None:
    found = project_cwd(project_dir)
    if found:
        return found
    transcripts = project_dir / "agent-transcripts"
    if transcripts.is_dir() and not transcripts.is_symlink():
        seen = 0
        try:
            files = sorted(transcripts.rglob("*.jsonl"))
        except OSError:
            files = []
        for path in files:
            if not path.is_file() or path.is_symlink():
                continue
            seen += 1
            if seen > 8:
                break
            try:
                with path.open(encoding="utf-8", errors="replace") as handle:
                    for count, line in enumerate(handle):
                        if count >= 20:
                            break
                        if '"cwd"' not in line and '"workspacePath"' not in line:
                            continue
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if not isinstance(record, dict):
                            continue
                        for key in ("cwd", "workspacePath"):
                            value = record.get(key)
                            if isinstance(value, str) and value:
                                return value
            except OSError:
                continue
    try:
        json_files = sorted(project_dir.glob("*.json"))
    except OSError:
        return None
    for path in json_files[:20]:
        if path.is_symlink():
            continue
        cwd = json_cwd(path)
        if cwd:
            return cwd
    return None


def select_cursor_projects(
    projects_dir: Path,
    tree_roots: list[Path],
    exact_roots: list[Path],
) -> list[Path]:
    selected = {
        path.resolve(): path
        for path in select_projects(projects_dir, tree_roots, exact_roots, cursor_slugs)
    }
    try:
        entries = sorted(
            (entry for entry in projects_dir.iterdir() if entry.is_dir() and not entry.is_symlink()),
            key=lambda entry: entry.name,
        )
    except OSError:
        return [selected[key] for key in sorted(selected)]
    for entry in entries:
        if entry.resolve() in selected:
            continue
        if cwd_selected(cursor_project_cwd(entry), tree_roots, exact_roots):
            selected[entry.resolve()] = entry
    return [selected[key] for key in sorted(selected)]


def cursor_workspace_hashes(roots: list[Path]) -> set[str]:
    hashes: set[str] = set()
    for root in roots:
        for form in path_forms(root):
            text = str(form)
            for variant in (text, text + "/"):
                hashes.add(hashlib.md5(variant.encode("utf-8", errors="replace")).hexdigest())
    return hashes


def select_cursor_chats(
    chats_dir: Path,
    tree_roots: list[Path],
    exact_roots: list[Path],
) -> list[Path]:
    """Workspace dirs whose hash matches, or individual chats whose meta cwd matches."""
    if not chats_dir.is_dir() or chats_dir.is_symlink():
        return []
    hashes = cursor_workspace_hashes(tree_roots + exact_roots)
    selected: dict[Path, Path] = {}
    try:
        hash_dirs = sorted(
            (entry for entry in chats_dir.iterdir() if entry.is_dir() and not entry.is_symlink()),
            key=lambda entry: entry.name,
        )
    except OSError:
        return []
    for hash_dir in hash_dirs:
        if hash_dir.name in hashes:
            selected[hash_dir.resolve()] = hash_dir
            continue
        try:
            children = sorted(
                (child for child in hash_dir.iterdir() if child.is_dir() and not child.is_symlink()),
                key=lambda entry: entry.name,
            )
        except OSError:
            continue
        for child in children:
            cwd = json_cwd(child / "meta.json")
            if cwd_selected(cwd, tree_roots, exact_roots):
                selected[child.resolve()] = child
    return [selected[key] for key in sorted(selected)]


def head_text(path: Path) -> str:
    if path.name.endswith(".zst"):
        executable = shutil.which("zstd")
        if executable is None:
            return ""
        try:
            proc = subprocess.Popen(
                [executable, "-dc", str(path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            return ""
        try:
            data = proc.stdout.read(HEAD_BYTES) if proc.stdout is not None else b""
        finally:
            if proc.stdout is not None:
                proc.stdout.close()
            proc.kill()
            proc.wait()
        return data.decode("utf-8", errors="replace")
    try:
        with path.open("rb") as handle:
            return handle.read(HEAD_BYTES).decode("utf-8", errors="replace")
    except OSError:
        return ""


def codex_cwd(path: Path) -> str | None:
    for line in head_text(path).splitlines()[:15]:
        if '"session_meta"' not in line and '"cwd"' not in line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict) or record.get("type") != "session_meta":
            continue
        payload = record.get("payload")
        if isinstance(payload, dict):
            cwd = payload.get("cwd")
            if isinstance(cwd, str) and cwd:
                return cwd
    return None


def iter_codex_rollouts(home: Path):
    for folder in ("sessions", "archived_sessions"):
        root = home / folder
        if not root.is_dir() or root.is_symlink():
            continue
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            dirnames[:] = sorted(
                name for name in dirnames if not (Path(dirpath) / name).is_symlink()
            )
            for name in sorted(filenames):
                if not CODEX_ROLLOUT_RE.fullmatch(name):
                    continue
                path = Path(dirpath) / name
                if path.is_file() and not path.is_symlink():
                    yield path


def select_codex_rollouts(
    home: Path,
    tree_roots: list[Path],
    exact_roots: list[Path],
) -> list[Path]:
    if not home.is_dir() or home.is_symlink():
        return []
    selected: list[Path] = []
    for path in iter_codex_rollouts(home):
        if cwd_selected(codex_cwd(path), tree_roots, exact_roots):
            selected.append(path)
    return selected


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        for name in sorted(filenames):
            yield Path(dirpath) / name


def item_files(item: Archived):
    if item.path.is_file():
        yield item.path
        return
    yield from iter_files(item.path)


def scan_secrets(items: list[Archived]) -> list[Path]:
    hits: list[Path] = []
    for item in items:
        for path in item_files(item):
            if not path.is_file():
                continue
            try:
                with path.open("rb") as handle:
                    tail = b""
                    while True:
                        block = handle.read(CHUNK)
                        if not block:
                            break
                        if b"\0" in block:
                            break
                        data = tail + block
                        if SECRET_RE.search(data.decode("utf-8", errors="replace")):
                            hits.append(path)
                            break
                        tail = data[-SECRET_OVERLAP:]
            except OSError as exc:
                print(f"Could not read {path}: {exc}", file=sys.stderr)
                hits.append(path)
    return hits


def session_count(project_dir: Path) -> int:
    return sum(
        1
        for path in project_dir.glob("*.jsonl")
        if path.is_file() and not path.name.startswith("agent-")
    )


def cursor_session_count(path: Path) -> int:
    if (path / "meta.json").is_file() or (path / "store.db").is_file():
        return 1
    try:
        children = [
            child for child in path.iterdir() if child.is_dir() and not child.is_symlink()
        ]
    except OSError:
        children = []
    chats = [
        child
        for child in children
        if (child / "meta.json").is_file() or (child / "store.db").is_file()
    ]
    if chats:
        return len(chats)
    try:
        files = path.rglob("*.jsonl")
    except OSError:
        return 0
    return sum(1 for file in files if file.is_file() and not file.is_symlink())


def dir_size(project_dir: Path) -> int:
    total = 0
    for path in iter_files(project_dir):
        if path.is_file():
            try:
                total += path.stat().st_size
            except OSError:
                pass
    return total


def item_size(item: Archived) -> int:
    if item.path.is_file():
        try:
            return item.path.stat().st_size
        except OSError:
            return 0
    return dir_size(item.path)


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def relative_arcname(prefix: str, root: Path, path: Path) -> str:
    relative = os.path.relpath(path, root)
    if relative.startswith("..") or os.path.isabs(relative):
        raise ValueError(f"{path} is outside {root}")
    return prefix + "/" + relative.replace(os.sep, "/")


def server_keys() -> list[bytes]:
    """The course server key's values known on this machine: $CS2680_API_KEY, and ~/a4/serve.key when readable."""
    values = [os.environ.get("CS2680_API_KEY", "")]
    try:
        values.append(SERVE_KEY.expanduser().read_text(encoding="utf-8", errors="replace"))
    except OSError:
        pass
    keys: list[bytes] = []
    for value in values:
        value = value.strip()
        if len(value) >= MIN_KEY_CHARS and value.encode() not in keys:
            keys.append(value.encode())
    return keys


def key_pattern(keys: list[bytes]) -> re.Pattern:
    """One pattern for every form of the key (KEY_CONTEXT + KEY_TOKEN, and each value in keys); in each
    alternative the group to scrub is the last one that matched."""
    alternatives = [KEY_CONTEXT + b"(" + KEY_TOKEN + b")"]
    alternatives += [b"(" + re.escape(key) + b")" for key in sorted(keys, key=len, reverse=True)]
    return re.compile(b"|".join(alternatives))


def redact_stream(src, dst, pattern: re.Pattern, overlap: int) -> int:
    """Copy src to dst with every match of pattern replaced by "REDACTED" repeated to the same length.
    Returns how many were replaced. A block's last `overlap` bytes (at least the longest match) are
    written only with the next block, so a key split across two reads is still found."""
    count = 0
    buf = bytearray()
    while True:
        block = src.read(CHUNK)
        buf += block
        # A match that ends where the reading stopped is left for the next block, unless the file ended: the hex
        # digits may go on there (a 40-hex hash after api_key is not a key). The kept overlap still holds it.
        spans = [m.span(m.lastindex) for m in pattern.finditer(buf) if not block or m.end() < len(buf)]
        for start, end in spans:
            buf[start:end] = (b"REDACTED" * ((end - start) // 8 + 1))[: end - start]
        count += len(spans)
        if not block:
            dst.write(buf)
            return count
        cut = max(0, len(buf) - overlap)
        dst.write(buf[:cut])
        del buf[:cut]


class Scrubber:
    """Scrubs the course server key from the files it archives (or, for a dry run, counts what it would)."""

    def __init__(self, keys: list[bytes]):
        self.pattern = key_pattern(keys)
        self.overlap = max([64] + [len(key) for key in keys]) + 16
        self.count = 0
        self.files = 0
        self.compressed: list[Path] = []

    def copy(self, path: Path, dst) -> None:
        """path's contents to dst, scrubbed unless the file is compressed."""
        with path.open("rb") as handle:
            if path.name.endswith(COMPRESSED):
                self.compressed.append(path)
                shutil.copyfileobj(handle, dst)
                return
            found = redact_stream(handle, dst, self.pattern, self.overlap)
        self.count += found
        self.files += 1 if found else 0

    def add(self, archive: tarfile.TarFile, path: Path, arcname: str) -> None:
        """As archive.add(path, arcname), recursively, with each regular file's contents scrubbed."""
        info = archive.gettarinfo(str(path), arcname)
        if info is None:                      # a socket or other file tar cannot hold
            print(f"Skipped {path}: not a file tar can archive", file=sys.stderr)
            return
        if info.isreg():
            with tempfile.SpooledTemporaryFile(max_size=64 * 1024 * 1024) as scrubbed:
                self.copy(path, scrubbed)
                info.size = scrubbed.tell()   # what was read now, if the file grew or shrank since
                scrubbed.seek(0)
                archive.addfile(info, scrubbed)
        elif info.isdir():
            archive.addfile(info)
            for name in sorted(os.listdir(path)):
                self.add(archive, path / name, arcname + "/" + name)
        else:
            archive.addfile(info)

    def count_only(self, items: list[Archived]) -> None:
        """For a dry run: what add() would scrub, without writing anything."""
        class Discard:
            def write(self, data):
                return len(data)
        for item in items:
            for path in item_files(item):
                if path.is_file() and not path.is_symlink():
                    try:
                        self.copy(path, Discard())
                    except OSError as exc:
                        print(f"Could not read {path}: {exc}", file=sys.stderr)

    def report(self, dry_run: bool) -> None:
        verb = "Would scrub" if dry_run else "Scrubbed"
        print(f"{verb} the course server key {self.count} time(s) in {self.files} file(s).")
        for path in self.compressed:
            print(f"  Not scrubbed (compressed): {path}")


def write_archive(items: list[Archived], output: Path, scrubber: Scrubber) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=".a5-sessions.",
        suffix=".tar.gz",
        dir=output.parent,
    )
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        with tarfile.open(tmp_path, "w:gz") as archive:
            for item in items:
                # Names that start with "-" are recorded as member names, so
                # tar does not read the leading hyphen as a flag.
                scrubber.add(archive, item.path, item.arcname)
        os.replace(tmp_path, output)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Package Claude Code, Cursor, and Codex sessions into "
            f"assignment5/{ARCHIVE_NAME}."
        )
    )
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        metavar="DIR",
        help="another directory you worked in; sessions there and in its subdirectories are included (repeatable)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ASSIGNMENT_DIR / ARCHIVE_NAME,
        help=f"archive path (default: assignment5/{ARCHIVE_NAME})",
    )
    parser.add_argument(
        "--projects-dir",
        help="Claude Code projects directory (default: $CLAUDE_CONFIG_DIR/projects or ~/.claude/projects)",
    )
    parser.add_argument(
        "--cursor-home",
        help="Cursor data directory (default: ~/.cursor)",
    )
    parser.add_argument(
        "--codex-home",
        help="Codex home (default: $CODEX_HOME or ~/.codex)",
    )
    parser.add_argument(
        "--no-repo-root",
        action="store_true",
        help="skip sessions started in the git repository root",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="write the archive even when the secret scan finds a match",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the files that would be archived and scan them, without writing the archive",
    )
    return parser.parse_args(argv)


def print_group(
    title: str,
    items: list[Archived],
    exact_roots: list[Path],
    home: Path,
    found: bool,
) -> None:
    print(f"{title}:")
    if not found:
        print(f"  (directory not found: {home})")
        return
    if not items:
        print("  (none)")
        return
    for item in items:
        if item.tool == "claude":
            count = session_count(item.path)
            label = ""
            if exact_roots and exact_slug_matches(item.path.name, exact_roots):
                label = " (repository root; includes every session started there)"
            noun = "session(s)"
        elif item.tool == "codex":
            count = 1
            label = ""
            noun = "rollout"
        else:
            count = cursor_session_count(item.path)
            label = ""
            noun = "session(s)"
        print(f"  {item.arcname}{label}: {count} {noun}, {format_size(item_size(item))}")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    projects_dir = claude_projects_dir(args.projects_dir)
    cursor_home = cursor_home_dir(args.cursor_home)
    codex_home = codex_home_dir(args.codex_home)
    tree_roots = [ASSIGNMENT_DIR]
    for raw in args.path:
        path = Path(raw).expanduser()
        absolute = Path(os.path.abspath(path))
        if not absolute.is_dir():
            print(f"Not a directory: {path}", file=sys.stderr)
            return 1
        # Keep the path as given. path_forms adds the symlink-resolved path,
        # so a session stored under either name still matches.
        tree_roots.append(absolute)

    exact_roots: list[Path] = []
    repo = git_root(ASSIGNMENT_DIR)
    if repo is not None and not args.no_repo_root:
        exact_roots.append(repo)

    items: list[Archived] = []
    claude_found = projects_dir.is_dir()
    claude_items: list[Archived] = []
    if claude_found:
        for project_dir in select_projects(projects_dir, tree_roots, exact_roots):
            claude_items.append(Archived("claude", project_dir, project_dir.name))

    cursor_found = cursor_home.is_dir()
    cursor_items: list[Archived] = []
    if cursor_found:
        for project_dir in select_cursor_projects(
            cursor_home / "projects", tree_roots, exact_roots
        ):
            cursor_items.append(
                Archived(
                    "cursor",
                    project_dir,
                    relative_arcname("cursor", cursor_home, project_dir),
                )
            )
        for chat_dir in select_cursor_chats(cursor_home / "chats", tree_roots, exact_roots):
            cursor_items.append(
                Archived(
                    "cursor",
                    chat_dir,
                    relative_arcname("cursor", cursor_home, chat_dir),
                )
            )

    codex_found = codex_home.is_dir()
    codex_items: list[Archived] = []
    if codex_found:
        for rollout in select_codex_rollouts(codex_home, tree_roots, exact_roots):
            codex_items.append(
                Archived("codex", rollout, relative_arcname("codex", codex_home, rollout))
            )

    items.extend(claude_items)
    items.extend(cursor_items)
    items.extend(codex_items)

    print_group("Claude Code", claude_items, exact_roots, projects_dir, claude_found)
    print_group("Cursor", cursor_items, exact_roots, cursor_home, cursor_found)
    print_group("Codex", codex_items, exact_roots, codex_home, codex_found)

    if not items:
        print(
            "No Claude Code, Cursor, or Codex sessions found for this assignment.",
            file=sys.stderr,
        )
        print("Looked for project directories matching:", file=sys.stderr)
        for root in tree_roots:
            for slug in sorted(path_slugs(root)):
                print(f"  {slug} and its subdirectories", file=sys.stderr)
        for root in exact_roots:
            for slug in sorted(path_slugs(root)):
                print(f"  {slug} (repository root only)", file=sys.stderr)
        print(
            "Also checked Cursor project folders and Codex rollouts whose cwd is in those trees.",
            file=sys.stderr,
        )
        print("Pass --path DIR for each other checkout you worked in.", file=sys.stderr)
        return 1

    hits = scan_secrets(items)
    if hits:
        print(
            "Secret scan found matches. The archive was not written."
            if not args.force
            else "Secret scan found matches.",
            file=sys.stderr,
        )
        for path in hits:
            print(f"  {path}", file=sys.stderr)
        print(
            "Remove credentials from those sessions, or re-run with --force if you have already checked them.",
            file=sys.stderr,
        )
        if not args.force:
            return 2

    output = args.output.expanduser()
    if not output.is_absolute():
        output = (Path.cwd() / output).resolve()
    scrubber = Scrubber(server_keys())
    if args.dry_run:
        scrubber.count_only(items)
        scrubber.report(dry_run=True)
        print(f"Dry run: would write {output}")
        return 0

    write_archive(items, output, scrubber)
    scrubber.report(dry_run=False)
    print(f"Wrote {output}")
    warn_if_ignored(output)
    print(f"Commit {output}. Do not gitignore it.")
    return 0


def warn_if_ignored(path: Path) -> None:
    try:
        result = subprocess.run(
            ["git", "-C", str(path.parent), "check-ignore", "-q", "--", path.name],
            check=False,
            capture_output=True,
        )
    except OSError:
        return
    if result.returncode == 0:
        print(
            f"Warning: git ignores {path.name}. Include this archive in your commit.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

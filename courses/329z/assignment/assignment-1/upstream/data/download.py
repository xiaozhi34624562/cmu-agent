"""Install the email archive at data/emails/emails.jsonl.

    uv run python data/download.py                   # verify and unpack
    uv run python data/download.py --from-file X.gz  # install from another copy

The archive is one gzip file, data/emails.jsonl.gz, which ships in this
repository. If it is missing, the script downloads it from the URL in
data/source.json instead. source.json also records the file's SHA-256, its
size in bytes, and how many emails it holds. The script checks the SHA-256
before unpacking, so a truncated or modified file is rejected. Only the
standard library is used.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
SOURCE = DATA_DIR / "source.json"
BUNDLED = DATA_DIR / "emails.jsonl.gz"
EMAILS_DIR = DATA_DIR / "emails"
EMAILS_PATH = EMAILS_DIR / "emails.jsonl"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url: str, dest: Path) -> None:
    print(f"Downloading {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "cs329z-hw1"})
    with urllib.request.urlopen(request, timeout=60) as response, open(dest, "wb") as out:
        total = int(response.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = response.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r  {done / 1e6:.1f} of {total / 1e6:.1f} MB", end="", flush=True)
        if total:
            print()


def install(gz_path: Path, source: dict) -> int:
    """Verify gz_path against source.json, unpack it, return the email count."""
    size = gz_path.stat().st_size
    if size != source["bytes"]:
        sys.exit(
            f"Size mismatch for {gz_path}: expected {source['bytes']} bytes, got {size}. "
            "The file is incomplete or is a different version of the archive."
        )
    actual = sha256_of(gz_path)
    if actual != source["sha256"]:
        sys.exit(
            f"SHA-256 mismatch for {gz_path}.\n  expected {source['sha256']}\n  got      {actual}\n"
            "The file is corrupted or is a different version of the archive."
        )
    EMAILS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = EMAILS_PATH.with_suffix(".jsonl.tmp")
    count = 0
    with gzip.open(gz_path, "rb") as src, open(tmp, "wb") as out:
        for line in src:
            out.write(line)
            count += 1
    if count != source["emails"]:
        tmp.unlink()
        sys.exit(f"Expected {source['emails']} emails, found {count} lines. Not installed.")
    if EMAILS_PATH.exists():
        EMAILS_PATH.chmod(0o644)  # the sandbox may have made it read-only
    tmp.replace(EMAILS_PATH)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Install the email archive.")
    parser.add_argument(
        "--from-file",
        metavar="PATH",
        help="install from a local emails.jsonl.gz instead of downloading",
    )
    args = parser.parse_args()

    source = json.loads(SOURCE.read_text())

    if args.from_file:
        gz_path = Path(args.from_file).expanduser()
        if not gz_path.exists():
            sys.exit(f"No such file: {gz_path}")
        count = install(gz_path, source)
    elif BUNDLED.exists():
        count = install(BUNDLED, source)
    else:
        url = source.get("url")
        if not url:
            sys.exit(
                "data/source.json has no download URL yet.\n"
                "Get emails.jsonl.gz from the course staff and run:\n"
                "  uv run python data/download.py --from-file PATH/TO/emails.jsonl.gz"
            )
        with tempfile.TemporaryDirectory() as tmpdir:
            gz_path = Path(tmpdir) / "emails.jsonl.gz"
            try:
                fetch(url, gz_path)
            except OSError as exc:  # URLError and HTTPError are OSErrors
                sys.exit(
                    f"Download failed: {exc}\n"
                    f"Check your connection and try again. You can also download {url} "
                    "yourself and run:\n"
                    "  uv run python data/download.py --from-file PATH/TO/emails.jsonl.gz"
                )
            count = install(gz_path, source)

    size_mb = EMAILS_PATH.stat().st_size / 1e6
    print(f"Installed {count} emails ({size_mb:.1f} MB) at {EMAILS_PATH}")


if __name__ == "__main__":
    main()

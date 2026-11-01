"""Course-provided loaders for the two corpora.

* The email archive, ``data/emails/emails.jsonl``: one JSON object per line,
  sorted by date. It is downloaded by ``uv run python data/download.py``.
* The Cardinal Energy documents, ``data/docs/*.md``, which ship with the
  repository.
"""

from __future__ import annotations

import functools
import json
from pathlib import Path

from cs329z_hw1.types import Email

REPO_ROOT = Path(__file__).resolve().parent.parent
EMAILS_PATH = REPO_ROOT / "data" / "emails" / "emails.jsonl"
DOCS_DIR = REPO_ROOT / "data" / "docs"


@functools.lru_cache(maxsize=2)
def _read_emails(path: Path) -> tuple[list[Email], dict[str, list[Email]]]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} is missing. Run `uv run python data/download.py` to download the email archive."
        )
    emails: list[Email] = []
    by_date: dict[str, list[Email]] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                email = json.loads(line)
                emails.append(email)
                by_date.setdefault(email["date"][:10], []).append(email)
    return emails, by_date


def load_emails() -> list[Email]:
    """Every email in the archive, in file order (sorted by date).

    The file is read once per process and the same list is returned on every
    call, so do not modify the list or the emails in it.
    """
    return _read_emails(EMAILS_PATH)[0]


def emails_on(date: str) -> list[Email]:
    """The emails sent on one calendar day, in archive order.

    ``date`` is "YYYY-MM-DD". An email belongs to the day given by the first
    ten characters of its ``date`` field, which is a UTC timestamp. Returns
    an empty list if there are none.
    """
    return list(_read_emails(EMAILS_PATH)[1].get(date, []))


def email_text(email: Email) -> str:
    """The text of an email that BM25 indexes: subject, newline, body."""
    return email["subject"] + "\n" + email["body"]


def load_docs() -> list[dict]:
    """The Cardinal Energy documents, sorted by ``doc_id``.

    Each document is a dict with three keys. ``doc_id`` is the file name
    without ``.md``. ``title`` is the text of the first line that starts with
    "# ", or the ``doc_id`` if there is no such line. ``text`` is the whole
    file. Line numbers in this assignment are 1-based positions in
    ``text.splitlines()``.
    """
    docs = []
    for path in sorted(DOCS_DIR.glob("*.md"), key=lambda p: p.stem):
        text = path.read_text(encoding="utf-8")
        title = next(
            (line[2:].strip() for line in text.splitlines() if line.startswith("# ")),
            path.stem,
        )
        docs.append({"doc_id": path.stem, "title": title, "text": text})
    return docs

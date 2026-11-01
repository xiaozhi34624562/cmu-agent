"""Small helpers shared by the tests (course-provided; do not edit)."""

from __future__ import annotations

import json
import re
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def truncated(text: str = "", *, max_tokens: int = 64):
    """A ScriptedLM script entry that raises OutputTruncated, as the real LM
    does when the model stops at max_tokens. ``text`` is what the model had
    written so far (``exc.text``)."""
    from cs329z_hw1.llm import OutputTruncated

    def raise_it(messages):
        raise OutputTruncated(
            text, model="scripted", max_tokens=max_tokens, output_tokens=max_tokens, reasoning_tokens=max_tokens - len(text.split())
        )

    return raise_it


def load_fixture(name: str):
    """Load tests/fixtures/<name> (.json, or .jsonl as a list)."""
    path = FIXTURES / name
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(text: str) -> str:
    """Lowercase, drop thousands separators inside numbers, turn every other
    non-alphanumeric run into one space. "$1,250.00 (USD)" -> "1250 00 usd"."""
    text = text.lower()
    text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)
    return " ".join(re.findall(r"[a-z0-9]+", text))


def contains(text: str, alias: str) -> bool:
    """True if ``alias`` appears in ``text`` as a whole-token sequence after
    normalization. contains("There were 120 emails", "12") is False."""
    haystack = f" {normalize(text)} "
    needle = normalize(alias)
    return bool(needle) and f" {needle} " in haystack


def contains_any(text: str, aliases) -> bool:
    return any(contains(text, alias) for alias in aliases)


def events(transcript, type_: str) -> list[dict]:
    """All transcript events of one type, in order."""
    return [e for e in transcript if e.get("type") == type_]

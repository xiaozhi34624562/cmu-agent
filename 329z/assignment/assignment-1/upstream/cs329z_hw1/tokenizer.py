"""Course-provided tokenizer for BM25.

This is the tokenizer the BM25 tests assume. Use it for both documents and
queries so that your scores match the expected ones.
"""

from __future__ import annotations

import re

_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase ``text`` and return its maximal runs of the characters a-z
    and 0-9, in order. Every other character separates tokens.

        tokenize("Re: Q3 gas-price forecast") == ["re", "q3", "gas", "price", "forecast"]
    """
    return _TOKEN.findall(text.lower())

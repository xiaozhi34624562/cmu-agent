"""Shared, title-based names for archived reading materials.

The catalog records titles checked against local PDFs/web pages, original URLs,
old paths, new paths and unchanged content hashes. It also resolves abbreviated
course labels (e.g. MLA) to the full title without changing the archived website.
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path(__file__).with_name("MATERIAL_RENAMES.json")


def url_key(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.lower() in {"arxiv.org", "www.arxiv.org"}:
        match = re.fullmatch(r"/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?/?", parsed.path)
        if match:
            return "arxiv:" + match[1]
    return parsed.netloc.lower() + unquote(parsed.path).rstrip("/") + ("?" + parsed.query if parsed.query else "")


@lru_cache(maxsize=1)
def catalog_indexes() -> tuple[dict, dict]:
    by_url, by_path = {}, {}
    for entry in json.loads(CATALOG.read_text(encoding="utf-8"))["entries"]:
        for key in ("old_path", "path"):
            by_path[str((ROOT / entry[key]).resolve())] = entry
        for url in entry["urls"]:
            key = url_key(url)
            previous = by_url.get(key)
            if previous and Path(previous["path"]).name != Path(entry["path"]).name:
                raise ValueError(f"Ambiguous material URL in {CATALOG}: {url}")
            by_url[key] = entry
    return by_url, by_path


def registered_material(url: str = "", source: Path | None = None) -> dict | None:
    by_url, by_path = catalog_indexes()
    return (by_path.get(str(source.resolve())) if source else None) or by_url.get(url_key(url))


def title_filename(title: str, extension: str) -> str:
    """Keep the complete title; replace filename/Markdown-unsafe punctuation.

    Do not silently truncate a title or drop its distinctive symbols. A title
    exceeding the filesystem component limit needs an explicit catalog name.
    """
    title = unicodedata.normalize("NFKC", title).replace("τ", "tau").replace("#", "Sharp")
    stem = re.sub(r"[^\w.+-]+", "_", title).strip("_.")
    name = stem + extension
    if not stem or len(name.encode("utf-8")) > 250:
        raise ValueError(f"Material needs a readable, filesystem-safe title: {title}")
    return name


def material_filename(title: str, url: str, extension: str, source: Path | None = None) -> str:
    entry = registered_material(url, source)
    if entry:
        name = Path(entry["path"]).name
        if Path(name).suffix == extension:
            return name
        title = entry["title"]
    return title_filename(title, extension)

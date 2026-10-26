#!/usr/bin/env python3
"""Offline checks for the reviewed CMU 11-768 and Harvard CS2680 study guides.

Run from any directory. Content review remains a human/agent reading task;
these checks validate coverage, recorded versions, links and source integrity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prose(text: str) -> str:
    """Remove fenced examples, respecting the outer fence length."""
    lines = []
    fence = None
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence is None:
            if match:
                fence = match[1]
            else:
                lines.append(line)
        elif match and match[1][0] == fence[0] and len(match[1]) >= len(fence):
            fence = None
    if fence is not None:
        raise ValueError("Unclosed Markdown code fence")
    return "\n".join(lines)


def targets(text: str):
    for match in re.finditer(r"!?\[[^\]\n]*\]\(", text):
        start = pos = match.end()
        depth = 1
        while pos < len(text) and depth:
            if text[pos] == "\\":
                pos += 2
                continue
            if text[pos] == "(":
                depth += 1
            elif text[pos] == ")":
                depth -= 1
            pos += 1
        if depth == 0:
            value = text[start:pos - 1].strip()
            if value.startswith("<") and ">" in value:
                value = value[1:value.index(">")]
            else:
                value = re.split(r'\s+["\']', value, maxsplit=1)[0]
            yield value


def anchors(text: str) -> set[str]:
    result = set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)', text))
    seen = {}
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match:
            label = re.sub(r"<[^>]+>", "", match[1]).lower()
            slug = re.sub(r"[^\w\-\s]", "", label).replace(" ", "-")
            count = seen.get(slug, 0)
            seen[slug] = count + 1
            result.add(slug + (f"-{count}" if count else ""))
    return result


def verify(course: str) -> dict:
    folder = ROOT / course
    review_path = folder / "REVIEW.json"
    errors = []
    if not review_path.exists():
        return {"course": course, "errors": ["Missing REVIEW.json"]}
    review = json.loads(review_path.read_text())
    docs = review["documents"]
    indexed = set()
    checked_links = 0
    pdf_counts = {}
    for entry in docs:
        path = ROOT / entry["note"]
        indexed.add(path.resolve())
        if not path.is_file():
            errors.append(f"Missing guide: {entry['note']}")
            continue
        if entry.get("final_sha256") != sha256(path):
            errors.append(f"Review hash stale: {entry['note']}")
        if entry.get("status") != "passed":
            errors.append(f"Review not passed: {entry['note']}")
        try:
            text = prose(path.read_text())
        except ValueError as exc:
            errors.append(f"{entry['note']}: {exc}")
            continue
        if re.search(r"\ue200(?:filecite|cite)|\ue202|turn\d+(?:file|search|view)\d+", text):
            errors.append(f"Conversation-only citation in {entry['note']}")
        if re.search(r"\\[\[\]\(\)]", text):
            errors.append(f"Legacy math delimiter in {entry['note']}")
        for target in targets(text):
            parsed = urlparse(target)
            if parsed.scheme or parsed.netloc:
                continue
            local = path.parent / unquote(parsed.path) if parsed.path else path
            if not local.exists():
                errors.append(f"Broken link: {entry['note']} -> {target}")
                continue
            if parsed.fragment and local.suffix.lower() == ".md":
                if unquote(parsed.fragment) not in anchors(prose(local.read_text())):
                    errors.append(f"Missing anchor: {entry['note']} -> {target}")
            if local.suffix.lower() == ".pdf" and (page := re.search(r"(?:^|&)page=(\d+)", parsed.fragment)):
                try:
                    import fitz
                    key = local.resolve()
                    if key not in pdf_counts:
                        with fitz.open(local) as pdf:
                            pdf_counts[key] = len(pdf)
                    if not 1 <= int(page[1]) <= pdf_counts[key]:
                        errors.append(f"PDF page out of range: {entry['note']} -> {target}")
                except ImportError:
                    errors.append("pymupdf required to validate explicit PDF page links")
            checked_links += 1
    # Include every top-level learning Markdown, excluding indexes and course metadata.
    lessons = sorted(p for p in folder.iterdir() if p.is_dir() and re.match(r"^[1-9]\d*\.", p.name))
    actual = {p.resolve() for lesson in lessons for p in lesson.glob("*.md") if p.name not in {"README.md", "SOURCES.md"}}
    for path in sorted(actual - indexed):
        errors.append(f"Guide missing from review: {path.relative_to(ROOT)}")
    published = []
    for lesson in lessons:
        if list(lesson.glob("*.pdf")) or (course == "2680" and lesson.name.startswith("9.")):
            published.append(lesson.name)
            if not any(p.parent == lesson.resolve() for p in indexed):
                errors.append(f"Published lesson without reviewed guide: {lesson.name}")
    supplemental = 0
    for lesson in lessons:
        refs = lesson / "REFERENCES.json"
        if not refs.exists():
            continue
        for item in json.loads(refs.read_text()):
            if item.get("status") != "saved":
                continue
            path = lesson / item["path"]
            if not path.is_file() or sha256(path) != item["sha256"]:
                errors.append(f"Supplementary source missing or changed: {path.relative_to(ROOT)}")
            supplemental += 1
    original = 0
    for relative, expected in review.get("original_sources", {}).items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != expected:
            errors.append(f"Original source changed: {relative}")
        original += 1
    return {"course": course, "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "reviewed_documents": len(docs), "published_lessons": published,
            "checked_local_links": checked_links, "explicit_pdf_page_links_sources": len(pdf_counts),
            "supplementary_sources": supplemental, "original_source_checksums": original,
            "scope": "Offline structure and integrity; not semantic proof or model benchmark replication",
            "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", choices=["11-768", "2680"])
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    results = [verify(course) for course in ([args.course] if args.course else ["11-768", "2680"])]
    if args.write_report:
        for result in results:
            (ROOT / result["course"] / "VERIFICATION.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    raise SystemExit(1 if any(r["errors"] for r in results) else 0)


if __name__ == "__main__":
    main()

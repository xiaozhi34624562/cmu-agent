#!/usr/bin/env python3
"""Check source integrity, weekly classification and local study-guide links.

Run after sync and after editing notes: python3 courses/MAS.S62/verify.py
Use --require-notes to require a guide for every week with a published PDF.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from sync import ROOT, inspect_download, material_target, parse_schedule, apply_schedule_overrides


def markdown_targets(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    # File names with spaces are URL-encoded by the organizer; angle brackets
    # also support author-written links. Stop at the balanced closing bracket.
    pattern = re.compile(r"!?\[[^\]\n]*\]\(")
    for match in pattern.finditer(text):
        start = match.end()
        depth = 1
        pos = start
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
            target = text[start:pos-1].strip()
            if target.startswith("<") and ">" in target:
                target = target[1:target.index(">")]
            else:
                target = re.split(r'\s+["\']', target, maxsplit=1)[0]
            yield target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-notes", action="store_true")
    parser.add_argument("--allow-deferred-notes", action="store_true",
                        help="Allow only explicit hash-bound deferred entries in REVIEW.json; all other checks remain strict")
    parser.add_argument("--output", type=Path, help="Optional verification JSON destination")
    args = parser.parse_args()
    manifest = json.loads((ROOT/"manifest.json").read_text())
    errors = []
    review = json.loads((ROOT/"REVIEW.json").read_text())
    deferred = {x["week"]: x for x in review.get("deferred_notes", [])}
    accepted_deferred = []
    material_hashes = {x.get("sha256") for x in manifest["resources"] if x["status"] == "saved"}
    for week, item in deferred.items():
        path = ROOT/item["path"]
        if not item.get("reason") or item.get("material_sha256") not in material_hashes:
            errors.append(f"Invalid deferred-note material binding: week {week}")
        if item["status"] == "review_required" and (not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != item.get("sha256")):
            errors.append(f"Deferred unchanged guide checksum mismatch: {item['path']}")
        if item["status"] not in {"review_required", "not_written"}:
            errors.append(f"Unsupported deferred-note state: week {week}")
    # Check the actual archived timetable, not just manifest self-consistency.
    try:
        timetable = apply_schedule_overrides(parse_schedule((ROOT/"site/schedule/index.html").read_text()))
    except (ValueError, OSError) as exc:
        errors.append(str(exc))
        timetable = []
    layout_keys = ("week", "date", "title", "folder")
    archived_layout = [tuple(w[k] for k in layout_keys) for w in timetable]
    indexed_layout = [tuple(w[k] for k in layout_keys) for w in manifest["weeks"]]
    if archived_layout != indexed_layout:
        errors.append("Course folders/dates/titles do not match the archived official timetable")
    indexed_folders = {w["folder"] for w in manifest["weeks"] if w.get("folder")} | {"0.CourseInformation"} | set(manifest.get("retained_folders", {}))
    for folder in ROOT.iterdir():
        if folder.is_dir() and re.match(r"^\d+\.", folder.name) and folder.name not in indexed_folders:
            errors.append(f"Numbered folder absent from the official timetable: {folder.name}")
    saved = 0
    for item in manifest["resources"] + manifest.get("historical_resources", []):
        if item["status"] != "saved":
            continue
        path = ROOT/item["path"]
        if not path.exists():
            errors.append(f"Missing source: {path.relative_to(ROOT)}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != item["sha256"]:
            errors.append(f"Manifest checksum mismatch: {item['path']}")
        try:
            inspect_download(path)
        except (ValueError, RuntimeError) as exc:
            errors.append(f"Invalid saved body: {item['path']}: {exc}")
        for relative in item.get("retained_copies", []):
            retained = ROOT/relative
            if not retained.is_file() or hashlib.sha256(retained.read_bytes()).hexdigest() != item["sha256"]:
                errors.append(f"Historical note source checksum mismatch: {relative}")
        saved += 1
    sources = {r["url"]: r for r in manifest["resources"]}
    required_weeks = []
    copies = 0
    notes = []
    for week in manifest["weeks"]:
        if week.get("folder") is None:
            if week.get("kind") != "no_class" or week.get("materials") or week.get("readings"):
                errors.append(f"Invalid schedule-only no-class row: week {week['week']}")
            continue
        folder = ROOT/week["folder"]
        if not (folder/"SOURCES.md").exists():
            errors.append(f"Missing weekly index: {week['folder']}")
        materials = [r for r in manifest["resources"] if week["week"] in r["weeks"] and r["kind"] in {"lecture", "guest", "tutorial", "notebook", "homework"}]
        if any(r["status"] == "saved" and r["kind"] in {"lecture", "guest", "tutorial"} for r in materials):
            required_weeks.append(week["week"])
            note_missing = not (folder/"notes.zh-CN.md").exists()
            deferred_item = deferred.get(week["week"])
            if args.require_notes and (note_missing or deferred_item):
                if args.allow_deferred_notes and deferred_item and ((note_missing and deferred_item["status"] == "not_written") or (not note_missing and deferred_item["status"] == "review_required")):
                    accepted_deferred.append(deferred_item)
                else:
                    errors.append(f"Missing or review-required study guide: {week['folder']}")
        expected = [(r, material_target(r, folder)) for r in materials if r["status"] == "saved"]
        for index, reading in enumerate(week["readings"], 1):
            r = sources[reading["url"]]
            if r["status"] == "saved":
                expected.append((r, material_target(r, folder, index)))
        for historical in manifest.get("historical_resources", []):
            for relative in historical.get("retained_copies", []):
                if (ROOT/relative).parent.parent == folder:
                    expected.append((historical, ROOT/relative))
        expected_paths = {target.resolve() for _, target in expected}
        for subdirectory in ("slides", "tutorials", "readings"):
            for target in (folder/subdirectory).glob("*"):
                if target.is_file() and target.name != ".DS_Store" and target.resolve() not in expected_paths:
                    errors.append(f"Unindexed course material: {target.relative_to(ROOT)}")
        for item, target in expected:
            if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != item["sha256"]:
                errors.append(f"Classification mismatch: {target.relative_to(ROOT)}")
            copies += 1
        note = folder/"notes.zh-CN.md"
        if note.exists():
            text = note.read_text()
            notes.append(dict(week=week["week"], path=str(note.relative_to(ROOT)), characters=len(text), lines=len(text.splitlines())))
        extra = folder/"REFERENCES.json"
        if extra.exists():
            for r in json.loads(extra.read_text()):
                if r.get("status", "saved") in {"saved", "downloaded"} and r.get("path"):
                    path = folder/r["path"]
                    if not path.is_file():
                        errors.append(f"Missing supplementary source: {path.relative_to(ROOT)}")
                    elif path.suffix in {".pdf", ".html", ".ipynb"}:
                        try:
                            inspect_download(path)
                        except (ValueError, RuntimeError) as exc:
                            errors.append(f"Invalid supplementary body: {path.relative_to(ROOT)}: {exc}")
    checked_links = 0
    pdf_pages = {}
    for path in ROOT.rglob("*.md"):
        if any(p in path.parts for p in ("site", "readings", "references")):
            continue
        for target in markdown_targets(path.read_text()):
            parsed = urlparse(target)
            if parsed.scheme or not parsed.path:
                continue
            local = path.parent/unquote(parsed.path)
            if not local.exists():
                errors.append(f"Broken link in {path.relative_to(ROOT)}: {target}")
            elif local.suffix == ".pdf" and (page := re.search(r"(?:^|&)page=(\d+)", parsed.fragment)):
                try:
                    import fitz
                    resolved = local.resolve()
                    if resolved not in pdf_pages:
                        with fitz.open(local) as doc:
                            pdf_pages[resolved] = len(doc)
                    if not 1 <= int(page.group(1)) <= pdf_pages[resolved]:
                        errors.append(f"PDF page outside source bounds in {path.relative_to(ROOT)}: {target}")
                except ImportError:
                    pass
            checked_links += 1
    checksum_count = 0
    checksummed_paths = set()
    for line in (ROOT/"CHECKSUMS.sha256").read_text().splitlines():
        expected, relative = line.split("  ", 1)
        checksummed_paths.add(relative)
        path = ROOT/relative
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f"Archive checksum mismatch: {relative}")
        checksum_count += 1
    archive_roots = [ROOT/"site", ROOT/"readings", *ROOT.glob("[0-9]*.*/references")]
    actual_archive_paths = {str(path.relative_to(ROOT)) for parent in archive_roots
                            for path in parent.rglob("*") if path.is_file()
                            and path.name != ".DS_Store" and "__pycache__" not in path.parts}
    for relative in sorted(actual_archive_paths - checksummed_paths):
        errors.append(f"Archived source missing from CHECKSUMS.sha256: {relative}")
    for item in manifest.get("supplementary_sources", []):
        if item.get("status") == "saved":
            path = ROOT/item["path"]
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
                errors.append(f"Supplementary manifest checksum mismatch: {item['path']}")
    result = dict(deferred_notes=accepted_deferred, content_review_complete=not deferred,
                  saved_sources=saved, classification_copies=copies, archive_checksums=checksum_count,
                  checked_local_links=checked_links, published_weeks=required_weeks, study_guides=notes, errors=errors)
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()

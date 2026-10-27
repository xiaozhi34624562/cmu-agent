#!/usr/bin/env python3
"""Verify title-based reading names, original bytes and organizer stability.

Run after either course organizer: python3 tools/verify_material_names.py
Use --write-report to save the current result beside the rename catalog.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

from material_names import CATALOG, ROOT, material_filename, title_filename
from verify_course_notes import prose, targets


def load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify() -> dict:
    entries = json.loads(CATALOG.read_text())["entries"]
    errors = []
    destinations = set()
    for entry in entries:
        path = ROOT / entry["path"]
        if path in destinations:
            errors.append(f"Duplicate material destination: {entry['path']}")
        destinations.add(path)
        if not path.is_file():
            errors.append(f"Missing renamed material: {entry['path']}")
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            errors.append(f"Renamed material bytes changed: {entry['path']}")
        if entry["old_path"] != entry["path"] and (ROOT / entry["old_path"]).exists():
            errors.append(f"Old name regenerated: {entry['old_path']}")
        if path.name != title_filename(entry["title"], path.suffix):
            errors.append(f"Filename does not contain the full title: {entry['path']}")
        for url in entry["urls"]:
            if material_filename("course abbreviation", url, path.suffix) != path.name:
                errors.append(f"Source URL resolves to another filename: {url}")

    # Exercise the actual sync/organize entry points without network downloads.
    # Import each independent course script separately (both are named sync.py).
    harvard = load_script("harvard_material_sync", ROOT / "2680/sync.py")
    mit = load_script("mit_material_sync", ROOT / "MAS.S62/sync.py")
    archive_urls = 0
    for entry in entries:
        for url in entry["urls"]:
            path = Path(entry["path"])
            if path.parts[:2] == ("2680", "readings"):
                actual = harvard.reading_destination(url)
                if actual != ROOT / path:
                    errors.append(f"Harvard sync would change a registered path: {entry['path']}")
                archive_urls += 1
            elif path.parts[:2] == ("MAS.S62", "readings"):
                item = mit.paper_resource("course abbreviation", url, "reading")
                if ROOT / "MAS.S62" / item["path"] != ROOT / path:
                    errors.append(f"MIT sync would change a registered path: {entry['path']}")
                archive_urls += 1
    for course in ("11-768", "2680", "MAS.S62"):
        for path in (ROOT / course).rglob("*.pdf"):
            if "site" in path.parts or "assignment" in path.parts or "assignments" in path.parts:
                continue
            if re.fullmatch(r"\d{4}\.\d{4,5}(?:v\d+)?|\d+", path.stem):
                errors.append(f"Number-only reading filename remains: {path.relative_to(ROOT)}")
    material_names = {Path(e[key]).name for e in entries for key in ("old_path", "path")}
    checked_material_links = 0
    for path in ROOT.rglob("*.md"):
        relative = path.relative_to(ROOT)
        if any(part in relative.parts for part in (".git", "code", "course-repo", "site", "readings", "references")):
            continue
        for target in targets(prose(path.read_text(encoding="utf-8"))):
            parsed = urlparse(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            local = path.parent / unquote(parsed.path)
            if local.name not in material_names:
                continue
            checked_material_links += 1
            if not local.is_file():
                errors.append(f"Broken material link: {relative} -> {target}")
    return {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Reading filenames, original content hashes and offline sync path resolution; no paper-content or model-experiment re-review",
        "renamed_materials": len(entries),
        "by_course_or_topic": dict(sorted(Counter(Path(e["path"]).parts[0] for e in entries).items())),
        "by_extension": dict(sorted(Counter(Path(e["path"]).suffix for e in entries).items())),
        "sync_archive_url_checks": archive_urls,
        "checked_material_links": checked_material_links,
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    result = verify()
    if args.write_report:
        CATALOG.with_name("MATERIAL_NAMES_VERIFICATION.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(result["errors"]))


if __name__ == "__main__":
    main()

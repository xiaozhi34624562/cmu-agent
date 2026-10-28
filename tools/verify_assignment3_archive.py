#!/usr/bin/env python3
"""Verify the unchanged CMU Assignment 3 snapshot and shipped dataset structure.

This checks archival integrity, not student solutions or RL learning quality.
Run at any location; --write-report saves assignment-3/VERIFICATION.json.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

from verify_course_notes import prose, targets

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "11-768/assignment/assignment-3"


def verify() -> dict:
    errors = []
    manifest = json.loads((ARCHIVE / "SNAPSHOT.json").read_text())
    expected = {item["path"]: item["sha256"] for item in manifest["files"]}
    if len(expected) != manifest["file_count"]:
        errors.append("Manifest file count or duplicate paths")
    checksum_lines = (ARCHIVE / "CHECKSUMS.sha256").read_text().splitlines()
    checksums = {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in checksum_lines}
    if checksums != expected:
        errors.append("CHECKSUMS.sha256 disagrees with SNAPSHOT.json")
    python_files = links = 0
    for relative, digest in expected.items():
        path = ARCHIVE / relative
        if not path.resolve().is_relative_to(ARCHIVE.resolve()) or not path.is_file():
            errors.append(f"Missing/unsafe upstream path: {relative}")
            continue
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            errors.append(f"Upstream bytes changed: {relative}")
        if path.suffix == ".py":
            try:
                ast.parse(data, filename=relative)
                python_files += 1
            except SyntaxError as exc:
                errors.append(f"Python parse failure: {relative}: {exc}")
    # Include the local source index as well as official Markdown; anchor syntax
    # is renderer-dependent, so this check verifies file targets, not anchors.
    for path in ARCHIVE.rglob("*.md"):
        for target in targets(prose(path.read_text())):
            parsed = urlparse(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            if not (path.parent / unquote(parsed.path)).exists():
                errors.append(f"Broken local link: {path.relative_to(ARCHIVE)} -> {target}")
            links += 1

    recipe_book = json.loads((ARCHIVE / "data/textcraft_recipes.json").read_text())
    known = set(recipe_book["base_items"]) | set(recipe_book["recipes"])
    for name, recipes in recipe_book["recipes"].items():
        for recipe in recipes:
            quantities = [recipe["result_count"], *recipe["ingredients"].values()]
            if not set(recipe["ingredients"]) <= known or any(type(v) is not int or v <= 0 for v in quantities):
                errors.append(f"Invalid recipe quantity/item: {name}")
    seen = set()
    datasets = []
    for filename, count in [
        ("number_search_train.jsonl", 50000), ("number_search_val.jsonl", 1000),
        ("textcraft_train.jsonl", 852), ("textcraft_val.jsonl", 213),
        ("textcraft_val_hard.jsonl", 136),
    ]:
        rows = [json.loads(line) for line in (ARCHIVE / "data" / filename).read_text().splitlines() if line.strip()]
        ids = [row["id"] for row in rows]
        overlap = seen & set(ids)
        if len(rows) != count or len(set(ids)) != len(ids) or overlap:
            errors.append(f"Unexpected count/duplicate ID: {filename}")
        seen.update(ids)
        invalid = []
        for row in rows:
            info = row["info"]
            if filename.startswith("number_search"):
                n = info["high"] - info["low"] + 1
                # For n positive integers, n.bit_length() == ceil(log2(n+1)).
                valid = info["low"] <= info["target"] <= info["high"] and row["max_steps"] == n.bit_length()
            else:
                quantities = [*info["target_items"].values(), *info["initial_inventory"].values()]
                valid = ((set(info["target_items"]) | set(info["initial_inventory"])) <= known
                         and all(type(v) is int and v > 0 for v in quantities)
                         and row["max_steps"] > 0)
            if not valid:
                invalid.append(row["id"])
        if invalid:
            errors.append(f"Invalid task schema/budget: {filename}: {invalid[:5]}")
        datasets.append({"file": filename, "rows": len(rows), "expected_rows": count,
                         "unique_ids": len(set(ids)), "cross_split_id_overlap": sorted(overlap),
                         "invalid_tasks": invalid})
    forbidden = [str(p.relative_to(ARCHIVE)) for p in ARCHIVE.rglob("*")
                 if p.name in {".git", ".env", ".DS_Store", ".venv"}]
    if forbidden:
        errors.append(f"Local artifacts inside archive: {forbidden}")
    return {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": manifest["repository"], "commit": manifest["commit"],
        "upstream_files": len(expected), "python_files_parsed": python_files,
        "local_file_links_checked": links, "datasets": datasets,
        "recipe_items": len(known), "recipe_count": len(recipe_book["recipes"]),
        "base_items": len(recipe_book["base_items"]),
        "scope": "Snapshot hashes, Python syntax, local file links and dataset structure; public-test results recorded separately in BASELINE_TESTS.json.",
        "limitations": ["Does not prove all TextCraft tasks solvable within the action budget.",
                        "No student functions implemented; no model/GPU training or evaluation performed."],
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    report = verify()
    if args.write_report:
        (ARCHIVE / "VERIFICATION.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(bool(report["errors"]))


if __name__ == "__main__":
    main()

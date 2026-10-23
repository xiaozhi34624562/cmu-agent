#!/usr/bin/env python3
"""Download the public CS2680 course site and its assigned readings.

Run from anywhere with ``python3 2680/sync.py``. Requires requests and bs4.
The course site is mirrored under site/; external reading URLs are indexed,
with PDFs and accessible HTML snapshots stored under readings/.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urljoin, urlparse, urlunparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


ROOT = Path(__file__).resolve().parent
BASE = "https://cs2680.com/"
HOST = "cs2680.com"
REPO = "https://github.com/HarvardMadSys/cs2680_assignments.git"
TODAY = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
VENDOR = {
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css": ROOT / "site/vendor/bootstrap.min.css",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js": ROOT / "site/vendor/bootstrap.bundle.min.js",
}
ALTERNATE_READINGS = {
    "https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents": "https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf",
    "https://docs.nvidia.com/cuda/cuda-c-programming-guide/": "https://docs.nvidia.com/cuda/pdf/CUDA_C_Programming_Guide.pdf",
}

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "CS2680-personal-study-archive/1.0"})
SESSION.mount("https://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])))


def normalized_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    return urlunparse((parsed.scheme, parsed.netloc.lower(), path, "", parsed.query, ""))


def local_path(url: str) -> Path:
    parsed = urlparse(url)
    path = unquote(parsed.path)
    parts = PurePosixPath(path).parts
    if ".." in parts or "\\" in path:
        raise ValueError(f"Unsafe URL path: {url}")
    if path.endswith("/") or not path:
        path += "index.html"
    elif not PurePosixPath(path).suffix:
        path += ".html"
    target = ROOT / "site" / path.lstrip("/")
    if parsed.query:
        digest = hashlib.sha256(parsed.query.encode()).hexdigest()[:10]
        target = target.with_name(f"{target.stem}-{digest}{target.suffix}")
    return target


def write_response(url: str, dest: Path) -> tuple[str, int]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with SESSION.get(url, timeout=35, stream=True) as response:
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0]
            with tempfile.NamedTemporaryFile(dir=dest.parent, prefix=f".{dest.name}.", delete=False) as file:
                temporary = Path(file.name)
                for chunk in response.iter_content(128 * 1024):
                    file.write(chunk)
        if temporary.stat().st_size == 0:
            raise ValueError(f"Empty response: {url}")
        os.replace(temporary, dest)
        return content_type, dest.stat().st_size
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def mirror_site() -> tuple[dict[str, Path], list[tuple[str, str]]]:
    queue = deque([BASE, BASE + "header.html"])
    seen: set[str] = set()
    mirrored: dict[str, Path] = {}
    failures: list[tuple[str, str]] = []
    while queue:
        url = normalized_url(queue.popleft())
        parsed = urlparse(url)
        if url in seen or parsed.netloc != HOST or parsed.path.startswith("/cdn-cgi/"):
            continue
        seen.add(url)
        dest = local_path(url)
        try:
            content_type, size = write_response(url, dest)
            mirrored[url] = dest
            print("SITE", size, dest.relative_to(ROOT))
            if content_type == "text/html":
                soup = BeautifulSoup(dest.read_bytes(), "html.parser")
                for tag in soup.select("a[href], link[href], script[src], img[src], source[src]"):
                    value = tag.get("href") or tag.get("src")
                    if not value or value.startswith(("#", "mailto:", "javascript:", "data:")):
                        continue
                    child = normalized_url(urljoin(url, value))
                    if urlparse(child).netloc == HOST:
                        queue.append(child)
            time.sleep(0.08)
        except (requests.RequestException, OSError, ValueError) as exc:
            failures.append((url, str(exc)))
            print("FAILED SITE", url, exc)
    for url, dest in VENDOR.items():
        try:
            content_type, size = write_response(url, dest)
            if content_type not in {"text/css", "application/javascript", "text/javascript"}:
                raise ValueError(f"Unexpected vendor content type: {content_type}")
            mirrored[url] = dest
            print("VENDOR", size, dest.relative_to(ROOT))
        except (requests.RequestException, OSError, ValueError) as exc:
            failures.append((url, str(exc)))
    # Make same-domain links work from local HTML while retaining original pages.
    for url, dest in mirrored.items():
        if dest.suffix != ".html":
            continue
        soup = BeautifulSoup(dest.read_bytes(), "html.parser")
        changed = False
        for tag in soup.select("a[href], link[href], script[src], img[src], source[src]"):
            key = "href" if tag.has_attr("href") else "src"
            value = tag.get(key, "")
            if not value or value.startswith(("#", "mailto:", "javascript:", "data:")):
                continue
            absolute = urljoin(url, value)
            parsed = urlparse(absolute)
            normalized = normalized_url(absolute)
            if normalized not in mirrored:
                continue
            relative = os.path.relpath(mirrored[normalized], dest.parent)
            tag[key] = relative + ("#" + parsed.fragment if parsed.fragment else "")
            changed = True
        if changed:
            dest.write_text(str(soup), encoding="utf-8")
    return mirrored, failures


def reading_links(mirrored: dict[str, Path]) -> dict[str, list[str]]:
    readings: dict[str, list[str]] = {}
    pages = [BASE, BASE + "readings.html"] + [url for url in mirrored if url.startswith(BASE + "readings/") and url.endswith(".html")]
    for url in pages:
        path = mirrored.get(url)
        if not path:
            continue
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        # The home-page schedule and detailed reading tables identify assigned work.
        selector = "table a[href]" if url in {BASE, BASE + "readings.html"} else "table.readings-table a[href]"
        for anchor in soup.select(selector):
            href = anchor.get("href", "")
            original = normalized_url(urljoin(url, href))
            host = urlparse(original).netloc
            if host and host != HOST and host not in {"madsys.seas.harvard.edu"}:
                title = anchor.get_text(" ", strip=True)
                if title and title not in readings.setdefault(original, []):
                    readings[original].append(title)
    return readings


def reading_destination(url: str) -> Path | None:
    if url in ALTERNATE_READINGS:
        return ROOT / "readings" / "papers" / Path(urlparse(ALTERNATE_READINGS[url]).path).name
    parsed = urlparse(url)
    if parsed.netloc in {"www.youtube.com", "youtube.com", "youtu.be"}:
        return None
    arxiv = re.search(r"/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:\.pdf)?$", parsed.path)
    if parsed.netloc == "arxiv.org" and arxiv:
        return ROOT / "readings" / "papers" / f"{arxiv.group(1)}.pdf"
    if parsed.path.lower().endswith(".pdf"):
        name = Path(unquote(parsed.path)).name
        return ROOT / "readings" / "papers" / name
    host = parsed.netloc.replace("www.", "").replace(".", "-")
    name = re.sub(r"[^a-z0-9]+", "-", parsed.path.lower()).strip("-")[-70:] or "index"
    digest = hashlib.sha256(url.encode()).hexdigest()[:8]
    stem = f"{host}-{name}-{digest}"
    detected_pdf = ROOT / "readings" / "papers" / f"{stem}.pdf"
    if detected_pdf.exists():
        return detected_pdf
    return ROOT / "readings" / "web" / f"{stem}.html"


def reading_snapshot_issue(path: Path) -> str | None:
    """An HTTP 200 verification page is not the requested reading."""
    if path.suffix != ".html" or not path.exists():
        return None
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    title = soup.title.get_text(" ", strip=True).lower() if soup.title else ""
    if title in {"verifying your browser | openreview", "just a moment...", "access denied", "403 forbidden"}:
        return "Archived browser verification/access page; reading body not downloaded"
    return None


def download_readings(readings: dict[str, list[str]]) -> tuple[dict[str, Path], list[tuple[str, str]]]:
    saved: dict[str, Path] = {}
    failures: list[tuple[str, str]] = []
    def download_one(url: str) -> tuple[str, Path | None, str | None]:
        dest = reading_destination(url)
        if dest is None:
            return url, None, None
        if dest.exists():
            if issue := reading_snapshot_issue(dest):
                return url, None, issue
            return url, dest, None
        download_url = ALTERNATE_READINGS.get(url, url)
        if urlparse(url).netloc == "arxiv.org":
            match = re.search(r"(\d{4}\.\d{4,5})", url)
            if match:
                download_url = f"https://arxiv.org/pdf/{match.group(1)}"
        try:
            content_type, size = write_response(download_url, dest)
            with dest.open("rb") as content:
                is_pdf = content.read(5) == b"%PDF-"
            if dest.suffix == ".html" and content_type == "application/pdf" and is_pdf:
                pdf_dest = ROOT / "readings" / "papers" / f"{dest.stem}.pdf"
                pdf_dest.parent.mkdir(parents=True, exist_ok=True)
                os.replace(dest, pdf_dest)
                dest = pdf_dest
            expected = "application/pdf" if dest.suffix == ".pdf" else "text/html"
            if content_type != expected or (dest.suffix == ".pdf" and not is_pdf):
                dest.unlink()
                raise ValueError(f"Expected {expected}, received {content_type}")
            if issue := reading_snapshot_issue(dest):
                return url, None, issue
            print("READING", size, dest.relative_to(ROOT))
            return url, dest, None
        except (requests.RequestException, OSError, ValueError) as exc:
            print("FAILED READING", url, exc)
            return url, None, str(exc)

    # Multiple course pages may link the same arXiv paper by abs and PDF URL.
    # Download each local file once to avoid concurrent writes to one path.
    grouped: dict[Path, list[str]] = {}
    for url in readings:
        dest = reading_destination(url)
        if dest is not None:
            grouped.setdefault(dest, []).append(url)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(download_one, urls[0]): urls for urls in grouped.values()}
        for future in as_completed(futures):
            url, dest, error = future.result()
            if dest:
                for related_url in futures[future]:
                    saved[related_url] = dest
            elif error:
                for related_url in futures[future]:
                    failures.append((related_url, error))
    return saved, failures


def archive_code() -> str | None:
    target = ROOT / "assignments" / "course-repo"
    metadata_path = ROOT / "assignments" / "SNAPSHOT.json"
    metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {"repository": REPO}
    metadata["last_attempt"] = TODAY
    with tempfile.TemporaryDirectory(prefix="cs2680-") as temp:
        try:
            subprocess.run(["git", "clone", "--depth", "1", "--quiet", REPO, temp + "/repo"], check=True, timeout=90)
            sha = subprocess.check_output(["git", "-C", temp + "/repo", "rev-parse", "HEAD"], text=True).strip()
            for source in (Path(temp) / "repo").iterdir():
                if source.is_dir() and re.fullmatch(r"assignment\d+", source.name):
                    shutil.copytree(source, target / source.name, dirs_exist_ok=True)
            metadata.update(commit=sha, snapshot_date=TODAY, status="updated")
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
            print("CODE", sha)
            return sha
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
            metadata["status"] = "upstream_unavailable"
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
            print("FAILED CODE", exc)
            return None


def write_sources(mirrored: dict[str, Path], readings: dict[str, list[str]], saved: dict[str, Path], site_failures: list[tuple[str, str]], reading_failures: list[tuple[str, str]], sha: str | None) -> None:
    lines = [
        "# CS2680 来源索引",
        "",
        f"- 课程：[CS2680 Modern AI Systems]({BASE})（2026 Fall）",
        f"- 本地同步日期：{TODAY}",
        "- `site/` 保存课程网站公开页面和站内文件；网页中的站内链接已改为本地路径。",
        "- `readings/` 保存可获取的外部论文 PDF 和网页快照；视频保留原始链接。",
        "- 原始网页内容、PDF 和作业代码均未翻译或修改；网页仅调整了站内链接。",
        "",
        "## 课程网站",
        "",
        "| 本地文件 | 原始链接 |",
        "|---|---|",
    ]
    for url, path in sorted(mirrored.items(), key=lambda item: str(item[1])):
        lines.append(f"| [{path.relative_to(ROOT)}]({path.relative_to(ROOT)}) | {url} |")
    lines += ["", "## 外部阅读资料", "", "| 阅读材料 | 本地文件 | 原始链接 |", "|---|---|---|"]
    for url, titles in readings.items():
        title = ", ".join(titles).replace("|", "\\|")
        path = saved.get(url)
        local = f"[{path.relative_to(ROOT)}]({path.relative_to(ROOT)})" if path else "仅链接"
        if path is None:
            snapshot = reading_destination(url)
            if snapshot is not None and reading_snapshot_issue(snapshot):
                relative = snapshot.relative_to(ROOT)
                local = f"[验证网页（无阅读正文）]({relative})"
        if path and url in ALTERNATE_READINGS:
            local += f"（[官方替代地址]({ALTERNATE_READINGS[url]})）"
        lines.append(f"| {title} | {local} | {url} |")
    lines += ["", "## 作业代码", ""]
    if sha:
        lines += [
            f"- 公开代码仓库：[HarvardMadSys/cs2680_assignments](https://github.com/HarvardMadSys/cs2680_assignments/tree/{sha})",
            f"- 固定提交：`{sha}`",
            "- 本地快照：[`assignments/course-repo/`](assignments/course-repo/)；保留上游 `assignment2/` 和 `assignment3/` 结构。",
        ]
    else:
        lines.append(f"- 公开代码仓库：{REPO}（本次未能获取快照）。")
        metadata_path = ROOT / "assignments" / "SNAPSHOT.json"
        metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
        if metadata.get("commit"):
            lines += [
                f"- 保留已有快照：[`assignments/course-repo/`](assignments/course-repo/)，获取日期 {metadata.get('snapshot_date', '未记录')}。",
                f"- 固定提交：`{metadata['commit']}`（本次未更新）。",
                "- 快照状态与版本：[`assignments/SNAPSHOT.json`](assignments/SNAPSHOT.json)。",
            ]
    archive = ROOT / "site" / "assignments" / "assignment2.tar.gz"
    if archive.exists():
        lines.append("- 网站提供的原始压缩包：[`site/assignments/assignment2.tar.gz`](site/assignments/assignment2.tar.gz)。")
        lines.append("- 原站文件名后缀是 `.tar.gz`，实际文件内容为普通 POSIX tar；可用 `tar -xf` 解包。公开仓库快照中的 `assignment2/` 与该归档内容一致。")
    for archive in sorted((ROOT / "site" / "assignments").glob("assignment*.tar.gz")):
        if archive.name != "assignment2.tar.gz":
            relative = archive.relative_to(ROOT)
            lines.append(f"- 网站提供的原始作业归档：[`{relative}`]({relative})；Source: {BASE}assignments/{archive.name}")
    lines += ["", "## 未获取的文件", ""]
    if not site_failures and not reading_failures:
        lines.append("- 无。")
    else:
        for url, error in site_failures + reading_failures:
            lines.append(f"- {url} — {error.replace(chr(10), ' ')[:180]}")
    (ROOT / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_checksums() -> None:
    lines = []
    for directory in ("site", "readings", "assignments"):
        for path in sorted((ROOT / directory).rglob("*")):
            if not path.is_file() or path.name == ".DS_Store" or "__pycache__" in path.parts:
                continue
            digest = hashlib.sha256()
            with path.open("rb") as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(chunk)
            lines.append(f"{digest.hexdigest()}  {path.relative_to(ROOT)}")
    (ROOT / "CHECKSUMS.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    mirrored, site_failures = mirror_site()
    readings = reading_links(mirrored)
    saved, reading_failures = download_readings(readings)
    sha = archive_code()
    write_sources(mirrored, readings, saved, site_failures, reading_failures, sha)
    from organize import main as organize_main

    organize_main()
    write_checksums()
    print("TOTAL", len(mirrored), "site files,", len(readings), "readings,", len(saved), "external files")


if __name__ == "__main__":
    main()

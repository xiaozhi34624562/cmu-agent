#!/usr/bin/env python3
"""Archive public MIT MAS.S62 Fall 2026 materials and organize weekly folders.

Run: python3 courses/MAS.S62/sync.py [--organize-only]
Dependencies: requests, beautifulsoup4. Optional pymupdf adds PDF metadata.
Original downloads are retained; generated indexes never overwrite study notes.
"""
from __future__ import annotations

import argparse
import copy as copy_module
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urljoin, urlparse, urlunparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1] / "tools"))
from material_names import material_filename, registered_material, title_filename, url_key

BASE = "https://mit-mi.github.io/how2ai-course/fall2026/"
ASSETS = "https://mit-mi.github.io/how2ai-course/assets/"
TODAY = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
SYLLABUS = "https://docs.google.com/document/d/1H1vs32fhWaxEuP6-nA2GP-a1aFuEmjOXNMcer2UyKpM/"
TEXTGRAD_ID = "1rL24Ydm9yQKRUPoGXHr2-zJumFbBRfvJ"
HW1_ID = "1aavmbVb3ykhv--jnhoCA_q6AylUhq0EW"
PDF_TITLES = {
    "lec1 - intro.pdf": "Lecture 1 — Introduction",
    "lec2 - context.pdf": "Lecture 2 — Context Evolution",
    "context_guest.pdf": "Guest — Agentic Context Engineering",
    "lec3 - llm optimizers.pdf": "Lecture 3 — LLMs as Context Optimizers",
    "lec4 - harness.pdf": "Lecture 4 — Harness Evolution",
    "harness_guest.pdf": "Guest — Rethinking the role of harnesses in LMs",
    "harness engineering tutorial.pdf": "Tutorial — Harness Engineering (Ao Qu)",
    "lec5 - multi agent.pdf": "Lecture 5 — Multi-Agent Evolution",
    "lec6 - training.pdf": "Lecture 6 — Test-time Training",
    "lec6 - rl in practice.pdf": "Tutorial — RL and Self-Distillation in Practice",
    "model_guest.pdf": "Guest — Continual Learning via Self-Distillation",
}


PAPER_TITLES = {"arxiv:2504.13837": "Does Reinforcement Learning Really Incentivize Reasoning Capacity in LLMs Beyond the Base Model?"}


def normalized(url):
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc.lower(), p.path, "", p.query, ""))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug(text, limit=90):
    text = text.replace("τ", "tau").replace("#", "Sharp")
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")[:limit] or "material"


def link(title, target, parent):
    return f"[{title}]({quote(os.path.relpath(target, parent), safe='/._-')})"


def resource(title, url, kind, weeks=(), path=None, download_url=None):
    url = normalized(url)
    return dict(id=hashlib.sha256(url.encode()).hexdigest()[:12], title=title,
                url=url, kind=kind, weeks=list(weeks), path=path,
                download_url=download_url or url, status="pending")


def session():
    s = requests.Session()
    s.headers["User-Agent"] = "MAS-S62-public-personal-study-archive/1.0"
    s.mount("https://", HTTPAdapter(max_retries=Retry(total=2, backoff_factor=.4,
              status_forcelist=[429, 500, 502, 503, 504])))
    return s


def inspect_download(path):
    data = path.read_bytes()
    if not data:
        raise ValueError("Empty download")
    meta = {}
    if path.suffix == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise ValueError("Expected PDF bytes, received another document")
        try:
            import fitz
            with fitz.open(path) as doc:
                meta.update(pages=len(doc), cover=" ".join(doc[0].get_text().split()))
                match = re.search(r"arXiv:(\d{4}\.\d{4,5}v\d+)", doc[0].get_text())
                if match:
                    meta["pdf_version"] = match.group(1)
        except ImportError:
            pass
    elif path.suffix == ".ipynb":
        notebook = json.loads(data)
        if not isinstance(notebook.get("cells"), list) or not notebook.get("nbformat"):
            raise ValueError("Response is not a Jupyter notebook")
        meta["cells"] = len(notebook["cells"])
    elif path.suffix == ".html":
        soup = BeautifulSoup(data, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        meta["html_title"] = title
        if any(x in title.lower() for x in ("verifying your browser", "just a moment", "access denied", "sign in - google")):
            raise ValueError(f"Verification/login page; reading body unavailable: {title}")
    return meta


def reuse_repository_body(item, target):
    """Reuse only a matching arXiv body; record provenance, never a new download."""
    match = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", item["url"])
    if not match or target.exists():
        return False
    repository = ROOT.parents[1]
    for candidate in sorted(repository.rglob(target.name)):
        if candidate == target or candidate.suffix != ".pdf":
            continue
        metadata = inspect_download(candidate)
        if not metadata.get("pdf_version", "").startswith(match.group(1) + "v"):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidate, target)
        item.update(reused_from=str(candidate.relative_to(repository)),
                    reuse_checked_at=TODAY, acquisition="repository_reuse")
        return True
    return False


def retain_version(item, target):
    old_hash = digest(target)
    archive = ROOT / "site/versions" / old_hash / target.name
    archive.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, archive)
    entry = dict(title=item["title"], url=item["url"], kind=item["kind"],
                 path=str(archive.relative_to(ROOT)), sha256=old_hash,
                 status="saved", superseded_at=TODAY, **inspect_download(archive))
    pinned = ROOT / "7.ModelEvolution1/tutorials/lec6 - rl in practice.pdf"
    entry.update(bytes=target.stat().st_size, previous_retrieved_at=item.get("retrieved_at"),
                 original_path=item["path"])
    if target.name == "lec6 - rl in practice.pdf" and pinned.is_file() and digest(pinned) == old_hash:
        entry.update(weeks=[7], retained_copies=[str(pinned.relative_to(ROOT))],
                     reason="Existing unchanged W7 guide cites this 15-page edition; current tutorial is W9")
    else:
        entry.update(weeks=[], retained_copies=[], reason="Superseded official source retained for provenance")
    versions = item.setdefault("versions", [])
    if not any(v["sha256"] == old_hash for v in versions):
        versions.append(entry)


def fetch(item, refresh=False):
    target = ROOT / item["path"]
    temporary = None
    try:
        if not refresh:
            reuse_repository_body(item, target)
        if not target.exists() or refresh:
            response = session().get(item["download_url"], timeout=35)
            response.raise_for_status()
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent, suffix=target.suffix, delete=False) as f:
                temporary = Path(f.name)
                f.write(response.content)
            meta = inspect_download(temporary)
            if target.exists() and digest(target) != digest(temporary) and item["kind"] != "site":
                retain_version(item, target)
            os.replace(temporary, target)
            item["retrieved_at"] = TODAY
            item["content_type"] = response.headers.get("Content-Type", "")
            item["final_url"] = response.url
            item["content_disposition"] = response.headers.get("Content-Disposition", "")
        else:
            meta = inspect_download(target)
            if item.get("acquisition") != "repository_reuse":
                item.setdefault("retrieved_at", TODAY)
        item.update(meta, status="saved", sha256=digest(target), bytes=target.stat().st_size)
        item.pop("error", None)
        print("SAVED", item["path"], flush=True)
    except (requests.RequestException, OSError, ValueError, RuntimeError) as exc:
        item.update(status="unavailable", checked_at=TODAY, error=str(exc)[:450])
        if target.exists():
            item["retained_snapshot"] = True
        print("UNAVAILABLE", item["url"], item["error"][:110], flush=True)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return item


def parse_schedule(html):
    soup = BeautifulSoup(html, "html.parser")
    weeks = []
    for row in soup.select("table tr"):
        cells = row.find_all(["th", "td"], recursive=False)
        if len(cells) < 3 or not re.fullmatch(r"\d+/\d+", cells[0].get_text(strip=True)):
            continue
        number = int(re.search(r"Week\s+(\d+)", cells[1].get_text()).group(1))
        title = cells[1].find("strong").get_text(" ", strip=True)
        month, day = cells[0].get_text(strip=True).split("/")
        folder = f"{number}." + "".join(word[0].upper() + word[1:] for word in re.findall(r"[A-Za-z0-9]+", title))
        weeks.append(dict(week=number, date=f"2026-{int(month):02d}-{int(day):02d}",
            title=title, folder=folder, topics=[li.get_text(" ", strip=True) for li in cells[1].select("li")],
            materials=[dict(label=a.get_text(" ", strip=True), url=normalized(urljoin(BASE+"schedule/", a["href"]))) for a in cells[1].select("a[href]")],
            readings=[dict(title=a.get_text(" ", strip=True), url=normalized(urljoin(BASE+"schedule/", a["href"]))) for a in cells[2].select("a[href]")]))
    if not weeks or len({w["week"] for w in weeks}) != len(weeks):
        raise ValueError("Schedule is empty or has duplicate weeks")
    return weeks


def paper_resource(title, url, kind, weeks=()):
    entry = registered_material(url)
    if entry:
        title = entry["title"]
    title = PAPER_TITLES.get(url_key(url), title)
    match = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)", url)
    if match:
        paper_id = match.group(1)
        name = title_filename(title, ".pdf") if url_key(url) in PAPER_TITLES else material_filename(title, url, ".pdf")
        return resource(title, url, kind, weeks, f"readings/papers/{name}", f"https://arxiv.org/pdf/{paper_id}")
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix == ".pdf":
        path = "readings/papers/" + material_filename(title, url, ".pdf")
    else:
        path = "readings/web/" + material_filename(title, url, ".html")
    return resource(title, url, kind, weeks, path)


def schedule_semantic_digest(weeks):
    rows = []
    for week in weeks:
        row = {key: week[key] for key in ("week", "date", "title", "folder", "topics")}
        row["materials"] = [{key: item[key] for key in ("label", "url")} for item in week["materials"]]
        row["readings"] = [{key: item[key] for key in ("title", "url")} for item in week["readings"]]
        rows.append(row)
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def apply_schedule_overrides(weeks):
    path = ROOT / "SCHEDULE_OVERRIDES.json"
    if not path.exists():
        return weeks
    policy = json.loads(path.read_text())
    if schedule_semantic_digest(weeks) != policy["conflicting_source"]["semantic_sha256"]:
        raise ValueError("Official HTML schedule content changed; recheck overrides before remapping weeks")
    source = ROOT / policy["authority"]["path"]
    if not source.is_file() or digest(source) != policy["authority"]["sha256"]:
        raise ValueError("Schedule override authority checksum mismatch; recheck the official syllabus")
    original = {w["week"]: w for w in weeks}
    current = []
    for week in weeks:
        override = policy.get("weeks", {}).get(str(week["week"]))
        row = copy_module.deepcopy(original[override.get("content_from_week", week["week"])]) if override else copy_module.deepcopy(week)
        if override:
            row.update({k: v for k, v in override.items() if k != "content_from_week"})
            row["week"] = week["week"]
            row["schedule_authority"] = "official_syllabus_override"
        current.append(row)
    return current


def build_manifest(refresh_materials=()):
    previous_path = ROOT / "manifest.json"
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {}
    old = {r["url"]: r for r in previous.get("resources", [])}
    resources = []
    for suffix, filename in (("", "index.html"), ("schedule/", "schedule/index.html"), ("projects/", "projects/index.html")):
        item = resource("Course " + (suffix.strip("/") or "home"), BASE+suffix, "site", path="site/"+filename)
        resources.append(fetch(item, refresh=True))
    schedule = ROOT / "site/schedule/index.html"
    if resources[1]["status"] != "saved":
        raise RuntimeError("Cannot read current course schedule; existing notes and materials preserved")
    weeks = parse_schedule(schedule.read_text())
    seen = {r["url"]: r for r in resources}

    def add(item):
        if item["url"] in seen:
            existing = seen[item["url"]]
            existing["weeks"] = sorted(set(existing["weeks"] + item["weeks"]))
            return
        if item["url"] in old:
            item = {**old[item["url"]], **item, **{k:old[item["url"]][k] for k in ("retrieved_at",) if k in old[item["url"]]}}
        seen[item["url"]] = item
        resources.append(item)

    # Only this semester and its referenced shared assets are in scope.
    for page in resources[:3]:
        if page["status"] != "saved":
            continue
        soup = BeautifulSoup((ROOT/page["path"]).read_text(), "html.parser")
        for tag in soup.select("img[src], script[src], link[href]"):
            href = tag.get("src") or tag.get("href")
            url = normalized(urljoin(page["url"], href))
            if url.startswith(ASSETS):
                relative = unquote(url[len(ASSETS):])
                if ".." not in PurePosixPath(relative).parts:
                    add(resource(Path(relative).name, url, "asset", path="site/assets/"+relative))
    for week in weeks:
        for material in week["materials"]:
            url = material["url"]
            if url == BASE+"schedule/":
                material["status"] = "placeholder"
                continue
            if urlparse(url).path.endswith(".pdf") and url.startswith(BASE):
                name = Path(unquote(urlparse(url).path)).name
                kind = "tutorial" if "tutorial" in name or name == "lec6 - rl in practice.pdf" else "guest" if "guest" in name else "lecture"
                add(resource(PDF_TITLES.get(name, material["label"]), url, kind, [week["week"]], "site/schedule/"+name))
        for reading in week["readings"]:
            add(paper_resource(reading["title"], reading["url"], "reading", [week["week"]]))
    add(resource("TextGrad Tutorial", f"https://colab.research.google.com/drive/{TEXTGRAD_ID}", "notebook", [2],
                 "site/tutorials/Textgrad_tutorial.ipynb", f"https://drive.google.com/uc?export=download&id={TEXTGRAD_ID}"))
    add(resource("Homework 1 (linked from Lecture 3 p.38)", f"https://colab.research.google.com/drive/{HW1_ID}", "homework", [3],
                 "site/assignments/OpenEvolve_assignment.ipynb", f"https://drive.google.com/uc?export=download&id={HW1_ID}"))
    for fmt in ("pdf", "txt"):
        add(resource("Official syllabus ("+fmt+")", SYLLABUS+"export?format="+fmt, "syllabus",
                     path="site/syllabus/ai4ai-syllabus."+fmt))
    projects = ROOT / "site/projects/index.html"
    if projects.exists():
        soup = BeautifulSoup(projects.read_text(), "html.parser")
        for a in soup.select("article a[href]"):
            url = normalized(urljoin(BASE+"projects/", a["href"]))
            title = a.get_text(" ", strip=True)
            if title and any(host in urlparse(url).netloc for host in ("arxiv.org", "openreview.net", "aclanthology.org", "openaccess.thecvf.com", "dl.acm.org", "ttic.edu", "nips2018vigil.github.io", "cmu-multicomp-lab.github.io")):
                add(paper_resource(title, url, "previous_project"))
    pending = [r for r in resources if r["status"] != "saved"]
    def acquire(item):
        refresh = any(value in (item["url"], item["path"], Path(item["path"]).name)
                      for value in refresh_materials)
        return fetch(item, refresh=refresh)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(acquire, pending))
    # Linked paper landing pages can expose the actual public PDF.
    attachments = []
    for item in list(resources):
        if item["status"] != "saved" or item["kind"] != "previous_project" or not item["path"].endswith(".html"):
            continue
        soup = BeautifulSoup((ROOT/item["path"]).read_bytes(), "html.parser")
        for a in soup.select("a[href]"):
            url = normalized(urljoin(item["url"], a["href"]))
            if urlparse(url).path.endswith(".pdf") and urlparse(url).netloc in {"aclanthology.org", "openaccess.thecvf.com"}:
                attachment = paper_resource(item["title"] + " (PDF)", url, "project_attachment")
                if url not in seen:
                    add(attachment)
                    attachments.append(seen[url])
                break
    # CSS font URLs retain their original relative layout for offline browsing.
    for item in list(resources):
        if item["kind"] != "asset" or item["status"] != "saved" or not item["path"].endswith(".css"):
            continue
        for href in re.findall(r"url\(['\"]?([^)'\"]+)", (ROOT/item["path"]).read_text()):
            url = normalized(urljoin(item["url"], href))
            if url.startswith(ASSETS) and url not in seen:
                relative = unquote(urlparse(url).path.split("/how2ai-course/assets/",1)[1])
                if ".." not in PurePosixPath(relative).parts:
                    add(resource(Path(relative).name, url, "asset", path="site/assets/"+relative))
                    attachments.append(seen[url])
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(fetch, attachments))
    current_weeks = apply_schedule_overrides(weeks)
    historical = [version for item in resources for version in item.get("versions", [])]
    return dict(course="MIT MAS.S62 — How to AI an AI for (Almost) Anything", semester="Fall 2026",
                snapshot_date=TODAY, base_url=BASE, weeks=current_weeks, resources=resources,
                historical_resources=historical,
                retained_folders={"12.FutureTopics": "Old W12 future topics merged into current W14; directory retained"},
                schedule_policy="SCHEDULE_OVERRIDES.json")


def material_target(item, folder, index=0):
    name = Path(item["path"]).name
    if item["kind"] in {"lecture", "guest"}:
        return folder / "slides" / name
    if item["kind"] in {"tutorial", "notebook"}:
        return folder / "tutorials" / name
    if item["kind"] == "homework":
        return ROOT / "assignment/assignment-1" / name
    return folder / "readings" / (name if url_key(item["url"]) in PAPER_TITLES else material_filename(item["title"], item["url"], Path(name).suffix, ROOT / item["path"]))


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or digest(source) != digest(target):
        shutil.copy2(source, target)


def latest_schedule_updates(manifest):
    """Expose newer syllabus links without claiming their bodies were fetched."""
    layout_path = ROOT.parent / 'COURSE_LAYOUT.json'
    if not layout_path.exists():
        return {}
    layout = json.loads(layout_path.read_text())
    if layout['as_of'] <= manifest['snapshot_date']:
        return {}
    rows = {row['id']: row for row in layout['rows'] if row['course'] == 'MIT MAS.S62'}
    updates = {}
    for week in manifest['weeks']:
        row = rows.get(f"MIT-W{week['week']}")
        if row is None:
            continue
        changed = any({url_key(item['url']) for item in row.get(key, [])}
                      != {url_key(item['url']) for item in week[key]}
                      for key in ('materials', 'readings'))
        if changed or any(row[key] != week[key] for key in ('date', 'title')):
            updates[week['week']] = dict(row, as_of=layout['as_of'])
    return updates


def latest_schedule_lines(row, manifest, folder):
    sources = {url_key(item['url']): item for item in manifest['resources'] + manifest.get('supplementary_sources', [])}
    lines = [f"## 最新完整课表（{row['as_of']}）", "",
             f"- [完整课表](../COURSE_SCHEDULE.md)：{row['date']} · {row['title']}。",
             "- 本节更新课表入口与指定阅读分类；未重新下载的正文不计作新版本，下面另保留旧归档及其讲解。", "",
             "### Lecture links", ""]
    for item in row.get('materials', []):
        url = quote(item['url'], safe=':/?#=&%')
        label = item['label'].strip('[]')
        lines.append(f"- [{label}]({url})")
        saved = sources.get(url_key(item['url']), {})
        if saved.get('status') == 'saved' and (ROOT / saved['path']).is_file():
            weeks = ', '.join(str(number) for number in saved.get('weeks', []))
            lines.append(f"  - {link('已有归档版本', ROOT / saved['path'], folder)}；旧归档归于 Week {weeks}。最新正文与课次归属待复核，不能据此认定本周讲义已齐备。")
        else:
            lines.append("  - 已有官网入口，尚未取得并核实本周正文。")
    if not row.get('materials'):
        lines.append('- 最新完整课表尚未列出可下载讲义。')
    lines += ["", "### Assigned readings", ""]
    for index, reading in enumerate(row.get('readings', []), 1):
        saved = sources.get(url_key(reading['url']), {})
        lines.append(f"- R{index:02d}: [{reading['label']}]({reading['url']})")
        if saved.get('status') == 'saved' and (ROOT / saved['path']).is_file():
            version = saved.get('pdf_version') or saved.get('version') or '以文件正文为准'
            lines.append(f"  - {link('已归档正文', ROOT / saved['path'], folder)}；版本：{version}。复用已有资料，本轮未重新获取。")
        else:
            lines.append('  - 未取得正文；先保留最新指定阅读入口，下载并核实后再记为已归档。')
    if not row.get('readings'):
        lines.append('- 最新完整课表未单列指定阅读。')
    return lines + ['']


def organize(manifest):
    review = json.loads((ROOT/"REVIEW.json").read_text()) if (ROOT/"REVIEW.json").exists() else {}
    deferred = {item["week"]: item for item in review.get("deferred_notes", [])}
    by_url = {r["url"]: r for r in manifest["resources"]}
    updates = latest_schedule_updates(manifest)
    for week in manifest["weeks"]:
        if week.get("folder") is None:
            continue
        folder = ROOT / week["folder"]
        folder.mkdir(parents=True, exist_ok=True)
        lines = [f"# Week {week['week']} — {week['title']}", "", f"- Date: {week['date']}",
                 f"- Source: {BASE}schedule/", f"- 资料归档日期：{manifest['snapshot_date']}；最新日历见[完整课表](../COURSE_SCHEDULE.md)。",
                 "- 目录编号保持稳定；当前官方 Week、日期单独记录，原 PDF 内的 Lecture 编号和文件名保持原样。", ""]
        if week.get("schedule_authority"):
            lines += ["- 当前安排依据[官方大纲及冲突处理](../SCHEDULE_OVERRIDES.json)；网页旧课表正文保留，未据此改写。", ""]
        if week['week'] in updates:
            lines += latest_schedule_lines(updates[week['week']], manifest, folder)
        lines += ["## Topics（归档快照）", ""]
        lines += [f"- {topic}" for topic in week["topics"]]
        lines += ["", "## Lecture, guest lectures and tutorials（归档快照）", ""]
        found = False
        for item in manifest["resources"]:
            if week["week"] not in item["weeks"] or item["kind"] not in {"lecture", "guest", "tutorial", "notebook", "homework"}:
                continue
            found = True
            if item["status"] == "saved":
                target = material_target(item, folder)
                copy(ROOT/item["path"], target)
                label = item["title"]
                lines += [f"- {link(target.name, target, folder)} — {item['kind']}", f"  - 内容：{label}",
                          f"  - Source: {item['url']}", f"  - SHA256: `{item['sha256']}`"]
                if item.get("pages"):
                    lines.append(f"  - PDF pages: {item['pages']}")
            else:
                lines += [f"- {item['title']} — 未获取正文；[原始入口]({item['url']})", f"  - Status: {item.get('error', 'unavailable')}"]
        if not found:
            lines.append("- 此次归档未取得本周讲义；项目展示周另见项目要求。")
        if any(m.get("status") == "placeholder" for m in week["materials"]):
            lines.append("- 此次归档时 [slides] 指回课表，为占位链接；这不代表最新完整课表的发布状态。")
        lines += ["", "## Assigned readings（归档快照）", ""]
        for index, reading in enumerate(week["readings"], 1):
            item = by_url[reading["url"]]
            if item["status"] == "saved":
                target = material_target(item, folder, index)
                copy(ROOT/item["path"], target)
                lines += [f"- R{index:02d}: {link(item['title'], target, folder)}", f"  - Source: {reading['url']}"]
                if item.get("pdf_version"):
                    lines.append("  - PDF version: " + item["pdf_version"])
            else:
                lines += [f"- R{index:02d}: [{reading['title']}]({reading['url']}) — 未取得正文", f"  - Status: {item.get('error', 'unavailable')}"]
        if not week["readings"]:
            lines.append("- 此次归档课表未单列本周阅读。" + ("最新指定阅读见上方更新节；" if week['week'] in updates else "") + "讲义引用及补充材料见下方 References。")
        historical = [r for r in manifest.get("historical_resources", []) if week["week"] in r.get("weeks", [])]
        if historical:
            lines += ["", "## 旧讲解绑定版本（保留原引用）", ""]
            for item in historical:
                lines += [f"- {link(item['title'], ROOT/item['path'], folder)}：旧版 {item.get('pages', '?')} 页，SHA256 `{item['sha256']}`。当前新版归属W9；本周旧讲解未修改，内容/页码复核延期，见 REVIEW.json。"]
                for relative in item.get("retained_copies", []):
                    lines.append(f"  - {link('旧讲解原链接', ROOT/relative, folder)}；保留旧字节，不替换为新版。")
        lines += ["", "## References and local study guide", ""]
        if (ROOT/"LECTURE_LINKS.json").exists():
            lines.append("- [讲义内嵌链接及其 PDF 页码](../LECTURE_LINKS.json)；JSON 按 week、pdf、page 记录，视频和通用网站入口仅作来源导航。")
        extra = folder / "REFERENCES.json"
        if extra.exists():
            for item in json.loads(extra.read_text()):
                target = folder/item["path"] if item.get("path") else None
                label = link(item["title"], target, folder) if target and target.is_file() and item.get("status", "saved") in {"saved", "downloaded"} else item["title"] + " — 仅保留来源入口/未获取正文"
                lines += [f"- {label}", f"  - Source: {item['url']}"]
        note = folder / "notes.zh-CN.md"
        if week["week"] in deferred:
            lines.append(f"- {link('旧版中文讲解（待复核）', note, folder)}；本轮只同步资料，旧版来源绑定及延期事项见 [REVIEW.json](../REVIEW.json)。" if note.exists() else "- 中文讲解：按本轮授权范围延期，资料已同步；未编写或审核新讲解，见 [REVIEW.json](../REVIEW.json)。")
        else:
            lines.append(f"- {link('完整中文课程讲解', note, folder)}" if note.exists() else "- 中文讲解：等待对应讲义资料齐备后编写。")
        (folder/"SOURCES.md").write_text("\n".join(lines)+"\n")
    for name, reason in manifest.get("retained_folders", {}).items():
        folder = ROOT/name
        folder.mkdir(exist_ok=True)
        (folder/"SOURCES.md").write_text("# 历史计划入口 — Future topics\n\n" + reason + "\n\n当前计划合并至[Week14](../14.FutureTopics/SOURCES.md)。本目录保留，不代表11月25日仍开设Future topics。\n\n来源：[官方大纲优先规则](../SCHEDULE_OVERRIDES.json)。\n")
    write_indexes(manifest, updates)


def write_indexes(manifest, updates):
    review = json.loads((ROOT/"REVIEW.json").read_text()) if (ROOT/"REVIEW.json").exists() else {}
    deferred = {item["week"]: item for item in review.get("deferred_notes", [])}
    resources = manifest["resources"]
    info = ROOT / "0.CourseInformation"
    info.mkdir(exist_ok=True)
    lines = ["# 课程信息与大纲", "", f"- Snapshot: {manifest['snapshot_date']}", f"- [官网]({BASE})", ""]
    for r in resources:
        if r["kind"] in {"syllabus", "site"}:
            label = link(r["title"], ROOT/r["path"], info) if r["status"] == "saved" else r["title"]+" — unavailable"
            lines += [f"- {label}", f"  - Source: {r['url']}"]
    (info/"SOURCES.md").write_text("\n".join(lines)+"\n")
    project = ROOT / "project"
    project.mkdir(exist_ok=True)
    lines = ["# 项目要求与往届参考", "", "项目要求以本学期 syllabus 为准；下列项目页及报告属于往届公开案例，不能作为本学期课程讲义或本届学生成果。", "",
             "- [本学期 syllabus](../site/syllabus/ai4ai-syllabus.pdf)", "- [官网项目案例页](../site/projects/index.html)", ""]
    for r in resources:
        if r["kind"] in {"previous_project", "project_attachment"}:
            label = link(r["title"], ROOT/r["path"], project) if r["status"] == "saved" else r["title"]+" — 未取得正文"
            lines += [f"- {label}", f"  - Source: {r['url']}"]
    (project/"SOURCES.md").write_text("\n".join(lines)+"\n")
    assignment = ROOT / "assignment"
    assignment.mkdir(exist_ok=True)
    lines = ["# 课程作业", "", "当前官方大纲逐项列Context、Harness、Model三项，但概述仍写四次作业；旧版第四项Task evolution是否取消未确认。具体题目和提交要求以教师最新说明为准。", "",
             "- [课程大纲](../site/syllabus/ai4ai-syllabus.pdf)", "- [Canvas（提交平台，需要对应课程权限）](https://canvas.mit.edu/courses/40521/)", ""]
    for r in resources:
        if r["kind"] == "homework":
            target = material_target(r, assignment)
            if r["status"] == "saved":
                copy(ROOT/r["path"], target)
                lines += [f"- {link(r['title'], target, assignment)}", f"  - Source: {r['url']}"]
                (target.parent/"SOURCES.md").write_text(f"# Homework 1\n\n- {link(target.name, target, target.parent)}\n- Source: {r['url']}\n- 入口来自 Lecture 3 p.38；保留原 notebook 内容和输出，未执行其中模型调用。\n")
            else:
                lines += [f"- [{r['title']}]({r['url']}) — 未获取正文", f"  - Status: {r.get('error', '')}"]
    lines += ["", "其余作业尚未在已核查公开页面发现可下载正文，保留大纲计划及 Canvas 入口。"]
    pending_details = {
        2: ("Harness evolution", "当前大纲保留此项，暂定SkillOpt、DGM或Meta-Harness；公开完整题目、代码和提交时间未取得。"),
        3: ("Model evolution", "当前大纲保留此项，暂定test-time training或continual learning；公开完整题目、代码和提交时间未取得。已有OpenEvolve notebook内题为Assignment 3，但课内入口归属仍待教师确认，不据此挪作Model作业。"),
        4: ("Task evolution — 状态未确认", "旧版大纲曾暂定PostTrainBench；当前大纲逐项列表不再列此项，但概述仍称四次作业。不能据此认定已取消，公开正文和教师确认均未取得。")}
    for number, (title, detail) in pending_details.items():
        pending = assignment / f"assignment-{number}" / "SOURCES.md"
        pending.parent.mkdir(exist_ok=True)
        pending.write_text(f"# MAS.S62：计划作业 {number} — {title}\n\n- 状态核对：{manifest['snapshot_date']}。\n- {detail}\n- [当前官方大纲](../../site/syllabus/ai4ai-syllabus.pdf)；[官方入口]({BASE})；[Canvas（需课程权限）](https://canvas.mit.edu/courses/40521/)。\n\n本目录仅保存来源和状态；未取得正文时不生成题目、starter或答案。\n")
        lines.append(f"- {link(f'计划作业 {number}：来源与状态', pending, assignment)}")
    (assignment/"SOURCES.md").write_text("\n".join(lines)+"\n")
    lines = ["# MAS.S62 全部来源", "", f"- 同步日期：{manifest['snapshot_date']}", f"- 本学期官网：{BASE}",
             "- 下载状态及 SHA256 见 [manifest.json](manifest.json)；HTTP 200 的登录/验证页面不计为阅读正文。",
             "- [完整课表](COURSE_SCHEDULE.md)可能更新于此归档；新发布但未取得的资料入口保留在逐周 SOURCES.md。", "",
             "| 类型 | 资料 | 本地文件/状态 | 来源 |", "|---|---|---|---|"]
    for r in resources:
        local = link(Path(r["path"]).name, ROOT/r["path"], ROOT) if r["status"] == "saved" else "未获取正文："+r.get("error", "unavailable").replace("|", " ")
        lines.append(f"| {r['kind']} | {r['title'].replace('|',' / ')} | {local} | {r['url']} |")
    lines += ["", "## 已保留的历史来源版本", "", "旧讲解不自动改绑新版；以下旧字节及版本关系保留用于追溯。", ""]
    for item in manifest.get("historical_resources", []):
        lines.append(f"- {link(item['title'], ROOT/item['path'], ROOT)}：SHA256 `{item['sha256']}`；{item['reason']}。")
    lines += ["", "## 逐课补充来源", ""]
    lines += ["补充来源由各课 REFERENCES.json 登记；核验日期表示本地文件检查日期，复用旧归档时不冒充原始下载日期。", "",
              "| 周次 | 补充资料 | 本地文件/状态 | 原始来源 |", "|---|---|---|---|"]
    for item in manifest.get("supplementary_sources", []):
        local = link(Path(item["path"]).name, ROOT/item["path"], ROOT) if item["status"] == "saved" else "未获取正文"
        lines.append(f"| {item['week']} | {item['title']} | {local} | {item['url']} |")
    (ROOT/"SOURCES.md").write_text("\n".join(lines)+"\n")
    pdfs = [r for r in resources if r["kind"] in {"lecture", "guest", "tutorial"} and r["status"] == "saved"]
    readings = [r for r in resources if r["kind"] == "reading"]
    lines = ["# MIT MAS.S62：自演化 AI 学习资料", "", "**How to AI an AI for (Almost) Anything · Fall 2026 · Paul Liang / Ao Qu**", "",
             "本资料库目录编号保持稳定，当前官方Week和日期单独记录。Lecture 构成中文讲解主线，Readings 补充机制与实验，References 补背景和实现。正文区分原文结论、教学推导与工程建议。", "",
             f"资料同步日期：**{manifest['snapshot_date']}**。已归档 {len(pdfs)} 份课程 PDF；课表有 {len(readings)} 个去重阅读入口，其中 {sum(r['status']=='saved' for r in readings)} 个已保存正文。", "",
             f"[官网]({BASE}) · [官方课表]({BASE}schedule/) · [全部来源](SOURCES.md) · [课程大纲](0.CourseInformation/SOURCES.md) · [作业](assignment/SOURCES.md) · [项目](project/SOURCES.md)", "",
             "## 课程目录", "", "| Week / 日期 | 官网课程名称 | 材料状态 | 中文讲解 |", "|---|---|---|---|"]
    for w in manifest["weeks"]:
        if w.get("folder") is None:
            lines.append(f"| {w['week']} / {w['date'][5:]} | {w['title']} | 停课（官方大纲）；网页课表冲突见 SCHEDULE_OVERRIDES.json | 无教学讲解要求 |")
            continue
        folder = ROOT/w["folder"]
        count = sum(w["week"] in r["weeks"] for r in pdfs)
        status = f"{count} 份 PDF" if count else "项目展示周" if "presentations" in w["title"] else "讲义链接尚为占位"
        note = folder/"notes.zh-CN.md"
        study = link("完整讲解", note, ROOT) if note.exists() else "见项目要求" if "presentations" in w["title"] else "待对应讲义公开" if not count else "编写中"
        if w["week"] in deferred:
            study = link("旧版讲解（待复核）", note, ROOT) if note.exists() else "延期未编写；见 REVIEW.json"
        if w['week'] in updates:
            status = f"旧归档 {count} 份 PDF；新课表入口与指定阅读见本周索引" if count else "新课表已有资料入口；最新正文/课次归属待复核"
            if not note.exists():
                study = "待本周讲义核实后编写"
        lines.append(f"| {w['week']} / {w['date'][5:]} | {link(w['title'], folder/'SOURCES.md', ROOT)} | {status} | {study} |")
    lines += ["", "## 学习方法", "", "1. 先阅读本课 notes.zh-CN.md 的导读与材料映射，建立核心问题。", "2. 沿正文学习机制、公式、实现案例和论文证据，按页码回读原讲义。", "3. 用自测及实验设计检查理解；区分来源已经报告的实验与尚未运行的本地实验计划。", "4. 更新系统时同时检查效果、预算、泛化、退化和回滚条件。", "",
              "## 归档与维护", "", "- site/：本学期页面、讲义、大纲导出、教程与公开作业 notebook；原始下载不翻译。", "- readings/：课程论文及往届公开项目参考的原始归档；下载状态见 manifest.json。", "- 每周 slides/、tutorials/、readings/ 是分类学习副本；讲义与教程保留官方原名，论文和阅读网页使用完整标题命名。", "- 论文原文件名、现路径、来源 URL 和未改变的内容校验值见 [文件改名记录](../../tools/MATERIAL_RENAMES.json)；同步与整理共用标题命名规则。", "- 周次不等于 PDF 的 Lecture 编号；例如 Week 5 对应 Lecture 4。", "- `lec6 - rl in practice.pdf` 当前19页版本按网页材料归属放在W9 tutorials/；W7旧讲解及其原链接仍绑定15页历史版本，未修改讲解正文，复核状态见 REVIEW.json。", "- 当前计划按官方Google大纲的明确停课/日期安排维护；原网页课表正文保留，冲突与来源优先规则见 [SCHEDULE_OVERRIDES.json](SCHEDULE_OVERRIDES.json)。", "- W9 已提供完整中文讲解；W7 受影响的历史内容仍显式延期，具体状态见 REVIEW.json。结构校验不替代内容审核。", "- 官网后续 [slides] 占位不计作讲义；未获取正文的材料保留明确状态。", "- 项目展示周按课表保留目录，项目参考注明为往届成果。", "",
              "更新：`python3 courses/MAS.S62/sync.py`；只重建分类与索引：`python3 courses/MAS.S62/sync.py --organize-only`。需要 requests、beautifulsoup4；pymupdf 可补充 PDF 封面和页数。更新脚本保留 notes.zh-CN.md、人工补充 references/ 和学习记录。", "",
              "校验： [CHECKSUMS.sha256](CHECKSUMS.sha256) 覆盖原始归档及逐课补充材料；[manifest.json](manifest.json) 记录 URL、下载地址、状态和版本信息。运行 `python3 courses/MAS.S62/verify.py --require-notes` 执行严格校验；本轮资料同步允许显式延期时增加 `--allow-deferred-notes`，仅放行 REVIEW.json 中绑定材料哈希的显式延期项（当前为W7），其他检查保持严格。", "",
              "[LECTURE_LINKS.json](LECTURE_LINKS.json) 另保存讲义内嵌的原始链接及实际 PDF 页码，便于追溯讲义中的参考、视频与作业入口。"]
    if (ROOT/"REVIEW.json").exists():
        lines += ["", "当前内容审核状态见 [REVIEW.json](REVIEW.json)，保留逐课版本、最近阅读范围、复读结论与核验限制；校验结果直接输出到终端。"]
    if (ROOT/"COURSE_SCHEDULE.md").exists():
        lines[2:2] = ["[完整课表与待更新目录](COURSE_SCHEDULE.md) · [四课学习路线](../ROADMAP.zh-CN.md)", "", "完整日历和当前发布状态见上述索引；下表为本次材料归档版本。", ""]
    (ROOT/"README.md").write_text("\n".join(lines)+"\n")


def checksums():
    paths = set()
    for parent in (ROOT/"site", ROOT/"readings"):
        paths.update(p for p in parent.rglob("*") if p.is_file())
    for parent in ROOT.glob("[0-9]*.*/references"):
        paths.update(p for p in parent.rglob("*") if p.is_file())
    paths = sorted(p for p in paths if p.name != ".DS_Store" and "__pycache__" not in p.parts)
    (ROOT/"CHECKSUMS.sha256").write_text("".join(f"{digest(p)}  {p.relative_to(ROOT)}\n" for p in paths))


def lecture_links(manifest):
    try:
        import fitz
    except ImportError:
        return
    rows = []
    for item in manifest["resources"] + manifest.get("historical_resources", []):
        if item["kind"] not in {"lecture", "guest", "tutorial"} or item["status"] != "saved":
            continue
        with fitz.open(ROOT/item["path"]) as doc:
            for page, content in enumerate(doc, 1):
                for target in content.get_links():
                    url = target.get("uri", "")
                    if url.startswith(("https://", "http://")):
                        rows.append(dict(weeks=item["weeks"], pdf=item["path"], sha256=item["sha256"],
                                         version_status="historical" if "superseded_at" in item else "current",
                                         page=page, url=url))
    (ROOT/"LECTURE_LINKS.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2)+"\n")


def supplementary_sources(manifest):
    rows = []
    for week in manifest["weeks"]:
        if week.get("folder") is None:
            continue
        folder = ROOT/week["folder"]
        index = folder/"REFERENCES.json"
        if not index.exists():
            continue
        for source in json.loads(index.read_text()):
            item = dict(source, week=week["week"], verified_at=TODAY)
            path = folder/source["path"] if source.get("path") else None
            if path:
                item["path"] = str(path.relative_to(ROOT))
            if path and path.is_file() and source.get("status", "saved") in {"saved", "downloaded"}:
                try:
                    item.update(inspect_download(path), status="saved", sha256=digest(path), bytes=path.stat().st_size)
                except (ValueError, RuntimeError) as exc:
                    item.update(status="unavailable", error=str(exc))
            else:
                item["status"] = "unavailable"
            rows.append(item)
    manifest["supplementary_sources"] = rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--organize-only", action="store_true")
    parser.add_argument("--refresh-materials", nargs="+", default=[], metavar="PATH_OR_URL",
                        help="Explicitly refresh named source files/URLs; changed old bytes are versioned")
    args = parser.parse_args()
    if args.organize_only:
        manifest = json.loads((ROOT/"manifest.json").read_text())
    else:
        manifest = build_manifest(args.refresh_materials)
        # Keep official HTML byte-for-byte; offline classification indexes provide local navigation.
    supplementary_sources(manifest)
    (ROOT/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
    lecture_links(manifest)
    organize(manifest)
    checksums()
    print("DONE", len(manifest["weeks"]), "weeks;", sum(r["status"] == "saved" for r in manifest["resources"]), "saved sources", flush=True)


if __name__ == "__main__":
    main()

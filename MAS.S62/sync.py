#!/usr/bin/env python3
"""Archive public MIT MAS.S62 Fall 2026 materials and organize weekly folders.

Run: python3 MAS.S62/sync.py [--organize-only]
Dependencies: requests, beautifulsoup4. Optional pymupdf adds PDF metadata.
Original downloads are retained; generated indexes never overwrite study notes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
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
    "lec6 - rl in practice.pdf": "Tutorial — RL and Self-Distillation (pp.1–2: guest introduction)",
    "model_guest.pdf": "Guest — Continual Learning via Self-Distillation",
}


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


def fetch(item, refresh=False):
    target = ROOT / item["path"]
    temporary = None
    try:
        if not target.exists() or refresh:
            response = session().get(item["download_url"], timeout=35)
            response.raise_for_status()
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent, suffix=target.suffix, delete=False) as f:
                temporary = Path(f.name)
                f.write(response.content)
            meta = inspect_download(temporary)
            os.replace(temporary, target)
            item["retrieved_at"] = TODAY
            item["content_type"] = response.headers.get("Content-Type", "")
            item["final_url"] = response.url
            item["content_disposition"] = response.headers.get("Content-Disposition", "")
        else:
            meta = inspect_download(target)
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
    match = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)", url)
    if match:
        paper_id = match.group(1)
        return resource(title, url, kind, weeks, f"readings/papers/{paper_id}.pdf", f"https://arxiv.org/pdf/{paper_id}")
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix == ".pdf":
        path = f"readings/papers/{Path(unquote(urlparse(url).path)).name}"
    else:
        path = f"readings/web/{slug(urlparse(url).netloc+'_'+urlparse(url).path,75)}_{hashlib.sha256(url.encode()).hexdigest()[:8]}.html"
    return resource(title, url, kind, weeks, path)


def build_manifest():
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
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(fetch, pending))
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
    return dict(course="MIT MAS.S62 — How to AI an AI for (Almost) Anything", semester="Fall 2026",
                snapshot_date=TODAY, base_url=BASE, weeks=weeks, resources=resources)


def material_target(item, folder, index=0):
    name = Path(item["path"]).name
    if item["kind"] in {"lecture", "guest"}:
        return folder / "slides" / name
    if item["kind"] in {"tutorial", "notebook"}:
        return folder / "tutorials" / name
    if item["kind"] == "homework":
        return ROOT / "assignment/assignment-1" / name
    return folder / "readings" / f"{index:03d}_{slug(item['title'],72)}_{name}"


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or digest(source) != digest(target):
        shutil.copy2(source, target)


def organize(manifest):
    by_url = {r["url"]: r for r in manifest["resources"]}
    for week in manifest["weeks"]:
        folder = ROOT / week["folder"]
        folder.mkdir(parents=True, exist_ok=True)
        lines = [f"# Week {week['week']} — {week['title']}", "", f"- Date: {week['date']}",
                 f"- Source: {BASE}schedule/", "- 编号采用官网 Week；原 PDF 内的 Lecture 编号和文件名保持原样。", "", "## Topics", ""]
        lines += [f"- {topic}" for topic in week["topics"]]
        lines += ["", "## Lecture, guest lectures and tutorials", ""]
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
            lines.append("- 本周为项目展示，或官网尚未发布讲义正文。")
        if any(m.get("status") == "placeholder" for m in week["materials"]):
            lines.append("- 官网 [slides] 当前指回课表，是占位链接，不计为已发布讲义。")
        lines += ["", "## Assigned readings", ""]
        for index, reading in enumerate(week["readings"], 1):
            item = by_url[reading["url"]]
            if item["status"] == "saved":
                target = material_target(item, folder, index)
                copy(ROOT/item["path"], target)
                lines += [f"- R{index:02d}: {link(reading['title'], target, folder)}", f"  - Source: {reading['url']}"]
                if item.get("pdf_version"):
                    lines.append("  - PDF version: " + item["pdf_version"])
            else:
                lines += [f"- R{index:02d}: [{reading['title']}]({reading['url']}) — 未取得正文", f"  - Status: {item.get('error', 'unavailable')}"]
        if not week["readings"]:
            lines.append("- 官网课表没有单独列出本周阅读；讲义内引用及补充材料见下方 References。")
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
        lines.append(f"- {link('完整中文课程讲解', note, folder)}" if note.exists() else "- 中文讲解：等待对应讲义资料齐备后编写。")
        (folder/"SOURCES.md").write_text("\n".join(lines)+"\n")
    write_indexes(manifest)


def write_indexes(manifest):
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
    lines = ["# 课程作业", "", "大纲计划四次作业：Context、Harness、Model、Task evolution；具体日期、题目和提交要求以教师最新说明为准。", "",
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
    (assignment/"SOURCES.md").write_text("\n".join(lines)+"\n")
    lines = ["# MAS.S62 全部来源", "", f"- 同步日期：{manifest['snapshot_date']}", f"- 本学期官网：{BASE}",
             "- 下载状态及 SHA256 见 [manifest.json](manifest.json)；HTTP 200 的登录/验证页面不计为阅读正文。", "",
             "| 类型 | 资料 | 本地文件/状态 | 来源 |", "|---|---|---|---|"]
    for r in resources:
        local = link(Path(r["path"]).name, ROOT/r["path"], ROOT) if r["status"] == "saved" else "未获取正文："+r.get("error", "unavailable").replace("|", " ")
        lines.append(f"| {r['kind']} | {r['title'].replace('|',' / ')} | {local} | {r['url']} |")
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
             "本资料库按官网 Week 组织。Lecture 构成中文讲解主线，Readings 补充机制与实验，References 补背景和实现。正文区分原文结论、教学推导与工程建议。", "",
             f"资料同步日期：**{manifest['snapshot_date']}**。已归档 {len(pdfs)} 份课程 PDF；课表有 {len(readings)} 个去重阅读入口，其中 {sum(r['status']=='saved' for r in readings)} 个已保存正文。", "",
             f"[官网]({BASE}) · [官方课表]({BASE}schedule/) · [全部来源](SOURCES.md) · [课程大纲](0.CourseInformation/SOURCES.md) · [作业](assignment/SOURCES.md) · [项目](project/SOURCES.md)", "",
             "## 课程目录", "", "| Week / 日期 | 官网课程名称 | 材料状态 | 中文讲解 |", "|---|---|---|---|"]
    for w in manifest["weeks"]:
        folder = ROOT/w["folder"]
        count = sum(w["week"] in r["weeks"] for r in pdfs)
        status = f"{count} 份 PDF" if count else "项目展示周" if "presentations" in w["title"] else "讲义链接尚为占位"
        note = folder/"notes.zh-CN.md"
        study = link("完整讲解", note, ROOT) if note.exists() else "见项目要求" if "presentations" in w["title"] else "待对应讲义公开" if not count else "编写中"
        lines.append(f"| {w['week']} / {w['date'][5:]} | {link(w['title'], folder/'SOURCES.md', ROOT)} | {status} | {study} |")
    lines += ["", "## 学习方法", "", "1. 先阅读本课 notes.zh-CN.md 的导读与材料映射，建立核心问题。", "2. 沿正文学习机制、公式、实现案例和论文证据，按页码回读原讲义。", "3. 用自测及实验设计检查理解；区分来源已经报告的实验与尚未运行的本地实验计划。", "4. 更新系统时同时检查效果、预算、泛化、退化和回滚条件。", "",
              "## 归档与维护", "", "- site/：本学期页面、讲义、大纲导出、教程与公开作业 notebook；原始下载不翻译。", "- readings/：课程论文及往届公开项目参考的原始归档；下载状态见 manifest.json。", "- 每周 slides/、tutorials/、readings/ 是分类学习副本；原始文件名保留。", "- 周次不等于 PDF 的 Lecture 编号；例如 Week 5 对应 Lecture 4。", "- `lec6 - rl in practice.pdf` 前两页为嘉宾介绍，后续为 RL/自蒸馏实践教程；学习副本归入第 7 周 tutorials/，以全文内容说明用途。", "- 官网后续 [slides] 占位不计作讲义；未获取正文的材料保留明确状态。", "- 项目展示周按课表保留目录，项目参考注明为往届成果。", "",
              "更新：`python3 MAS.S62/sync.py`；只重建分类与索引：`python3 MAS.S62/sync.py --organize-only`。需要 requests、beautifulsoup4；pymupdf 可补充 PDF 封面和页数。更新脚本保留 notes.zh-CN.md、人工补充 references/ 和学习记录。", "",
              "校验： [CHECKSUMS.sha256](CHECKSUMS.sha256) 覆盖原始归档及逐课补充材料；[manifest.json](manifest.json) 记录 URL、下载地址、状态和版本信息。运行 `python3 MAS.S62/verify.py --require-notes` 检查归档校验值、分类副本、来源状态与讲解链接。", "",
              "[LECTURE_LINKS.json](LECTURE_LINKS.json) 另保存讲义内嵌的原始链接及实际 PDF 页码，便于追溯讲义中的参考、视频与作业入口。"]
    if (ROOT/"REVIEW.json").exists():
        lines += ["", "内容复核与修正记录见 [REVIEW.json](REVIEW.json)，包含逐课覆盖、修改后复读及核验限制；复核范围以记录日期与文件校验值为准。"]
    (ROOT/"README.md").write_text("\n".join(lines)+"\n")


def checksums():
    paths = set()
    for parent in (ROOT/"site", ROOT/"readings"):
        paths.update(p for p in parent.rglob("*") if p.is_file())
    for parent in ROOT.glob("[0-9]*.*/references"):
        paths.update(p for p in parent.rglob("*") if p.is_file())
    paths = sorted(p for p in paths if p.name != ".DS_Store" and "__pycache__" not in p.parts)
    (ROOT/"CHECKSUMS.sha256").write_text("".join(f"{digest(p)}  {p.relative_to(ROOT)}\n" for p in paths))


def localize_pages(manifest):
    """Only rewrite navigation; downloads' original URLs stay in manifest."""
    targets = {r["url"]: ROOT/r["path"] for r in manifest["resources"] if r["status"] == "saved"}
    for item in manifest["resources"]:
        if item["kind"] != "site" or item["status"] != "saved":
            continue
        path = ROOT/item["path"]
        soup = BeautifulSoup(path.read_bytes(), "html.parser")
        for tag in soup.select("a[href], link[href], img[src], script[src]"):
            key = "href" if tag.has_attr("href") else "src"
            original = urljoin(item["url"], tag[key])
            target = targets.get(normalized(original))
            if target:
                tag[key] = quote(os.path.relpath(target, path.parent), safe="/._-") + ("#"+urlparse(original).fragment if urlparse(original).fragment else "")
            elif tag[key].startswith("//"):
                tag[key] = "https:" + tag[key]
        path.write_text(str(soup))
        item["sha256"] = digest(path)


def lecture_links(manifest):
    try:
        import fitz
    except ImportError:
        return
    rows = []
    for item in manifest["resources"]:
        if item["kind"] not in {"lecture", "guest", "tutorial"} or item["status"] != "saved":
            continue
        with fitz.open(ROOT/item["path"]) as doc:
            for page, content in enumerate(doc, 1):
                for target in content.get_links():
                    url = target.get("uri", "")
                    if url.startswith(("https://", "http://")):
                        rows.append(dict(weeks=item["weeks"], pdf=item["path"], page=page, url=url))
    (ROOT/"LECTURE_LINKS.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2)+"\n")


def supplementary_sources(manifest):
    rows = []
    for week in manifest["weeks"]:
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
    args = parser.parse_args()
    if args.organize_only:
        manifest = json.loads((ROOT/"manifest.json").read_text())
    else:
        manifest = build_manifest()
        localize_pages(manifest)
    supplementary_sources(manifest)
    (ROOT/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
    lecture_links(manifest)
    organize(manifest)
    checksums()
    print("DONE", len(manifest["weeks"]), "weeks;", sum(r["status"] == "saved" for r in manifest["resources"]), "saved sources", flush=True)


if __name__ == "__main__":
    main()

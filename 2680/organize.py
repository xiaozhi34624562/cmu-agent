#!/usr/bin/env python3
"""Build CMU-style course folders from the raw CS2680 source archive.

The original downloads remain in site/, readings/, and assignments/. This
script copies available materials into numbered lesson and assignment folders,
and writes one SOURCES.md per folder. Re-running it keeps user notes intact.
"""

from __future__ import annotations

import filecmp
import json
import os
import re
import shutil
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from sync import BASE, ROOT, normalized_url, reading_destination, reading_snapshot_issue
from material_names import material_filename


def archive_snapshot_date() -> str:
    """Use the archive's recorded sync date, not a local reorganization date."""
    sources = ROOT / "SOURCES.md"
    if sources.exists():
        match = re.search(r"本地同步日期：([0-9]{4}-[0-9]{2}-[0-9]{2})", sources.read_text(encoding="utf-8"))
        if match:
            return match[1]
    return "未记录"


@dataclass(frozen=True)
class Lesson:
    number: int
    folder: str
    date: str
    title: str
    meeting_id: str | None
    slides: tuple[tuple[str, str], ...] = ()
    references: tuple[tuple[str, str], ...] = ()
    paper_discussion: bool = False


LESSONS = (
    Lesson(1, "1.CourseOverviewAndLogistics", "2026-09-02", "Course overview and logistics", None,
           (("Lecture slides", "slides/1_intro.pdf"),),
           (("Assignment 1", "assignments/assignment1.html"),)),
    Lesson(2, "2.AgentsUseI.HowClaudeCodeWorks", "2026-09-09", "Agents use I: How Claude Code Works", "sep-09",
           (("Lecture slides", "slides/2_agent_use_1.pdf"),)),
    Lesson(3, "3.AgentsUseII.100xEngineerWithMultiAgents", "2026-09-14", "Agents use II: 100x Engineer with Multi-agents", "sep-14",
           (("Lecture slides", "slides/3_agent_use_2.pdf"),)),
    Lesson(4, "4.AgentsDesignI.ContextManagementAndToolDesign", "2026-09-16", "Agents design I: context management and tool design", "sep-16",
           (("Lecture slides", "slides/4_agent_design_1.pdf"),)),
    Lesson(5, "5.AgentsDesignII.MultiAgentArchitectureCoordinationAndCommunication", "2026-09-23", "Agents design II: multi-agent architecture, coordination, and communication", "sep-23",
           (("Lecture slides", "slides/5_agent_design_2.pdf"),)),
    Lesson(6, "6.AgentsDesignIII.AgentMemoryAndReliability", "2026-09-28", "Agents design III: agent memory and reliability", "sep-28",
           (("Lecture slides", "slides/6_agent_design_3.pdf"),)),
    Lesson(7, "7.AgentDesignIV.AgentEvaluation", "2026-09-30", "Agent design IV: agent evaluation", "sep-30",
           (("Lecture slides", "slides/7_agent_design_4.pdf"),),
           (("Agent evaluation and benchmarks", "notes/agent-evaluation.html"),)),
    Lesson(8, "8.AdvancedAgentDesignI.CostAndPerformance", "2026-10-07", "Advanced agent design I: Cost and performance", "oct-07",
           (("Lecture slides", "slides/8_agent_design_5.pdf"), ("Assignment 3 slides", "slides/8_assignment3.pdf")),
           (("Cost-effective agents", "notes/cost-effective-agents.html"),)),
    Lesson(9, "9.AdvancedAgentDesignII.AgentSafetySelfEvolvingHarness", "2026-10-14", "Advanced agent design II: agent safety, self-evolving harness", "oct-14",
           references=(("Paper discussion format", "discussion.html"),), paper_discussion=True),
    Lesson(10, "10.EfficientLLMServingBasicsI.IntroToLLMs", "2026-10-19", "Efficient LLM serving basics I: intro to LLMs", "oct-19",
           references=(("Transformers and LLM foundations", "notes/transformers.html"),)),
    Lesson(11, "11.EfficientLLMServingBasicsII.IntroToGPUs", "2026-10-21", "Efficient LLM serving basics II: intro to GPUs", "oct-21"),
    Lesson(12, "12.EfficientLLMServingBasicsIII.BatchingPagingAndParallelism", "2026-10-28", "Efficient LLM serving basics III: Batching, paging, and parallelism", "oct-28"),
    Lesson(13, "13.EfficientLLMServing.SpeculativeDecoding", "2026-11-02", "Efficient LLM serving: speculative decoding", "nov-02"),
    Lesson(14, "14.EfficientAgenticSystems.SchedulingAndPrefixCaching", "2026-11-04", "Efficient agentic systems: scheduling and prefix caching", "nov-04"),
    Lesson(15, "15.EfficientLLMServing.PruningAndQuantization", "2026-11-11", "Efficient LLM serving: pruning and quantization", "nov-11"),
    Lesson(16, "16.EfficientLLMServing.KVCacheOptimizationAndModelArchitectures", "2026-11-16", "Efficient LLM serving: KV-cache optimization and model architectures", "nov-16",
           references=(("Paper discussion format", "discussion.html"),), paper_discussion=True),
    Lesson(17, "17.EfficientAgenticSystem.RoutingAndLoadBalancing", "2026-11-23", "Efficient agentic system: routing and load balancing", "nov-23"),
    Lesson(18, "18.EfficientAgenticSystems.Others", "2026-11-30", "Efficient agentic systems: others", "nov-30"),
)


def course_title_folder(number: int, title: str) -> str:
    """Keep the official title words and Roman numerals in a filesystem name."""
    parts = title.split(":")
    slug = ".".join("".join(word[0].upper() + word[1:]
                            for word in re.findall(r"[A-Za-z0-9]+", part))
                    for part in parts)
    return f"{number}.{slug}"


def validate_course_layout() -> None:
    soup = BeautifulSoup((ROOT / "site/index.html").read_text(encoding="utf-8"), "html.parser")
    titles = {}
    for row in soup.select("table tr"):
        cells = row.find_all(["td", "th"], recursive=False)
        if len(cells) < 4:
            continue
        date = cells[1].get_text(" ", strip=True)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            continue
        for anchor in cells[3].select("a"):
            anchor.decompose()
        titles[date] = cells[3].get_text(" ", strip=True)
    for number, lesson in enumerate(sorted(LESSONS, key=lambda item: item.date), 1):
        official_title = titles.get(lesson.date)
        if official_title != lesson.title:
            raise ValueError(f"Course title changed on {lesson.date}: {official_title!r}; update LESSONS before organizing.")
        if lesson.number != number or lesson.folder != course_title_folder(number, official_title):
            raise ValueError(f"Course folder does not match its date and title: {lesson.folder}")


def markdown_link(label: str, target: Path, from_dir: Path) -> str:
    relative = Path(os.path.relpath(target, from_dir))
    return f"[{label}]({relative.as_posix()})"


def copy_if_changed(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or not filecmp.cmp(source, target, shallow=False):
        shutil.copy2(source, target)


def filename_for(title: str, url: str, number: int, extension: str) -> str:
    return material_filename(title, url, extension)


def slide_destination(site_path: str, lesson_folder: Path) -> Path:
    name = Path(site_path).name
    assignment = re.search(r"assignment(\d+)", name, re.I)
    if assignment:
        return ROOT / "assignment" / f"assignment-{assignment.group(1)}" / name
    return lesson_folder / name


def meeting_readings(soup: BeautifulSoup, meeting_id: str) -> list[tuple[str, str]]:
    meeting = soup.find(class_="reading-meeting", id=meeting_id)
    if meeting is None:
        return []
    items = []
    seen = set()
    for anchor in meeting.select("table.readings-table a[href]"):
        url = normalized_url(urljoin(BASE + "readings.html", anchor["href"]))
        title = anchor.get_text(" ", strip=True)
        if urlparse(url).netloc == "cs2680.com":
            continue
        if url not in seen and title:
            items.append((title, url))
            seen.add(url)
    return items


def schedule_slides() -> dict[str, tuple[tuple[str, str], ...]]:
    soup = BeautifulSoup((ROOT / "site/index.html").read_text(encoding="utf-8"), "html.parser")
    by_date = {}
    for row in soup.select("table tr"):
        cells = row.find_all(["td", "th"], recursive=False)
        if len(cells) < 4:
            continue
        date = cells[1].get_text(" ", strip=True)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            continue
        found = []
        for anchor in cells[3].select("a[href]"):
            absolute = urljoin(BASE, anchor["href"])
            parsed = urlparse(absolute)
            if parsed.netloc != "cs2680.com" or not parsed.path.endswith(".pdf"):
                continue
            label = anchor.get_text(" ", strip=True).strip("[]")
            label = "Lecture slides" if label.lower() == "slide" else label or "Slides"
            found.append((label, parsed.path.lstrip("/")))
        if found:
            by_date[date] = tuple(found)
    return by_date


def organize_lessons() -> None:
    soup = BeautifulSoup((ROOT / "site/readings.html").read_text(encoding="utf-8"), "html.parser")
    slides_by_date = schedule_slides()
    total_copies = 0
    for lesson in LESSONS:
        folder = ROOT / lesson.folder
        folder.mkdir(exist_ok=True)
        lines = [f"# {lesson.number}. {lesson.title}", "", f"- Date: {lesson.date}"]
        if lesson.paper_discussion:
            lines.append("- Format: Paper discussion（论文讨论课）")
        lines += ["", "## Slides", ""]
        slides = tuple({path: (label, path) for label, path in
                        (*lesson.slides, *slides_by_date.get(lesson.date, ())) }.values())
        lecture_slides = [(label, path) for label, path in slides
                          if slide_destination(path, folder).parent == folder]
        assignment_slides = [(label, path) for label, path in slides
                             if slide_destination(path, folder).parent != folder]
        if lecture_slides:
            for label, site_path in lecture_slides:
                source = ROOT / "site" / site_path
                target = folder / source.name
                if source.exists():
                    copy_if_changed(source, target)
                    lines += [f"- {markdown_link(label, target, folder)}", f"  - Source: {BASE}{site_path}"]
                    source_number = re.match(r"(\d+)_", source.name)
                    if source_number and int(source_number.group(1)) != lesson.number:
                        lines.append(f"  - 编号说明：目录 {lesson.number} 按课表日期排序；文件名前缀 {source_number.group(1)} 是官网原始讲义编号。内容按本课日期与主题核对，保留原文件名。")
                else:
                    lines += [f"- {label}: source file unavailable", f"  - Source: {BASE}{site_path}"]
        elif lesson.paper_discussion:
            lines.append(f"- 本节为论文讨论课；截至 {archive_snapshot_date()}，课程主页未提供该课的公开讲义 PDF 下载链接。阅读论文列在下方，不能当作教师讲义。")
        else:
            lines.append(f"- No slides linked on the course website as of {archive_snapshot_date()}.")
        if assignment_slides:
            lines += ["", "## Assignment materials", ""]
            for label, site_path in assignment_slides:
                source = ROOT / "site" / site_path
                target = slide_destination(site_path, folder)
                if source.exists():
                    copy_if_changed(source, target)
                    lines += [f"- {markdown_link(label, target, folder)}（作业说明，单独归入作业目录）",
                              f"  - Source: {BASE}{site_path}"]
        lines += ["", "## Readings", ""]
        items = meeting_readings(soup, lesson.meeting_id) if lesson.meeting_id else []
        expected_readings: set[Path] = set()
        if items:
            file_index = 0
            for title, url in items:
                source = reading_destination(url, title)
                if source is not None and source.exists():
                    file_index += 1
                    issue = reading_snapshot_issue(source)
                    filename_title = f"{title} browser verification" if issue else title
                    target = folder / "readings" / filename_for(filename_title, url, file_index, source.suffix)
                    copy_if_changed(source, target)
                    expected_readings.add(target)
                    total_copies += 1
                    label = f"{title} — 浏览器验证页（未获取正文）" if issue else title
                    lines += [f"- {markdown_link(label, target, folder)}", f"  - Source: {url}"]
                else:
                    lines += [f"- {title} — [online source]({url})", f"  - Source: {url}"]
        else:
            lines.append("- None listed for this meeting.")
        for stale in (folder / "readings").glob("*"):
            if stale.is_file() and stale not in expected_readings and re.match(r"^\d{3}_.+_[0-9a-f]{6}\.(?:pdf|html)$", stale.name):
                stale.unlink()
        notes = sorted(path for path in folder.glob("*.md") if path.name not in {"README.md", "SOURCES.md"})
        if notes:
            lines += ["", "## Local study notes", "", "以下为本地中文学习笔记，文件名保留现有名称；教师原始讲义见上方 Slides。", ""]
            for path in notes:
                lines.append(f"- {markdown_link(path.name, path, folder)}")
        lines += ["", "## References", ""]
        if lesson.meeting_id:
            detailed = ROOT / "site/readings" / f"{lesson.meeting_id}.html"
            full = ROOT / "site/readings.html"
            target = detailed if detailed.exists() else full
            label = "Course reading notes" if detailed.exists() else "Full course reading list"
            url = f"{BASE}readings/{lesson.meeting_id}.html" if detailed.exists() else f"{BASE}readings.html#{lesson.meeting_id}"
            lines += [f"- {markdown_link(label, target, folder)}", f"  - Source: {url}"]
        for label, site_path in lesson.references:
            target = ROOT / "site" / site_path
            lines += [f"- {markdown_link(label, target, folder)}", f"  - Source: {BASE}{site_path}"]
        if not lesson.meeting_id and not lesson.references:
            lines.append("- None listed.")
        supplemental = folder / "REFERENCES.json"
        if supplemental.exists():
            lines += ["", "## Supplemental primary sources", "",
                      "以下为中文讲解补充的一手资料；与上方官网指定 Readings 分开登记。版本、获取状态与校验值见 [REFERENCES.json](REFERENCES.json)。", ""]
            for item in json.loads(supplemental.read_text(encoding="utf-8")):
                path = item.get("path")
                target = folder / path if path else None
                title = item.get("title", path or "Reference")
                label = markdown_link(title, target, folder) if target and target.is_file() else title + "（未获取正文）"
                lines += [f"- {label}", f"  - Source: {item['url']}"]
        (folder / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("ORGANIZED", len(LESSONS), "lesson folders,", total_copies, "reading copies")


def copy_archive_code(archive: Path, folder: Path, number: int) -> None:
    """Copy regular source files from an official archive without executing them."""
    with tempfile.TemporaryDirectory(prefix="cs2680-starter-") as staging:
        with tarfile.open(archive, "r:*") as source:
            for member in source.getmembers():
                parts = PurePosixPath(member.name).parts
                if not parts or parts[0] != f"assignment{number}" or ".." in parts or member.name.startswith("/"):
                    raise ValueError(f"Unsafe assignment archive path: {member.name}")
                if not member.isfile():
                    if member.isdir():
                        continue
                    raise ValueError(f"Unsupported assignment archive entry: {member.name}")
                if Path(member.name).name == ".DS_Store":
                    continue
                relative = Path(*parts[1:])
                temporary = Path(staging) / relative
                temporary.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as data, temporary.open("wb") as output:
                    shutil.copyfileobj(data, output)
                os.chmod(temporary, member.mode & 0o777)
                os.utime(temporary, (member.mtime, member.mtime))
                copy_if_changed(temporary, folder / "code" / relative)


def organize_assignments() -> None:
    numbers = sorted(int(re.fullmatch(r"assignment(\d+)\.html", p.name).group(1))
                     for p in (ROOT / "site/assignments").glob("assignment*.html")
                     if re.fullmatch(r"assignment\d+\.html", p.name))
    for number in numbers:
        folder = ROOT / "assignment" / f"assignment-{number}"
        folder.mkdir(parents=True, exist_ok=True)
        site_path = f"assignments/assignment{number}.html"
        source = ROOT / "site" / site_path
        lines = [f"# Assignment {number}", "", "## Instructions", "",
                 f"- {markdown_link('Official assignment page', source, folder)}",
                 f"  - Source: {BASE}{site_path}"]
        code = ROOT / "assignments/course-repo" / f"assignment{number}"
        archive = ROOT / "site/assignments" / f"assignment{number}.tar.gz"
        if archive.exists():
            copy_archive_code(archive, folder, number)
            lines += ["", "## Starter code", "",
                      "- [Official archive contents](code/)",
                      f"  - Source: {BASE}assignments/{archive.name}"]
        elif code.is_dir():
            for file in code.rglob("*"):
                if file.is_file():
                    copy_if_changed(file, folder / "code" / file.relative_to(code))
            lines += ["", "## Starter code", "",
                      "- [Local course code snapshot](code/)",
                      "  - Source: https://github.com/HarvardMadSys/cs2680_assignments (fixed commit in the root SOURCES.md)"]
        if archive.exists():
            lines += ["", "## Original archive", "",
                      f"- {markdown_link(archive.name, archive, folder)}",
                      f"  - Source: {BASE}assignments/{archive.name}"]
            if number == 2:
                lines.append("  - The server names this file `.tar.gz`, but its content is a plain POSIX tar archive; use `tar -xf`.")
        if number == 3:
            slide_source = ROOT / "site/slides/8_assignment3.pdf"
            slide_target = folder / slide_source.name
            if slide_source.exists():
                copy_if_changed(slide_source, slide_target)
                lines += ["", "## Slides", "",
                          f"- {markdown_link('Assignment 3 slides', slide_target, folder)}",
                          f"  - Source: {BASE}slides/8_assignment3.pdf"]
        slide_source = ROOT / "site/slides" / f"assignment{number}.pdf"
        if slide_source.exists():
            slide_target = folder / slide_source.name
            copy_if_changed(slide_source, slide_target)
            lines += ["", "## Slides", "",
                      f"- {markdown_link(f'Assignment {number} slides', slide_target, folder)}",
                      f"  - Source: {BASE}slides/{slide_source.name}"]
        (folder / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def organize_course_info() -> None:
    folder = ROOT / "0.CourseInformation"
    folder.mkdir(exist_ok=True)
    sections = {
        "Course pages": [
            ("Course overview and schedule", "index.html"),
            ("Full reading list", "readings.html"),
            ("Readings by date", "readings/index.html"),
            ("Course policy", "policy.html"),
            ("Computing setup", "computing/index.html"),
            ("Paper discussions", "discussion.html"),
        ],
        "Background and notes": [
            ("Transformers and LLM foundations", "notes/transformers.html"),
            ("Agent evaluation and benchmarks", "notes/agent-evaluation.html"),
            ("Cost-effective agents", "notes/cost-effective-agents.html"),
        ],
    }
    lines = ["# 0. Course information", "", f"- Snapshot date: {archive_snapshot_date()}"]
    for heading, pages in sections.items():
        lines += ["", f"## {heading}", ""]
        for label, path in pages:
            local = ROOT / "site" / path
            lines += [f"- {markdown_link(label, local, folder)}", f"  - Source: {BASE}{path}"]
    (folder / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    project = ROOT / "project"
    project.mkdir(exist_ok=True)
    page = ROOT / "site/project.html"
    lines = ["# Final project", "", "## Instructions", "",
             f"- {markdown_link('Official project page', page, project)}",
             f"  - Source: {BASE}project.html"]
    (project / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_course_index() -> None:
    """Keep the root navigation in the same order and wording as the folders."""
    slides_by_date = schedule_slides()
    sections = []
    for heading, lessons in (
        ("Part I：Introduction to LLMs and agents", [l for l in LESSONS if l.date < "2026-10-19"]),
        ("Part II：Systems for LLMs and agents", [l for l in LESSONS if l.date >= "2026-10-19"]),
    ):
        sections += [f"## {heading}", "", "| 日期 | 课程原题与资料入口 | 官方讲义 PDF | 中文学习讲解 |", "|---|---|---|---|"]
        for lesson in lessons:
            folder = ROOT / lesson.folder
            entry = folder / ("README.md" if (folder / "README.md").exists() else "SOURCES.md")
            slide_links = [markdown_link(Path(path).name, folder / Path(path).name, ROOT)
                           for _, path in slides_by_date.get(lesson.date, ())
                           if slide_destination(path, folder).parent == folder
                           and (folder / Path(path).name).is_file()]
            status = " · ".join(slide_links) if slide_links else (
                "论文讨论课；官网未提供讲义 PDF" if lesson.paper_discussion else "官网尚未提供"
            )
            notes = sorted(path for path in folder.glob("*.md") if path.name not in {"README.md", "SOURCES.md"})
            preferred = folder / "notes.zh-CN.md"
            primary = preferred if preferred in notes else next((path for path in notes if path.name.startswith("lecture_02")), notes[0] if notes else None)
            note_status = markdown_link("中文讲解", primary, ROOT) if primary else "暂无中文讲解"
            if len(notes) > 1:
                note_status += " · " + markdown_link("补充学习文档", folder / "SOURCES.md", ROOT)
            sections.append(f"| {lesson.date[5:]} | {markdown_link(f'{lesson.number}. {lesson.title}', entry, ROOT)} | {status} | {note_status} |")
        sections.append("")
    sections += ["完整课表以[本地课程主页](site/index.html)为准。上表收录已有讲义或阅读资料的课次；原始 PDF 文件名保留官网编号。", ""]
    sections += ["### 文件名与归档位置核对（2026-10-23）", "",
                 "本次按课表日期、讲义封面、阅读链接和原始归档的校验值核对全部 18 个课次。264 份阅读副本均与对应原始下载文件一致；其中 LPC 的 HTML 是浏览器验证页，未取得阅读正文，已在第 14 课索引中明确标注。", "",
                 "| 容易混淆的文件 | 核对结论与处理 |", "|---|---|",
                 "| 第 10 课的 `9_llm_serving_basics_1.pdf` | 封面为 Introduction to LLM，对应 10 月 19 日；位置正确，保留官网文件名。 |",
                 "| 第 11 课的 `10_llm_serving_basics_2a.pdf` | 封面为 Intro to GPUs，对应 10 月 21 日；位置正确，保留官网文件名。 |",
                 "| 第 8 课的 `8_agent_design_5.pdf` | 封面用 Agent design V，课表用 Advanced agent design I；内容都是成本与性能，位置正确。 |",
                 "| `8_assignment3.pdf` | 是 Assignment 3: MadsOpt 的作业说明；归入 [作业 3](assignment/assignment-3/SOURCES.md)，第 8 课保留交叉链接。 |",
                 "| τ-bench、QuIP# | 文件名保留区分论文身份的符号含义，分别用 tau、Sharp 表示，并使用完整论文标题；旧名见改名记录。 |",
                 "| 笔记中的 `SOURCES(数字).md` | 上传时产生的旧别名，引用统一指向本课 `SOURCES.md`。 |", "",
                 "论文归档与阅读副本统一使用完整标题命名，网页阅读材料使用页面标题；MLA、SWA 等官网简称仍保留在课表和阅读标签中，文件名分别使用对应论文 DeepSeek-V2、Mistral 7B 的完整标题。原文件名、现路径、来源 URL 和内容校验值见 [文件改名记录](../tools/MATERIAL_RENAMES.json)。同步与整理共用标题命名规则。各课的 SOURCES.md 另列本地学习笔记，便于区分笔记与教师讲义。", ""]
    begin, end = "<!-- BEGIN COURSE INDEX -->", "<!-- END COURSE INDEX -->"
    replacement = begin + "\n\n" + "\n".join(sections) + "\n" + end + "\n\n"
    path = ROOT / "README.md"
    content = path.read_text(encoding="utf-8")
    if begin in content and end in content:
        content = re.sub(re.escape(begin) + r".*?" + re.escape(end) + r"\s*", lambda _: replacement, content, count=1, flags=re.S)
    else:
        content, count = re.subn(r"## Part I[^\n]*\n.*?(?=## 作业与项目)", lambda _: replacement, content, count=1, flags=re.S)
        if count != 1:
            raise ValueError("Cannot find the course index section in README.md")
    path.write_text(content, encoding="utf-8")


def main() -> None:
    validate_course_layout()
    organize_course_info()
    organize_lessons()
    organize_assignments()
    update_course_index()


if __name__ == "__main__":
    main()

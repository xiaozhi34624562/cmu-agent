#!/usr/bin/env python3
"""Build CMU-style course folders from the raw CS2680 source archive.

The original downloads remain in site/, readings/, and assignments/. This
script copies available materials into numbered lesson and assignment folders,
and writes one SOURCES.md per folder. Re-running it keeps user notes intact.
"""

from __future__ import annotations

import filecmp
import hashlib
import os
import re
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from sync import BASE, ROOT, TODAY, normalized_url, reading_destination


@dataclass(frozen=True)
class Lesson:
    number: int
    folder: str
    date: str
    title: str
    meeting_id: str | None
    slides: tuple[tuple[str, str], ...] = ()
    references: tuple[tuple[str, str], ...] = ()


LESSONS = (
    Lesson(1, "1.CourseOverview", "2026-09-02", "Course overview and logistics", None,
           (("Lecture slides", "slides/1_intro.pdf"),),
           (("Assignment 1", "assignments/assignment1.html"),)),
    Lesson(2, "2.UsingCodingAgents", "2026-09-09", "Agents use I: How Claude Code Works", "sep-09",
           (("Lecture slides", "slides/2_agent_use_1.pdf"),)),
    Lesson(3, "3.MultiAgentEngineering", "2026-09-14", "Agents use II: 100x Engineer with Multi-agents", "sep-14",
           (("Lecture slides", "slides/3_agent_use_2.pdf"),)),
    Lesson(4, "4.ContextAndToolDesign", "2026-09-16", "Agents design I: context management and tool design", "sep-16",
           (("Lecture slides", "slides/4_agent_design_1.pdf"),)),
    Lesson(5, "5.MultiAgentCoordination", "2026-09-23", "Agents design II: multi-agent architecture, coordination, and communication", "sep-23",
           (("Lecture slides", "slides/5_agent_design_2.pdf"),)),
    Lesson(6, "6.AgentMemoryAndReliability", "2026-09-28", "Agents design III: agent memory and reliability", "sep-28",
           (("Lecture slides", "slides/6_agent_design_3.pdf"),)),
    Lesson(7, "7.AgentEvaluation", "2026-09-30", "Agent design IV: agent evaluation", "sep-30",
           (("Lecture slides", "slides/7_agent_design_4.pdf"),),
           (("Agent evaluation and benchmarks", "notes/agent-evaluation.html"),)),
    Lesson(8, "8.CostAndPerformance", "2026-10-07", "Advanced agent design I: Cost and performance", "oct-07",
           (("Lecture slides", "slides/8_agent_design_5.pdf"), ("Assignment 3 slides", "slides/8_assignment3.pdf")),
           (("Cost-effective agents", "notes/cost-effective-agents.html"),)),
    Lesson(9, "9.AgentSafetyAndHarness", "2026-10-14", "Advanced agent design II: agent safety, self-evolving harness", "oct-14"),
    Lesson(10, "10.LLMServingBasics", "2026-10-21", "Efficient LLM serving: basics II", "oct-21"),
    Lesson(11, "11.SpeculativeDecoding", "2026-10-28", "Efficient LLM serving: speculative decoding", "oct-28"),
    Lesson(12, "12.SchedulingAndPrefixCaching", "2026-11-02", "Efficient agentic systems: scheduling and prefix caching", "nov-02"),
    Lesson(13, "13.PruningAndQuantization", "2026-11-04", "Efficient LLM serving: pruning and quantization", "nov-04"),
    Lesson(14, "14.GPUAndKernels", "2026-11-11", "Efficient LLM serving: GPU and kernels", "nov-11"),
    Lesson(15, "15.KVCacheAndModelArchitecture", "2026-11-16", "Efficient LLM serving: KV-cache optimization and model architectures", "nov-16"),
    Lesson(16, "16.RoutingAndLoadBalancing", "2026-11-23", "Efficient agentic system: routing and load balancing", "nov-23"),
    Lesson(17, "17.EfficientAgentSystems", "2026-11-30", "Efficient agentic systems: others", "nov-30"),
)


def markdown_link(label: str, target: Path, from_dir: Path) -> str:
    relative = Path(os.path.relpath(target, from_dir))
    return f"[{label}]({relative.as_posix()})"


def copy_if_changed(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or not filecmp.cmp(source, target, shallow=False):
        shutil.copy2(source, target)


def filename_for(title: str, url: str, number: int, extension: str) -> str:
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", ascii_title).strip("_")[:64] or "Reading"
    digest = hashlib.sha256(url.encode()).hexdigest()[:6]
    return f"{number:03d}_{slug}_{digest}{extension}"


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
        lines = [f"# {lesson.number}. {lesson.title}", "", f"- Date: {lesson.date}", "", "## Slides", ""]
        slides = slides_by_date.get(lesson.date, lesson.slides)
        if slides:
            for label, site_path in slides:
                source = ROOT / "site" / site_path
                target = folder / f"lecture-{lesson.number:02d}-{source.name}"
                if source.exists():
                    copy_if_changed(source, target)
                    lines += [f"- {markdown_link(label, target, folder)}", f"  - Source: {BASE}{site_path}"]
                else:
                    lines += [f"- {label}: source file unavailable", f"  - Source: {BASE}{site_path}"]
        else:
            lines.append(f"- No slides linked on the course website as of {TODAY}.")
        lines += ["", "## Readings", ""]
        items = meeting_readings(soup, lesson.meeting_id) if lesson.meeting_id else []
        expected_readings: set[Path] = set()
        if items:
            file_index = 0
            for title, url in items:
                source = reading_destination(url)
                if source is not None and source.exists():
                    file_index += 1
                    target = folder / "readings" / filename_for(title, url, file_index, source.suffix)
                    copy_if_changed(source, target)
                    expected_readings.add(target)
                    total_copies += 1
                    lines += [f"- {markdown_link(title, target, folder)}", f"  - Source: {url}"]
                else:
                    lines += [f"- {title} — [online source]({url})", f"  - Source: {url}"]
        else:
            lines.append("- None listed for this meeting.")
        for stale in (folder / "readings").glob("*"):
            if stale.is_file() and stale not in expected_readings and re.match(r"^\d{3}_.+_[0-9a-f]{6}\.(?:pdf|html)$", stale.name):
                stale.unlink()
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
        (folder / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("ORGANIZED", len(LESSONS), "lesson folders,", total_copies, "reading copies")


def organize_assignments() -> None:
    for number in (1, 2, 3):
        folder = ROOT / "assignment" / f"assignment-{number}"
        folder.mkdir(parents=True, exist_ok=True)
        site_path = f"assignments/assignment{number}.html"
        source = ROOT / "site" / site_path
        lines = [f"# Assignment {number}", "", "## Instructions", "",
                 f"- {markdown_link('Official assignment page', source, folder)}",
                 f"  - Source: {BASE}{site_path}"]
        code = ROOT / "assignments/course-repo" / f"assignment{number}"
        if code.is_dir():
            for file in code.rglob("*"):
                if file.is_file():
                    copy_if_changed(file, folder / "code" / file.relative_to(code))
            lines += ["", "## Starter code", "",
                      "- [Local course code snapshot](code/)",
                      "  - Source: https://github.com/HarvardMadSys/cs2680_assignments (fixed commit in the root SOURCES.md)"]
        if number == 2:
            archive = ROOT / "site/assignments/assignment2.tar.gz"
            lines += ["", "## Original archive", "",
                      f"- {markdown_link('assignment2.tar.gz', archive, folder)}",
                      f"  - Source: {BASE}assignments/assignment2.tar.gz",
                      "  - The server names this file `.tar.gz`, but its content is a plain POSIX tar archive; use `tar -xf`."]
        if number == 3:
            slide_source = ROOT / "site/slides/8_assignment3.pdf"
            slide_target = folder / "assignment3-slides.pdf"
            if slide_source.exists():
                copy_if_changed(slide_source, slide_target)
                lines += ["", "## Slides", "",
                          f"- {markdown_link('Assignment 3 slides', slide_target, folder)}",
                          f"  - Source: {BASE}slides/8_assignment3.pdf"]
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
    lines = ["# 0. Course information", "", f"- Snapshot date: {TODAY}"]
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


def main() -> None:
    organize_course_info()
    organize_lessons()
    organize_assignments()


if __name__ == "__main__":
    main()

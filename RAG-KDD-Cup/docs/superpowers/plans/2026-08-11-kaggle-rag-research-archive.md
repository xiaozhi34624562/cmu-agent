# Kaggle RAG Research Archive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a locally verifiable research archive for FinanceRAG Challenge 2024, WattBot Challenge 2025, and EReL@MIR 2025 containing papers, public code, provenance records, and senior-level Chinese technical analyses.

**Architecture:** Each competition is an independent archive with `papers/`, `code/`, `resources/source-manifest.md`, and a top-level `README.md`. Primary sources establish competition identity, ranking, paper, and code provenance; PDFs and repositories are then inspected to produce evidence-calibrated technical explanations and reproducibility notes.

**Tech Stack:** Kaggle/web primary sources, arXiv/ACM PDFs, Git, GitHub repositories, Poppler (`pdfinfo`, `pdftotext`, `pdftoppm`), Markdown.

**Execution status (2026-08-12):** All checkboxes below are closed against the final artifact and verification state. They record acceptance outcomes, not a claim that every historical shell command was executed verbatim or committed at each originally proposed boundary. The archive was consolidated in repository commits and re-audited from `/Users/wangmingzhi/qg/code/RAGKK`.

## Global Constraints

- Use competition names as top-level folder names.
- Include the Multi-Reranker and KohakuRAG papers and their public code.
- Include the official EReL@MIR 2025 overview and the public code and approaches of the final top three teams.
- Record exact source URLs, repository commit hashes, branches, licenses, and reproducibility limitations.
- Distinguish source-backed facts from engineering interpretation.
- Do not invent unavailable papers, code, weights, datasets, or rankings.

---

### Task 1: Verify primary sources

**Files:**
- Create: `FinanceRAG Challenge 2024/resources/source-manifest.md`
- Create: `WattBot Challenge 2025/resources/source-manifest.md`
- Create: `EReL@MIR 2025/resources/source-manifest.md`

- [x] Search official Kaggle competition, leaderboard, discussion, writeup, notebook, challenge-site, paper, and repository pages.
- [x] Cross-check paper titles, author/team identities, final ranking, and licenses against primary sources.
- [x] Record inaccessible or ambiguous sources explicitly.

### Task 2: Download and validate artifacts

**Files:**
- Create: `*/papers/*.pdf`
- Create: `*/code/<repository>/`

- [x] Download canonical PDFs using stable descriptive filenames.
- [x] Clone public repositories with Git history and capture exact commit hashes.
- [x] Validate each PDF with `pdfinfo`, extract text with `pdftotext`, and visually inspect representative rendered pages.
- [x] Inventory whether each repository includes preprocessing, training, inference, evaluation, configs, weights, and data.

### Task 3: Write competition analyses

**Files:**
- Create: `FinanceRAG Challenge 2024/README.md`
- Create: `WattBot Challenge 2025/README.md`
- Create: `EReL@MIR 2025/README.md`

- [x] Explain background, task, dataset, metrics, leaderboard context, and solution-sharing URLs.
- [x] Map paper architecture to code entry points and data flow.
- [x] Explain design rationale, ablations, error modes, compute/cost trade-offs, limitations, and production implications.
- [x] For EReL, compare the top three teams along retrieval model, reranking, visual features, fusion, training cost, and reproducibility.
- [x] Add actionable transfer guidance for financial PDF RAG.

### Task 4: Final verification

**Files:**
- Verify all files under the three competition directories.

- [x] Check that every cited local artifact exists and every external URL is traceable.
- [x] Confirm rankings and team names against official sources.
- [x] Scan Markdown for placeholders, contradictions, unsupported certainty, and broken relative paths.
- [x] Produce a final inventory with file sizes, PDF page counts, repository commits, and known gaps.

# Meta KDD Cup CRAG Research Archive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a source-verifiable local archive for ten Meta KDD Cup CRAG/CRAG-MM papers, their official public code where available, senior-level Chinese technical notes, and a repository-wide RAG learning navigation.

**Architecture:** Treat each paper directory as a self-contained research unit containing a canonical PDF, an official repository clone or an explicit no-code record, a source manifest, and a technical README. Keep upstream repositories as independent nested Git worktrees pinned by commit in the manifests; the root Git repository tracks the authored documentation, PDFs, and manifests. Build year-level, topic-level, and root-level navigation only after primary-source facts have been normalized.

**Tech Stack:** Git, zsh, curl, OpenReview/KDD Cup/arXiv/GitHub primary sources, Poppler (`pdfinfo`, `pdftotext`, `pdftoppm`), Python 3 AST validation, Markdown link checks.

**Execution status (2026-08-12):** Checkboxes below record acceptance outcomes, not a claim that every historical shell command was executed verbatim or committed at each originally proposed boundary. Work was consolidated on branch `meta-crag-archive` in `/Users/wangmingzhi/qg/code/RAGKK`; unavailable upstream GitLab repositories remain explicitly documented rather than substituted. Authored Markdown has zero missing local targets. Six missing targets inside untouched upstream clones are documented upstream defects and are excluded from the authored-link gate.

## Global Constraints

- Final scope is exactly eight CRAG 2024 papers and two CRAG-MM 2025 papers listed in the approved design.
- Use official KDD Cup/Meta CRAG/workshop, OpenReview, arXiv/ACM/NeurIPS/author, and official GitHub sources in that priority order.
- Distinguish workshop technical reports, benchmark papers, and KDD main-track papers.
- Do not infer task rank from a paper title; record automatic and human evaluation separately when the official sources distinguish them.
- Never present third-party reimplementations as official code.
- Preserve every existing FinanceRAG, WattBot, and EReL file; only add repository-wide navigation to them.
- Download public PDFs, source repositories, small configs, prompts, and samples; do not download multi-GB weights, credentialed datasets, or private artifacts.
- Every source-backed statement must have a nearby URL or a source-manifest citation; label engineering conclusions as analysis or inference.
- Do not claim leaderboard reproduction because GPU/API-heavy evaluation is outside scope.
- Retain nested upstream `.git` directories and record full commit hashes; do not flatten or rewrite upstream history.

## File Map

- `README.md`: global RAG learning map linking existing and new archives.
- `.gitignore`: root-only transient files and exact nested upstream worktree paths.
- `Meta KDD Cup CRAG/README.md`: cross-year competition comparison and ten-paper synthesis.
- `Meta KDD Cup CRAG/CRAG 2024/README.md`: 2024 task, metric, and eight-paper navigation.
- `Meta KDD Cup CRAG/CRAG-MM 2025/README.md`: 2025 multimodal task and two-paper navigation.
- `Meta KDD Cup CRAG/<year>/<paper>/README.md`: one senior-engineer technical analysis per paper.
- `Meta KDD Cup CRAG/<year>/<paper>/papers/*.pdf`: canonical local paper artifact.
- `Meta KDD Cup CRAG/<year>/<paper>/code/<repo>/`: official upstream repository, if released.
- `Meta KDD Cup CRAG/<year>/<paper>/code/README.md`: explicit author-code search result when no official repository is available.
- `Meta KDD Cup CRAG/<year>/<paper>/resources/source-manifest.md`: bibliographic, ranking, URL, commit, license, artifact, and reproducibility evidence.

---

### Task 1: Root Git Hygiene and Archive Skeleton

**Files:**
- Create: `.gitignore`
- Create: `Meta KDD Cup CRAG/README.md`
- Create: `Meta KDD Cup CRAG/CRAG 2024/README.md`
- Create: `Meta KDD Cup CRAG/CRAG-MM 2025/README.md`
- Create directories for all ten paper units defined below.

**Interfaces:**
- Consumes: approved design at `docs/superpowers/specs/2026-08-12-meta-crag-research-archive-design.md`.
- Produces: stable folder paths consumed by every later task.

- [x] **Step 1: Confirm the root repository and preserve nested repositories**

Run: `git rev-parse --show-toplevel && find . -mindepth 2 -name .git -type d -print`

Expected: root is `/Users/xiaozhi/Downloads/RAG`; five existing nested source repositories are listed and remain untouched.

- [x] **Step 2: Create the ten paper directory trees**

Create `papers/`, `code/`, and `resources/` under:

```text
Meta KDD Cup CRAG/CRAG 2024/01-Winning-Solution
Meta KDD Cup CRAG/CRAG 2024/02-Revisiting-CRAG
Meta KDD Cup CRAG/CRAG 2024/03-Simple-Effective-RAG
Meta KDD Cup CRAG/CRAG 2024/04-KG-Self-Verification
Meta KDD Cup CRAG/CRAG 2024/05-Honest-AI
Meta KDD Cup CRAG/CRAG 2024/06-TCAF
Meta KDD Cup CRAG/CRAG 2024/07-Hybrid-RAG
Meta KDD Cup CRAG/CRAG 2024/08-MARAGS
Meta KDD Cup CRAG/CRAG-MM 2025/09-Winning-Task-2
Meta KDD Cup CRAG/CRAG-MM 2025/10-DB3-Solution
```

- [x] **Step 3: Add root ignore rules**

Use `.gitignore` for `.DS_Store`, Python caches, PDF render scratch output, and exact cloned upstream repository directories after their names are known. Do not ignore `README.md`, `papers/`, or `resources/` trees.

- [x] **Step 4: Validate the skeleton**

Run: `find 'Meta KDD Cup CRAG' -type d | sort`

Expected: three navigation levels and all thirty per-paper artifact directories are present.

- [x] **Step 5: Commit the structural baseline**

```bash
git add .gitignore 'Meta KDD Cup CRAG/README.md' 'Meta KDD Cup CRAG/CRAG 2024/README.md' 'Meta KDD Cup CRAG/CRAG-MM 2025/README.md'
git commit -m "chore: scaffold Meta CRAG research archive"
```

### Task 2: Primary-Source Identity and Competition-Fact Matrix

**Files:**
- Create: all ten `resources/source-manifest.md` files.

**Interfaces:**
- Consumes: exact user title aliases and official web sources.
- Produces: normalized title, authors, venue type, paper URL, PDF URL, task/rank evidence, competition URL, workshop URL, and code URL status for use by Tasks 3–8.

- [x] **Step 1: Locate official competition and workshop hubs**

Search the official Meta CRAG/KDD Cup pages and OpenReview groups for 2024 and 2025. Record the competition overview, rules/scoring, task definitions, final leaderboard or workshop acceptance page, and OpenReview venue page. Use Kaggle only as a cross-check if a primary page is unavailable.

- [x] **Step 2: Resolve all ten title aliases**

For each alias, open the official forum/landing page and PDF metadata. Normalize punctuation and capitalization from the paper itself, record all authors, year, publication type, forum identifier, and direct PDF URL.

- [x] **Step 3: Resolve rank wording**

Cross-check each claimed task/rank against official results. Record task number, track/category, score where explicitly published, and whether the rank is automatic, human, or an author claim not independently confirmed.

- [x] **Step 4: Resolve official code status**

Follow repository links from OpenReview PDFs, author profiles, project pages, and GitHub organization/user pages. A repository qualifies as official only when the paper/author/team links it or repository ownership and README attribution establish authorship.

- [x] **Step 5: Write complete manifests**

Each manifest must contain these literal headings:

```markdown
# Source Manifest
## Bibliographic identity
## Competition and ranking evidence
## Paper sources
## Code sources
## Artifact inventory
## Reproduction dependencies
## Known gaps and confidence
```

Every absent artifact must state the searched primary locations and checked date `2026-08-12`.

- [x] **Step 6: Verify coverage and commit**

Run a shell check that each of the ten manifests contains all seven headings and at least one `https://` link. Expected: ten files pass.

```bash
git add 'Meta KDD Cup CRAG'/**/resources/source-manifest.md
git commit -m "docs: record primary sources for Meta CRAG papers"
```

### Task 3: Canonical Paper Downloads and PDF Validation

**Files:**
- Create: one canonical PDF in each of the ten `papers/` directories.
- Modify: manifests if a canonical URL redirects to an official mirror.

**Interfaces:**
- Consumes: direct PDF URLs from Task 2.
- Produces: readable, non-HTML PDF files for technical analysis.

- [x] **Step 1: Download with redirect and failure handling**

Use `curl -fL --retry 3 --retry-delay 2` and stable ASCII filenames derived from each canonical title. Never save a failed HTML response with a `.pdf` suffix.

- [x] **Step 2: Validate MIME, size, and page count**

For every PDF run `file`, `pdfinfo`, and `pdftotext`. Expected: PDF MIME/signature, nonzero byte size, positive page count, and nonempty extracted text.

- [x] **Step 3: Render representative pages**

Use `pdftoppm -png -f 1 -singlefile` for page 1 and render one architecture/results page selected from extracted text. Visually inspect title/authors, diagrams/tables, clipping, and corruption using the PDF skill workflow.

- [x] **Step 4: Remove scratch renders and record checksums**

Remove only the temporary render directory. Add local filename, byte size, page count, and SHA-256 to each manifest.

- [x] **Step 5: Commit PDFs and manifest metadata**

```bash
git add 'Meta KDD Cup CRAG'/**/papers/*.pdf 'Meta KDD Cup CRAG'/**/resources/source-manifest.md
git commit -m "docs: archive canonical Meta CRAG papers"
```

### Task 4: Official Code Acquisition and Static Audit

**Files:**
- Create: official repository clones under the corresponding `code/` directories.
- Create: `code/README.md` for every paper without author-released code.
- Modify: `.gitignore`
- Modify: all ten manifests.

**Interfaces:**
- Consumes: official repository decisions from Task 2.
- Produces: pinned source trees or explicit no-code records, plus a reproducibility inventory for the technical READMEs.

- [x] **Step 1: Clone each official repository with full visible history**

Use `git clone <official-url> <paper>/code/<repository-name>`. Do not fetch Git LFS model weights or competition datasets. If two papers share a repository, clone it independently into both self-contained paper units.

- [x] **Step 2: Pin and inventory repository state**

For every clone record remote URL, default branch, `git rev-parse HEAD`, commit date, clean/dirty state, license filename or absence, languages, and top-level files in the manifest.

- [x] **Step 3: Map reproducibility coverage**

Record whether preprocessing, training/fine-tuning, retrieval, reranking, generation, verification, evaluation, prompts/configs, sample data, model weights, and setup instructions are present. List required API keys, model downloads, CUDA/GPU assumptions, absolute paths, and unavailable data.

- [x] **Step 4: Create no-code evidence files**

Where no official repository exists, create `code/README.md` with the canonical title, searched official pages, checked date, result, and a warning that third-party implementations were intentionally excluded.

- [x] **Step 5: Run static integrity checks**

Run `git fsck --full` in every clone. Parse tracked Python files with `python3 -m py_compile` only where doing so does not generate persistent caches, or use `ast.parse` over source text. Report syntax errors without editing upstream code.

- [x] **Step 6: Protect nested histories from root Git**

Add each exact cloned repository directory to root `.gitignore`. Confirm `git status --short` does not show embedded-repository warnings and that code availability remains navigable on disk.

- [x] **Step 7: Commit authored audit records**

```bash
git add .gitignore 'Meta KDD Cup CRAG'/**/code/README.md 'Meta KDD Cup CRAG'/**/resources/source-manifest.md
git commit -m "docs: audit Meta CRAG source releases"
```

### Task 5: 2024 Full-System Paper Analyses

**Files:**
- Create: `Meta KDD Cup CRAG/CRAG 2024/01-Winning-Solution/README.md`
- Create: `Meta KDD Cup CRAG/CRAG 2024/02-Revisiting-CRAG/README.md`
- Create: `Meta KDD Cup CRAG/CRAG 2024/03-Simple-Effective-RAG/README.md`

**Interfaces:**
- Consumes: validated PDFs, manifests, and code audits for papers 1–3.
- Produces: comparable descriptions of high-performing end-to-end CRAG pipelines.

- [x] **Step 1: Extract architecture and experiment evidence**

Build notes from the abstract, method, experimental setup, main results, ablations, limitations, and appendices. Preserve table/section references for every exact number.

- [x] **Step 2: Write the three senior-level analyses**

Each README must cover conclusion, identity/context, target task/scoring, problem diagnosis, end-to-end data flow, retrieval/routing/generation/verification, experiments, metric-aware explanation, code mapping, reproduction, engineering limits, and financial-RAG transfer.

- [x] **Step 3: Separate evidence from inference**

Prefix non-paper operational conclusions with `工程判断：`; do not convert an author-reported rank into an official rank without Task 2 evidence.

- [x] **Step 4: Validate links and commit**

Check that all relative PDF/code/manifest links resolve and all external links use HTTPS.

```bash
git add 'Meta KDD Cup CRAG/CRAG 2024/01-Winning-Solution/README.md' 'Meta KDD Cup CRAG/CRAG 2024/02-Revisiting-CRAG/README.md' 'Meta KDD Cup CRAG/CRAG 2024/03-Simple-Effective-RAG/README.md'
git commit -m "docs: analyze CRAG 2024 full-system solutions"
```

### Task 6: Reliability and Abstention Paper Analyses

**Files:**
- Create: `Meta KDD Cup CRAG/CRAG 2024/04-KG-Self-Verification/README.md`
- Create: `Meta KDD Cup CRAG/CRAG 2024/05-Honest-AI/README.md`

**Interfaces:**
- Consumes: papers 4–5 artifacts and CRAG scoring evidence.
- Produces: mechanism-level analysis of graph integration, self-verification, calibration, and “I don't know” behavior.

- [x] **Step 1: Trace the reliability control loops**

Identify where evidence is retrieved, normalized, fused, checked, rejected, regenerated, or converted to abstention, including supervision and threshold choices.

- [x] **Step 2: Explain expected utility under asymmetric scoring**

Relate false answers (`-1`), missing answers (`0`), acceptable answers (`0.5`), and perfect answers (`1`) to verification and abstention decisions without inventing an unpublished threshold.

- [x] **Step 3: Write both analyses and code maps**

Use the common twelve-section README structure and explicitly state whether the released code contains training, inference, evaluator, checkpoints, and prompts.

- [x] **Step 4: Validate and commit**

```bash
git add 'Meta KDD Cup CRAG/CRAG 2024/04-KG-Self-Verification/README.md' 'Meta KDD Cup CRAG/CRAG 2024/05-Honest-AI/README.md'
git commit -m "docs: analyze CRAG verification and abstention methods"
```

### Task 7: Agentic Reasoning, Hybrid Retrieval, and Adapter Analyses

**Files:**
- Create: `Meta KDD Cup CRAG/CRAG 2024/06-TCAF/README.md`
- Create: `Meta KDD Cup CRAG/CRAG 2024/07-Hybrid-RAG/README.md`
- Create: `Meta KDD Cup CRAG/CRAG 2024/08-MARAGS/README.md`

**Interfaces:**
- Consumes: papers 6–8 artifacts and code audits.
- Produces: comparative treatment of agent decomposition, thought-chain orchestration, hybrid retrieval, complex reasoning, and multi-adapter routing.

- [x] **Step 1: Reconstruct each control/data flow**

Identify planner/router roles, tool boundaries, state passed between agents or adapters, retrieval fusion, stopping conditions, and failure propagation.

- [x] **Step 2: Analyze latency and cost**

Separate reported measurements from engineering estimates. Explain serial LLM calls, retrieval fan-out, cache opportunities, batching limits, and operational observability.

- [x] **Step 3: Write all three analyses**

Use consistent terminology and include a concrete financial-RAG transfer section covering filings, tables, temporal validity, and auditable citations.

- [x] **Step 4: Validate and commit**

```bash
git add 'Meta KDD Cup CRAG/CRAG 2024/06-TCAF/README.md' 'Meta KDD Cup CRAG/CRAG 2024/07-Hybrid-RAG/README.md' 'Meta KDD Cup CRAG/CRAG 2024/08-MARAGS/README.md'
git commit -m "docs: analyze CRAG agentic and adapter systems"
```

### Task 8: CRAG-MM 2025 Winning-System Analyses

**Files:**
- Create: `Meta KDD Cup CRAG/CRAG-MM 2025/09-Winning-Task-2/README.md`
- Create: `Meta KDD Cup CRAG/CRAG-MM 2025/10-DB3-Solution/README.md`

**Interfaces:**
- Consumes: CRAG-MM competition definitions, papers 9–10, official code audits.
- Produces: senior-level analysis of multimodal, multi-turn retrieval and generation systems.

- [x] **Step 1: Normalize the 2025 task/evaluation model**

Explain modalities, conversational context, retrieval/generation boundaries, and automatic versus human evaluation before discussing rankings.

- [x] **Step 2: Reconstruct multimodal pipelines**

Trace text, image, table, layout, web/KG evidence, query rewriting, routing, fusion, generation, and verification where present.

- [x] **Step 3: Write both analyses**

Use the common structure and explicitly compare the winning Task 2 report with DB3's scope, artifact completeness, latency, and reproducibility.

- [x] **Step 4: Validate and commit**

```bash
git add 'Meta KDD Cup CRAG/CRAG-MM 2025/09-Winning-Task-2/README.md' 'Meta KDD Cup CRAG/CRAG-MM 2025/10-DB3-Solution/README.md'
git commit -m "docs: analyze CRAG-MM 2025 winning systems"
```

### Task 9: Year and Cross-Year Navigation

**Files:**
- Modify: `Meta KDD Cup CRAG/CRAG 2024/README.md`
- Modify: `Meta KDD Cup CRAG/CRAG-MM 2025/README.md`
- Modify: `Meta KDD Cup CRAG/README.md`

**Interfaces:**
- Consumes: all ten finalized paper units.
- Produces: competition-centered learning paths and a method/reproducibility matrix.

- [x] **Step 1: Write the 2024 navigation**

Document the three tasks, scoring rule, official links, eight-paper table, code availability, claimed/verified ranks, and a recommended reading order from full systems to reliability and agentic specialization.

- [x] **Step 2: Write the 2025 navigation**

Document CRAG-MM tasks/modalities, evaluation distinctions, official links, both winning reports, code availability, and their differing system emphases.

- [x] **Step 3: Write the cross-year synthesis**

Compare CRAG 2024 and CRAG-MM 2025 and synthesize four themes: full winning systems; KG/verification/abstention; complex reasoning/adapters/agents; multimodal multi-turn RAG. Include a ten-row method/reproducibility matrix and financial-RAG implications.

- [x] **Step 4: Check all local links and commit**

Resolve every relative Markdown target from its containing file and fail the check on missing files.

```bash
git add 'Meta KDD Cup CRAG/README.md' 'Meta KDD Cup CRAG/CRAG 2024/README.md' 'Meta KDD Cup CRAG/CRAG-MM 2025/README.md'
git commit -m "docs: add Meta CRAG learning navigation"
```

### Task 10: Repository-Wide RAG Learning Map

**Files:**
- Create: `README.md`

**Interfaces:**
- Consumes: existing FinanceRAG, WattBot, EReL READMEs and the completed Meta CRAG archive.
- Produces: the repository entry point requested by the user.

- [x] **Step 1: Inventory existing projects without rewriting them**

Read `FinanceRAG Challenge 2024/README.md`, `WattBot Challenge 2025/README.md`, and `EReL@MIR 2025/README.md`; link their papers, code, and source manifests using paths that exist locally.

- [x] **Step 2: Write repository conventions and project table**

Explain artifact layout, source trust policy, code/no-code distinction, pinned commits, and non-reproduction caveat. Add rows for FinanceRAG 2024, WattBot 2025, EReL@MIR 2025, CRAG 2024, and CRAG-MM 2025.

- [x] **Step 3: Add ten concise paper introductions**

Write 100–200 Chinese characters per CRAG paper covering its problem, core method, and learning value; link directly to its README, PDF, code/no-code record, and manifest.

- [x] **Step 4: Add role-based learning tracks**

Provide ordered tracks for retrieval/reranking, hierarchy/citations, verification/abstention, agentic reasoning, and multimodal RAG, ending with a recommended senior-engineer reproduction checklist.

- [x] **Step 5: Validate links and commit**

```bash
git add README.md
git commit -m "docs: add repository-wide RAG learning map"
```

### Task 11: Final Acceptance Audit

**Files:**
- Modify: any authored README or manifest that fails validation.

**Interfaces:**
- Consumes: the complete archive.
- Produces: evidence that every approved acceptance criterion is met, with explicit disclosures for unavailable artifacts.

- [x] **Step 1: Count required artifacts**

Expected: ten paper directories, ten technical READMEs, ten manifests, ten valid PDFs unless an official paper is genuinely inaccessible and documented, and one code disposition per paper.

- [x] **Step 2: Re-run PDF checks**

Run `pdfinfo` and `pdftotext` across every CRAG PDF. Expected: no parse failures, positive page counts, and nonempty text output.

- [x] **Step 3: Re-run repository checks**

Run `git fsck --full`, confirm the recorded commit matches `HEAD`, verify clean status, and AST-parse Python source in every official clone. Expected: all checks pass or an upstream defect is explicitly documented without local mutation.

- [x] **Step 4: Validate every local Markdown link**

Use a small read-only checker to resolve local links relative to each Markdown file while ignoring URL fragments and HTTP(S) links. Expected: zero missing local targets.

- [x] **Step 5: Audit claims and disclosure language**

Search for all occurrences of `第一`, `冠军`, `winning`, ranks, and exact scores. Confirm each is tied to official evidence or clearly labelled as an author claim. Confirm missing code/data/weights and unexecuted GPU/API workflows are disclosed.

- [x] **Step 6: Review root Git state**

Run `git status --short`, `git log --oneline --decorate -12`, and `git fsck --full`. Ensure no nested upstream repository was accidentally staged as a gitlink and no `.DS_Store` or scratch render is tracked.

- [x] **Step 7: Commit audit corrections**

```bash
git add README.md .gitignore 'Meta KDD Cup CRAG' docs/superpowers/plans/2026-08-12-meta-crag-research-archive.md
git commit -m "docs: complete Meta CRAG archive verification"
```

Expected: if there are no audit corrections, skip the empty commit and report the existing final commit hash.

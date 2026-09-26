# Meta KDD Cup CRAG Research Archive Design

**Date:** 2026-08-12

## Objective

Extend `/Users/xiaozhi/Downloads/RAG/` with a source-verifiable learning archive for ten Meta KDD Cup CRAG papers and their official public code, while adding a repository-wide `README.md` that navigates both the existing FinanceRAG/WattBot/EReL materials and the new CRAG collection.

## Final paper scope

### Meta KDD Cup CRAG 2024

1. Winning Solution For Meta KDD Cup’24 CRAG
2. Revisiting the Solution of Meta KDD Cup 2024: CRAG
3. A Simple yet Effective Retrieval-Augmented Generation Framework for Meta KDD Cup 2024
4. Knowledge Graph Integration and Self-Verification for CRAG
5. Honest AI: Fine-Tuning Small Language Models to Say "I Don't Know"
6. TCAF: Multi-Agent Approach of Thought Chain for RAG
7. Hybrid RAG System with Comprehensive Enhancement on Complex Reasoning
8. MARAGS: Multi-Adapter System for Multi-Task RAG QA

### Meta KDD Cup CRAG-MM 2025

9. Winning Meta KDD Cup’25 Task 2
10. DB3 Team’s Solution For Meta KDD Cup’25

Exact titles, author lists, task ranks, publication type, and URLs will be normalized from official OpenReview/KDD Cup/author sources. The shorter titles supplied by the user remain search aliases, not automatically the canonical bibliographic titles.

## Directory design

```text
/Users/xiaozhi/Downloads/RAG/
├── README.md
├── Meta KDD Cup CRAG/
│   ├── README.md
│   ├── CRAG 2024/
│   │   ├── README.md
│   │   ├── 01-Winning-Solution/
│   │   ├── 02-Revisiting-CRAG/
│   │   ├── 03-Simple-Effective-RAG/
│   │   ├── 04-KG-Self-Verification/
│   │   ├── 05-Honest-AI/
│   │   ├── 06-TCAF/
│   │   ├── 07-Hybrid-RAG/
│   │   └── 08-MARAGS/
│   └── CRAG-MM 2025/
│       ├── README.md
│       ├── 09-Winning-Task-2/
│       └── 10-DB3-Solution/
├── FinanceRAG Challenge 2024/
├── WattBot Challenge 2025/
└── EReL@MIR 2025/
```

Each paper directory contains:

```text
<paper>/
├── README.md
├── papers/
│   └── <canonical-stable-name>.pdf
├── code/
│   └── <official-repository>/
└── resources/
    └── source-manifest.md
```

If no official code exists, `code/` will contain a short `README.md` documenting the search result and the absence of author-released code. Third-party reimplementations will not be presented as official code. If two papers share one official repository, each paper directory remains self-contained and records the same exact upstream commit rather than using an opaque local symlink.

## Source policy

Source priority:

1. Official KDD Cup / Meta CRAG competition and workshop pages
2. Official OpenReview forum and attachments
3. arXiv, ACM, NeurIPS, or author-hosted canonical paper pages
4. Author/team GitHub repositories and model cards
5. Kaggle or other mirrors only for cross-checking when the primary artifact is inaccessible

Every `source-manifest.md` records:

- canonical title, authors, year, venue/publication type
- competition task and reported rank, with automatic/human evaluation distinctions
- paper page, direct PDF URL, competition page, leaderboard/workshop page
- repository URL, branch, full commit hash, latest checked commit date
- license file/declaration status
- presence of preprocessing, training, inference, evaluation, configs, weights, and data
- external APIs, credentials, model downloads, hardware, and hard-coded paths
- known gaps between paper claims and released code

Workshop technical reports, benchmark papers, and KDD main-track papers must be labelled separately. Competition rank must not be inferred from paper wording alone.

## Per-paper README design

Each paper receives a Chinese technical analysis with these sections:

1. One-paragraph conclusion
2. Paper identity and competition context
3. CRAG task/scoring target addressed
4. Problem diagnosis and baseline weakness
5. End-to-end architecture and data flow
6. Retrieval, routing, KG, generation, verification, abstention, adapters, or agents as applicable
7. Key experiments, ablations, and reported scores
8. Why the method works under `Perfect=1 / Acceptable=0.5 / Missing=0 / Incorrect=-1`
9. Code map from paper modules to files/entry points
10. Reproduction requirements and unavailable artifacts
11. Engineering limitations, latency/cost, and failure propagation
12. Transfer guidance for financial RAG

The analysis distinguishes source-backed facts from engineering inference. Unsupported exact numbers will not be invented.

## Navigation documents

### Repository root `README.md`

The root README is a global learning map and includes:

- repository purpose and artifact conventions
- a table for FinanceRAG, WattBot, EReL, CRAG 2024, and CRAG-MM 2025
- learning tracks: retrieval/reranking, hierarchy/citations, verification/abstention, agentic reasoning, multimodal RAG
- a 100–200 Chinese-character introduction for each of the ten new papers
- direct local links to each project README, PDF, code, and source manifest
- recommended progression from retrieval basics to reliable and multimodal/agentic RAG

Existing project directories and their documents are preserved. The new root README links them rather than rewriting their contents.

### `Meta KDD Cup CRAG/README.md`

The topic README includes:

- CRAG 2024 vs. CRAG-MM 2025 task and metric comparison
- official competition, leaderboard, workshop, OpenReview, dataset, and benchmark links
- a ten-paper method/reproducibility matrix
- four study themes: full winning systems; KG/verification/abstention; complex reasoning/adapters/agents; multimodal multi-turn CRAG-MM
- cross-paper architecture synthesis and recommended reading order
- implications for point-in-time financial QA, wrong-premise handling, confidence calibration, and source verification

Year-level READMEs provide shorter tables and direct links for their respective papers.

## Download boundaries

In scope:

- canonical PDFs and public supplemental reports
- public Git repositories with history
- small repository-bundled configs, prompts, and sample files

Out of scope unless explicitly requested later:

- multi-GB model weights
- full competition datasets requiring terms acceptance or credentials
- private APIs, credentials, or unavailable checkpoints
- execution of GPU-heavy training/inference solely to reproduce leaderboard scores

These external artifacts are linked and documented instead of silently omitted.

## Failure handling

- If a PDF link is unavailable, search official mirrors and preserve the canonical landing page.
- If code is absent, document the evidence and do not substitute unofficial code.
- If a repository is archived or broken, clone the latest accessible commit and record the state.
- If rank claims conflict, prefer official final results and explain automatic vs. human evaluation differences.
- If a paper title differs across OpenReview/PDF/arXiv, use the PDF/OpenReview canonical title and record aliases.
- If a file already exists, verify it before deciding whether to preserve or update; do not overwrite unrelated user material.

## Verification and acceptance criteria

The archive is complete only when:

- all ten paper directories exist
- every available canonical paper PDF opens, has nonzero pages, supports text extraction, and has representative pages rendered for visual inspection
- every official repository clone passes Git integrity checks and records branch/commit/license metadata
- Python source is syntax-parsed where applicable without installing heavyweight model dependencies
- each paper has a README and source manifest
- repository, topic, and year README local links resolve
- the root README includes existing projects and ten short paper introductions
- the CRAG raw facts, publication types, task ranks, and code availability are cross-checked against primary sources
- missing code/data/weights and unexecuted GPU/API workflows are explicitly disclosed
- temporary extraction/rendering artifacts are removed after verification

## Non-goals

- No benchmark-score reproduction claim without actually running the required official evaluation.
- No renaming Workshop reports as KDD main-conference papers.
- No assumption that “winning” means one overall champion when CRAG-MM tasks and evaluation modes have separate ranks.
- No modification of the existing FinanceRAG, WattBot, or EReL research content beyond adding root navigation links.

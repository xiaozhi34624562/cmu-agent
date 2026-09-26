# Source manifest

核验日期：2026-08-11

## Competition

- Kaggle competition: https://www.kaggle.com/competitions/WattBot2025
- Overview: https://www.kaggle.com/competitions/WattBot2025/overview
- Leaderboard: https://www.kaggle.com/competitions/WattBot2025/leaderboard
- Discussion（选手交流与方案讨论）: https://www.kaggle.com/competitions/WattBot2025/discussion
- Code / Notebooks: https://www.kaggle.com/competitions/WattBot2025/code
- Note: the repository README also uses the alias `wattbot-2025`; the paper's canonical citation uses `WattBot2025`.

## Paper

- Title: KohakuRAG: A simple RAG framework with hierarchical document indexing
- Authors: Shih-Ying Yeh, Yueh-Feng Ku, Ko-Wei Huang, Buu-Khang Tu
- arXiv: https://arxiv.org/abs/2603.07612
- PDF: https://arxiv.org/pdf/2603.07612
- Local file: `../papers/KohakuRAG.pdf`
- Local validation: 38 pages, 12,113,563 bytes, PDF 1.7; text extraction and representative-page rendering succeeded.
- Date clarification: WattBot was held in 2025; the detailed KohakuRAG paper was submitted to arXiv on 2026-03-08.

## Code

- Repository: https://github.com/KohakuBlueleaf/KohakuRAG
- Local directory: `../code/KohakuRAG/`
- Branch: `main`
- Commit: `f3d27c8d24616b75508795766355632640979e5b`
- Commit date: 2026-05-09
- License status: `pyproject.toml` declares Apache-2.0 and the README links to `LICENSE`, but this checked-out commit does not contain a `LICENSE` file. Treat the declaration as repository metadata, not as a complete license artifact.

## Reproducibility status

- Included: PDF parsing, hierarchical nodes, Jina v3/v4 embeddings, SQLite/sqlite-vec storage, BM25 option, multi-query planning, deduplication/reranking, context expansion, structured answer generation, retry-on-abstention, validation, ensemble aggregation, sweeps, multimodal image indexing, and WattBot workflows.
- Tests are present, but several are integration tests requiring model downloads and external APIs.
- External requirements: Python 3.10+, KohakuEngine, KohakuVault/sqlite-vec, Jina model downloads (roughly 2–4 GB according to the repository docs), OpenAI/OpenRouter-compatible APIs for generation/planning, and Kaggle data access.
- The winning configuration uses multiple paid/frontier models and repeated inference. A source-code checkout alone does not include API access, competition data, or every external model weight.


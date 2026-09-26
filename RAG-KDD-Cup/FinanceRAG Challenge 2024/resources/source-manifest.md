# Source manifest

核验日期：2026-08-11

## Competition

- Kaggle competition: https://www.kaggle.com/competitions/icaif-24-finance-rag-challenge
- Overview: https://www.kaggle.com/competitions/icaif-24-finance-rag-challenge/overview
- Leaderboard: https://www.kaggle.com/competitions/icaif-24-finance-rag-challenge/leaderboard
- Discussion（选手交流与方案讨论）: https://www.kaggle.com/competitions/icaif-24-finance-rag-challenge/discussion
- Code / Notebooks: https://www.kaggle.com/competitions/icaif-24-finance-rag-challenge/code

## Paper

- Title: Multi-Reranker: Maximizing performance of retrieval-augmented generation in the FinanceRAG challenge
- Authors: Joohyun Lee, Minji Roh
- arXiv: https://arxiv.org/abs/2411.16732
- PDF: https://arxiv.org/pdf/2411.16732
- Local file: `../papers/Multi-Reranker.pdf`
- Local validation: 4 pages, 567,352 bytes, PDF 1.5; `pdfinfo` and `pdftotext` succeeded; representative page rendered successfully.

## Code

- Repository: https://github.com/cv-lee/FinanceRAG
- Local directory: `../code/FinanceRAG/`
- Branch: `main`
- Commit: `a4fc6e94279f185263b579e74633d22036036446`
- Commit date: 2024-11-27
- License: MIT (`LICENSE` is present)

## Reproducibility status

- Included: Kaggle data downloader, query expansion, MultiHiertt table extraction, two-stage cross-encoder reranking, dataset-specific reranker selection, submission post-processing.
- Not included: the paper's Task 2 generation pipeline, 32K context split, two-answer fusion, final answer-generation evaluation. The upstream README explicitly says long-context management is “not included yet”.
- External requirements: Kaggle credentials, OpenAI API key, Python 3.10+, CUDA 12.2+, FlashAttention, and GPU memory roughly at A100 class for the published run configuration.
- The repository contains prepared query-expansion files but not the full Kaggle corpora; `prepare_dataset.py` downloads them after the user accepts Kaggle rules and configures credentials.


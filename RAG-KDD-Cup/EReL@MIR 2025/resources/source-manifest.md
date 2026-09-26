# Source manifest

核验日期：2026-08-11

## Competition and official results

- Kaggle competition: https://www.kaggle.com/competitions/multimodal-document-retrieval-challenge
- Leaderboard: https://www.kaggle.com/competitions/multimodal-document-retrieval-challenge/leaderboard
- Discussion（选手交流与方案讨论）: https://www.kaggle.com/competitions/multimodal-document-retrieval-challenge/discussion
- Code / Notebooks: https://www.kaggle.com/competitions/multimodal-document-retrieval-challenge/code
- Official challenge page: https://erel-mir.github.io/challenge/mdr-track1/
- Official winners and code links: https://erel-mir.github.io/challenge/results/
- Official workshop discussion page: https://erel-mir.github.io/challenge/discussion/ (currently marked TBA)

Important ranking distinction:

- Raw leaderboard #3 was `GoAhead` with 60.73, but the result could not be verified because required code was not submitted; it was ineligible for an award.
- Official awarded top three are therefore: 1st `iLearn` (65.69), 2nd `LLMHunter` (65.59), 3rd `GPU is all you need` (57.30).
- This archive follows the official winners page and downloads those three public codebases.

## Papers

### Challenge overview

- Title: Overview of the EReL@MIR 2025 Multimodal Document Retrieval Challenge (Track 1)
- Author: Jingbiao Mei
- arXiv: https://arxiv.org/abs/2606.04240
- PDF: https://arxiv.org/pdf/2606.04240
- Local file: `../papers/EReL-Multimodal-Document-Retrieval-Challenge-Overview.pdf`
- Validation: 5 pages, 467,936 bytes, PDF 1.7; text extraction and representative-page rendering succeeded.

### First-place technical report

- Title: Visual Anchor Point for Multimodal Document Retrieval
- Authors: Bohan Hou, Haoqiang Lin, Xuemeng Song, Haokun Wen, Liqiang Nie
- Original artifact: `../code/01-iLearn-MDR/report.pdf`
- Local paper copy: `../papers/1st-iLearn-Technical-Report.pdf`
- Validation: 3 pages, 464,454 bytes, PDF 1.5; text extraction and rendering succeeded.

No separate PDF report was present in the downloaded second- and third-place repositories. Their approaches are documented by the official 2026 overview paper and repository code/README files.

## Awarded code repositories

### 1st — iLearn

- Repository: https://github.com/hbhalpha/MDR
- Local directory: `../code/01-iLearn-MDR/`
- Branch / commit: `main` / `ccda92dc2b1729241a132e4f259029cb8ee9add1`
- Commit date: 2025-05-09
- License: MIT
- Major gap: scripts contain placeholder and author-machine absolute paths; LoRA checkpoints and full datasets are not bundled. README reports 8×A100 40 GB for the full system.

### 2nd — LLMHunter

- Repository: https://github.com/i2vec/MMDocRetrievalChallenge
- Local directory: `../code/02-LLMHunter-MMDocRetrievalChallenge/`
- Branch / commit: `main` / `4a6080a15f2368a0cc1e96a5bbc1984d6d4aa685`
- Commit date: 2025-03-29
- License: Apache-2.0
- Major gap: model/data paths must be supplied; the full reranker uses Qwen2.5-VL-72B-AWQ and is hardware intensive.

### 3rd — GPU is all you need

- Repository: https://github.com/bargav25/MultiModal_InformationRetrieval
- Local directory: `../code/03-GPU-is-all-you-need-MultiModal_InformationRetrieval/`
- Branch / commit: `main` / `e9010f258e9e885dd2891d05294e3fba88a80cbd`
- Commit date: 2025-03-29
- License: MIT
- Major gap: full datasets and models must be downloaded separately; README reports multiple A100/L40S GPUs with about 48 GB VRAM. Task 2 can depend on live Wikipedia image scraping, so exact results may drift over time.

## Dataset references

- MMDocIR challenge data: https://huggingface.co/datasets/MMDocIR/MMDocIR-Challenge
- M2KR challenge data: https://huggingface.co/datasets/Jingbiao/M2KR-WWW2025-Challenge
- M2KR project / PreFLMR: https://preflmr.github.io/


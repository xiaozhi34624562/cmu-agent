# Source Manifest

## Bibliographic identity

- Canonical title: *DB3 Team's Solution For Meta KDD Cup' 25*
- Authors: Yikuan Xia, Jiazun Chen, Yirui Zhan, Suifeng Zhao, Weipeng Jiang, Chaorui Zhang, Wei Han, Bo Bai, Jun Gao
- Publication: 2025 KDD Cup CRAG-MM Workshop technical paper; arXiv:2509.09681
- OpenReview: <https://openreview.net/forum?id=WeXV5NydU1>
- arXiv: <https://arxiv.org/abs/2509.09681>

## Competition and ranking evidence

- Paper reports Task 1 second, Task 2 second, Task 3 first, plus the grand prize for ego-centric queries.
- PKU report confirms the team result and release: <https://cs.pku.edu.cn/info/1264/3911.htm>.
- Official challenge: <https://kddcup25.github.io/index.html>

## Paper sources

- Downloaded from <https://arxiv.org/pdf/2509.09681>.
- Local file: `../papers/DB3-Team-Solution-For-Meta-KDD-Cup-25.pdf`
- Verification: 9 pages; 1,456,792 bytes; SHA-256 `18e946f6a3eb690646958a16f89f8d9814090346f51475169dc0c9e20d795297`.

## Code sources

- Author repository: <https://gitlab.aicrowd.com/jiazunchen/db3-team-s-solution-for-meta-kdd-cup-25>
- Status checked 2026-08-12: HTTP 503 from `git ls-remote`; no commit or license can be pinned.

## Artifact inventory

- Paper present; official code announced but currently inaccessible. Model checkpoints and competition data are not bundled.

## Reproduction dependencies

- Grounding DINO/CLIP/image reranking, OCR/web retrieval, domain routing, Llama 3.2 Vision, SFT/DPO/GRPO, checkpoint ensembles, judge models and substantial GPU inference are required.

## Known gaps and confidence

- Identity/rank is supported by OpenReview, arXiv and PKU. Source-tree completeness and runtime reproduction remain blocked by upstream 503 and missing weights/data.

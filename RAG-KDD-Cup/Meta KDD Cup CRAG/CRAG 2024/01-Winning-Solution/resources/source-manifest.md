# Source Manifest

## Bibliographic identity

- Canonical title: *Winning Solution For Meta KDD Cup' 24*
- Authors: Yikuan Xia, Jiazun Chen, Jun Gao
- Publication: 2024 KDD Cup CRAG Workshop technical paper; also arXiv:2410.00005
- OpenReview: <https://openreview.net/forum?id=oWNPeoP1uC>
- arXiv: <https://arxiv.org/abs/2410.00005>

## Competition and ranking evidence

- Scope: CRAG Tasks 1, 2 and 3.
- The paper reports first place in all three tasks, with scores 28.4%, 42.7% and 47.8%. The official Peking University report independently states that db3 won all three tasks: <https://hcst.pku.edu.cn/info/1029/1798.htm>.
- Competition: <https://www.aicrowd.com/challenges/meta-comprehensive-rag-benchmark-kdd-cup-2024>
- Workshop/results context: <https://kddcup24.github.io/pages/schedule.html>

## Paper sources

- Downloaded from arXiv PDF: <https://arxiv.org/pdf/2410.00005>
- Local file: `../papers/Winning-Solution-For-Meta-KDD-Cup-24.pdf`
- Verification: 8 pages; 604,407 bytes; SHA-256 `042737fe9f0bebdb16b2907d5d9c3d8eed0c73d78035142fb9964e8b30c64035`.

## Code sources

- Author repository: <https://gitlab.aicrowd.com/jiazunchen/kdd2024cup-crag-db3>
- Status checked 2026-08-12: `git ls-remote` returned HTTP 503; no commit can be honestly pinned.
- License status: unavailable while the repository is offline.

## Artifact inventory

- Paper: present and text-extractable.
- Code: author-published upstream, currently unavailable locally; see `../code/README.md`.
- Paper describes web extraction/chunking, reranking, public-data retrieval, LLM fine-tuning, KG/API generation and prompts.

## Reproduction dependencies

- LangChain/BeautifulSoup, BCEmbedding, vLLM, LLaMA-family models, domain public datasets and CRAG mock APIs are referenced.
- Model weights, competition data and the temporarily unavailable GitLab source are not bundled.

## Known gaps and confidence

- High confidence in identity/rank from OpenReview, arXiv and PKU; no leaderboard reproduction was run.
- Code completeness, commit and license remain unverified because the official host returned 503.

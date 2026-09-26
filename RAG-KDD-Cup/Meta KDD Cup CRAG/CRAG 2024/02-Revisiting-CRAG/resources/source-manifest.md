# Source Manifest

## Bibliographic identity

- Canonical title: *Revisiting the Solution of Meta KDD Cup 2024: CRAG*
- Authors: Jie Ouyang, Yucong Luo, Mingyue Cheng, Daoyu Wang, Shuo Yu, Qi Liu, Enhong Chen
- Publication: 2024 KDD Cup CRAG Workshop technical paper; arXiv:2409.15337
- OpenReview: <https://openreview.net/forum?id=PUzLjWIgqC>
- arXiv: <https://arxiv.org/abs/2409.15337>

## Competition and ranking evidence

- Scope: all three stages/tasks, with emphasis on Tasks 2 and 3.
- OpenReview records the APEX author claim of second place in Tasks 2 and 3. This archive labels it as paper/OpenReview-reported because the historical interactive leaderboard is not reproduced locally.
- Competition: <https://www.aicrowd.com/challenges/meta-comprehensive-rag-benchmark-kdd-cup-2024>

## Paper sources

- Downloaded from <https://arxiv.org/pdf/2409.15337>.
- Local file: `../papers/Revisiting-the-Solution-of-Meta-KDD-Cup-2024-CRAG.pdf`
- Verification: 8 pages; 1,104,873 bytes; SHA-256 `95a4d56e213661619c91e9634462e7d6219ccdc1c4323150ef24b03ad841343c`.

## Code sources

- Official repository linked by paper: <https://github.com/USTCAGI/CRAG-in-KDD-Cup2024>
- Local clone: `../code/CRAG-in-KDD-Cup2024`
- Default branch/commit: `master` / `df3fea49e365520124453de85b70063a634c4b4d`
- License: no standalone LICENSE found at the pinned commit.

## Artifact inventory

- Present: README, main/evaluation scripts, domain routing, API extractor, web retriever, prompt templates, tokenizer files and architecture images.
- Absent: trained model weights and full competition data.

## Reproduction dependencies

- Requires LLM/embedding/reranker downloads, CRAG data, KG mock APIs and GPU inference; `requirements.txt` is present.
- Full leaderboard execution was not run.

## Known gaps and confidence

- High confidence in source ownership because the paper links this repository.
- Static Git integrity passed; runtime behavior remains unverified without models/data.

# Source Manifest

## Bibliographic identity

- Canonical title: *MARAGS: A Multi-Adapter System for Multi-Task Retrieval Augmented Generation Question Answering*
- Author: Mitchell DeHaven
- Publication: 2024 KDD Cup CRAG Workshop technical paper; arXiv:2409.03171
- OpenReview: <https://openreview.net/forum?id=lqmLis4sSX>
- arXiv: <https://arxiv.org/abs/2409.03171>

## Competition and ranking evidence

- The paper reports second place for Task 1 and third place for Task 2; a later official AIcrowd winner spotlight describes md_dh as third place in Task 1, creating a rank inconsistency.
- Spotlight: <https://discourse.aicrowd.com/t/winner-spotlight-series-md-d-meta-kdd-cup-2024/17036>
- This archive flags the conflict instead of choosing a convenient rank.

## Paper sources

- Downloaded from <https://arxiv.org/pdf/2409.03171>.
- Local file: `../papers/MARAGS.pdf`
- Verification: 6 pages; 1,533,295 bytes; SHA-256 `2b53853679b763f6fafda0e924d7032eeefa632a72181392fdfb10ac5c9b1a40`.

## Code sources

- No official source repository or adapter weights found in OpenReview, arXiv, the AIcrowd spotlight or author/title searches.
- Code disposition: `../code/README.md`.

## Artifact inventory

- Paper present; no preprocessing/training/inference/evaluation code, configs or adapters released.

## Reproduction dependencies

- Llama 3, task-specific LoRA adapters, sentence-transformer embeddings, MS MARCO MiniLM cross-encoder, CRAG APIs/data and GPU memory are required.

## Known gaps and confidence

- Method is well described, but absence of code/adapters limits exact reproduction. Rank discrepancy is explicitly unresolved.

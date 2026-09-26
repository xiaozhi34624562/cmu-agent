# Source Manifest

## Bibliographic identity

- Canonical title: *Winning Meta KDD Cup'25 Task 2*
- Authors: Raja Biswas, Chris Deotte, Gilberto Titericz Junior, Kazuki Onodera, Ahmet Erdem
- Publication: 2025 KDD Cup CRAG-MM Workshop technical paper
- OpenReview: <https://openreview.net/forum?id=7VTwu1Qu5d>

## Competition and ranking evidence

- Scope: CRAG-MM Task 2 multi-source augmentation.
- OpenReview reports Team NVIDIA first in final human evaluation with score 0.233. Automatic and human evaluation are not conflated.
- Official challenge: <https://kddcup25.github.io/index.html>
- AIcrowd: <https://www.aicrowd.com/challenges/meta-crag-mm-challenge-2025>

## Paper sources

- Downloaded from the official OpenReview attachment: <https://openreview.net/pdf?id=7VTwu1Qu5d>.
- Local file: `../papers/18_Winning_Meta_KDD_Cup_25_Tas.pdf`
- Verification: 7 pages; 2,155,747 bytes; SHA-256 `b0d81e55c40b22eb7e29285231fe465f3ee491d7e08f068ee0319c3a70a3dd39`.

## Code sources

- Official repository linked by paper: <https://github.com/rbiswasfc/crag-mm>
- Local clone: `../code/crag-mm`
- Default branch/commit: `main` / `2728d3a21b474afee1ad88f21941c80479c678b7`
- License: Apache License 2.0 (`LICENSE`).

## Artifact inventory

- Present: paper, agents, Task 2 submission agent, dataset generation, synthetic query writing, training script, local evaluator, Dockerfile, requirements and docs.
- External releases: dataset <https://huggingface.co/datasets/rbiswasfc/kddcup-sft-datamix>; model <https://huggingface.co/rbiswasfc/aicrowd-kddcup-v9>.

## Reproduction dependencies

- Llama-3.2-11B-Vision-Instruct derivative, HF gated access, image/data assets, search API, CUDA/GPU and judge-model dependencies are required. Large weights/data were not downloaded.

## Known gaps and confidence

- Code identity/commit and human-eval claim are high confidence. Full competition execution and model-weight verification were not performed.

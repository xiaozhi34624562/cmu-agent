# Source Manifest

## Bibliographic identity

- Canonical title: *Honest AI: Fine-Tuning "Small" Language Models to Say "I Don't Know", and Reducing Hallucination in RAG*
- Authors: Xinxi Chen, Li Wang, Wei Wu, Qi Tang, Yiyao Liu
- Publication: 2024 KDD Cup CRAG Workshop technical paper; arXiv:2410.09699
- OpenReview: <https://openreview.net/forum?id=X4UoRsiU72>
- arXiv: <https://arxiv.org/abs/2410.09699>

## Competition and ranking evidence

- Paper reports first place for Task 2 false-premise questions; this is a category result, not overall Task 2 first.
- Competition: <https://www.aicrowd.com/challenges/meta-comprehensive-rag-benchmark-kdd-cup-2024>

## Paper sources

- Downloaded from <https://arxiv.org/pdf/2410.09699>.
- Local file: `../papers/Honest-AI.pdf`
- Verification: 8 pages; 1,135,466 bytes; SHA-256 `ec121b5ed4c007f352a1a229f0c19c21ae9cc1cc15b8efa257a9df4874d708a3`.

## Code sources

- No official repository or checkpoint found in OpenReview, arXiv or author/title searches checked 2026-08-12.
- Code disposition: `../code/README.md`.

## Artifact inventory

- Paper includes QLoRA data relabeling/training hyperparameters and comparative experiments; code, adapters and processed data are absent.

## Reproduction dependencies

- Llama-2-7B-chat, QLoRA/4-bit training, CRAG training data, Gemini/Search/KG experiments and organizer evaluator are required.

## Known gaps and confidence

- Hyperparameters are reproducible from the paper; exact data split, seeds, prompts and checkpoint are incomplete.

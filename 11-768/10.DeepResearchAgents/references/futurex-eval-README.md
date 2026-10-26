# FutureX Evaluation Scripts

This repository contains the evaluation code for the FutureX benchmark from the paper
[FutureX: An Advanced Live Benchmark for LLM Agents in Future Prediction](https://arxiv.org/abs/2508.11987).

It provides the core scoring functions used in FutureX evaluation:

- Level 1/2 (Type-A style): set/multi-label F1 scoring.
- Level 3/4 (Type-B style): LLM-as-judge scoring for numeric, string, and ranking answers.

## Environment Setup

Use Python 3.9+ and install required packages:

```bash
pip install openai tenacity diskcache
```

Set the LLM judge environment variables:

```bash
export OPENAI_API_KEY="YOUR_API_KEY"
export OPENAI_API_BASE="YOUR_API_BASE"   # optional for official OpenAI
export OPENAI_API_MODEL="YOUR_API_MODEL" # e.g. gpt-4.1 / volc-deepseek-v3
```

Or use DeepSeek V4 Flash through its OpenAI-compatible endpoint:

```bash
export DEEPSEEK_API_KEY="YOUR_API_KEY"
export DEEPSEEK_BASE_URL="https://api.deepseek.com"
export DEEPSEEK_MODEL="deepseek-v4-flash"
```

`DEEPSEEK_API_KEY` takes precedence when it is configured.

## Main Files

- `eval.py`: public scoring entrypoints and evaluation helpers.
- `llm_judge_level_34.py`: L3/L4 judge implementation.
- `metric_router.py`: one cached LLM route per resolved question.
- `utils.py`: number parsing helpers (`to_float`, `is_number`).

## Usage

### Level 1/2

```python
from eval import estimate_type_a_score

y_true = [set(["A"]), set(["A", "B"])]
y_pred = [set(["A"]), set(["B"])]
scores, avg = estimate_type_a_score(y_true, y_pred)
print(scores, avg)
```

### Level 3/4

```python
from eval import estimate_type_b_score

questions = ["Q1", "Q2"]
y_true = [[3.2], ["Beijing"]]
y_pred = [["3.1"], ["北京市"]]
stds = [0.5, 1.0]
scores, avg = estimate_type_b_score(questions, y_true, y_pred, stds)
print(scores, avg)
```

### Routed Scoring

Use routed scoring when a weekly batch may include unordered entity sets. The
router receives each question and its resolved GT once, persists the selected
metric by model/endpoint/prompt version, and every model submission reuses it.
Level-3/4 judge responses use the same versioned disk-cache scheme.

```python
from eval import prewarm_metric_routes, estimate_routed_scores

questions = ["Name eight qualifying teams; order does not matter."]
y_true = [["AG.AL", "T1"]]
y_pred = [["T1", "Anyone's Legend"]]
levels = [4]
ids = ["example-id"]

prewarm_metric_routes(questions, y_true, levels=levels, question_ids=ids)
scores, avg, routes = estimate_routed_scores(
    questions, y_true, y_pred, [None], levels=levels, question_ids=ids
)
print(scores, avg, routes[0].metric)
```

## Notes On Level-3/4 Logic

- Numeric GT is normalized before scoring (including single-string numbers).
- Numeric `std` is auto-derived for numeric GT (`0.05 * gt`, with `0 -> 0.01`).
- Multi-choice ranking answers (e.g. `["A", "B", "C"]`) support order-insensitive exact match shortcut.
- Non-exact ranking answers use overlap-based partial credit.
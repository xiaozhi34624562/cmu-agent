# Dataset provenance (do not regenerate or edit)

Graders evaluate against these exact splits.

| file | contents |
|---|---|
| `number_search_train.jsonl` | 50,000 Number Search tasks (train split) |
| `number_search_val.jsonl` | 1,000 held-out tasks |
| `textcraft_train.jsonl` | 852 TextCraft-Synth tasks, **medium** difficulty (train split) |
| `textcraft_val.jsonl` | 213 held-out medium tasks |
| `textcraft_val_hard.jsonl` | 136 held-out **hard** tasks (generalization probe) |
| `textcraft_recipes.json` | the full synthetic recipe book (1,452 items) all TextCraft tasks were generated against |

Notes:
- Number Search `max_steps` is `ceil(log2(high - low + 2))`, the exact
  worst-case binary-search budget including the final correct guess. There
  are no extra guesses; each LLM turn uses one step.
- TextCraft tasks provide `target_items` and `initial_inventory` in
  `task.info`; raw materials only come from the initial inventory (there is
  no gather action), and reward requires calling `finish()`.

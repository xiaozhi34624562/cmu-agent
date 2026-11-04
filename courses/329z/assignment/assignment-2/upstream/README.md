# CS329Z Assignment 2: Building an Evaluation Task

This is the starter repository for Assignment 2.

**Start by reading the handout, [`cs329z_assignment2_evaluation.pdf`](cs329z_assignment2_evaluation.pdf), in this directory.**
It states every problem and what is graded. This file covers setup, the
commands you will run, and where things are.

## Layout

```text
cs329z_assignment2_evaluation.pdf  # assignment handout
tasks/humaneval-0/                 # example Harbor task used in Section 3
writeup/                           # response files and report templates for each section
check_submission.py                # lists anything missing from your submission
pinned_agent.py                    # pins mini-SWE-agent's versions (do not edit)
.env.example                       # template for your .env
pyproject.toml                     # pinned dependencies (Harbor, matplotlib)
uv.lock                            # reproducible Python environment
```

## Setup

1. Install [uv](https://docs.astral.sh/uv/) and Docker.
2. Create your `.env` file and add your API key:

   ```bash
   cp .env.example .env
   ```

   The file is gitignored. Do not commit it.
3. Install the dependencies and check Harbor:

   ```bash
   uv sync
   uv run harbor --version
   ```

See Section 2 of the handout for full setup instructions.

On an Apple Silicon Mac, the SWE-bench task in Section 3.2 needs
`export DOCKER_DEFAULT_PLATFORM=linux/amd64` first (see the handout).

Run every command with `uv run` from the repository root.
Need another package? Use `uv add <package>`, not `pip install`.
Commit the updated `pyproject.toml` and `uv.lock`.

## Before you submit

Check that every expected file and run artifact is in place:

```bash
uv run python check_submission.py
```

It lists anything missing and any unanswered placeholders left in your responses.

Then upload your repository to Gradescope with its GitHub integration (due 11/23).
Keep your repository private.

## Acknowledgements

This assignment was designed and built by John Yang for Stanford's CS329Z
Engineering AI Agents course with lots of help from Claude Opus 5.5. We owe a
debt of gratitude to the various people who shared thoughts and feedback on
this assignment. In particular we would like to highlight Michael Ryan, Diyi
Yang, Shreyas Sharma, and Anantharaman Iyer.

If you would like to use this assignment for your course you are welcome to do
so with brief attribution. It is released under the MIT license (see
`LICENSE`).

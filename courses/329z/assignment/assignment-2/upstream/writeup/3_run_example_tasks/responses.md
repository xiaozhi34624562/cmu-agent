# Section 3: Run Example Tasks

## 3.1 Task 1: HumanEval

**Problem 3 (`run-example-task`)**

1. Which files are available to the agent while it works, and which files become available only during verification? Why does this separation matter?

   <!-- Your response here. -->

2. Run `uv run harbor run --help`. Name two agent scaffolds other than `oracle` and two environment backends other than Docker. What distinct role does each category play?

   <!-- Your response here. -->

3. Trace the verification process after the agent finishes: which file does Harbor execute, where do the private tests come from, and how is the final reward communicated back to Harbor?

   <!-- Your response here. -->

**Problem 4 (`run-example-agent`)**

1. Summarize the agent's approach. Which files and commands did it use?

   <!-- Your response here. -->

2. Identify one decision in the trajectory that helped or hurt the final result. Cite the relevant step.

   <!-- Your response here. -->

3. Did the verifier reward accurately reflect the quality of the agent's solution? Why or why not?

   <!-- Your response here. -->

## 3.2 Task 2: SWE-bench Verified

**Problem 5 (`run-swebench-agent`)**

1. Summarize the agent's approach. How did it locate the relevant code, and what change did it make?

   <!-- Your response here. -->

2. Identify one point where the agent used repository context that would not exist in a self-contained HumanEval task.

   <!-- Your response here. -->

3. Compare this trajectory with the HumanEval trajectory. What made this task more difficult to understand, modify, or verify?

   <!-- Your response here. -->

4. Did the final reward accurately reflect the quality of the agent's solution? Support your answer with evidence from the verifier logs.

   <!-- Your response here. -->

## 3.3 Task 3: Terminal-Bench 2.1

**Problem 6 (`run-terminal-bench-agent`)**

1. Summarize the agent's approach. What information did it gather, and what solution strategy did it pursue?

   <!-- Your response here. -->

2. Identify one point where the agent made meaningful progress and one point where its approach broke down or became unproductive.

   <!-- Your response here. -->

3. What evidence does the verifier provide beyond the scalar reward? Does it capture partial progress on this task?

   <!-- Your response here. -->

4. How did the open-ended terminal environment affect the agent's ability to plan, test its assumptions, and recover from mistakes?

   <!-- Your response here. -->

## 3.4 Analyzing Agent Trajectories

**Problem 7 (`analyze-trajectories`)**

Answer **three** of the seven questions below and **delete the other four**. For each question you answer, save the figure as a PNG in `writeup/3_run_example_tasks/` using the filename shown, then explain in 2–3 sentences what you measured, how you computed it, and what you conclude.

### `effort-distribution.png`

How did the agent distribute its effort across activities such as inspecting files, editing code, running tests, and debugging?

![](effort-distribution.png)

<!-- Your response here. -->

### `bash-command-usage.png`

`mini-SWE-agent` performs its work through `execute_bash`. What command-line programs and command patterns did it use across the three trajectories, and how did their use vary by task?

![](bash-command-usage.png)

<!-- Your response here. -->

### `exploration-to-implementation.png`

At what points did each agent appear to transition from exploring the task to implementing a solution? Define how your visualization identifies that transition.

![](exploration-to-implementation.png)

<!-- Your response here. -->

### `repeated-effort.png`

Where did the agent repeat commands, revisit earlier hypotheses, or otherwise spend effort without making clear progress?

![](repeated-effort.png)

<!-- Your response here. -->

### `context-consulted.png`

How did the amount and type of repository or environment context consulted by the agent differ across tasks?

![](context-consulted.png)

<!-- Your response here. -->

### `failure-recovery.png`

What patterns of failure and recovery appear in the trajectories? For example, when a command or hypothesis failed, what did the agent do next?

![](failure-recovery.png)

<!-- Your response here. -->

### `custom-analysis.png`

Choose another measurable property of the trajectories that you believe reveals something important about agent behavior. Explain why you selected it.

![](custom-analysis.png)

<!-- Your response here. -->

# Week 6 本地运行记录

日期：2026-10-28。Python 3.11.10。

仅执行标准库教学样例：交接契约检查、损失筛选与统计指标算术、Python 正则边界。没有调用模型、运行 Django、复现论文基准、测量多 Agent 加速，或运行 mini-swe-agent CLI。

命令：`python3 MAS.S62/6.HarnessEvolution2/examples/handoff_contract.py`，退出码 0。

```text
PASS: paired handoff, stale/evidence/unresolved/incomplete rejection
```

命令：`python3 MAS.S62/6.HarnessEvolution2/examples/metrics_and_boundaries.py`，退出码 0。

```text
Toolformer teaching loss improvement: 0.500
Task macro average: 0.666667
Gain: 16.6 percentage points; relative 48.967552%
R squared: 0.888889; kappa: 0.800; Jaccard: 0.333333
PASS: arithmetic and trailing-newline boundary; no Django or model run
```


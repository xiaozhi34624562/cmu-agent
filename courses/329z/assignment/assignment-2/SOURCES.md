# CS329Z Assignment 2：Building an Evaluation Task

- 状态核对与取得日期：2026-11-04；学习阶段 P3。
- 官方仓库：[cs329z/assignment2-harness](https://github.com/cs329z/assignment2-harness)。
- 固定提交：`be78339f6e74d58cd426f272f61885d619f6edd1`；28 个原始文件。
- [官方 handout：Version 26.1.0，17 页](upstream/cs329z_assignment2_evaluation.pdf) · [官方 README](upstream/README.md) · [代码和样例](upstream/) · [来源与逐文件校验](SNAPSHOT.json)。
- 官方 [课表](../../site/index.html) 和 [课程要求](../../site/logistics.html)；截止时间按官网 Pacific Time。

## 作业目标与交付

已取得完整原题与 starter，替代先前只有概要的状态。题目要求构造并验证一个有现实用途、需要多轮行动的 Agent 评测任务。

| 部分 | handout 实际页序 | 工作 | 权重 |
|---|---|---|---:|
| Basics | 3–4 | 理解 Docker 与 Harbor，确认可复现环境和执行接口 | 5% |
| Run example tasks | 5–11 | 对照 HumanEval、SWE-bench Verified、Terminal-Bench，读取轨迹并制作三幅分析图 | 10% |
| Create your own task | 12–14 | 定义任务、环境、oracle、verifier，保存五次独立模型尝试和一页报告 | 70% |
| Peer review | 15 | 评审三位同学的任务、报告和轨迹，给出证据及改进建议 | 15% |

任务仓库 **2026-11-23** 提交；三份评审合为 `peer_review.pdf`，**2026-12-02** 提交。学校提交平台、课程 gallery 和学生结果不在此归档中。

## 核心任务契约

handout pp.12–14 要求：

1. 描述清楚且能力目标明确；失败来自能力缺口，不能靠隐含要求或脆弱环境制造困难。
2. 初始环境能从干净检出构建，Agent 需要通过观察和行动完成有意义的多轮工作。
3. oracle 与模型尝试使用同一个 verifier；oracle 应取得完整奖励。
4. verifier 检查真实结果，不只检查文件存在或关键字；初始未操作状态应为 0，并接受不同于 oracle 的正确方案。
5. 奖励位于 `[0,1]`，允许二元、离散或连续评分；需检查错误、不完整和合理替代方案。
6. 最终任务使用指定 mini-SWE-agent 与 Gemini 3.8 Flash，保存全部五次尝试，不挑选有利运行。
7. 一页报告说明能力、环境、验证和五次结果。原题难度评分包含“至多两次成功/五次尝试”，但不得为此损坏任务或引入歧义。

此前 logistics 概要提到 LLM Judge；取得 handout 后以原题实际验证契约为准，不再把“至少一个 LLM Judge”列为这份作业的统一必做项。

## 环境与入口

- [pyproject.toml](upstream/pyproject.toml)：Python `>=3.12,<3.14`，Harbor `0.18.0`、matplotlib `3.11.2`；版本锁定见 [uv.lock](upstream/uv.lock)。
- [pinned_agent.py](upstream/pinned_agent.py) 固定 Agent 相关依赖，按原题不修改。
- [.env.example](upstream/.env.example) 只是凭据模板；未保存实际 API key 或 `.env`。
- [官方样例](upstream/tasks/humaneval-0/) 包含 instruction、环境、tests 与 oracle；[writeup](upstream/writeup/) 保留未填写的响应和报告模板。
- [check_submission.py](upstream/check_submission.py) 检查提交文件、产物与占位项，不判断答案语义。

正式练习应在本作业自己的工作副本中按 README 执行 `uv sync` 和 `uv run`；需要 Docker 与实际模型凭据。本资料库根目录不是作业环境。Apple Silicon 上的指定 SWE-bench 镜像按 handout p.8 使用 `DOCKER_DEFAULT_PLATFORM=linux/amd64`。

## 当前验证范围

已核对固定提交、28 个原始文件的清单与哈希、17 页 handout、README 和依赖声明。SNAPSHOT.json 保存来源与逐文件 SHA-256，课程 CHECKSUMS 同时覆盖快照。学生待实现内容保留原样。

**未运行**依赖安装、Docker、Harbor oracle、真实模型/API、五次尝试、提交检查或学校提交。缺少学生答案和运行产物是官方 starter 的预期状态，不记作归档损坏或作业已完成。

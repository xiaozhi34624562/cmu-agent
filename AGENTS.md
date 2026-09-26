# CMU AI Agents 学习资料库

## 项目内容

本仓库整理 Carnegie Mellon University 11-768 AI Agents 课程的讲义、阅读材料、中文学习笔记和作业资料，也收录相关研究与工程案例。它是学习资料库，不是一个统一构建或运行的应用项目。

课程主题按目录编号组织：

| 目录 | 内容 |
|---|---|
| `1.WhatIsAnAgent/` | Agent 基础、ReAct 与工具使用入门 |
| `2.ToolUse/` | 工具调用、结构约束、API、MCP 与工具评测 |
| `3.LongContext/` | 长上下文方法与评测 |
| `4.SkillsAndMemory/` | Agent Skills、记忆机制与相关研究 |
| `5.PlanningAndCoordination/` | 规划、多 Agent 协作与协调 |
| `6.CodingAgents/` | Coding Agent、软件工程任务与评测 |
| `7.ComputerUseAgents/` | 浏览器和桌面等计算机使用 Agent |
| `8.SupervisedFineTuning/` | SFT、数据格式、损失设计与训练实践 |
| `9.TrainingRLBasics/` | 强化学习基础、策略梯度、GRPO 与 DrGRPO |
| `10.DeepResearchAgents/` | Deep Research Agent、搜索、研究基准与评测 |

课程目录中的 `SOURCES.md` 列出讲义、阅读材料和来源链接；综合笔记通常按课程讲义与参考资料组织，并标注引用位置和结论边界。

其他资料位于：

- `assignment/assignment-1/`、`assignment/assignment-2/`：11-768 的 Agent Harness 与数据可视化 Agent 作业资料、代码、测试和样例数据。
- `RAG-KDD-Cup/`：多个 KDD Cup RAG 挑战赛的论文、说明、笔记和参赛代码快照。目录中部分上游项目曾有独立 Git 历史；本仓库只管理其中收录的文件。
- `DSec/`：DeepSeek DSec 论文和中文解读。
- `BuildReasoningLLM/`：推理模型构建相关资料。
- `infra/`：AI 基础设施与 Agent 工程相关 PDF。
- `memoryForLLM/`：LLM 记忆机制综述及配套笔记。

## 编辑与维护

- 先查看目标主题目录的 `SOURCES.md`、README 或笔记中的资料索引，再编辑相关内容；没有统一的依赖安装、构建或测试命令。
- 保留来源文件名、链接、版本和页码。区分原文结论、基于来源的推导和工程建议，不把不同论文的实验结果混成统一结论。
- 新增课程或主题时，沿用编号目录结构，并提供 `SOURCES.md` 作为该目录的资料入口；笔记中的引用应能对应到仓库中的资料或稳定来源链接。
- 更新作业代码时，在对应作业目录中查看其 `README.md`、`ASSIGNMENT.md` 和 `pyproject.toml`，按该作业自己的环境与说明工作。不要假设仓库根目录有通用测试套件。
- 保留作业、挑战赛和上游快照中的原始文件结构。不要把根仓库误配置成这些子目录的工作环境，也不要覆盖未经本次任务授权修改的内容。
- 上传前排除 `.DS_Store`、缓存、实际凭据和本地环境文件；保留明确作为示例的 `.env.example`。二进制资料应保留原文件，不做可能损坏内容的文本转换。


# Agent 与 AI Systems 学习资料库

## 项目内容

本仓库整理 Agent 与 AI Systems 相关课程的讲义、阅读材料、中文学习笔记和作业资料，也收录相关研究与工程案例。它是学习资料库，不是一个统一构建或运行的应用项目。

当前主要课程位于：

- `11-768/`：Carnegie Mellon University 11-768 AI Agents 课程资料。
- `2680/`：Harvard CS2680 Modern AI Systems: Agents and System Optimizations 课程资料。

`11-768/` 的课程主题按目录编号组织：

| 目录 | 内容 |
|---|---|
| `11-768/1.WhatIsAnAgent/` | Agent 基础、ReAct 与工具使用入门 |
| `11-768/2.ToolUse/` | 工具调用、结构约束、API、MCP 与工具评测 |
| `11-768/3.LongContext/` | 长上下文方法与评测 |
| `11-768/4.SkillsAndMemory/` | Agent Skills、记忆机制与相关研究 |
| `11-768/5.PlanningAndCoordination/` | 规划、多 Agent 协作与协调 |
| `11-768/6.CodingAgents/` | Coding Agent、软件工程任务与评测 |
| `11-768/7.ComputerUseAgents/` | 浏览器和桌面等计算机使用 Agent |
| `11-768/8.SupervisedFineTuning/` | SFT、数据格式、损失设计与训练实践 |
| `11-768/9.TrainingRLBasics/` | 强化学习基础、策略梯度、GRPO 与 DrGRPO |
| `11-768/10.DeepResearchAgents/` | Deep Research Agent、搜索、研究基准与评测 |
| `11-768/11.AdvancedRLAlgorithms/` | 面向 Agent 的进阶强化学习算法、信用分配、PPO 系列、可靠奖励与蒸馏 |
| `11-768/12.TrainingRLSystems/` | RL 训练系统资料 |
| `11-768/13.AgentSafety/` | Agent 安全、沙箱、权限、监控与风险案例 |
| `11-768/14.OpenHands/` | OpenHands、软件 Agent SDK 与 Coding Agent 案例 |
| `11-768/15.OrchestrationAndMonitoring/` | Agent 编排、工作流、评测、可观测性与行为监控 |

`2680/` 的根目录 `README.md` 和 `SOURCES.md` 是课程总入口。18 个编号课次按官网日期排序，目录名保留课程原题；每课的 `SOURCES.md` 记录讲义、阅读资料、来源链接及尚未获取的内容。目录编号不一定等于官方讲义 PDF 的编号。

课程目录中的 `SOURCES.md` 列出讲义、阅读材料和来源链接；综合笔记通常按课程讲义与参考资料组织，并标注引用位置和结论边界。`11-768/10.DeepResearchAgents/` 可包含与 Deep Research 相关的金融 Agent 研究补充，例如 FutureX-Pro、MBABench、AURA 等论文核查笔记。

其他资料位于：

- `11-768/assignment/assignment-1/`、`11-768/assignment/assignment-2/`：11-768 的 Agent Harness 与数据可视化 Agent 作业资料、代码、测试和样例数据。
- `2680/assignment/`、`2680/assignments/`、`2680/project/`：CS2680 的作业 1–4、公开作业仓库快照和项目资料；作业入口见 `2680/README.md`。
- `RAG-KDD-Cup/`：多个 KDD Cup RAG 挑战赛的论文、说明、笔记和参赛代码快照。目录中部分上游项目曾有独立 Git 历史；本仓库只管理其中收录的文件。
- `DSec/`：DeepSeek DSec 论文和中文解读。
- `BuildReasoningLLM/`：推理模型构建相关资料。
- `engineering/`：面向具体工程问题的专题研究，例如 Knowledge Agents、金融投研智能体、OCR、文档上下文层和 CCA 工作流。该目录不是课程新增讲次；有些专题使用独立 `SOURCES.md`，有些把来源索引合并在主文末尾。
- `infra/`：AI 基础设施与 Agent 工程相关 PDF；`infra/1.DocumentContextLayer/` 存放文档上下文层、OCR、LlamaParse 与券商研报解析研究资料。
- `memoryForLLM/`：LLM 记忆机制综述及配套笔记。

## 编辑与维护

- 先查看目标主题目录的 `SOURCES.md`、README 或笔记中的资料索引，再编辑相关内容；没有统一的依赖安装、构建或测试命令。
- 保留来源文件名、链接、版本和页码。区分原文结论、基于来源的推导和工程建议，不把不同论文的实验结果混成统一结论。
- 新增课程或主题时，沿用编号目录结构，并提供 `SOURCES.md` 作为该目录的资料入口；笔记中的引用应能对应到仓库中的资料或稳定来源链接。
- 更新作业代码时，在对应作业目录中查看其 `README.md`、`ASSIGNMENT.md` 和 `pyproject.toml`，按该作业自己的环境与说明工作。不要假设仓库根目录有通用测试套件。
- 保留作业、挑战赛和上游快照中的原始文件结构。不要把根仓库误配置成这些子目录的工作环境，也不要覆盖未经本次任务授权修改的内容。
- 上传前排除 `.DS_Store`、缓存、实际凭据和本地环境文件；保留明确作为示例的 `.env.example`。二进制资料应保留原文件，不做可能损坏内容的文本转换。

## 两个课程的更新方式

- 更新 `11-768/` 时，按课次目录手工维护：新增讲义、阅读材料或参考资料后，同步更新该课次的 `SOURCES.md`，在综合笔记中保留引用位置和结论边界；新增课次时使用 `编号.主题名/` 目录，并在本文件的 11-768 表格中补充说明。
- 更新 `2680/` 时，运行 `python3 2680/sync.py` 同步公开网站、阅读材料和作业；该脚本会调用 `organize.py` 整理课次目录，并更新来源索引与校验值。只整理已有下载文件时，单独运行 `python3 2680/organize.py`。脚本需要 `requests` 和 `beautifulsoup4`。官网课表变化时，先核对 `2680/organize.py` 中的课次日期、标题和目录名；运行后检查 `2680/README.md`、`2680/SOURCES.md`、各课次及作业的 `SOURCES.md`、`2680/assignments/SNAPSHOT.json` 与 `2680/CHECKSUMS.sha256`。下载失败、仅有验证页或上游快照未更新时，保留相应状态说明，不将其记为已获取的正文。
- `2680/site/`、`2680/readings/` 和 `2680/assignments/course-repo/` 是原始归档或固定快照；不要直接翻译或改写其中原始内容。学习笔记、中文整理和工程解读应放在对应编号课次目录或明确的专题文件中。

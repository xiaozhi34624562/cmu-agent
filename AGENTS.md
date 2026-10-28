# Agent 与 AI Systems 学习资料库

## 项目内容

本仓库整理 Agent 与 AI Systems 相关课程的讲义、阅读材料、中文学习笔记和作业资料，也收录相关研究与工程案例。它是学习资料库，不是一个统一构建或运行的应用项目。

当前主要课程位于：

- `11-768/`：Carnegie Mellon University 11-768 AI Agents 课程资料。
- `2680/`：Harvard CS2680 Modern AI Systems: Agents and System Optimizations 课程资料。
- `MAS.S62/`：MIT MAS.S62 How to AI an AI for (Almost) Anything（Fall 2026，自演化 AI）课程资料。

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
| `11-768/16.AgentsAndTheFutureOfWork/` | 面向人类工作的 Agent、任务自动化与增强、职业任务评测和人机协作 |

`2680/` 的根目录 `README.md` 和 `SOURCES.md` 是课程总入口。18 个编号课次按官网日期排序，目录名保留课程原题；每课的 `SOURCES.md` 记录讲义、阅读资料、来源链接及尚未获取的内容。目录编号不一定等于官方讲义 PDF 的编号。

`MAS.S62/` 按官网 14 个 Week 编号，包含项目展示周；周次不等于讲义中的 Lecture 编号。根目录 `README.md`、`SOURCES.md` 与 `manifest.json` 提供课表、来源和下载状态。已公开讲义的教学周在对应目录提供 `notes.zh-CN.md`：以讲义为主线，结合阅读和参考资料解释机制、实验证据、实现、选型、成本及故障诊断，注明页码、版本和工程推导边界。

课程目录中的 `SOURCES.md` 列出讲义、阅读材料和来源链接；综合笔记通常按课程讲义与参考资料组织，并标注引用位置和结论边界。`11-768/10.DeepResearchAgents/` 可包含与 Deep Research 相关的金融 Agent 研究补充，例如 FutureX-Pro、MBABench、AURA 等论文核查笔记。

其他资料位于：

- `11-768/assignment/assignment-1/`、`11-768/assignment/assignment-2/`、`11-768/assignment/assignment-3/`：11-768 的 Agent Harness、数据可视化 Agent 评测与强化学习训练作业资料、代码、测试和样例数据。作业 3 保留官方未完成的 starter code；来源提交与逐文件校验值见其 `SNAPSHOT.json`，不要把学生待实现部分当作归档损坏而填入答案。
- `2680/assignment/`、`2680/assignments/`、`2680/project/`：CS2680 的作业 1–4、公开作业仓库快照和项目资料；作业入口见 `2680/README.md`。
- `RAG-KDD-Cup/`：多个 KDD Cup RAG 挑战赛的论文、说明、笔记和参赛代码快照。目录中部分上游项目曾有独立 Git 历史；本仓库只管理其中收录的文件。
- `DSec/`：DeepSeek DSec 论文和中文解读。
- `BuildReasoningLLM/`：推理模型构建相关资料。
- `eval/`：AI 评测与评测工程相关资料。
- `engineering/`：面向具体工程问题的专题研究，例如 Knowledge Agents、金融投研智能体、OCR、文档上下文层和 CCA 工作流。该目录不是课程新增讲次；有些专题使用独立 `SOURCES.md`，有些把来源索引合并在主文末尾。
- `infra/`：AI 基础设施与 Agent 工程相关 PDF；`infra/1.DocumentContextLayer/` 存放文档上下文层、OCR、LlamaParse 与券商研报解析研究资料。
- `memoryForLLM/`：LLM 记忆机制综述及配套笔记。

## 编辑与维护

- 先查看目标主题目录的 `SOURCES.md`、README 或笔记中的资料索引，再编辑相关内容；没有统一的依赖安装、构建或测试命令。
- 论文和阅读网页使用完整标题命名，避免只用编号、方法简称、截断标题或 URL 摘要；文件系统不安全的标点替换为下划线。课程讲义、教程和上游代码快照保留官方原名及结构。原始论文文件名、来源链接、版本、页码和内容校验值保留在来源索引与 `tools/MATERIAL_RENAMES.json` 中，改名时同步更新本地引用、索引及校验记录。区分原文结论、基于来源的推导和工程建议，不把不同论文的实验结果混成统一结论。
- 新增课程或主题时，沿用编号目录结构，并提供 `SOURCES.md` 作为该目录的资料入口；笔记中的引用应能对应到仓库中的资料或稳定来源链接。
- 更新作业代码时，在对应作业目录中查看其 `README.md`、`ASSIGNMENT.md` 和 `pyproject.toml`，按该作业自己的环境与说明工作。不要假设仓库根目录有通用测试套件。
- 保留作业、挑战赛和上游快照中的原始文件结构。不要把根仓库误配置成这些子目录的工作环境，也不要覆盖未经本次任务授权修改的内容。
- 上传前排除 `.DS_Store`、缓存、实际凭据和本地环境文件；保留明确作为示例的 `.env.example`。二进制资料应保留原文件，不做可能损坏内容的文本转换。

## 课程的更新方式

- 更新 `11-768/` 时，按课次目录手工维护：新增讲义、阅读材料或参考资料后，同步更新该课次的 `SOURCES.md`，在综合笔记中保留引用位置和结论边界；新增课次时使用 `编号.主题名/` 目录，并在本文件的 11-768 表格中补充说明。
- 更新 `2680/` 时，运行 `python3 2680/sync.py` 同步公开网站、阅读材料和作业；该脚本会调用 `organize.py` 整理课次目录，并更新来源索引与校验值。只整理已有下载文件时，单独运行 `python3 2680/organize.py`。脚本需要 `requests` 和 `beautifulsoup4`。官网课表变化时，先核对 `2680/organize.py` 中的课次日期、标题和目录名；运行后检查 `2680/README.md`、`2680/SOURCES.md`、各课次及作业的 `SOURCES.md`、`2680/assignments/SNAPSHOT.json` 与 `2680/CHECKSUMS.sha256`。下载失败、仅有验证页或上游快照未更新时，保留相应状态说明，不将其记为已获取的正文。
- 更新 `MAS.S62/` 时，按下方“MAS.S62 后续更新流程”完成资料同步、逐课讲解维护和校验。依赖 `requests`、`beautifulsoup4`，可选 `pymupdf` 提取 PDF 元数据与检查引用页码。
- `2680/site/`、`2680/readings/` 和 `2680/assignments/course-repo/` 是原始归档或固定快照；不要直接翻译或改写其中原始内容。学习笔记、中文整理和工程解读应放在对应编号课次目录或明确的专题文件中。

### MAS.S62 后续更新流程

用户要求同步或更新 MAS.S62 时，更新范围同时包含公开资料和对应中文课程讲解。

1. **核对变化**：先读 `MAS.S62/README.md`、`SOURCES.md`、`manifest.json` 和目标周的 `SOURCES.md`，对照本学期官网课表，确认新增讲义、嘉宾材料、教程、阅读和作业。以官网 Week、日期和课程原题确定归档位置，以 PDF 全文核实材料用途；周次、Lecture 编号和原文件名分别保留。课表改名或调整周次时，同步维护已有笔记、参考资料与引用，避免产生重复目录。
2. **同步资料**：运行 `python3 MAS.S62/sync.py`，检查下载状态与文件实际内容。脚本会复用已有非网页文件；同一 URL 的讲义或论文发生修订时，需显式重新获取并核对版本、校验值及相关笔记。`site/`、`readings/` 保留原始内容，网页仅可调整本地导航。占位链接、登录页、验证页和下载失败保留明确状态，不计为已获取正文；项目页报告注明为往届案例。
3. **补齐逐课讲解**：每个新增公开讲义的教学周编写一篇完整 `notes.zh-CN.md`，同周主讲、嘉宾和教程整合讲解。以 Lecture 决定主线，Readings 补机制与实验证据，References 补背景和实现；先建立讲义页码、讲解章节与辅助材料的对应关系。按 Senior AI Engineer 的学习标准，覆盖优化对象、更新机制、反馈、持久状态、方法选型、实现流程、贯穿案例、实验对照与归因、成本、泛化、故障诊断、自测和答案。深度随课程内容调整，不用摘要或模板填充代替完整讲解。
4. **维护引用与版本**：已有课程的资料修订后，检查受影响的正文、公式、数字、图表及页码，保留用户已有补充。引用使用实际 PDF 页序（从 1 开始）、论文章节和本地文件链接，注明版本差异，区分原文结论、教学推导和工程建议。新增一手参考登记到本课 `REFERENCES.json`，记录 `title`、`url`、相对课目录的 `path` 和 `status`；取得并核实正文后用 `saved`，复用旧归档时另记来源，不冒充新的下载日期。
5. **刷新索引**：完成笔记和参考资料维护后，运行 `python3 MAS.S62/sync.py --organize-only`，更新根目录与逐课 `SOURCES.md`、`README.md`、`manifest.json`、`LECTURE_LINKS.json` 和 `CHECKSUMS.sha256`。同步脚本不自动编写或覆盖 `notes.zh-CN.md`。
6. **验证与交付**：运行 `python3 MAS.S62/verify.py --require-notes`，检查原始文件、分类副本、来源状态、本地链接和 PDF 引用页码；将本次实际结果保存到 `MAS.S62/VERIFICATION.json`。修改教学示例时实际运行并更新对应运行记录，说明验证范围。更新完成须满足：新增公开讲义的教学周均有完整讲解，修订资料对应的引用已更新，校验无错误，未取得内容及未运行的模型实验如实说明。向用户汇总新增资料、讲解入口和剩余获取限制。

### 11-768 与 2680 的中文讲解维护

- 完整讲解沿用 MAS.S62 的学习标准：讲义决定问题链，Readings 补机制和对照证据，References 补实现与背景；说明符号、假设、贯穿案例、实现流程、选型、成本、泛化与故障诊断，并提供自测和答案。课程导论、基础系统课按实际内容调整深度，不用模板填充。
- 新课先核对日期、官方标题、讲义封面与实际 PDF 页序；`2680` 第 9 课是论文讨论课，以官方阅读分组和讨论要求为主线，明确没有教师讲义 PDF，不把论文改称 lecture。
- 逐篇审核须完整阅读讲解，回查主讲义与高风险数字、公式、图表、版本和实验条件；发现问题修改后全文复读。删除依赖旧聊天的称谓和内部引用标记，使用可访问的本地来源链接；代码外数学采用 `$...$` / `$$...$$`。
- 补充原文放本课 `references/`，在 `REFERENCES.json` 记录 `title`、`url`、课目录相对 `path`、`status` 与取得文件的 SHA-256；复用旧归档记录原位置，不冒充新下载。未取得正文保留状态，不把验证页记为论文。`2680/organize.py` 会将补充索引写回 SOURCES.md 并保留学习文档。
- 本轮及后续复核记录写在各课程 `REVIEW.json`，逐篇绑定最终文件校验值、问题修正、来源核查范围、全文复读结果及限制。运行 `python3 tools/verify_course_notes.py --write-report` 检查记录、讲解覆盖、本地链接、PDF 页码和补充文件校验；结果保存至各课程 `VERIFICATION.json`。该检查不自动评判内容正确性，也不替代人工精读。
- 可运行教学示例实际执行并保存结果；没有执行的 GPU、模型、API 或论文实验明确写为计划或未复现。提交前检查原始资料未被改写、学习入口可达，并按用户授权完成提交和推送。

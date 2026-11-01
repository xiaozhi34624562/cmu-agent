# Stanford CS329Z：Engineering AI Agents

[完整课表与待更新目录](COURSE_SCHEDULE.md) · [四课学习路线](../ROADMAP.zh-CN.md)

Fall 2026。按官网日期展示课程，既有目录编号保持稳定；插入新课采用追加编号。Week、目录编号、PDF Lecture 编号分别保留。官网可能调整课表，原始页面和来源版本均可追溯。

本轮索引日期：2026-11-01。已核实归档 11 份讲义；57 个去重阅读入口中 54 个有有效正文。材料的复用来源和获取限制见 [SOURCES.md](SOURCES.md) 与 [manifest.json](manifest.json)。

[官网](https://cs329z.stanford.edu/) · [课程信息](0.CourseInformation/SOURCES.md) · [作业](assignment/SOURCES.md) · [项目](project/SOURCES.md) · [课堂代码](code/SOURCES.md)

## 课程目录

| 课次 / Week / 日期 | 官网原题 | 讲义 | 中文讲解 |
|---|---|---|---|
| 1 / 1 / 09-23 | [Introduction — What Are Agentic Systems?](1.IntroductionWhatAreAgenticSystems/SOURCES.md) | 71 页 | [完整讲解](1.IntroductionWhatAreAgenticSystems/notes.zh-CN.md) |
| 2 / 2 / 09-28 | [LLMs for Builders](2.LLMsForBuilders/SOURCES.md) | 176 页 | [完整讲解](2.LLMsForBuilders/notes.zh-CN.md) |
| 3 / 2 / 09-30 | [Retrieval-Augmented Generation (RAG)](3.RetrievalAugmentedGenerationRAG/SOURCES.md) | 63 页 | [完整讲解](3.RetrievalAugmentedGenerationRAG/notes.zh-CN.md) |
| 4 / 3 / 10-05 | [Tool Use & Function Calling](4.ToolUseFunctionCalling/SOURCES.md) | 68 页 | [完整讲解](4.ToolUseFunctionCalling/notes.zh-CN.md) |
| 5 / 3 / 10-07 | [Frameworks & Orchestration](5.FrameworksOrchestration/SOURCES.md) | 132 页 | [完整讲解](5.FrameworksOrchestration/notes.zh-CN.md) |
| 6 / 4 / 10-12 | [Agent Design Patterns & Scaffolds](6.AgentDesignPatternsScaffolds/SOURCES.md) | 86 页 | [完整讲解](6.AgentDesignPatternsScaffolds/notes.zh-CN.md) |
| 7 / 4 / 10-14 | [Agent Memory Architectures](7.AgentMemoryArchitectures/SOURCES.md) | 103 页 | [完整讲解](7.AgentMemoryArchitectures/notes.zh-CN.md) |
| 8 / 5 / 10-19 | [Multi-Agent Systems](8.MultiAgentSystems/SOURCES.md) | 92 页 | [完整讲解](8.MultiAgentSystems/notes.zh-CN.md) |
| 9 / 5 / 10-21 | [Optimization](9.Optimization/SOURCES.md) | 125 页 | [完整讲解](9.Optimization/notes.zh-CN.md) |
| 10 / 6 / 10-26 | [Guest Lecture: Terminal-Bench](10.GuestLectureTerminalBench/SOURCES.md) | 64 页 | [完整讲解](10.GuestLectureTerminalBench/notes.zh-CN.md) |
| 11 / 6 / 10-28 | [What Data Do Agents Need?](11.WhatDataDoAgentsNeed/SOURCES.md) | 75 页 | [完整讲解](11.WhatDataDoAgentsNeed/notes.zh-CN.md) |
| 12 / 7 / 11-02 | [Data Selection & Quality](12.DataSelectionQuality/SOURCES.md) | 尚未公开 | 待讲义公开/核实 |
| 13 / 7 / 11-04 | [Evaluation Fundamentals & Benchmark Design](13.EvaluationFundamentalsBenchmarkDesign/SOURCES.md) | 尚未公开 | 待讲义公开/核实 |
| 14 / 8 / 11-09 | [Fireside Chat with Andrew Ng](14.FiresideChatWithAndrewNg/SOURCES.md) | 尚未公开 | 待讲义公开/核实 |
| 15 / 8 / 11-11 | [LLM-as-Judge & Evaluation Infrastructure](15.LLMAsJudgeEvaluationInfrastructure/SOURCES.md) | 尚未公开 | 待讲义公开/核实 |
| 16 / 9 / 11-16 | [Guest Lecture: SWE-bench](16.GuestLectureSWEBench/SOURCES.md) | 尚未公开 | 待讲义公开/核实 |
| 17 / 9 / 11-18 | [Agent Safety & Guardrails](17.AgentSafetyGuardrails/SOURCES.md) | 尚未公开 | 待讲义公开/核实 |
| 18 / 11 / 11-30 | [Coding & Software Agents](18.CodingSoftwareAgents/SOURCES.md) | 尚未公开 | 待讲义公开/核实 |
| 19 / 11 / 12-02 | [Proactive Agents](19.ProactiveAgents/SOURCES.md) | 尚未公开 | 待讲义公开/核实 |

## 学习和证据边界

逐课 notes.zh-CN.md 以讲义的问题链为主线，指定阅读补机制与实验，Additional readings 和 references/ 补背景与实现。PDF 页码为从 1 开始的实际页序。正文区分来源结论、教学推导和工程建议；未运行的模型/API/GPU 实验明确说明。

site/ 和 readings/ 保留原始字节；各课 slides/、readings/ 为按课次分类的副本。论文和网页按完整标题命名，讲义和上游代码保留官方名称及结构。相同 URL 的修订需显式刷新，旧版保存在 versions/ 并标记 review_required，避免笔记继续引用旧页码。

## 同步与验证

```bash
python3 courses/329z/sync.py
python3 courses/329z/sync.py --organize-only
python3 courses/329z/verify.py --require-notes
```

依赖 requests、beautifulsoup4、pymupdf。同步不覆盖中文讲解、补充参考及复核记录；失败重试保留已验证旧版并单独记录刷新失败。上游代码快照使用固定提交，见各 SNAPSHOT.json；学生待实现内容保留原貌。

改题或调课沿用已有目录；删除课次或无法明确匹配时停止同步，先人工核对映射。课程页面与匹配清单一起提交，写入失败时回滚；若进程中断，下次启动先恢复未完成的页面提交，再读取清单。

Python HTTP 不可用时，可选用 `node courses/329z/download.mjs /tmp/cs329z-downloads` 获取待下载原始响应，再运行 `python3 courses/329z/sync.py --import-downloads /tmp/cs329z-downloads` 验证导入。该传输脚本逐请求保存来源日志；大文件的分段下载只接受连续范围、强 ETag 和完整字节长度，审计记录随来源一起校验，不将摘要页或验证页冒充论文正文。

[CHECKSUMS.sha256](CHECKSUMS.sha256) · [讲义内嵌链接及 PDF 页码](LECTURE_LINKS.json) · [当前内容审核状态](REVIEW.json)

校验结果默认输出到终端；需要保存时显式指定 `--output /tmp/cs329z-check.json`。REVIEW.json 仅维护当前版本的来源绑定、内容审核结论与限制。

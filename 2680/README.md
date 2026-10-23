# Harvard CS2680 Modern AI Systems 学习资料

本目录按 CMU 11-768 资料库的方式，**以课次为单位**整理 Harvard CS2680: Modern AI Systems: Agents and System Optimizations（2026 年秋季学期）。目录按课程日期连续编号，名称保留官网课程原题的词语及 I、II、III 等分节标记。每个目录包含原始讲义、`readings/` 阅读文件和逐课 `SOURCES.md`；本地课次包含论文讨论课，因此目录编号不等同于官网 PDF 文件名中的编号。

资料抓取日期：**2026-10-23**。[原课程网站](https://cs2680.com/) · [完整来源索引](SOURCES.md) · [课程信息](0.CourseInformation/SOURCES.md)

<!-- BEGIN COURSE INDEX -->

## Part I：Introduction to LLMs and agents

| 日期 | 课程原题与资料入口 | 官方讲义 PDF |
|---|---|---|
| 09-02 | [1. Course overview and logistics](1.CourseOverviewAndLogistics/SOURCES.md) | [1_intro.pdf](1.CourseOverviewAndLogistics/1_intro.pdf) |
| 09-09 | [2. Agents use I: How Claude Code Works](2.AgentsUseI.HowClaudeCodeWorks/SOURCES.md) | [2_agent_use_1.pdf](2.AgentsUseI.HowClaudeCodeWorks/2_agent_use_1.pdf) |
| 09-14 | [3. Agents use II: 100x Engineer with Multi-agents](3.AgentsUseII.100xEngineerWithMultiAgents/SOURCES.md) | [3_agent_use_2.pdf](3.AgentsUseII.100xEngineerWithMultiAgents/3_agent_use_2.pdf) |
| 09-16 | [4. Agents design I: context management and tool design](4.AgentsDesignI.ContextManagementAndToolDesign/SOURCES.md) | [4_agent_design_1.pdf](4.AgentsDesignI.ContextManagementAndToolDesign/4_agent_design_1.pdf) |
| 09-23 | [5. Agents design II: multi-agent architecture, coordination, and communication](5.AgentsDesignII.MultiAgentArchitectureCoordinationAndCommunication/SOURCES.md) | [5_agent_design_2.pdf](5.AgentsDesignII.MultiAgentArchitectureCoordinationAndCommunication/5_agent_design_2.pdf) |
| 09-28 | [6. Agents design III: agent memory and reliability](6.AgentsDesignIII.AgentMemoryAndReliability/SOURCES.md) | [6_agent_design_3.pdf](6.AgentsDesignIII.AgentMemoryAndReliability/6_agent_design_3.pdf) |
| 09-30 | [7. Agent design IV: agent evaluation](7.AgentDesignIV.AgentEvaluation/SOURCES.md) | [7_agent_design_4.pdf](7.AgentDesignIV.AgentEvaluation/7_agent_design_4.pdf) |
| 10-07 | [8. Advanced agent design I: Cost and performance](8.AdvancedAgentDesignI.CostAndPerformance/SOURCES.md) | [8_agent_design_5.pdf](8.AdvancedAgentDesignI.CostAndPerformance/8_agent_design_5.pdf) |
| 10-14 | [9. Advanced agent design II: agent safety, self-evolving harness](9.AdvancedAgentDesignII.AgentSafetySelfEvolvingHarness/README.md) | 论文讨论课；官网未提供讲义 PDF |

## Part II：Systems for LLMs and agents

| 日期 | 课程原题与资料入口 | 官方讲义 PDF |
|---|---|---|
| 10-19 | [10. Efficient LLM serving basics I: intro to LLMs](10.EfficientLLMServingBasicsI.IntroToLLMs/SOURCES.md) | [9_llm_serving_basics_1.pdf](10.EfficientLLMServingBasicsI.IntroToLLMs/9_llm_serving_basics_1.pdf) |
| 10-21 | [11. Efficient LLM serving basics II: intro to GPUs](11.EfficientLLMServingBasicsII.IntroToGPUs/SOURCES.md) | [10_llm_serving_basics_2a.pdf](11.EfficientLLMServingBasicsII.IntroToGPUs/10_llm_serving_basics_2a.pdf) |
| 10-28 | [12. Efficient LLM serving basics III: Batching, paging, and parallelism](12.EfficientLLMServingBasicsIII.BatchingPagingAndParallelism/SOURCES.md) | 官网尚未提供 |
| 11-02 | [13. Efficient LLM serving: speculative decoding](13.EfficientLLMServing.SpeculativeDecoding/SOURCES.md) | 官网尚未提供 |
| 11-04 | [14. Efficient agentic systems: scheduling and prefix caching](14.EfficientAgenticSystems.SchedulingAndPrefixCaching/SOURCES.md) | 官网尚未提供 |
| 11-11 | [15. Efficient LLM serving: pruning and quantization](15.EfficientLLMServing.PruningAndQuantization/SOURCES.md) | 官网尚未提供 |
| 11-16 | [16. Efficient LLM serving: KV-cache optimization and model architectures](16.EfficientLLMServing.KVCacheOptimizationAndModelArchitectures/SOURCES.md) | 论文讨论课；官网未提供讲义 PDF |
| 11-23 | [17. Efficient agentic system: routing and load balancing](17.EfficientAgenticSystem.RoutingAndLoadBalancing/SOURCES.md) | 官网尚未提供 |
| 11-30 | [18. Efficient agentic systems: others](18.EfficientAgenticSystems.Others/SOURCES.md) | 官网尚未提供 |

完整课表以[本地课程主页](site/index.html)为准。上表收录已有讲义或阅读资料的课次；原始 PDF 文件名保留官网编号。

### 文件名与归档位置核对（2026-10-23）

本次按课表日期、讲义封面、阅读链接和原始归档的校验值核对全部 18 个课次。264 份阅读副本均与对应原始下载文件一致；其中 LPC 的 HTML 是浏览器验证页，未取得阅读正文，已在第 14 课索引中明确标注。

| 容易混淆的文件 | 核对结论与处理 |
|---|---|
| 第 10 课的 `9_llm_serving_basics_1.pdf` | 封面为 Introduction to LLM，对应 10 月 19 日；位置正确，保留官网文件名。 |
| 第 11 课的 `10_llm_serving_basics_2a.pdf` | 封面为 Intro to GPUs，对应 10 月 21 日；位置正确，保留官网文件名。 |
| 第 8 课的 `8_agent_design_5.pdf` | 封面用 Agent design V，课表用 Advanced agent design I；内容都是成本与性能，位置正确。 |
| `8_assignment3.pdf` | 是 Assignment 3: MadsOpt 的作业说明；归入 [作业 3](assignment/assignment-3/SOURCES.md)，第 8 课保留交叉链接。 |
| `008_bench_9e1bf2.pdf`、`028_QuIP_0bdf3d.pdf` | 命名时丢失 τ 和 #；学习副本改为 `008_tau_bench_9e1bf2.pdf`、`028_QuIPSharp_0bdf3d.pdf`，原始下载不变。 |
| 笔记中的 `SOURCES(数字).md` | 上传时产生的旧别名，引用统一指向本课 `SOURCES.md`。 |

阅读副本文件名格式为 `序号_课程阅读标签_URL摘要.pdf/html`；例如 MLA 对应 DeepSeek-V2、SWA 对应 Mistral 7B，属于官网用方法简称指代论文，已核对来源，无须移动。各课的 SOURCES.md 另列本地学习笔记，便于区分笔记与教师讲义。

<!-- END COURSE INDEX -->

## 作业与项目

| 资料 | 本地入口 |
|---|---|
| 作业 1 · Mads-Lens | [说明及来源](assignment/assignment-1/SOURCES.md) |
| 作业 2 · Mads-Loop | [说明、starter code 与原始归档](assignment/assignment-2/SOURCES.md) |
| 作业 3 · Mads-Opt | [说明与 starter code](assignment/assignment-3/SOURCES.md) |
| 作业 4 · Mads-Serve | [说明、幻灯片与官方 starter code](assignment/assignment-4/SOURCES.md) |
| 期末项目 | [项目说明](project/SOURCES.md) |

作业 4 已发布；作业 5 目前仅有[概要](site/assignments/index.html)。课程模型 API、集群和私有评测资源不在本目录中。原站提供的 `assignment2.tar.gz` 实际是普通 tar 归档，可用 `tar -xf` 解包。

## 原始归档与更新

- `site/`：课程网站的网页、幻灯片、样式和图片，保留原站目录结构。
- `readings/`：外部论文与网页的原始下载归档；编号课次目录中有按主题命名的学习副本。
- `assignments/course-repo/`：作业仓库的既有快照。2026-10-23 上游仓库返回不可访问，保留 2026-10-13 的固定提交；状态见 [SNAPSHOT.json](assignments/SNAPSHOT.json)。作业 4 使用课程网站的官方归档。
- [CHECKSUMS.sha256](CHECKSUMS.sha256)：原始归档文件的校验值。

视频和无法自动下载的网页保留在对应课次的 `SOURCES.md` 中；失败原因汇总于根目录 [SOURCES.md](SOURCES.md)。

运行 `python3 2680/sync.py` 可更新公开资料、课次目录和来源索引；仅重新整理已有下载文件时可运行 `python3 2680/organize.py`。脚本需要 Python 的 `requests` 与 `beautifulsoup4`。浏览完整的本地网站时，可在仓库根目录运行 `python3 -m http.server 8765 --directory 2680/site`，然后访问 `http://localhost:8765/`。

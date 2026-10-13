# Harvard CS2680 Modern AI Systems 学习资料

本目录按 CMU 11-768 资料库的方式，**以课次为单位**整理 Harvard CS2680: Modern AI Systems: Agents and System Optimizations（2026 年秋季学期）。每个编号目录包含可获取的原始幻灯片、`readings/` 阅读文件和逐项标注原始链接的 `SOURCES.md`。编号是本资料库的整理顺序，并非课程官方讲次编号。

资料抓取日期：**2026-10-13**。[原课程网站](https://cs2680.com/) · [完整来源索引](SOURCES.md) · [课程信息](0.CourseInformation/SOURCES.md)

## Part I：LLM 与 Agent

| 日期 | 课次资料 | 当前内容 |
|---|---|---|
| 09-02 | [1. Course overview](1.CourseOverview/SOURCES.md) | 幻灯片、作业 1 入口 |
| 09-09 | [2. Using coding agents](2.UsingCodingAgents/SOURCES.md) | 幻灯片、阅读材料 |
| 09-14 | [3. Multi-agent engineering](3.MultiAgentEngineering/SOURCES.md) | 幻灯片、阅读材料 |
| 09-16 | [4. Context and tool design](4.ContextAndToolDesign/SOURCES.md) | 幻灯片、阅读材料 |
| 09-23 | [5. Multi-agent coordination](5.MultiAgentCoordination/SOURCES.md) | 幻灯片、阅读材料 |
| 09-28 | [6. Memory and reliability](6.AgentMemoryAndReliability/SOURCES.md) | 幻灯片、阅读材料 |
| 09-30 | [7. Agent evaluation](7.AgentEvaluation/SOURCES.md) | 幻灯片、阅读材料、专题笔记 |
| 10-07 | [8. Cost and performance](8.CostAndPerformance/SOURCES.md) | 幻灯片、作业 3 幻灯片、阅读材料 |
| 10-14 | [9. Safety and harness](9.AgentSafetyAndHarness/SOURCES.md) | 已公开的阅读材料；幻灯片尚未发布 |

## Part II：LLM 与 Agent 系统

以下课次的阅读书目已在课程网站公开，幻灯片尚未发布。

| 日期 | 课次资料 |
|---|---|
| 10-21 | [10. LLM serving basics](10.LLMServingBasics/SOURCES.md) |
| 10-28 | [11. Speculative decoding](11.SpeculativeDecoding/SOURCES.md) |
| 11-02 | [12. Scheduling and prefix caching](12.SchedulingAndPrefixCaching/SOURCES.md) |
| 11-04 | [13. Pruning and quantization](13.PruningAndQuantization/SOURCES.md) |
| 11-11 | [14. GPU and kernels](14.GPUAndKernels/SOURCES.md) |
| 11-16 | [15. KV cache and model architectures](15.KVCacheAndModelArchitecture/SOURCES.md) |
| 11-23 | [16. Routing and load balancing](16.RoutingAndLoadBalancing/SOURCES.md) |
| 11-30 | [17. Efficient agentic systems](17.EfficientAgentSystems/SOURCES.md) |

完整课表仍以[本地课程主页](site/index.html)为准；上表按已公开资料整理，不包含尚无资料的课堂分享、嘉宾讲座和休课日。

## 作业与项目

| 资料 | 本地入口 |
|---|---|
| 作业 1 · Mads-Lens | [说明及来源](assignment/assignment-1/SOURCES.md) |
| 作业 2 · Mads-Loop | [说明、starter code 与原始归档](assignment/assignment-2/SOURCES.md) |
| 作业 3 · Mads-Opt | [说明与 starter code](assignment/assignment-3/SOURCES.md) |
| 期末项目 | [项目说明](project/SOURCES.md) |

作业 4、5 的概要已列在[作业目录](site/assignments/index.html)，完整说明尚未发布。课程模型 API、集群和私有评测资源不在本目录中。原站提供的 `assignment2.tar.gz` 实际是普通 tar 归档，可用 `tar -xf` 解包。

## 原始归档与更新

- `site/`：课程网站的网页、幻灯片、样式和图片，保留原站目录结构。
- `readings/`：外部论文与网页的原始下载归档；编号课次目录中有按主题命名的学习副本。
- `assignments/course-repo/`：公开作业仓库的固定提交快照；版本见 [SOURCES.md](SOURCES.md)。
- [CHECKSUMS.sha256](CHECKSUMS.sha256)：原始归档文件的校验值。

视频和无法自动下载的网页保留在对应课次的 `SOURCES.md` 中；失败原因汇总于根目录 [SOURCES.md](SOURCES.md)。

运行 `python3 2680/sync.py` 可更新公开资料、课次目录和来源索引；仅重新整理已有下载文件时可运行 `python3 2680/organize.py`。脚本需要 Python 的 `requests` 与 `beautifulsoup4`。浏览完整的本地网站时，可在仓库根目录运行 `python3 -m http.server 8765 --directory 2680/site`，然后访问 `http://localhost:8765/`。

# CMU 11-768 来源总入口

- [官方课程](https://www.cmu-agents.com/) · [官方课表](https://www.cmu-agents.com/#/schedule) · [官方作业](https://www.cmu-agents.com/#/assignments)。
- [课程入口](README.md) · [完整课表与待更新目录](COURSE_SCHEDULE.md) · [官方大纲来源](../syllabus-snapshots/2026-11-20/README.md)。
- 材料最近同步核对日期：2026-11-20；完整学期课表核对日期：2026-11-20。各课 SOURCES.md 保留官方 URL、取得状态及版本边界，补充来源见 REFERENCES.json。

## 当前归档与材料状态

- 2026-11-20 补齐 [Human-Agent Interaction](19.HumanAgentInteraction/SOURCES.md) 的 89 页讲义、5 篇指定阅读和 10 项参考，以及 [Tree Search](21.TreeSearch/SOURCES.md) 的 100 页讲义、6 篇指定阅读和 20 项参考。41 项正文全部保存，32 项本轮下载、9 项复用既有归档并保留原路径与版本；讲义与论文原始字节保留。
- 新增 [人机交互中文讲解](19.HumanAgentInteraction/notes.zh-CN.md) 和 [树搜索中文讲解](21.TreeSearch/notes.zh-CN.md)。实际来源和全文复读范围见 [REVIEW.json](REVIEW.json)。
- 11/19、11/24 嘉宾课题目现为 **How to Trust Your AI Agents**（Karthik Narasimhan）、**Lessons in Building a Coding Agent**（Sasha Rush）；稳定目录保持不变，仍无公开讲义/阅读/参考。
- [研究项目](project/SOURCES.md)已同步当前原文：报告 2026-12-04 23:59 截止，可用最多 3 天 late days，最迟 12/7 23:59，之后不接受；Project Hours/Poster 不可 late days。官网未注明该截止字段的时区。

- 2026-11-13 重新取得官网当前 18 份主讲义：既有 Lecture 1–15、10/27 嘉宾课和 Lecture 18 共 17 份与本地归档逐字节一致；新增 Lecture 20，31 页。原讲义来源与哈希见各课索引，新资料记录在对应 MATERIALS.json/REFERENCES.json。旧讲解内容审核记录不因资料同步而更新。
- 10 月 27 日嘉宾课 [Agents and the Future of Work](16.AgentsAndTheFutureOfWork/SOURCES.md) 已取得：Zora Wang，62 页，封面为 AI Agents for Human Work。本地目录号 16 不代表官方 Lecture 编号。
- [作业 3](assignment/assignment-3/SOURCES.md) 按固定提交 88d1b1f 归档 59 个原始文件，保留 starter code、数据、测试和部署说明；代码版本见作业 SNAPSHOT.json。
- 10 月 29 日 [Multi-Agent Interaction](18.MultiAgentInteraction/SOURCES.md) 已取得：Saujas Vaduguru，44 页；6 篇指定阅读与 17 项参考正文已归档，提供完整中文讲解及确定性教学实验。
- 11 月 12 日 [Reranking and Critic Models](20.RerankingAndCriticModels/SOURCES.md) 已取得 31 页官方讲义（封面 Search over Trajectories，Daniel Fried）、4 篇指定阅读及 23 项参考：24 份论文 PDF、1 份文档正文和 2 个固定提交的代码/README 文件。[完整中文讲解](20.RerankingAndCriticModels/notes.zh-CN.md)已完成，实际阅读范围、全文复读结论及示例执行边界见 [REVIEW.json](REVIEW.json)。
- [研究项目指南](project/SOURCES.md) 已按当前官网同步：2–4 人，Project Hours 5%、Poster 15%、Report 30%；完整英文原文、报告格式和状态见项目入口。
- [10/22 Observability and Monitoring](17.ObservabilityAndMonitoring/SOURCES.md) 仍无公开 slides；已补官方指定安全文章索引，直接正文归档返回 HTTP 403，未取得本地正文。第 19、21 课现已取得讲义；第 22、23 课仍等待。完整当前状态见 COURSE_SCHEDULE.md。
- 作业 1–3 上游最新提交均未变化；作业 3 仍为 `88d1b1fa2aea58938d6d251847ce5559c4ac6558`，未修改 starter code 或运行训练。
- 本轮按用户要求不处理录像：不新增整理、下载或审核视频/字幕。历史视频入口保留原状。动态演示、受限网页和失效链接以各课 SOURCES.md 的状态为准。11/13 的既有材料哈希核验不代表本轮重新检查全部历史文件，也不代表所有外部论文都已追踪最新版本。

官方 PDF 与上游作业保留原始字节。原文题名、数字或链接问题在中文说明中解释，校正不覆盖原件。

## 校验与学习边界

在资料库根目录运行，结果直接输出到终端：

```bash
python3 tools/verify_course_notes.py --course 11-768
python3 tools/verify_assignment3_archive.py
python3 tools/verify_material_names.py
```

[REVIEW.json](REVIEW.json) 记录当前讲解版本、最近内容审核范围及限制；自动检查验证结构、引用与字节完整性，不代替语义精读。作业 3 公开测试的运行环境、失败类型和范围保留在 [BASELINE_TESTS.json](assignment/assignment-3/BASELINE_TESTS.json)。未运行的 GPU、真实模型/API、公开基准训练与学校提交，不记为已完成。

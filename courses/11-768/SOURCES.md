# CMU 11-768 来源总入口

- [官方课程](https://www.cmu-agents.com/) · [官方课表](https://www.cmu-agents.com/#/schedule) · [官方作业](https://www.cmu-agents.com/#/assignments)。
- [课程入口](README.md) · [完整课表与待更新目录](COURSE_SCHEDULE.md) · [官方大纲来源](../syllabus-snapshots/2026-11-04/README.md)。
- 材料最近同步核对日期：2026-11-04；完整学期课表核对日期：2026-11-04。各课 SOURCES.md 保留官方 URL、取得状态及版本边界，补充来源见 REFERENCES.json。

## 当前归档与材料状态

- Lecture 1–15 主讲义于 2026-10-28 与官网 PDF 核对，字节与既有归档一致。来源 URL 见各课索引，归档校验值保存在 [REVIEW.json](REVIEW.json) 的 original_sources 中。
- 10 月 27 日嘉宾课 [Agents and the Future of Work](16.AgentsAndTheFutureOfWork/SOURCES.md) 已取得：Zora Wang，62 页，封面为 AI Agents for Human Work。本地目录号 16 不代表官方 Lecture 编号。
- [作业 3](assignment/assignment-3/SOURCES.md) 按固定提交 88d1b1f 归档 59 个原始文件，保留 starter code、数据、测试和部署说明；代码版本见作业 SNAPSHOT.json。
- 10 月 29 日 [Multi-Agent Interaction](18.MultiAgentInteraction/SOURCES.md) 已取得：Saujas Vaduguru，44 页；6 篇指定阅读与 17 项参考正文已归档，提供完整中文讲解及确定性教学实验。
- 10 月 22 日 Observability and Monitoring 及后续尚无正文的课次仍保留待发布状态；完整状态见 COURSE_SCHEDULE.md。
- 官方视频仅保留入口，未下载视频或字幕。动态演示、受限网页和失效链接以各课 SOURCES.md 的状态为准。既有材料哈希相同不代表所有外部论文都已追踪最新版本。

官方 PDF 与上游作业保留原始字节。原文题名、数字或链接问题在中文说明中解释，校正不覆盖原件。

## 校验与学习边界

在资料库根目录运行，结果直接输出到终端：

```bash
python3 tools/verify_course_notes.py --course 11-768
python3 tools/verify_assignment3_archive.py
python3 tools/verify_material_names.py
```

[REVIEW.json](REVIEW.json) 记录当前讲解版本、最近内容审核范围及限制；自动检查验证结构、引用与字节完整性，不代替语义精读。作业 3 公开测试的运行环境、失败类型和范围保留在 [BASELINE_TESTS.json](assignment/assignment-3/BASELINE_TESTS.json)。未运行的 GPU、真实模型/API、公开基准训练与学校提交，不记为已完成。

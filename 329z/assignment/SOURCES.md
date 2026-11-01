# CS329Z Fall 2026：作业与论文视频

- 官网：[课表与截止时间](https://cs329z.stanford.edu/index.html#schedule)、[课程要求](https://cs329z.stanford.edu/logistics.html)。本地页面：[课表](../site/index.html)、[课程要求](../site/logistics.html)。
- 课程主入口：[README.md](../README.md)。期末项目单独见 [project/SOURCES.md](../project/SOURCES.md)。
- 时间要求以官网太平洋时间为准；本索引记录归档快照，不代替课程后续公告。

| 项目 | 本地资料 | 当前归档状态 |
|---|---|---|
| HW1：Building an Agentic Harness | [来源与使用入口](assignment-1/SOURCES.md)、[官方 handout](assignment-1/upstream/cs329z_assignment1_harness.pdf) | 官方 starter 完整固定提交快照；学生待实现部分保持原样 |
| HW2：Evaluate an Agent | [官方课程要求](../site/logistics.html) | 已保存概要；官网公开页面尚未给出可归档的作业正文或代码入口，不记为已取得完整作业 |
| Paper Video：Presenting an Agent Paper | [官方 handout](../site/assignments/paper_video.pdf) | 已保存 6 页 PDF；来源及校验值见 [manifest.json](../manifest.json) |

## 资料来源与范围

- HW1 官方仓库：https://github.com/cs329z/assignment1-harness 。固定提交、原始文件校验值和获取元数据见 [SNAPSHOT.json](assignment-1/SNAPSHOT.json)。
- HW2 目前可核实的概要：为给定 Agent 设计评测套件，包含代码评分器、至少一种 LLM-as-Judge 评测、按 request / environment / stopping criteria / scorer 构造的任务，以及错误分析。此说明来自课程 logistics 页面，不是独立作业 handout。
- Paper Video 原始 PDF：https://web.stanford.edu/class/cs329z/assignments/paper_video.pdf 。官方要求为 10–15 分钟的论文讲解、批判性分析和超出阅读本身的实践观察；具体提交内容和评分按 PDF 原文核对。
- 录像访问入口在 Canvas，需要课程登录；本目录未取得录像，也未将录像计入学习讲解的已核查来源。

## 验证边界

[HW1 BASELINE.json](assignment-1/BASELINE.json) 记录本次真实执行的完整性与局部测试。未完成的官方 starter 不应被补写为答案。未运行的 live tests、模拟用户评测和完整 Agent 实验均未声称通过。

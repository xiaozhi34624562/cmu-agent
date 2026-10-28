# CMU 11-768 来源总入口

- 官方课程：[11-768 · AI Agents](https://www.cmu-agents.com/)。
- [官方课表](https://www.cmu-agents.com/#/schedule) · [官方作业](https://www.cmu-agents.com/#/assignments)。
- 本轮核对、取得与同步日期：**2026-10-28（Asia/Shanghai）**。
- 逐课原件、readings、references 和中文讲解入口见 [README.md](README.md)。各课 `SOURCES.md` 保留官方 URL、取得状态及版本边界；补充来源见各课 `REFERENCES.json`。

## 本轮新增与修正

| 范围 | 本地入口 | 核对结果 |
|---|---|---|
| 10 月 27 日嘉宾课 · Agents and the Future of Work | [第 16 课来源](16.AgentsAndTheFutureOfWork/SOURCES.md) · [完整中文讲解](16.AgentsAndTheFutureOfWork/notes.zh-CN.md) | Zora Wang；62 页；PDF 封面为 *AI Agents for Human Work*。本地目录序号 16 不冒充官方 Lecture 编号。 |
| 作业 3 · Training Agents with Reinforcement Learning | [作业来源](assignment/assignment-3/SOURCES.md) · [官方说明](assignment/assignment-3/ASSIGNMENT.md) | 固定提交 `88d1b1f`，59 个原始文件，保留 starter code、数据、测试和部署说明。 |
| 现有 Lecture 1–15 主讲义 | [逐课入口](README.md) · [在线核对记录](SYNC.json) | 15 份官网 PDF 均与既有归档逐字节一致，无须替换。 |
| 现有归档、来源和讲解 | [复核记录](REVIEW.json) · [结构校验](VERIFICATION.json) | 保留历史全文审稿记录；本轮另记原件校验、来源映射、重点语义复核与修正范围，不将自动检查称为全部论文的重新精读。 |

官方原始 PDF 与上游作业文件保持原始字节。若发现原文题名、链接或数字存在问题，在来源索引和中文说明中区分原文与校正，不直接改写原始文件。

## 仍未取得的课程材料

- **10 月 22 日 · Safety 2: Observability and Monitoring**：课表有安排，但核对时未提供 slides、readings 或 references，不据此生成讲义或讲解。
- **10 月 29 日 · Interaction 1: Multi-Agent Interaction**：核对时尚无 slides 链接。
- **官方视频**：按各课来源索引保留入口，本轮没有下载视频或字幕；网页链接不代表已经保存视频正文。
- 各课历史动态演示、受限网页或失效链接仍以本课 `SOURCES.md` 的具体状态为准。既有材料的 SHA-256 相同不代表其外部论文从未发布新版本；本轮没有对所有外部论文逐一追踪新版。

## 校验入口

在资料库根目录运行：

```bash
python3 tools/verify_course_notes.py --course 11-768 --write-report
python3 tools/verify_assignment3_archive.py --write-report
python3 tools/verify_material_names.py --write-report
```

[SYNC.json](SYNC.json) 记录本轮官网讲义 URL、文件 SHA-256、归档位置与未公开状态；[REVIEW.json](REVIEW.json) 记录讲解的实际内容复核。作业 3 的公开测试实测另见 [BASELINE_TESTS.json](assignment/assignment-3/BASELINE_TESTS.json)。本次没有运行 GPU、真实模型/API、公开基准训练实验或学校提交。

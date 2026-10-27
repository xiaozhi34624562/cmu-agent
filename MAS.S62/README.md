# MIT MAS.S62：自演化 AI 学习资料

**How to AI an AI for (Almost) Anything · Fall 2026 · Paul Liang / Ao Qu**

本资料库按官网 Week 组织。Lecture 构成中文讲解主线，Readings 补充机制与实验，References 补背景和实现。正文区分原文结论、教学推导与工程建议。

资料同步日期：**2026-10-26**。已归档 11 份课程 PDF；课表有 28 个去重阅读入口，其中 28 个已保存正文。

[官网](https://mit-mi.github.io/how2ai-course/fall2026/) · [官方课表](https://mit-mi.github.io/how2ai-course/fall2026/schedule/) · [全部来源](SOURCES.md) · [课程大纲](0.CourseInformation/SOURCES.md) · [作业](assignment/SOURCES.md) · [项目](project/SOURCES.md)

## 课程目录

| Week / 日期 | 官网课程名称 | 材料状态 | 中文讲解 |
|---|---|---|---|
| 1 / 09-09 | [Course introduction](1.CourseIntroduction/SOURCES.md) | 1 份 PDF | [完整讲解](1.CourseIntroduction/notes.zh-CN.md) |
| 2 / 09-16 | [Context evolution 1](2.ContextEvolution1/SOURCES.md) | 2 份 PDF | [完整讲解](2.ContextEvolution1/notes.zh-CN.md) |
| 3 / 09-23 | [Context evolution 2](3.ContextEvolution2/SOURCES.md) | 1 份 PDF | [完整讲解](3.ContextEvolution2/notes.zh-CN.md) |
| 4 / 09-30 | [Project proposal presentations](4.ProjectProposalPresentations/SOURCES.md) | 项目展示周 | 见项目要求 |
| 5 / 10-07 | [Harness evolution 1](5.HarnessEvolution1/SOURCES.md) | 2 份 PDF | [完整讲解](5.HarnessEvolution1/notes.zh-CN.md) |
| 6 / 10-14 | [Harness evolution 2](6.HarnessEvolution2/SOURCES.md) | 2 份 PDF | [完整讲解](6.HarnessEvolution2/notes.zh-CN.md) |
| 7 / 10-21 | [Model evolution 1](7.ModelEvolution1/SOURCES.md) | 3 份 PDF | [完整讲解](7.ModelEvolution1/notes.zh-CN.md) |
| 8 / 10-28 | [Project midterm presentations](8.ProjectMidtermPresentations/SOURCES.md) | 项目展示周 | 见项目要求 |
| 9 / 11-04 | [Model evolution 2](9.ModelEvolution2/SOURCES.md) | 讲义链接尚为占位 | 待对应讲义公开 |
| 10 / 11-11 | [Environment evolution 1](10.EnvironmentEvolution1/SOURCES.md) | 讲义链接尚为占位 | 待对应讲义公开 |
| 11 / 11-18 | [Environment evolution 2](11.EnvironmentEvolution2/SOURCES.md) | 讲义链接尚为占位 | 待对应讲义公开 |
| 12 / 11-25 | [Future topics](12.FutureTopics/SOURCES.md) | 讲义链接尚为占位 | 待对应讲义公开 |
| 13 / 12-02 | [Project final presentations](13.ProjectFinalPresentations/SOURCES.md) | 项目展示周 | 见项目要求 |
| 14 / 12-09 | [Future topics](14.FutureTopics/SOURCES.md) | 讲义链接尚为占位 | 待对应讲义公开 |

## 学习方法

1. 先阅读本课 notes.zh-CN.md 的导读与材料映射，建立核心问题。
2. 沿正文学习机制、公式、实现案例和论文证据，按页码回读原讲义。
3. 用自测及实验设计检查理解；区分来源已经报告的实验与尚未运行的本地实验计划。
4. 更新系统时同时检查效果、预算、泛化、退化和回滚条件。

## 归档与维护

- site/：本学期页面、讲义、大纲导出、教程与公开作业 notebook；原始下载不翻译。
- readings/：课程论文及往届公开项目参考的原始归档；下载状态见 manifest.json。
- 每周 slides/、tutorials/、readings/ 是分类学习副本；讲义与教程保留官方原名，论文和阅读网页使用完整标题命名。
- 论文原文件名、现路径、来源 URL 和未改变的内容校验值见 [文件改名记录](../tools/MATERIAL_RENAMES.json)；同步与整理共用标题命名规则。
- 周次不等于 PDF 的 Lecture 编号；例如 Week 5 对应 Lecture 4。
- `lec6 - rl in practice.pdf` 前两页为嘉宾介绍，后续为 RL/自蒸馏实践教程；学习副本归入第 7 周 tutorials/，以全文内容说明用途。
- 官网后续 [slides] 占位不计作讲义；未获取正文的材料保留明确状态。
- 项目展示周按课表保留目录，项目参考注明为往届成果。

更新：`python3 MAS.S62/sync.py`；只重建分类与索引：`python3 MAS.S62/sync.py --organize-only`。需要 requests、beautifulsoup4；pymupdf 可补充 PDF 封面和页数。更新脚本保留 notes.zh-CN.md、人工补充 references/ 和学习记录。

校验： [CHECKSUMS.sha256](CHECKSUMS.sha256) 覆盖原始归档及逐课补充材料；[manifest.json](manifest.json) 记录 URL、下载地址、状态和版本信息。运行 `python3 MAS.S62/verify.py --require-notes` 检查归档校验值、分类副本、来源状态与讲解链接。

[LECTURE_LINKS.json](LECTURE_LINKS.json) 另保存讲义内嵌的原始链接及实际 PDF 页码，便于追溯讲义中的参考、视频与作业入口。

内容复核与修正记录见 [REVIEW.json](REVIEW.json)，包含逐课覆盖、修改后复读及核验限制；复核范围以记录日期与文件校验值为准。

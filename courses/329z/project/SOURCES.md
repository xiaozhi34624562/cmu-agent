# CS329Z Course Project

- [官方项目说明原文](../site/project.html) — https://cs329z.stanford.edu/project.html
- [课程评分与 AI 使用说明](../site/logistics.html) — https://cs329z.stanford.edu/logistics.html
- [原始课表与截止时间](../site/index.html#deadlines) — https://cs329z.stanford.edu/index.html#deadlines
- 来源文件版本、取得时间及 SHA-256 见 [manifest.json](../manifest.json)。截止时间按官网 Pacific Time 原样理解；本地说明不替代最新课程通知。

## 项目主线

官方项目要求 1–3 人设计、实现并评测一个与构建 Agent、Agent 数据或评测安全有关的系统。关键是尽早定义任务、环境、数据获取方式、成功条件和评价方法，报告有意义的一组任务、基线比较及失败分析，不能用单次成功演示代替评测。

| 阶段 | 原文要求 | 学习时应形成的产物 |
|---|---|---|
| Proposal / Week 3 | 1–2 页；问题动机、已有工作比较、下一步和判定有效的方法 | 一个明确任务，以及可以证伪方案的评价设计 |
| Midpoint / Week 7 | 工作原型录像、可运行 GitHub 仓库；3–4 页 midway report | 环境和数据、架构、初步评测与剩余风险 |
| Final / Finals Week | 8 页 ICLR 格式报告、代码、现场演示 | 多任务评测、基线、误差分析、局限及可复现入口 |

页数不含参考文献；具体版式、评分细则、AI-Use Disclosure、Authorship、安全与伦理章节以原文为准。项目说明将最终提交分为报告 20 分和可复现性 5 分；这是该提交内部的评分，不应直接替代 logistics 中的全课程权重。

代码 README 必须让未看过项目的同学完成安装、凭据配置、运行 Agent 和复现报告中的评价。课程的可复现性检查只运行一个小实例，并不表示教师重新执行完整实验。

## 自学与工程实践

可以把贯穿案例设为企业内部助手或投研证据助手：先固定一组带时间边界和权限约束的任务，再实现检索、工具和状态，最后比较固定工作流、单 Agent 与增加复杂度后的方案。该建议是学习应用，不是课程指定选题，也不是已经执行的模型实验。

本目录仅归档课程要求，不包含学生报告、私有项目数据、账户权限或完成的项目答案。

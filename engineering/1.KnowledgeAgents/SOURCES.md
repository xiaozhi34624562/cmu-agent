# Knowledge Agents 与金融投研：资料索引

核查日期：2026-10-03。主文档：[从知识检索到研究判断：金融投研智能体的系统设计](knowledge-agents-for-financial-research.md)。

本目录是用户要求建立的工程专题，不是新增 CMU 课程讲次。沿用仓库对来源、版本与结论边界的要求。

## 来源关系

- S01 是演讲的主办方完整时间戳文字稿；原视频播放访问失败，未逐帧核验画面，未获得独立幻灯片文件。
- S02—S05 用于核查演讲涉及的基准和厂商实验；论文、口述、博客与动态榜单不是同一实验，不能拼接数字。
- S06—S09 是相关一手工程材料，不能冒充讲者在台上逐项引用的文献。
- 主文的金融领域模型、控制流程、合成案例、评测方案与架构选择均为工程推导，没有在用户系统中实测。

## 一手资料

### S01 · 演讲及完整时间戳文字稿

- [AI Engineer：If we want them to do Knowledge Work, design them as Knowledge Agents](https://ai.engineer/talks/O84lhGc1OOI-if-we-want-them-do-knowledge-work)
- [YouTube 原视频](https://www.youtube.com/watch?v=O84lhGc1OOI)
- Benjamin Clavié，Mixedbread；视频约 18 分钟。参考定位：3:42 代码与任务定义；5:42 工具和组织；9:20 检索实验；11:09 律所研究分工；12:42 MADQA；15:13 工具与上下文。
- 自动文字稿有转写误差，实验专名按原论文核对。88.9%、增加 3.5 个百分点、99.4% 与约 40% 的口述未完全算术一致，不反推未公开配置。

### S02 · BrowseComp-Plus，v1

- [论文全文](https://arxiv.org/html/2508.06600v1)，2025-08-08。
- [项目页](https://texttron.github.io/BrowseComp-Plus/)。
- 重点：§3 数据与语料；§4.3—4.5 评测与主结果；§4.8.1 oracle；§4.8.3 全文读取。
- 仓库原始 PDF：[003_BrowseComp-Plus.pdf](../../10.DeepResearchAgents/references/003_BrowseComp-Plus.pdf)。
- 固定语料实验不能直接代表开放式投研判断；oracle 结果必须保留对应模型。

### S03 · MADQA，v2

- [Strategic Navigation or Stochastic Search? How Agents and Humans Reason Over Document Collections](https://arxiv.org/html/2603.12180v2)，2026-03-20 修订。
- 重点：§2 数据；§3 和 Table 3 指标与结果；附录 G.1 基线；附录 H.3 错误分解；§7 限制。
- 全量 2,250 题与测试集 500 题是不同范围。99.4% 是 Human + Oracle Retriever，不是模型理论上限。Kuiper 不能读成工具调用次数。

### S04 · MADQA 数据与实现

- [官方数据卡](https://huggingface.co/datasets/OxRML/MADQA)。
- [官方代码](https://github.com/OxRML/MADQA)。
- 交叉核对 train/dev/test 划分、证据标注及可访问范围；动态入口不代表本文复现实验。

### S05 · Closing the Oracle Gap for Your Agents

- [Mixedbread 原文](https://www.mixedbread.com/blog/closing-gap)，2026-03-24。
- 厂商实验说明；MADQA 的 88.2% 单次检索配置与 91.7% Button 配置包含不同模型和框架，不能视为演讲同模型消融。
- [动态评测页](https://www.mixedbread.com/evals/madqa)只作补充入口，不用当前榜单替换演讲历史成绩。

### S06 · Our Research Vision, Part 1

- [Mixedbread 原文](https://www.mixedbread.com/blog/research-vision)，Benjamin Clavié、Aamir Shakir，2025-09-24。
- 重点：动态外部知识、搜索的价值、真实可用性、服务成本与延迟。研究愿景不是金融场景效果证明。

### S07 · How we built our multi-agent research system

- [Anthropic 原文](https://www.anthropic.com/engineering/multi-agent-research-system)，2025-06-13。
- 重点：任务适配、委派规格、独立上下文、成本与共享上下文限制、成果持久化。
- 其 90.2% 是内部研究评测的相对提升，与 S01 的准确率数字无关；约 4 倍和 15 倍 token 都以普通聊天为比较基准。

### S08 · Writing effective tools for AI agents—using AI agents

- [Anthropic 原文](https://www.anthropic.com/engineering/writing-tools-for-agents)，2025-09-11。
- 重点：适合真实任务的工具边界、高信号返回、错误说明与工具评测。没有规定所有系统采用相同工具粒度。

### S09 · Effective context engineering for AI agents

- [Anthropic 原文](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)，2025-09-29。
- 重点：按需获取、轻量引用、外部笔记、压缩和独立子任务上下文。金融事实模型与版本失效传播是本文独立设计。

## 仓库内的补充阅读

- [前期基准核查记录](../../10.DeepResearchAgents/knowledge-agents-benchmark-verification.md)：保留更多表格和数字核查。
- [前期扩展资料核查记录](../../10.DeepResearchAgents/knowledge-agents-extension-sources.md)。
- [文档上下文层与研报解析专题](../ocr/document-context-layer-and-financial-report-parsing.md)：原始页面、布局、表格与事实抽取。
- [CCA Foundations](../CCA/CCA_Foundations.md)：通用 Agent 工作流、工具协议与恢复机制。

主文可以独立阅读。上述仓库笔记用于连接主题，不代替外部一手资料，也不预设读者已经读过它们。

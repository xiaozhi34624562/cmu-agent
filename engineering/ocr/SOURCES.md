# OCR 与文档上下文层：资料索引

研究日期：2026-10-03。

主文档：[从 OCR 到可信文档上下文：Jerry Liu 演讲与券商研报解析的工程研究](document-context-layer-and-financial-report-parsing.md)。

本目录是工程专题，按用户指定放在 engineering/ocr，不是 CMU 课程新增讲次。研究以一手材料为依据。商业服务未公开的内部实现、本域部署效果与性能提升，不被当作已验证事实。

## 材料关系与阅读方法

- 演讲：[原始 YouTube 视频](https://www.youtube.com/watch?v=RQi7x-navxU)，AI Engineer World's Fair 2026，21:03；完整时间戳文字稿见 S01。未取得独立幻灯片文件。
- 与演讲核心内容直接对应：S01；PDF 处理困难与 S05 高度对应；ParseBench 见 S07、S13–S15；LiteParse 见 S20–S21。
- 补充作者解释：S04、S06、S19、S22、S24–S26。它们与演讲观点有关，不表示每一篇都曾被演讲逐项引用。
- 产品接口核验：S08–S12、S23、S27–S28。动态文档可能变化，实施前应记录所用版本与配置。
- 对照研究与底层原理：S02–S03、S16–S18。本文没有用它们推定 LlamaParse 采用了相同内部模型。
- 自行提出的部分：故障干预实验、事实数据契约、覆盖检查、接纳策略、成本分析与工程路线。主文已将这些内容与来源事实区分。

## 一手来源

### S01 · [大会演讲与完整时间戳文字稿](https://ai.engineer/talks/RQi7x-navxU-building-document-context-layer-ai-agents)

演讲一手记录。主线、时间点、产品框架与展望的依据；本文未逐帧核验视频。

### S02 · [pypdf：Extract Text](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)

交叉核对 PDF 文本抽取、扫描页与隐藏 OCR 层的限制。

### S03 · [PyMuPDF：Text Recipes](https://pymupdf.readthedocs.io/en/latest/recipes-text.html)

交叉核对位置、阅读顺序与表格恢复。

### S04 · [LlamaParse Update: New and Upcoming Features](https://www.llamaindex.ai/blog/llamaparse-update-new-and-upcoming-features)

2025-02-20。文字、截图、语言/视觉模型与结构恢复的历史方法说明；旧模式名称不是当前配置指南。

### S05 · [Why Reading PDFs is Hard](https://www.llamaindex.ai/blog/why-reading-pdfs-is-hard)

2026-03-12。文件信息与视觉处理的互补；与演讲提及的 PDF 困难文章高度对应，口述没有明确给出标题。

### S06 · [LLM APIs Are Not Complete Document Parsers](https://www.llamaindex.ai/blog/llm-apis-are-not-complete-document-parsers)

Jerry Liu，2025-07-24。包含股票研究报告案例；案例是机制证据，不是中文研报性能保证。

### S07 · [ParseBench: A Document Parsing Benchmark for AI Agents，v3](https://arxiv.org/html/2604.08538v3)

2026-04-13 修订。重点 §2–3、§4.1、Table 2、Table 5。它是评测论文，不是 LlamaParse 完整算法论文。

### S08 · [LlamaParse：Tables](https://developers.llamaindex.ai/llamaparse/parse/features/tables/)

表格表示、合并单元格、跨页处理。产品能力不等于任意表格的质量承诺。

### S09 · [LlamaParse：Layout and Bounding Boxes](https://developers.llamaindex.ai/llamaparse/parse/features/layout-and-bounding-boxes/)

位置、grounding 与坐标约定；对接需按所用输出字段逐一核对。

### S10 · [LlamaParse：Response Format](https://developers.llamaindex.ai/llamaparse/parse/guides/response-format/)

结构化输出、grounded items 与文本跨度；不应直接把字节偏移当字符偏移。

### S11 · [LlamaParse：Charts and Figures](https://developers.llamaindex.ai/llamaparse/parse/features/charts-and-figures/)

图表与图像能力。正文关于精确标签和估读数值的输出政策，是本文工程建议。

### S12 · [LlamaParse：Tiers](https://developers.llamaindex.ai/llamaparse/parse/guides/tiers/)

当前解析档位。本文未抄录动态价格，也未将历史文章档位等同当前服务。

### S13 · [ParseBench 官方数据集](https://huggingface.co/datasets/llamaindex/ParseBench)

数据与评估维度入口；未见中文券商研报独立成绩。

### S14 · [ParseBench 固定版本排行榜](https://github.com/run-llama/ParseBench/blob/afb36bd83ed8df7846f9d4f18c58bb948d9d5de0/leaderboard.csv)

提交 afb36bd83ed8df7846f9d4f18c58bb948d9d5de0，日期 2026-09-29。正文成绩来自此版本，与论文初始结果分开。

### S15 · [TableRecordMatch 指标实现](https://github.com/run-llama/ParseBench/blob/afb36bd83ed8df7846f9d4f18c58bb948d9d5de0/src/parse_bench/evaluation/metrics/parse/table_record_match_metric.py)

同一固定提交。表头字段、记录构造与匹配的依据；该指标不是通用事实三元组 F1。

### S16 · [MinerU2.5 论文，v1](https://arxiv.org/html/2509.22186v1)

2025-09-26。原论文两阶段解耦架构；不能自动视为后来 Pro 版本的全部实现。

### S17 · [PaddleOCR-VL 论文，v1](https://arxiv.org/html/2510.14528v1)

2025-10-16。原版布局、局部识别与整合流程；与后续 1.5/1.6 版本分开。

### S18 · [PaddleOCR-VL 完整流程文档，固定提交](https://github.com/PaddlePaddle/PaddleOCR/blob/dab3fe35379033fdcb2d0e9572fac0b36c9a9ebf/docs/version3.x/pipeline_usage/PaddleOCR-VL.en.md)

完整 pipeline 与独立模型区别、图表及输出过滤配置。不能据此推定用户实际运行版本。

### S19 · [Just-in-Time Agentic OCR](https://www.llamaindex.ai/blog/just-in-time-agentic-ocr)

Jerry Liu，2026-09-11。按任务精读与长期离线语料的分界；是补充阅读，不冒充演讲逐字内容。

### S20 · [LiteParse 官方文档](https://developers.llamaindex.ai/liteparse/)

本地、不依赖 LLM 的解析及传统 OCR 路径；用当前官方拼写 LiteParse。

### S21 · [LiteParse：Document Complexity](https://developers.llamaindex.ai/liteparse/guides/complexity/)

文字是否需要 OCR 与布局复杂度是不同信号。

### S22 · [A practical guide to extraction confidence scores](https://www.llamaindex.ai/blog/what-makes-an-extraction-confidence-score-useful)

2026-09-16。抽取置信度、证据与复核；本文本域校准方法为工程建议。

### S23 · [LlamaExtract：Response Format](https://developers.llamaindex.ai/llamaparse/extract/guides/response-format/)

字段抽取、引用和返回信息；字段分数不等于页面或字符识别分数。

### S24 · [Files Are All You Need](https://www.llamaindex.ai/blog/files-are-all-you-need)

Jerry Liu，2026-01-15。Agent 通过文件工具获取上下文的作者论述。

### S25 · [Did Filesystem Tools Kill Vector Search?](https://www.llamaindex.ai/blog/did-filesystem-tools-kill-vector-search)

2026-01-13。小规模实验；不外推为所有任务或规模下的技术胜负。

### S26 · [Introducing Extract v2.5](https://www.llamaindex.ai/blog/introducing-extract-v2-5)

2026-10-01。结构、长列表和跨页抽取的产品补充；厂商发布说明不是用户场景实测。

### S27 · [LlamaIndex：MCP](https://developers.llamaindex.ai/llamaparse/for-agents/mcp/)

当前 Agent 接入方式；正文示意的业务工具划分不是官方工具清单。

### S28 · [LlamaIndex：Skills](https://developers.llamaindex.ai/llamaparse/for-agents/skills/)

当前 Agent 操作说明与接入入口。

## 相关网站与扩展入口

- [ParseBench 网站](https://www.parsebench.ai/)：动态展示；数字以固定论文或固定仓库提交为准。
- [ParseBench 官方仓库](https://github.com/run-llama/ParseBench)：评估代码与接入方式。
- [MinerU 官方仓库](https://github.com/opendatalab/MinerU)：部署与版本信息。
- [PaddleOCR 官方仓库](https://github.com/PaddlePaddle/PaddleOCR)：完整处理流程与模型组件。
- [LiteParse 官方仓库](https://github.com/run-llama/liteparse)：快速解析实现。
- [FinanceBench 官方仓库](https://github.com/patronus-ai/financebench)：JIT OCR 文章金融问答案例的相关基准，不能把单次示例当通用质量评测。
- [LayoutLMv3 论文](https://arxiv.org/abs/2204.08387)：文字、图像和布局联合表征的背景阅读，不是 LlamaParse 内部模型的证据。

## 尚未获得的证据

没有实际运行用户的研报样本，也没有同版本、同配置下的中文券商研报配对实验。因此本文提供的是可检验的工程判断和实施路线，不提供已经完成的产品选型结论。

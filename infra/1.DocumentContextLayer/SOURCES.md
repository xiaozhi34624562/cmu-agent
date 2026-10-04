# Document Context Layer：演讲与券商研报解析研究资料

- 研究日期：2026-10-03。
- 类型：相关工程研究，不是 CMU 课程新增讲次。
- 综合讲解：[Jerry Liu 演讲、OCR 与券商研报解析](JerryLiu_文档上下文层与券商研报解析研究.md)。
- 范围：原演讲可辨识的一手材料、作者补充文章、当前产品文档，以及用于比较用户现有方案的研究。补充资料不自动视为演讲直接引用。
- 未取得独立演讲幻灯片文件；通过大会完整时间戳文字稿核对演讲内容，未逐帧核验视频画面。

## 1. 演讲入口

- [Building the Document Context Layer for AI Agents — Jerry Liu, LlamaIndex](https://www.youtube.com/watch?v=RQi7x-navxU)
  - AI Engineer World's Fair 2026，21:03，视频 ID `RQi7x-navxU`。
- [大会原始完整时间戳文字稿](https://ai.engineer/talks/RQi7x-navxU-building-document-context-layer-ai-agents)
  - 重点：8:35–15:03 文档解析；15:08–18:24 成本/延迟及 LiteParse；18:28–20:16 抽取和搜索。

## 2. 作者及官方技术文章

- [Why Reading PDFs is Hard](https://www.llamaindex.ai/blog/why-reading-pdfs-is-hard)，2026-03-12。
  - 与演讲 8:44 提及的 PDF 解析困难文章内容高度对应；演讲口述未明确给出文章标题。
- [LLM APIs Are Not Complete Document Parsers](https://www.llamaindex.ai/blog/llm-apis-are-not-complete-document-parsers)，Jerry Liu，2025-07-24。
  - 包含 equity research report 图表案例；旧 Premium 等名称不当作当前配置指南。
- [Just-in-Time Agentic OCR](https://www.llamaindex.ai/blog/just-in-time-agentic-ocr)，Jerry Liu，2026-09-11。
  - 重要边界：临时 data room 与长期离线语料/批量抽取采用不同策略。
- [Files Are All You Need](https://www.llamaindex.ai/blog/files-are-all-you-need)，Jerry Liu，2026-01-15。
- [Did Filesystem Tools Kill Vector Search?](https://www.llamaindex.ai/blog/did-filesystem-tools-kill-vector-search)，2026-01-13。
  - 小规模试验，不能推导出所有规模下文件搜索优于向量检索。
- [Introducing ParseBench](https://www.llamaindex.ai/blog/parsebench)，2026-04-13。
- [Introducing Extract v2.5](https://www.llamaindex.ai/blog/introducing-extract-v2-5)，2026-10-01。
  - 演讲之后的产品补充，不是演讲已经展开的细节。
- [A practical guide to extraction confidence scores](https://www.llamaindex.ai/blog/what-makes-an-extraction-confidence-score-useful)，2026-09-16。

## 3. 论文、数据与评测

- [ParseBench: A Document Parsing Benchmark for AI Agents](https://arxiv.org/abs/2604.08538)
  - 固定论文入口：[v1](https://arxiv.org/html/2604.08538v1)，2026-04-09；结果见 Table 5。
- [ParseBench 官方代码](https://github.com/run-llama/ParseBench)
  - 当前榜单会更新；综合笔记另记录核对时的固定 commit。
- [ParseBench 数据集](https://huggingface.co/datasets/llamaindex/ParseBench)
- [ParseBench 网站](https://www.parsebench.ai/)
  - 动态展示站；结果数字优先使用可固定版本的论文与官方代码。
- [FinanceBench 作者代码及公开样本](https://github.com/patronus-ai/financebench)
  - JIT OCR 文章案例使用的金融 QA 基准；区别完整题库与公开样本。
- [MinerU2.5: A Decoupled Vision-Language Model for Efficient High-Quality Document Parsing](https://arxiv.org/abs/2509.22186)
- [MinerU 官方代码](https://github.com/opendatalab/MinerU)
- [PaddleOCR-VL: Boosting Multilingual Document Parsing via a 0.9B Ultra-Compact Vision-Language Model](https://arxiv.org/abs/2510.14528)
- [PaddleOCR 官方代码](https://github.com/PaddlePaddle/PaddleOCR)
- [LayoutLMv3: Pre-training for Document AI with Unified Text and Image Masking](https://arxiv.org/abs/2204.08387)
  - 原理背景扩展阅读，不是 LlamaParse 内部模型的证明。

## 4. 当前开发者文档

- [LlamaIndex 产品与项目关系](https://developers.llamaindex.ai/home/)
- [LlamaParse 表格](https://developers.llamaindex.ai/llamaparse/parse/features/tables/)
- [LlamaParse 图表和图像](https://developers.llamaindex.ai/llamaparse/parse/features/charts-and-figures/)
- [当前 Parse 档位](https://developers.llamaindex.ai/llamaparse/parse/guides/tiers/)
- [中文与 OCR](https://developers.llamaindex.ai/llamaparse/parse/features/ocr-and-languages/)
- [Parse 配置与水印](https://developers.llamaindex.ai/llamaparse/parse/guides/configuring-parse/)
- [布局、边界框与坐标](https://developers.llamaindex.ai/llamaparse/parse/features/layout-and-bounding-boxes/)
- [Parse 返回格式](https://developers.llamaindex.ai/llamaparse/parse/guides/response-format/)
- [Extract 返回格式](https://developers.llamaindex.ai/llamaparse/extract/guides/response-format/)
- [Extract 配置](https://developers.llamaindex.ai/llamaparse/extract/guides/configuring-extract/)
- [Extract 引用与置信度扩展](https://developers.llamaindex.ai/llamaparse/extract/guides/extensions/)
- [平台 MCP](https://developers.llamaindex.ai/llamaparse/for-agents/mcp/)
- [平台 Skills](https://developers.llamaindex.ai/llamaparse/for-agents/skills/)
- [LiteParse 文档](https://developers.llamaindex.ai/liteparse/)
- [LiteParse 官方代码](https://github.com/run-llama/liteparse)
- [LiteParse Markdown 输出与质量边界](https://developers.llamaindex.ai/liteparse/guides/markdown/)
- [LiteParse 文档复杂度：OCR 与 layout 分开](https://developers.llamaindex.ai/liteparse/guides/complexity/)
- [LiteParse OCR 配置](https://developers.llamaindex.ai/liteparse/guides/ocr/)

## 5. PDF 底层行为交叉核对

- [pypdf：文字抽取为何困难、原生/扫描/OCR 文本层区别](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)
- [PyMuPDF：文本位置、阅读顺序、表格与字符映射问题](https://pymupdf.readthedocs.io/en/latest/recipes-text.html)

以上网页除固定论文/commit 外均可能更新。笔记记录本次核对状态，不保证后续产品行为完全相同。

## 6. 详细证据记录

- [解析评测与开源模型证据](references/001_解析评测与开源模型证据.md)：论文表格、当前榜单、TRM、MinerU 与 Paddle 配置。
- [LlamaParse 官方能力证据](references/002_LlamaParse官方能力证据.md)：具体文档、版本差异、中文、水印、表格、grounding、抽取与置信度。
- [当前榜单固定快照](https://github.com/run-llama/ParseBench/blob/afb36bd83ed8df7846f9d4f18c58bb948d9d5de0/leaderboard.csv)，commit 日期 2026-09-29。

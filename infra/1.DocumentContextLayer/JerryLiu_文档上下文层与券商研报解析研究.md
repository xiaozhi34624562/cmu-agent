# Jerry Liu：文档上下文层、OCR 与券商研报解析研究

研究日期：2026-10-03。资料入口：[SOURCES.md](SOURCES.md)。逐项技术证据：[解析评测与开源模型](references/001_解析评测与开源模型证据.md)、[LlamaParse 官方能力](references/002_LlamaParse官方能力证据.md)。

## 研究方法与结论

本次重新逐段核对[大会完整时间戳文字稿](https://ai.engineer/talks/RQi7x-navxU-building-document-context-layer-ai-agents)，查阅作者文章、产品开发文档、ParseBench 论文和固定版本榜单，以及 MinerU/PaddleOCR 一手材料。未取得独立幻灯片文件，未逐帧核验视频，未调用商业 API 或测试用户研报。这是研究与工程判断，不是中文研报性能实测。

本文区分演讲原内容、后续产品能力与工程建议。最重要的判断是：**这套方法值得用于你的失败页，尤其多级表头、密集表格、阅读顺序、跨页内容与可核验抽取。用户的原生文字与视觉结构融合路线已经有根据，进一步应把融合对象提升到结构关系与证据，而不是只替换文字。**

附件原讲解还需要修正两点：先粗读再精读并非所有任务的通用入库策略；84.9 是早期 ParseBench 数字，当前榜单已包含 MinerU/Paddle，旧论文结果与今日配置不能混用。

## 1. 整场演讲在讲什么

| 时间 | 演讲主线 | 对研报工作的含义（本文解释） |
|---|---|---|
| 0:12–3:07 | 固定 RAG 转向 Agent 推理与上下文访问分工 | 可以调整查询、继续阅读和回查 |
| 3:09–6:48 | MCP、Skills、自然语言 runbook、组织文档 | 工具和任务定义决定能访问什么信息 |
| 6:52–8:33 | 解析、语义存储、可重复工作流三层 | 文件可读、材料可管理、任务可稳定执行 |
| 8:35–10:51 | PDF 绘制结构与人类理解结构的差距 | 可提取文字不等于可正确理解表格 |
| 10:55–13:11 | 文件引擎、专用视觉模型、前沿模型及路由 | 内容按类型和难度分工 |
| 13:14–15:03 | ParseBench，关注可理解性 | 评结构、忠实度、定位，而不只是字符 |
| 15:08–18:24 | 准确率、成本、延迟；快读与视觉精读 | 按场景选择处理强度 |
| 18:28–20:16 | 抽取、来源、置信度、文档搜索 | 数据入库前作出接纳决策 |

最后的 agent-native 格式、版本管理、编辑协作、hill climbing as a service 等属于展望，没有展开实现。15:17 的99%–近100%指机构的要求，不是已达到的精度。[来源：大会文字稿](https://ai.engineer/talks/RQi7x-navxU-building-document-context-layer-ai-agents)。

## 2. 为什么你的“VLM版面 + 原PDF文字”仍然会错

以下是本文诊断框架，不是对尚未提供的失败页作出的结论。

| 层 | 典型错误 | 原文替换的作用 |
|---|---|---|
| 字符 | 数字改写、漏负号、凭空文字 | 可靠文本层且正确对齐时有帮助 |
| 区域 | 图注并入正文、表格裁掉一列 | 错框不因替换文字修复 |
| 阅读顺序 | 双栏交错、页眉夹进段落 | 字符正确仍可能顺序错误 |
| 表格关系 | 表头父级错、值挂到相邻列 | 替换字符串不能修复关系 |
| 业务含义 | 新旧预测、A/E、半年/全年、单位错 | 需任务抽取与证据核验 |

普通检测器的错框/分类错误与狭义生成式幻觉不是同一个问题，应分开统计；下游都可能表现为错误事实。

### 教学例子：没有一个数字编造，事实依然错误

以下为虚构数据：

| 指标（亿元） | 2024A | 2025E：旧预测 | 2025E：新预测 |
|---|---:|---:|---:|
| 营业收入 | 100 | 120 | 135 |
| 归母净利润 | 10 | 12 | 13.5 |

原 PDF 可能第一层是跨两列的2025E，第二层才是旧预测/新预测。模型漏掉第二层后输出“2025年预测收入120亿元”，所有字都能在原文找到，含义却不完整；若业务任务需要最新预测，应该得到135。

你的替换机制只能确认120确实存在，不能确认它属于最新预测。正确验收对象应是“营业收入—2025E—新预测—135—亿元”，连同表标题、脚注和每项来源。

### 原生文字也需要质量判断

[pypdf 文档](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)区分原生、扫描、扫描后带OCR文本层的文件；可复制文字不等于没有OCR错误。[PyMuPDF 文档](https://pymupdf.readthedocs.io/en/latest/recipes-text.html)说明默认提取顺序可能不符合阅读顺序，并提供带坐标的文字块与单词。

对你的融合流程，优先检查：

- 字符映射是否损坏，复制中文、特殊符号是否与页面一致。
- 渲染、模型输入、原生坐标是否统一处理旋转、裁剪和缩放。
- PDF text block 是否被错误等同一个段落或一个单元格。
- 模型区域边界是否遗漏字、跨进邻区；同一片段是否被重复归属。
- 水印、隐藏文字和旧OCR层是否混入正文。

这些是你的方法容易产生故障的位置。应将“原生坐标+模型框+最终单元格”叠加查看，先判断框错还是匹配规则错。

## 3. LlamaParse 的公开路线与你的方案有什么不同

### 文件信息与视觉信息互补

[Why Reading PDFs is Hard](https://www.llamaindex.ai/blog/why-reading-pdfs-is-hard)解释了文字编码、字体、坐标、表格线条及可选Tagged PDF，并描述文本提取、语言模型结构重建、布局检测和困难区域视觉处理的组合。合理理解是许多PDF缺乏可靠语义结构，不能说所有PDF都没有文字或结构。

[LLM APIs Are Not Complete Document Parsers](https://www.llamaindex.ai/blog/llm-apis-are-not-complete-document-parsers)有一个非常贴近你的 equity research report 图表例子：截图直接送模型会出现值的错误，结合文件信息后改善。它还讨论元数据、流程维护和规模化处理；这是厂商案例，不能推导所有中文研报同样效果。

用户和LlamaParse都可能使用混合路线。“混合”本身不是充分的胜出理由，更值得比较的是：

| 对象 | 进一步建设的能力（本文建议） |
|---|---|
| 内容 | 原生文字、OCR与视觉候选保留冲突，正确对齐 |
| 布局 | 区域类别、阅读顺序、遗漏与覆盖检查 |
| 表格 | 单元格跨度、完整表头路径、单位、脚注和续页 |
| 调度 | 简单内容便宜处理，困难内容升级 |
| 质量 | 输出疑点可复核，可返回不确定 |
| 表示 | Markdown阅读视图与结构化数据并存 |

### Agentic 公开了什么

[ParseBench §4.1](https://arxiv.org/html/2604.08538v3#S4.SS1)描述单次Cost Effective与多步Agentic：后者组织视觉模型、专用工具和迭代改进。没有完整公开服务端的模型名单、路由阈值、校验器和停止规则。

因此不能把“固定N轮、自主重裁切、多模型投票、逐token校验”等自行设计流程讲成官方内部算法。多步也不是零错误保证。

还应分清两个混合层次：解析器内部的多种方法分工；外部Agent先检索、再精读相关页。第二种能否工作，依赖粗读和检索能否发现相关页。

## 4. 复杂表格和图表：能力确实有，表示要保留

### 表格的三步要求

这是本文的工程拆分：

1. 几何结构：行列边界、跨行跨列、表格范围。
2. 逻辑结构：父子表头、值归属、单位/脚注作用范围、续表关联。
3. 业务抽取：指标选择、期间、A/E、新旧预测及口径。

OCR把所有词认对，只完成其中一部分。

[LlamaParse表格文档](https://developers.llamaindex.ai/llamaparse/parse/features/tables/)支持rows/CSV/HTML/Markdown、合并单元格及续表合并来源。HTML能保留rowspan/colspan，管道式Markdown不能充分表达这些关系。积极的无边框表检测也可能误报。[当前档位文档](https://developers.llamaindex.ai/llamaparse/parse/guides/tiers/)将Agentic Plus定位于密集财务文档等困难材料。

建议每张表保留原页、标题、单位、脚注、单元格原始显示值、行列跨度、逻辑表头路径、定位、跨页片段与冲突状态。复杂表的HTML适合保真展示，业务字段仍需要显式表头关系。

### 跨页“接得上”不等于“接得对”

本文建议用标题/续表标记、列位置、表头层级、单位和行连续性核验。仅因为相邻且列数相同就合并，会误接不同表。续页单位从前页继承时，记录该解释及上页证据；遇冲突保留片段并复核。

### 图表的数值有不同证据等级

[官方图表文档](https://developers.llamaindex.ai/llamaparse/parse/features/charts-and-figures/)有专用路线，可把图读成数据表并保留图片。曲线上的值不一定以数字文字存在于PDF。

建议区分明确标注值、视觉估计值、原始数据值。无标注折线只能估读时，不把结果当精确历史序列。双轴、图例、倍率和百分比/绝对值也须核验。产生整齐CSV不是正确性的证据。

## 5. 来源、置信度与完整性不能互相替代

[布局文档](https://developers.llamaindex.ai/llamaparse/parse/features/layout-and-bounding-boxes/)提供typed items以及词/行/cell框；[返回格式](https://developers.llamaindex.ai/llamaparse/parse/guides/response-format/)说明UTF-8字节span与page points坐标，中文实现不能直接用字符下标替代字节偏移。

一个135的框只能定位数字。若要证明“2025新预测收入135亿元”，还需行标题、年份、新旧预测、单位和脚注。bbox让结果可核验，不负责证明绑定关系正确。

[Extract返回格式](https://developers.llamaindex.ai/llamaparse/extract/guides/response-format/)区分解析与抽取置信度，提供字段引用；[官方置信度指南](https://www.llamaindex.ai/blog/what-makes-an-extraction-confidence-score-useful)要求用自己的样本验证阈值。不要把Extract字段校准套到Parse页面分数。

本文特别建议独立检查遗漏：100行只输出90行，这90行都可以很自信，漏的10行却没有低分字段供你筛选。高精度也不能通过全部拒绝来获得；应同时报告自动接纳比例。

## 6. ParseBench 如何阅读，为什么值得用来设计你的评估

[数据集](https://huggingface.co/datasets/llamaindex/ParseBench)和[代码](https://github.com/run-llama/ParseBench)覆盖表格、图表、内容忠实度、语义格式、视觉定位。表格记录匹配关心表头键与值的关联，不只是Markdown外观。具体TRM/GriTS定义、规则与代码链接见[详细证据](references/001_解析评测与开源模型证据.md)。

[2026-04论文Table 5](https://arxiv.org/html/2604.08538v3#S4.T5)：Cost Effective综合71.89、表格73.16；Agentic综合84.88、表格90.74。论文14方法未包括MinerU/Paddle。论文共2,078页、1,180文档、169,011规则，但没有中文券商研报单独成绩。

下面是[2026-09-29固定commit榜单](https://github.com/run-llama/ParseBench/blob/afb36bd83ed8df7846f9d4f18c58bb948d9d5de0/leaderboard.csv)，不是旧论文的同一次试验：

| 配置 | 综合 | 表格 | 图表 | 内容忠实度 | 语义格式 | 视觉定位 |
|---|---:|---:|---:|---:|---:|---:|
| LlamaParse Agentic | 87.01 | 88.88 | 88.68 | 91.78 | 81.44 | 84.25 |
| LlamaParse Agentic Plus | 90.20 | 93.37 | 94.18 | 92.25 | 87.12 | 84.09 |
| MinerU2.5-Pro-2605-1.2B | 72.78 | 77.59 | 61.64 | 87.88 | 57.49 | 79.30 |
| PaddleOCR-VL-1.6 | 67.43 | 67.77 | 54.24 | 82.71 | 54.64 | 77.80 |

这是LlamaIndex建立的基准上的配置结果，不是你的当前配置测试，也不是独立认证。综合90.20不是90.20%的页面全正确，更不能转写为幻觉率9.80%。总分可被不支持图表或某些格式拉低，不应解释为字符识别差。

## 7. 与Paddle、MinerU公平比较

[MinerU2.5原论文](https://arxiv.org/abs/2509.22186)公开低分辨率整页布局与原分辨率区域识别。[PaddleOCR-VL原论文](https://arxiv.org/abs/2510.14528)和[完整pipeline文档](https://github.com/PaddlePaddle/PaddleOCR/blob/dab3fe35379033fdcb2d0e9572fac0b36c9a9ebf/docs/version3.x/pipeline_usage/PaddleOCR-VL.en.md)也有布局、排序、区域识别和合成。不能将它们归为通用VLM一次整页自由生成。

Paddle官方特别提醒独立VLM不等于完整流水线。图表开关、图像块处理、Markdown过滤脚注/侧栏等也应核对；遗漏有时来自配置。MinerU原2.5与Pro要分版本。

用户具体版本、backend和失败页尚未知，不能假设已试过今日最新配置。本文的共同风险推断是：上游布局漏表头或裁错，下游识别再强也读不到被排除的信息。因此需要原页覆盖检查、候选保留和带上下文的复核。

## 8. LiteParse和JIT OCR：哪些适合你

[LiteParse当前文档](https://developers.llamaindex.ai/liteparse/)描述本地Rust工具、空间文字、截图、传统OCR；不是完整商业解析流程的开源版。[Markdown文档](https://developers.llamaindex.ai/liteparse/guides/markdown/)区分简单/中等表格与困难结构的质量边界。[OCR配置](https://developers.llamaindex.ai/liteparse/guides/ocr/)允许接自有PaddleOCR等服务。

[复杂度文档](https://developers.llamaindex.ai/liteparse/guides/complexity/)有一个很重要的分离：needs_ocr和layout.is_complex。清晰数字表可能不需识字，却仍需复杂表头恢复。建议路由结合二者及业务重要性。

[Jerry的JIT OCR文章](https://www.llamaindex.ai/blog/just-in-time-agentic-ocr)用84份金融文件说明快读后精读相关页，并明确区分临时data room与长期离线大库/批量抽取：后者应先取得高质量表示，否则粗读遗漏会让检索错过资料。[FinanceBench作者仓库](https://github.com/patronus-ai/financebench)另区分公开150题样本与完整题库。文档量是场景示例，不是普适阈值。

| 你的用途 | 本文建议 |
|---|---|
| 临时上传几份研报问答 | 快读、检索、精读关键页/原图 |
| 长期更新的研报库 | 入库前处理正文与图表覆盖、缓存高质量结果、查询仍能回查 |
| 批量盈利预测抽取 | 目标表提前结构解析、字段核验与完整性检查 |
| 快速浏览界面 | 初步结果先展示，后台精解析并标记版本 |

不要把用来找资料的粗表示自动当可用于计算的事实。未提取图片页也要有页级存在标记；关键问题搜不到时扩大候选文档检查，而非直接宣称未披露。

## 9. OCR之外的内容如何落实

[Files Are All You Need](https://www.llamaindex.ai/blog/files-are-all-you-need)强调交替搜索与阅读、文件承载上下文/Skills，同时承认规模化搜索需要索引。[文件搜索实验](https://www.llamaindex.ai/blog/did-filesystem-tools-kill-vector-search)样本与题数有限，不能推导向量库无用。

本文建议投研Agent能按公司/日期筛选、关键词与语义搜索、读章节、读整表、看原图、比较报告版本。问题如“盈利预测为什么调高”需要找两版表和相关正文，再核对脚注口径。

Parsing产出文档表示；Extraction按业务schema选择字段。[Extract配置](https://developers.llamaindex.ai/llamaparse/extract/guides/configuring-extract/)要求明确字段说明、类型和缺失行为。JSON合法不等于数据正确。

[平台MCP](https://developers.llamaindex.ai/llamaparse/for-agents/mcp/)与[Skills](https://developers.llamaindex.ai/llamaparse/for-agents/skills/)让工具可调用、流程可学习，本身不提高OCR精度。语义存储可以管理公司、发布日期、版本、章节和来源；可重复工作流则固定“预测更新”“行业数据抽取”等任务的字段、证据、异常与验收。

## 10. 演讲之后的相关产品进展

[2026-10-01 Extract v2.5](https://www.llamaindex.ai/blog/introducing-extract-v2-5)公开结构推理、中间表示、长列表覆盖、多页交叉核对、专门读取/转换/定位工具。这有助解释Agentic怎样处理复杂任务，但不是演讲已展示的完整算法，也不是OCR字符准确率保证。

中文研报还应关注[中文OCR配置](https://developers.llamaindex.ai/llamaparse/parse/features/ocr-and-languages/)与[水印配置](https://developers.llamaindex.ai/llamaparse/parse/guides/configuring-parse/#watermarks)。语言hint影响图像OCR；水印处理有版本要求，使用时检查有效图注是否误删。详情见[官方能力证据](references/002_LlamaParse官方能力证据.md)。

## 11. 针对你的工程改进方案

以下全是本文建议，未经用户文档验证，不是LlamaParse内部流程。

### 三层数据与证据约束

    原始证据：PDF、页面图、原生文字及坐标、OCR候选、模型原始输出
        ↓
    结构解释：区域、阅读顺序、章节、cell、表头路径、跨页关系、冲突
        ↓
    业务字段：公司、指标、期间、A/E、新旧预测、单位、原始值、证据、状态

原始证据不随结构修正而覆盖。模型尽量引用已有token来组织内容，主要输出归属与关系，程序拼接原始文字。扫描件仍需要OCR候选及字符核验。

允许未分配、跨边界、多个候选。复核局部要包含完整表头、标题和脚注。字段可以为空或待审；单位换算/数值归一化放后续确定性步骤，保留原值与换算记录。

一个示意记录可包括：metric=营业收入，period=2025，annual，forecast，revision=new，value_raw=135，unit_raw=亿元；column_header_path=[2025E,新预测]；引用分别指向value、row_header、column_headers、unit、footnotes；另有status与issues。这是设计示例，非原始API返回格式。

### 用检查结果触发局部复核

| 信号 | 后续动作 |
|---|---|
| 非空列没有完整表头路径 | 扩大到整张表检查合并表头 |
| token与模型框对不上 | 核对坐标变换和归属 |
| 源图有表但结果没有 | 检查漏检、输出过滤和覆盖 |
| 两种结构候选不同 | 查看整页+高分辨率局部，保留冲突 |
| 续页标题/单位/列不相容 | 暂停合并、回查两页 |
| 负号/括号/百分号冲突 | 检查原始显示文字 |
| 关键字段没证据或分数缺失 | 待审，不能自动接纳 |
| 算术不一致 | 标疑点、确认口径与舍入，禁止擅自改数 |

不同来源一致只能增加证据，不是正确性证明。避免同一模型重复确认到“自信”；复核应改变信息视角或使用独立规则。

## 12. 一次能指导决策的对照实验

建议从约100–300页起步，包括随机页和已知难页；这是实施建议，非统计保证。覆盖双栏、密集图表、无边框、多级表头、跨页、水印、小字和扫描件。

| 组 | 要回答的问题 |
|---|---|
| 当前MinerU | 真实基线是什么 |
| 同一MinerU+对齐/证据/检查/局部复核 | 不换主解析器，系统建设能改善多少 |
| Agentic+同样检查 | 换后端的额外收益 |
| Agentic Plus+同样检查 | 更高成本是否减少关键失败 |

分开报告原始解析质量与拒绝/复核后质量；记录人工参与、版本/backend、参数、分辨率、缓存。按研报/模板划分开发、校准和最终测试，避免相邻页泄漏。

本文建议重点测：

- 字符：关键数字、负号、括号、百分比。
- 结构：整表检出、漏行漏列、表头路径、值绑定、续表。
- 业务事实：公司、指标、期间、A/E、预测版本、单位、数值一起正确。
- 完整性：应有记录找到了多少；未输出也计失败。
- 接纳质量与覆盖：自动可用字段中错误多少，自动接纳比例多少。
- 证据与成本：能否核验完整含义；费用、延迟、升级次数、人工分钟；按通过验收的结果计成本。

如果主要错误来自坐标后处理，先修后处理；如果更强后端只对密集表有效，可仅在这类内容使用；如果两种后端都错，应改善表示与复核上下文。真实实验比Markdown观感更能定位下一步投入。

## 建议阅读路径

先读[PDF为什么难](https://www.llamaindex.ai/blog/why-reading-pdfs-is-hard)与[LLM API和解析系统的区别](https://www.llamaindex.ai/blog/llm-apis-are-not-complete-document-parsers)，然后结合[表格文档](https://developers.llamaindex.ai/llamaparse/parse/features/tables/)和[grounding](https://developers.llamaindex.ai/llamaparse/parse/features/layout-and-bounding-boxes/)理解输出。用[ParseBench](https://arxiv.org/abs/2604.08538)建立评估，再用[JIT OCR](https://www.llamaindex.ai/blog/just-in-time-agentic-ocr)决定何时处理。需要数据入库时读[Extract v2.5](https://www.llamaindex.ai/blog/introducing-extract-v2-5)与[置信度指南](https://www.llamaindex.ai/blog/what-makes-an-extraction-confidence-score-useful)。原生/布局/视觉联合表征的背景扩展可读[LayoutLMv3](https://arxiv.org/abs/2204.08387)，它不证明LlamaParse采用同样模型。

本次覆盖演讲关键材料及用户问题需要的相关研究，没有递归追踪所有历史OCR论文，也未取得商业解析器未公开的内部实现。

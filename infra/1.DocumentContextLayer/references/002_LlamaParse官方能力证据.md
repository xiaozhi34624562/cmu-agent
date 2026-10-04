# LlamaParse 官方能力核对（2026-10-03）

范围：已打开下列官方文档和博客正文，不仅搜索摘要；未调用付费 API、未实测用户中文券商研报。本文区分公开产品能力、厂商实验与工程推论，不证明对指定报告零错误。

## 1. 对用户问题最直接的回答

可以针对复杂版面、合并表头、无边框表格、跨页表格、图表等使用专门的解析路线；公开材料显示它并非只有一个 OCR/VLM 模型，而是文档表示、模型、工具、结构恢复、校验与证据定位相结合的工程系统。用户“VLM识别版面 + 原PDF文字替换”的思路与早期 LlamaParse 的原生文本/截图混合方法相近，但替换文字并不能单独修复阅读顺序、单元格归属、多层表头、单位、跨页续接等结构性错误。这一段是基于下列能力与用户现状的工程分析。

推荐对用户保留判断：“值得在你的坏例上认真试，因为它专门处理你遇到的那类问题；目前不能据演讲、文档或英文基准保证它已解决你的中文研报问题。”

## 2. 旧方法与产品演进证据

[LlamaParse update: new and upcoming features — 2025-02-20](https://www.llamaindex.ai/blog/llamaparse-update-new-and-upcoming-features)

- 明确公开主线：传统手段拿文本和截图，再交给 LLM/LVM 重建结构，早期同样经历幻觉与漏内容。
- 无 AI 路线输出 spatial laid-out text并做 OCR；LLM 路线以抽出的文字恢复结构且做错误修正；LVM 路线读截图；Agent 路线按需要结合 LLM 与 LVM，耗时和费用更高。
- 当时强调应看整份文档、多页表格和标题层级，但还在推进全篇功能；不得把2025“going forward”当成当时已全面实现的保证。
- 当时预设名为 Fast/Balanced/Premium，不能直接照搬今天 API。

[Parse migration v1→v2](https://developers.llamaindex.ai/llamaparse/parse/guides/migration-v1-to-v2/)

- v2以嵌套 JSON代替70多个平铺参数；tier和version必填，页码从0基改为1基。
- parse_mode改为tier；model按tier自动选，旧gpt4o_mode/premium_mode/vendor_multimodal等移除。
- high_res_ocr和precise_bounding_box在v2默认始终启用。
- 注意：模型和内部实现是tier的一部分，不应声称用户能选择或知道服务内部所有模型。

## 3. 当前 Parse 四档及复现

[Tiers](https://developers.llamaindex.ai/llamaparse/parse/guides/tiers/)

| tier | 官方建议用途 |
|---|---|
| fast | 原生文字/简单扫描、原始或空间文字；没有页面AI推理，不读图表数据、拒绝agentic_options |
| cost_effective | 文字为主、简单表格，较低成本结构恢复 |
| agentic | 扫描、多栏、真实表格、图表；默认推荐 |
| agentic_plus | 密集财务报告、复杂表格图示、复杂多栏 |

- 各tier是不同pipeline/model/prompt/config组合，Plus并非简单开更多开关。
- 生产固定真实已发布的dated版本，开发可以latest；具体latest以返回metadata.version为准，本研究没有运行API所以不虚构当前latest日期。
- 固定版本锁住配置，仍不等于数学保证每次输出完全相同。
- 混合复杂度可用 Cost Optimizer；官方另一页提示需要exact reproducibility时跳过自动路由。
- 注意文档小冲突：Tiers和layout页说当前fast也有items/markdown，配置总览局部仍说fast没有layout不能granular；需要依API/具体版本验证，推荐研报用agentic/Plus可避开此歧义。

## 4. OCR与中文、原生PDF文字

[OCR and languages](https://developers.llamaindex.ai/llamaparse/parse/features/ocr-and-languages/)

- 有原生文本层直接读；无文本层、扫描、内嵌图像自动OCR。它并非要求所有PDF文本都用VLM重写。
- `processing_options.ocr_parameters.languages`，中文简体`ch_sim`、繁体`ch_tra`，主语言放第一，例如`["ch_sim", "en"]`；只影响图像OCR，不影响原生文字。
- 文档承认图像质量限制；image-only无文字会NO_DATA_FOUND_IN_FILE。
- 默认图像OCR失败可留下空文字继续任务；需要设置`fail_on_image_ocr_error`才整任务失败。因此“完成”不等于每个区域完整正确。
- `ignore_text_in_image`关闭整job OCR；别拿它清logo结果把研报扫描页正文一起关闭。

## 5. 表格：能力和容易忽略的限制

[Tables](https://developers.llamaindex.ai/llamaparse/parse/features/tables/)

- 专门列出财务报表、合并表头、跨页、无边框表格作为目标场景。
- Table item可有rows/csv/html/md；Markdown pipe table无法表达合并单元格，HTML可表达colspan/rowspan。复杂表头应保留HTML和结构，别只存Markdown。
- `output_options.markdown.tables.output_tables_as_markdown: false`保留HTML。
- `merge_continued_tables: true`合并续页，放在第一页，提供`merged_from_pages`。
- `tables_as_spreadsheet.enable: true`可导出XLSX，每张表一sheet；导出只是表示，不是数字质量证明。
- `aggressive_table_extraction`对无边框表更积极，但官方明确可能false positives；`disable_heuristics`用于关闭造成错误的outlined-table/adaptive-long-table heuristics。

用户多级表头问题的工程解释：识别出“2025E”文字正确但挂在“收入/营业利润”的错父标题下，仍会产生错误财务事实；必须评测行列头路径与值绑定，而不只文字CER/WER。

## 6. 布局、grounding与可核查输出

[Layout and bounding boxes](https://developers.llamaindex.ai/llamaparse/parse/features/layout-and-bounding-boxes/)

- items是每页按顺序排列的typed tree，包括标题、正文、表格、图、页眉/页脚。
- `output_options.granular_bboxes: ["word", "line", "cell"]`另出grounded_items JSONL sidecar，与item-level boxes不同；可用于原PDF同步高亮。
- 页眉页脚独立字段；crop_box按几何裁切去页面边栏，不过统一crop可能删内容，要检查。
- 输出printed_page_number可以区别PDF序号和纸面“第xx页”。

[Parse response format](https://developers.llamaindex.ai/llamaparse/parse/guides/response-format/)

- bbox单位page points，原点左上，不是pixels也不是0–1 normalized；每页大小可能不同，有rotation。
- grounding spans是UTF-8 byte offsets，不是字符索引；中文用普通字符串切片会定位漂移。
- JSONL每页可success=false；表格cell grounding可null，要检查缺失。
- 页面confidence 0–1；high-effort下document mean、min_page_score、scored_pages与total_pages可见。均值高也会掩盖最差页。
- “bbox能指回来源”只提供可验证证据，不保证框/识别/语义本身正确。

## 7. 图表不要混为表格OCR

[Charts and figures](https://developers.llamaindex.ai/llamaparse/parse/features/charts-and-figures/)

- specialised chart parsing把bar/line/pie等图表读为table item，让agent对数值而非像素分析；Plus默认启用，agentic/cost_effective需opt-in，fast不支持。
- `processing_options.specialized_chart_parsing`值efficient/agentic/agentic_plus。
- `images_to_save`可以保留整页screenshot、embedded图片、裁切layout图，便于人工/二次视觉检查。
- 图表数字不一定在PDF原生文字层，即便轴标签、legend能抽出，也不能靠“替换文本”精确恢复曲线数值。后者是工程推论。
- 对中文券商双Y轴、密集折线、小字号、无数值标注图，应保留原图和“估读/明确标注”区别；服务能输出table不等于这些数已变成精确测量。这也是工程建议，文档不提供该特定场景精度保证。

## 8. 当前参数：水印与页面级confidence

[Configuring Parse](https://developers.llamaindex.ai/llamaparse/parse/guides/configuring-parse/)

- 2026-09-28起cost_effective/agentic/Plus支持watermark_handling remove/move_to_start/move_to_end，扫描页也支持，metadata有watermark。默认move_to_end。
- 与ignore_diagonal_text不同：后者丢掉原生层旋转文字；水印功能针对识别的水印内容。text output里嵌在正文line中水印可能仍留着。
- `processing_options.confidence_score_effort: "high"`增强页面质量评估，多5credits/page，metadata可看文档最差页/均值等。
- 我未找到Parse页面confidence等同已校准正确概率的公开保证；不要套用下节Extract字段校准。
- Cost Optimizer按页面复杂度路由较廉价tier；先在小样本固定tier建立基线，再测自动路由更合理（建议）。

## 9. Extract：从整份报告结构到业务字段

[Configuring Extract](https://developers.llamaindex.ai/llamaparse/extract/guides/configuring-extract/)

- schema定义字段、类型、description；description供模型决定含义、所在位置、格式。
- 要区分required和nullable；建议明确required列表，Extract省略required时默认所有字段required，与标准JSON Schema不同。
- version当前可以2.5/latest或日期；不要把Parse dated version与Extract version name混淆。
- schema根必须object；变量条目放array，nullable字段允许缺失值，不要逼模型填数字。
- spreadsheet mode直接读Excel/CSV cells，但不产生citations/confidence；用户PDF导表后再做此模式会丢某些证据流程，需留PDF侧出处（建议）。
- 正文不支持继续照抄旧per_table_row/per_page examples；当前案例统一per_doc。搜索摘要曾返回旧schema元数据，正式正文已变化，优先正文和版本。

[Extract response format](https://developers.llamaindex.ai/llamaparse/extract/guides/response-format/)

- `cite_sources`和`confidence_scores`需显式启用，取结果要expand=extract_metadata。
- 字段引用提供page、matching_text、bounding_boxes、page_dimensions；Turbo仅文字级citation。
- 字段metadata对应schema叶子，例如items[0].amount，而非items[0]整体。
- confidence合并parsing_confidence和extraction_confidence，区分“源文档结构读错”和“从表示映射字段出错”。

## 10. Confidence校准真正说了什么

[Metadata Extensions](https://developers.llamaindex.ai/llamaparse/extract/guides/extensions/)

- 官方说Cost Effective/Agentic/Agentic Plus已校准，score近似真实correctness probability；0.8 cutoff约75%抽取错误落在阈值下。
- 这不是“0.8以上零错”，也不是“整份报告80%正确”。75%是错误捕获比例，不是正确率。
- Agentic Max/Turbo是较早模型，仅适用于排序，不能套同一校准。
- 要自有样本文档ground truth验证cutoff；长summary/description通常更低，不能直接认为比短事实准确率低。
- confidence/citation增加时间；reasoning metadata只至2026-03-31版本，新版本不再返回每字段reasoning strings。别把reasoning当证据或当前默认。

[A practical guide to extraction confidence scores — 2026-09-16](https://www.llamaindex.ai/blog/what-makes-an-extraction-confidence-score-useful)

- 官方在370个ExtractBench文档/4869页/841895字段上分析，confidence模型训练校准使用benchmark外文档。
- 字段池化统计，长文档权重更大，不等于leaderboard按文档平均；阈值是事后挑选的benchmark operating points。
- 部署应在一组本域标签样本选cutoff，另一组验证；missing expected fields需要独立检查；unscored value不可自动接受。
- 其叙述与用户真实场景的连接：漏行/漏表没有输出就未必有低confidence字段，必须另外检查完整性。这是本文建议。

## 11. 演讲之后的新架构证据（切勿写成演讲原话）

[Introducing Extract v2.5 — 2026-10-01](https://www.llamaindex.ai/blog/introducing-extract-v2-5)

- 新purpose-built agent harness借鉴coding agents，cross-reference多页，返回原始证据；structural reasoning按类型/版面/密度调整effort。
- 长重复列表用intermediate representations处理整套数据与schema校验；多页记录保持关联。工具读、转换和定位文档信息。
- Advanced Citations适用于值不逐字出现在原文的难字段，Plus已有初版，现在改进并扩展Agentic。
- 厂商报告ExtractBench value F1：Cost Effective87.1→93.9、Agentic89.8→95.8、Plus95.1→96.4；Agentic/Plus grounding80.6/82.2。这些都不是OCR字符准确率，也不是中文券商报告正确率。
- 若篇幅有限，保留结构推理/跨页/中间表示/grounding思路，避免塞产品分数稀释用户实际问题。

[Why Can't VLMs Read Forms? — 2026-09-28](https://www.llamaindex.ai/blog/why-vlms-can-t-read-forms)

- 一种相关例证：纯VLM推理增加不一定改善parse；form需要组合内容抽取、框定位与结构归属。
- 表单以sections/fields tree保存结构，两个“Date”要属于不同父section；flat list会失去归属。
- 此文章是表单，不是表格跨页准确率证明；能说明“结构关系正确”是OCR文字正确之外的另一层目标。

## 12. OCR之外：Agent怎样消费文档

[LlamaParse MCP](https://developers.llamaindex.ai/llamaparse/for-agents/mcp/)

- MCP把Parse/Classify/Split/Extract/Index暴露为tools；是访问接口，不本身提高OCR。
- Parse tools含parseFile、parseWithLiteParse、estimateFileComplexity；复杂页走重解析，其余较轻。
- Extract schema模板、自动schema/config生成与extractFile，避免Agent只拿截断长文后靠prompt抽字段。
- Index除hybrid sparse+dense retrieval，还可findFiles/readFile/grepFile，像文件系统定位、阅读与搜索。
- 知识库createIndex后需getIndexStatus等ready；syncIndex显式刷新，否则不会自动看到新增文件。
- 文档MCP developers.llamaindex.ai/mcp只用于浏览官方文档，平台MCP mcp.llamaindex.ai/mcp才用于处理用户文件，别混淆。

[Skills and Plugins](https://developers.llamaindex.ai/llamaparse/for-agents/skills/)

- llamaparse skill教Agent使用cloud advanced parse，需API key；liteparse本地无key，强调快和spatial text。
- plugin可把skill/MCP打包给coding agent；skill是操作知识/流程，不是另一个OCR模型。
- open-source LiteParse不等于LlamaParse的完整先进商业pipeline已开源；也不保证相同复杂表能力。

## 13. 给券商研报的可操作研究方案（本人建议，非服务内部算法）

1. 对同一批已失败页面取原PDF、页面渲染、原生文字与坐标；先保留MinerU基线，固定版本、prompt、dpi。
2. LlamaParse agentic与Plus试同一批。先不自动路由；中文/英文OCR hints；保存items+HTML+grounded cells+截图+页面metadata。
3. 不以“Markdown读着通顺”评分；分开记录字符、阅读顺序、表格检出/漏表、多层表头路径、值-行列绑定、漏行/重复行、跨页续接、单位、负号、百分号、年份A/E。
4. 对目标业务字段做schema抽取：报告日期、公司、预测年份、actual/estimate、metric、原始显示值、unit/currency、period、table_id/page；可null、禁止未见数值补齐。强调“抽取”和下游归一化/计算分步。
5. 证据链不是只给page：每事实应关联表头路径、行标题、cell框、单位/脚注框。错列正确字仍应判错。
6. 外部确定性校验：列数/表头一致、跨页重复表头、单位与数量级、已印合计与加和、增长率与已提数字；仅在同一口径下可比较。发现矛盾用于拒绝/升级，不得用算式强行覆盖原文。
7. 原生文本替换时按区域/cell对齐，保留原值；PDF可能font映射/隐藏OCR层错误，不能把原生层绝对视作真值。
8. low-confidence、视觉/文字不一致、验证失败、缺失框等触发区域重新解析或人工审阅；不要无限LLM自我检查直到自信。
9. 评估整表完整性与已接受字段错误率，尤其没输出的条目；本域train/calibration/test独立。成本同时计页数、latency、升级比例、人工分钟数。
10. 问答/Agent上下文把整表及标题/单位/脚注保持一体，表格data进入结构化数值路径；检索用混合搜索+全文/grep/原图回看，跨页不是盲目逐页chunk。

## 14. 不能有的断言

- 没公开训练细节/内部tool策略，不能编造“所有页必定多模型投票、OCR对比、自纠正N轮”之类pipeline。
- 没有用户PDF实测，不能说中文券商报告全面胜过MinerU/Paddle，也不能用英文财报/表单例证明。
- schema conformant不等于内容准确，citations不是truth证书，confidence不是免审保证，agentic不是保证不存在结构幻觉。
- 不能用最新2026功能为旧演讲还没上线的产品做倒证；正文可明确“下面是后续官方产品实现补充”。

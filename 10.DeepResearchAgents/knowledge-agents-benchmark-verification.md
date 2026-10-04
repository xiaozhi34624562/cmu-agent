# Knowledge Agents 演讲：BrowseComp-Plus 与 MADQA 证据核查

核查日期：2026-10-03。本文是资料核查备忘，不是演讲逐字稿，也不是独立复现实验。先读本目录 `SOURCES.md`；未修改其他仓库文件。

## 来源与版本

- [BrowseComp-Plus 原论文 v1，2025-08-08](https://arxiv.org/html/2508.06600v1)：读取正文及实验、消融和附录工具提示。
- [MADQA 原论文 v2，2026-03-20](https://arxiv.org/html/2603.12180v2)：读取正文及相关附录；对比 v1/v2，所述关键实验数字未变化；v2 主要调整相关研究表述、链接和少量文字。
- [MADQA 官方数据卡](https://huggingface.co/datasets/OxRML/MADQA)；[官方实现](https://github.com/OxRML/MADQA)。注意旧论文 v1 的 Snowflake-Labs 仓库链接已不如 OxRML 版本完整。
- [BrowseComp-Plus 官方项目页](https://texttron.github.io/BrowseComp-Plus/)。
- [Mixedbread 第一方实验文章，2026-03-24](https://www.mixedbread.com/blog/closing-gap)。这是厂商报告，与论文实验分开引用。
- [Mixedbread 当前 MADQA 评测页](https://www.mixedbread.com/evals/madqa)。页面动态更新，不用当前数据替代演讲当时结果。

## 1. 最重要的核查结论

1. MADQA 的 2,250 是全量题数；500 是测试集，另有 1,550 train、200 dev，二者不矛盾。[数据卡 Splits](https://huggingface.co/datasets/OxRML/MADQA#splits)
2. 99.4% 是 **人类拿到 oracle 证据**的成绩。不能称为“同一个模型在完美检索下的成绩”或普遍可达的模型上限。[MADQA 表 3](https://arxiv.org/html/2603.12180v2#S3)
3. BrowseComp-Plus 的 93.49% 是 **GPT-4.1** 直接获得全部正例文档后的成绩。把别的模型/框架与 93.5% 相减只能得到参照差距，不能严格识别该系统的纯检索损失。[BrowseComp-Plus §4.8.1](https://arxiv.org/html/2508.06600v1#S4.SS8.SSS1)
4. 演讲口述的 88.9%、+3.5 个百分点、99.4%、缩小约40%：若前三项确为同一实验，算术应是 `3.5 / (99.4 - 88.9) = 33.3%`。88.9→92.4 后剩余差距7.0个百分点。本次没有找到这组实验的完整公开一手配置和表格；不能把它补写成已验证的论文结论。主代理已核对[主办方逐字稿14:41附近](https://ai.engineer/talks/O84lhGc1OOI-if-we-want-them-do-knowledge-work)，确有该口述；应如实写“口述数字存在算术不一致，公开一手资料不足以补全实验配置”，不要擅自把40%改成已证实的精确效果。
5. 厂商3月文章实际公开的是 MADQA one-shot 88.2%、Button 91.7%，二者正好相差3.5，但模型和系统也变了：后者是 Gemini 3.1 Pro + Button，前者是 Gemini 3 Pro one-shot。**不能拿这组数字替演讲补全同模型多 Agent 消融**。[厂商原表](https://www.mixedbread.com/blog/closing-gap#madqa)
6. 当前 Mixedbread 评测页出现“Claude Sonnet 4.5 + BM25，35.1 calls”；原论文表3对应35.1是 **Kuiper 校准统计量**。不能据此说Claude平均调用35.1次工具，也不能由这组数字计算调用次数降幅。[厂商页面](https://www.mixedbread.com/evals/madqa)；[论文表3](https://arxiv.org/html/2603.12180v2#S3)

## 2. BrowseComp-Plus：它能证明什么

### 2.1 任务和控制变量

固定100,195份网页文档、830个问题；每题平均6.1份 evidence 文档，2.9份语义上含最终答案的 gold 文档。它把原BrowseComp的实时搜索环境改为固定语料，因此更容易研究检索器与推理器分别贡献多少。evidence不是“出现答案字面字符串的文档”：可以包括推理链上的辅助证据。[论文 §3.2–3.4](https://arxiv.org/html/2508.06600v1#S3)

默认工具一次返回top-5，每份只展示前512 tokens；因此默认成绩也受到可见上下文限制。论文用GPT-4.1判最终答案，另测全轨迹证据召回、搜索调用数、置信度校准和引用质量。[论文 §4.3–4.4](https://arxiv.org/html/2508.06600v1#S4.SS3)

### 2.2 有价值的同模型对照

| 固定模型 | 检索器 | 准确率 | 每题搜索调用 |
|---|---|---:|---:|
| GPT-4.1 | BM25 | 14.58% | 10.35 |
| GPT-4.1 | Qwen3-Embedding-8B | 35.42% | 8.67 |
| GPT-5 | BM25 | 55.90% | 23.23 |
| GPT-5 | Qwen3-Embedding-8B | 70.12% | 21.74 |

事实来源：[论文表1](https://arxiv.org/html/2508.06600v1#S4.SS5)。这支持“检索改善可以同时提升准确率并减少搜索”，不支持“任何语义检索都永远优于BM25”。这里的BM25配置、文档长度、查询习惯和返回片段规则均具体限定了比较。

加入全文读取工具后，GPT-4.1 + Qwen3检索从35.42升到43.61，平均1.85次全文阅读；Qwen3-32B从10.36到11.69，全文工具平均仅0.27次。工具的存在和模型有效利用工具是两件事。[论文 §4.8.3、表5](https://arxiv.org/html/2508.06600v1#S4.SS8.SSS3)

### 2.3 Oracle的正确解读

GPT-4.1获得全部正例文档后93.49%；剩余6.51%经人工确认文档可答，模型仍然推理失误。Qwen3-32B oracle 83.25%，其中约6%全部题因为正例上下文超过窗口出错。Oracle不是消除阅读与推理问题，也不是100%。[论文 §4.8.1](https://arxiv.org/html/2508.06600v1#S4.SS8.SSS1)

厂商后续报告 Mixedbread standard 80.00、get_document 90.48；Reason-ModernColBERT相应79.52与87.59。厂商所说“距离oracle3.02”用的是论文GPT-4.1的93.5参照，应注明来源和非同条件限制。[Mixedbread 原表](https://www.mixedbread.com/blog/closing-gap#browsecomp-plus)

## 3. MADQA：真实文档智能的三个测量维度

### 3.1 数据及范围

800份PDF、18,619页，13大领域、63细类。全量2250题中17.3%多跳，8.3%跨页、9.0%跨文档，其余82.7%单跳；并不是所有题都要复杂多 Agent规划。Financial领域131份、6149页、460题；Financial/Tax另39份、2925页、82题。58%问题从版面、表格或视觉信息获益，但不能把这句话升级成“58%必须用视觉编码器”：作者明说部分表格关系可从线性化文本恢复。[论文 §2、表2、图4](https://arxiv.org/html/2603.12180v2#S2)

测试集500题的最小证据标注在官方数据卡中隐藏。任务核心是封闭语料内的有依据问答；并不等价于开放式证券研究、未来预测和投资建议。[数据卡](https://huggingface.co/datasets/OxRML/MADQA#schema)；[论文 §7](https://arxiv.org/html/2603.12180v2#S7)

### 3.2 基线工作方式

BM25 MLLM Agent对OCR页文本建立Whoosh索引，支持布尔、短语和通配查询；检索后交给模型的是**页面图片**。默认最多10次模型迭代，每次返回5页，最后一轮强制回答。它不是“完全不看视觉的传统关键词RAG”。[论文附录G.1](https://arxiv.org/html/2603.12180v2#A7.SS1)

人类用相同关键词检索引擎，能在PDF中翻页并选证据；系统记录查询、页面浏览、时间。人类oracle直接获得相关证据，认知负荷也会减少。这意味着人类oracle和模型agent的差异不只有retriever这一项。[论文附录C.2](https://arxiv.org/html/2603.12180v2#A3.SS2)

### 3.3 表3关键结果

| 系统 | Accuracy | X-Page | X-Doc | Page F1 | Doc F1 | Kuiper↓ |
|---|---:|---:|---:|---:|---:|---:|
| Human + Oracle | 99.4 | 100.0 | 98.0 | — | — | — |
| Human + BM25 | 82.2 | 79.6 | 72.0 | 79.3 | 93.4 | 14.6 |
| Gemini 3 Pro + BM25 Agent | 82.2 | 66.8 | 73.0 | 78.5 | 90.2 | 25.8 |
| Claude Sonnet4.5 + BM25 Agent | 80.6 | 66.8 | 82.0 | 79.1 | 93.0 | 35.1 |
| Gemini 3 Pro File Search | 78.6 | 74.1 | 75.0 | 70.1 | 94.2 | — |
| GPT-5 + BM25 Agent | 77.7 | 60.1 | 74.0 | 74.2 | 86.5 | 52.6 |

来源：[论文表3](https://arxiv.org/html/2603.12180v2#S3)。表中省略论文置信区间，分数单位均为百分制，但Kuiper不是准确率、百分比或工具调用次数。

- 答案正确性：语义裁判，经过人工校准，并对聚合结果做偏差校正。
- Page F1：预测引用页与人工最小证据页集合的重叠；Doc F1降到文档粒度。二者分离能定位“找对文档但引用错页”。
- Kuiper：把样本按投入排序后，正确率相对总体平均的累计偏离范围；低值意味着准确率较少随投入变化，不能单独证明会思考、会止损。需与准确率、引用、tokens、耗时和成本一起读。

以上定义：[论文 §3](https://arxiv.org/html/2603.12180v2#S3)。例如FileSearch Doc F1 94.2但Page F1 70.1，不能拿“文档找对了”冒充“数字出处已精确核验”。

### 3.4 不应遗漏的反直觉发现

- 同为82.2，不代表相同能力。人类与Gemini3Pro在107题结果不一致，其中54题仅人类正确，53题仅模型正确；校正机会一致性κ=0.24。**不能说它们做对题目几乎不重叠**：这是低机会校正一致性，不是正确集合不相交。[§5.2、附录H.4](https://arxiv.org/html/2603.12180v2#S5.SS2)
- 人类第一轮完成并答对约50%题，Gemini约12%；但附录H.5“首轮找到正确文档”是约80% vs70%。这是**完成准确率**与**证据召回**两个指标，不矛盾。[图9、附录H.5](https://arxiv.org/html/2603.12180v2#S5.SS2)
- 82.2比78.6高3.6个百分点，或相对提升4.58%。Snowflake博客的“4.6%”应按相对增幅解读，不要写“4.6个百分点”。[论文表3](https://arxiv.org/html/2603.12180v2#S3)；[作者机构博客](https://www.snowflake.com/en/blog/engineering/madqa-multimodal-agent-reasoning-benchmark/)
- 原文正文强调retrieval瓶颈，但附录错误分析表明强模型开始更多卡在comprehension。17个agent的3273个错误中，wrong-doc35.7%、right-doc-wrong-page23.0%、right-page-wrong-answer28.8%、refusal12.6%。**这些比例的分母是错误数量，不是全部题**。[附录H.3、表17](https://arxiv.org/html/2603.12180v2#A8.SS3)
- Sonnet4.5在全部预测中wrong-doc仅4.0%，right-page-wrong-answer8.6%。因此即使检索足够强，也可能读错表、否定、时间或角色，不能说“接近oracle意味着检索问题已经解决”。[附录H.3](https://arxiv.org/html/2603.12180v2#A8.SS3)
- Claude Sonnet4.5 RLM在500题测试上用了约2.7亿输入tokens、约850美元，准确率70.5，低于其BM25 Agent80.6。这只否定该配置下“无约束多花预算必然更好”，不证明所有递归式系统都差。[§5、图7](https://arxiv.org/html/2603.12180v2#S5)

## 4. 对投研系统的推导与建议（不是原论文结论）

以下是基于上述证据的工程推导，应在最终文章明确标为建议。

1. 设计同模型oracle测试：固定模型、提示、工具预算和答案格式，仅把检索替换为人工金标准证据。另设金标准结构化表格，区分找不到、读不对、算不对、判断不当。
2. 证据精度至少到“文件版本/披露日期/页码/表名/行列/单位/时间区间/合并范围”。Page F1只能查到页，不足以发现同页读错字段。
3. 单独记录关键证据完整率、答案正确率、引用支持率、算式可复现率；不要用一个最终accuracy覆盖它们。
4. 同时画预算曲线：首次可用证据时间、1/3/5次检索下表现、每题成本、p95耗时。论文说满预算冠军可能在低预算条件下落后，不能直接以排行榜冠军决定交互式产品配置。[论据：MADQA §7](https://arxiv.org/html/2603.12180v2#S7)
5. 以“尚缺哪个事实/哪条反证”为重试条件，而不是持续同义改写；每轮存新增证据、未解决矛盾和停止理由。查询变化幅度与成功的相关性提供思路，但不是“查询越不同越好”的因果保证。[论据：MADQA附录H.6](https://arxiv.org/html/2603.12180v2#A8.SS6)
6. MADQA是英文、偏美国、公开文档、良性输入、有答案问答；不测中文公告口径、信息披露时间可见性、未来收益、攻击文档或组合决策。企业上线需另建自身评测。[论据：MADQA §7](https://arxiv.org/html/2603.12180v2#S7)

## 5. 引用时的措辞边界

建议写：这些研究说明，在指定语料、模型和工具设置中，获取正确证据与有效组织搜索经常占据很大提升空间；多模态阅读、全文读取和检索器质量都可能显著改变结果。

不要写：知识工作只剩检索；金融投研不需要推理；MADQA证明多Agent一定更强；99.4%是所有知识智能体的理论上限；厂商相近百分比必然来自同一实验。

# Agent Harness 如何自演化：RRSI、Harness²、Evo² 与 OO-Harness

核查日期：2026-11-13。面向 Senior AI Engineer。固定版本、原始文件名、页数、SHA-256 与核查范围见 [SOURCES.md](SOURCES.md) 和 [REFERENCES.json](REFERENCES.json)。下文页码均为本地 PDF 从 1 开始的实际页序。

## 1. 讲解路线：先看优化问题，再看算法，最后检查证据

这四篇论文可以用同一组问题贯穿：系统把什么当作可更新状态？反馈来自哪里？一次修改如何归因？什么被保留到下一个任务？改进离开演化数据后是否仍成立？计算成本由谁支付？

建议阅读顺序是 RRSI → Harness² → Evo² → OO-Harness。先认识演化中的过拟合，再看没有答案的在线修改，然后看如何训练修改者，最后看异质任务的程序组织与路由。这是教学组织，不表示四篇构成前后依赖的官方技术路线。

| 论文 | 主要问题 | 被更新的对象 | 主要反馈 | 跨任务保留的状态 |
|---|---|---|---|---|
| RRSI | 反复使用有限演化集，会选中噪声、泄漏和复杂度 | 一个可编辑的执行 harness | evolve-set verifier、轨迹、成本 | harness、编辑历史与归因记录 |
| Harness² | 新任务没有 ground-truth verifier，且任务不断变化 | 当前任务的执行 harness；跨任务改进库 | 匹配条件下的行为对比与模型判断 | 可执行 harness 组件与经验库；下一任务从共同 H0 开始 |
| Evo² | 固定的演化器可能不会有效修改和诊断 | harness 搜索树；共享 Proposer/Reflector 的权重 | 外部任务分数的增量、执行有效性 | harness、策略库、演化器权重 |
| OO-Harness | 一个全局程序难以兼顾异质任务 | harness 类层次、任务簇、设计/路由经验 | discovery-task grader 与轨迹 | 冻结的类目录与经验；测试时选择 |

表格对应 RRSI §2–3 pp.3–6；Harness² §2 pp.3–7；Evo² §3 pp.4–7；OO-Harness §3 pp.3–5。四篇没有在同一 executor、数据集、预算与评分体系下做共同实验，因此不能直接排列谁最强。

## 2. 统一概念：Harness 是可执行策略，不只是提示词

**论文共同背景。** 对一个固定模型 $M$，harness $H$ 规定每一步如何构造上下文、展示工具、处理工具返回、调用子任务、保留记忆、压缩上下文以及决定何时结束。简写为：

$$
\tau,y = \operatorname{Run}(M,H,x,E)
$$

$x$ 为任务，$E$ 为环境，$\tau$ 为轨迹，$y$ 为最终产物。即便 $M$ 不变，$H$ 也会改变模型实际看到的信息与可执行动作，因此会改变行为和成本。RRSI §2 p.3；Harness² Figure2 p.3。

**教学推导。** 以研报证据核查为贯穿案例：系统要从 PDF/Excel 找到数字，统一期间与单位，生成有出处的分析。以下四种更新属于不同层面：

- 把“提交前核对单位”加入提示，是软约束；
- 在完成事件前执行单位与出处检查，是控制流；
- 写一个确定性单位转换脚本，是工具能力；
- 保留“合并报表与母公司报表混用”的适用条件和失败证据，是经验状态。

这些设计由论文的 harness 概念推导，用于帮助理解，不是四篇已经验证过的金融实验。

用一个工程目标表达我们真正关心的事：

$$
\max_H \mathbb E_{x\sim D_{deploy}}[Q(M,H,x)]
\quad \text{s.t.}\quad C(H)\le B,\;\operatorname{Valid}(H)
$$

这里的部署分布 $D_{deploy}$ 通常不可直接优化；论文只能用有限任务和代理反馈逼近它。后面的分歧，本质上是如何处理这种不完美反馈。这个约束目标是教学抽象，不是四篇共享的原始目标函数。

## 3. RRSI：把演化当作会过拟合的自适应程序搜索

原文：[RRSI: Regularized Recursive Self-Improvement of Agent Harnesses](references/RRSI_Regularized_Recursive_Self-Improvement_of_Agent_Harnesses.pdf)，arXiv 2609.24972v3。

### 3.1 为什么测试集不泄漏，仍可能演化过拟合

**论文机制，§2–3 pp.3–6。** 一个普通演化循环是：运行当前 harness → 总结失败 → 生成候选 → 在同一 evolve set 上评分 → 保留最高分者。第 $t$ 轮候选已经依赖前 $t-1$ 轮对同一数据的观察，因此这是自适应经验优化，不能把每轮评测看成互相独立的新证据。

三种问题可以同时发生：

1. **任务拟合**：把 evolve-set 的题目名称、实体、格式或答案规律写进程序。
2. **噪声追逐**：候选真实能力相近，但随机执行的最高分者被选中。候选越多，极值偏差可能越明显。
3. **复杂度累积**：不断增加重试、反思、上下文和子 agent，在有限集合上涨分，却把成本和迁移风险留给部署。

**教学例子。** 看见训练样本都用“百万元”，就强制按百万元解释数字，会在同单位的训练题得分，却在“万元”材料上出错。更可迁移的更新是从表头或脚注读取单位，并在转换前记录证据。前者记忆数据规律，后者改变通用处理机制。

### 3.2 提议端：控制每轮响应反馈的容量

**论文机制，§3.2 pp.5，App D pp.20–21。**

**退火编辑预算。** 一个候选最多包含 $b_t$ 个可独立归因的修改：

$$
b_t=\left\lceil b_{min}+(b_{max}-b_{min})\frac{1+\cos(\pi t/T)}2\right\rceil.
$$

早期可以探索几个协同机制，后期减少同时变化的机制。限制的是独立编辑数，不是改动行数、候选数或 token 上限。它不会禁止未来修改某个组件。

**全历史证据。** 每个候选记录轮次、组件、假设、diff、分数差、成本差与是否被接受。失败假设也进入历史，以免模型把旧失败重新包装为新创意。多个编辑被捆绑时，共享同一候选级分数，归因仍不完整；稀疏化只能缓解这个问题。

**停滞后的结构探索。** 最近 $w$ 轮进展未超过噪声带时，预留候选位置，探索尚未尝试的组件。例子是停止反复扩写 system prompt，转而尝试工具错误修复、context 管理或输出检查。

### 3.3 选择端：高分必须同时满足几道门槛

**论文机制，§3.3 pp.5–6，Algorithms1–2 p.20，App D.3 pp.21–22。**

第一道是评分前的 diff critic：拒绝显式 benchmark/task 特定逻辑及无效新增结构。这是模型审查，不是数据隔离的形式化保证。

第二道是全局历史最优分数地板：

$$
\widehat S(H')\ge S^*-\delta.
$$

$\delta$ 来自对不变 base harness 的重复运行。相对历史最优设地板，能防止“每次只退一点”累计下滑。它并不要求每个被接受候选都比当前候选高一个 $\delta$，也不是显著性检验。

第三道是分支成本规则。设分数变化为 $\Delta S$，相对 policy-token 增长为 $\Delta C$。当 $\Delta S>\delta$ 时：

$$
\Delta C\le\beta_0+\beta_1\Delta S.
$$

收益必须支付复杂度增长。若落在噪声带内，论文用另一条规则：

$$
w_s\Delta S-w_c\Delta C+w_n\nu_t(H')>0.
$$

$\nu_t$ 只计算首次进入获胜编辑的特定结构组件类型，不是任意文本新颖度。编码设置取 $w_s=0$，因此微小分数上涨本身不能让候选过关；成本下降或结构探索可以提供额外理由。还必须满足全局分数地板和领域 guard。

第四道是结构剪枝：最近窗口没有正贡献证据的组件进入删除目标，再经后续提议与评测处理。它不是见到一个负分就立刻删掉运行中的模块。

论文用 L0/L1/L2 类比编辑稀疏、结构删除和总体成本抑制；它没有对 harness 参数实施 Lasso/Ridge，也没有给出对应的泛化定理。具体规则比正则化名称更值得移植。

### 3.4 实验证据：训练分数更高，迁移可能更差

**论文报告，Table2 p.9。** 同一个 frozen policy、base 与 evolve set 下：

| 方案 | LAB evolve | LAB ID held-out | 三个 OOD 平均 | 百万 policy tokens/trial |
|---|---:|---:|---:|---:|
| Base | 89.4 | 86.9 | 39.7 | 1.56 |
| 无正则演化 | 92.8 | 88.9 | 40.3 | 3.80 |
| 去掉提议约束 | 90.7 | 88.8 | 41.9 | 2.69 |
| 去掉接受约束 | 91.5 | 88.7 | 41.0 | 3.59 |
| RRSI | 90.5 | 89.2 | 43.6 | 2.42 |

最关键的不是 evolve 最高分，而是 RRSI 放弃部分 evolve-set 增益，得到更高的 OOD 均值。2.42 对 3.80 约少 36.3%，但对原始 base 的 1.56 仍约多 55.1%。这是特定 trial 的 policy-token 统计，不包括全部搜索、分析器与 critic 成本，不能写成总费用下降36%。

主实验冻结 Claude Opus4.8，coding 从 Terminal-Bench2.1 演化后转 SWE-bench Verified；workspace 从 LAB 演化后转 JobBench、GDPval、APEX；engineering 从 EngDesign 转 Frontier-Eng。Figure3 p.8 报告 SWE 82.0→83.8、JobBench36.0→40.7、GDPval48.8→52.3、APEX34.2→37.9、Frontier-Eng17.7→22.0。这些是不同领域的独立演化实例，不是一个 harness 跨所有任务通吃。

附录 E.1 与 Table5 p.23 给 coding/workspace 20轮、engineering40轮，每轮2候选；每任务试跑2/2/4次。Table6 p.24 是按任务配对 bootstrap 的95%区间，Table7 p.25 补一次独立搜索；两次 workspace OOD 平均43.6/43.7。按任务重采样区分了同题重复执行与独立样本，但两次搜索仍不足以描绘广泛的搜索方差。

### 3.5 阅读时需要保留的复现问题

- 摘要称 OOD 最高+4.3，Figure3与Table6的 JobBench为+4.7。采用具体图表，保留原文不一致。
- App D.3说 $w_s,w_c,w_n$ 在Table5中报告，实际该表未列这三项。不能凭空补出可复现配置。
- 按公式使用 $t=0,\dots,T-1$ 且取 ceiling，最终轮通常仍为2，虽然文字称收尾为1。实际实现的索引/终点需另查代码。
- critic 无法保证消除隐性 benchmark 拟合；base 上估计的噪声带也不保证适用于所有新 harness。
- policy tokens 是成本代理，无法覆盖工具等待、网络费用、GPU、人工接受质量等部署目标。

**工程建议。** 先实现原子 diff、可回放评测、历史记录、成本门槛和独立 holdout，再考虑完整的 proposer/critic/pruner 自动闭环。将新机制的收益与额外重试收益分开衡量，比一开始复制全部组件更容易诊断。

## 4. Harness²：无答案时，利用行为对比改当前任务，并积累改进经验

原文：[Harness²: Recursive Agent Harnessing for an Open World](references/Harness_2_Recursive_Agent_Harnessing_for_an_Open_World.pdf)，arXiv2610.14224v1。

### 4.1 两层递归分别改变什么

**论文机制，§2 pp.3–7。** 第一层是 task-level recursion：针对当前任务修改执行 harness。第二层是 harnessing-level recursion：从本次修改过程更新 improvement library，让未来更会修改。

一个特别重要的状态边界：每个新任务都从共同的执行 harness $H_0$ 开始；上一个任务的执行程序不会直接成为下一个任务的起点。跨任务累积的是 improvement harness 中的组件与经验库。模型权重、阶段指令和决策规则固定。

库条目保存可执行 harness 和 EXPERIENCE.md，记录适用情境、观察、机制与证据；索引支持按需查看。它既包含“如何做任务”的部件，也包含“何时采用某种修改”的经验。论文并没有证明其获得了通用元学习能力。

### 4.2 Propose–Probe–Compose 的因果意图与证据边界

**论文机制，§2.2 pp.4–6。**

先执行当前 harness 得参考轨迹，再提出两个范围不同的候选：

- invariant editor 检查跨领域缺陷，如规划、上下文、工具使用和委派；
- domain editor 检查当前领域的知识、程序与约束。

两个候选在相同任务、模型和匹配环境配置下试跑。Compose 读取参考轨迹、候选 diff、各自产物与行为对比，选择有证据的变化，可以合并、修正冲突、只采纳一个，或保持原 harness。组合结果必须再执行，而不是把代码合并成功当作行为验证。

**教学案例。** 原系统一直搜索却未写报告。invariant候选加“剩余预算低于阈值先写产物”的 middleware；domain候选加“财报期间、币种、单位核查”skill。Probe显示前者确实及时落盘，后者减少单位遗漏；Compose才考虑同时保留。两者单独工作不意味着组合一定工作，故必须执行组合版本。

这些轨迹可证明某个机制触发、某个遗漏减少，不能保证报告事实正确。若所有候选都读错原始表头，答案可能一致地错误。没有 ground-truth verifier 不等于没有模型判断，更不等于已解决验证难题。

### 4.3 并行与串行是宽度和深度的选择

**论文机制，§2.2.2 pp.5–6。** 并行方式收集 $k$ 个参考执行、$k$ 个 invariant候选和$k$个domain候选及其 probes，再独立做 $k$ 次composition并执行。每个composition可查看整个候选池，实现的是一轮群体更新，$k$控制宽度。

**根据流程的计算推导。** 单次并行更新有 $k+2k+k=4k$ 次 executor rollout：$k=1$是4次，$k=5$是20次，还不包括editor、composer和selector调用。它不是只跑5次模型。最终需要把这些总成本与交付质量配对比较。

串行方式把前一轮 harness 和累计执行记录传入下一轮。它适合针对真实观察持续纠错，但错误修改也可能沿链传播；并行保留差异，有额外组合复杂度。论文在小范围预算下比较，未证明某一种普遍最优。

$k>1$ 时，selector对匿名产物做选择，不能看到产物来自哪个harness，也不合成新内容。$H^*$ 的星号表示被采纳，不表示外部验证的全局最优。$k=1$直接使用composition后的产物。

### 4.4 可修改的不止是提示词

Figure2 p.3和App D列8类文件：system prompt、guardrails、memory、tool guidance、subagents、skills、scripts、middleware plugin。它们的触发位置不同：常驻上下文每次花token，skill按需读，script经shell调用，middleware在工具调用周围执行。Senior工程判断需要考虑“规则有没有真的进入执行路径”，而非文件里有没有写。

**工程推导。** 确定性转换优先放脚本；必须触发的预算/完成检查放hook；按需领域流程放skill；system prompt保持短。这个位置选择依据论文的组件激活机制，具体取舍尚需在目标系统测量。

### 4.5 实验及限制

**论文报告，Tables1–2 pp.8–9。** Gemini3.5Flash+OpenCode的WorkBuddy平均分72.4→77.5（一步）→80.8（并行$k=5$）；JobBench31.5→36.0→39.0。GLM5+OpenCode的WorkBuddy64.2→75.7→79.6。默认editor是ClaudeOpus4.8，executor冻结。不能把“较小executor超过较强base”理解为纯粹较小模型自行改进。

主表每种方法3次运行，任务顺序打乱；库在每个benchmark流开始时为空，随后在线积累。论文还做同模型兼任editor/executor实验，但属于另外设置。单步不是全部配置最好：Gemini+Codex的LAB，Meta-Harness76.5高于单步75.6。

Table3 p.10在同一$k=1$设置消融：完整方法WorkBuddy77.5/JobBench36.0；去库74.4/34.2；去scoping74.6/32.3；去composition75.9/34.1。三项有贡献，但未证明对任意任务流都存在相同增益。

Figure6 p.10的算力比较包括最终提交前执行与改进token，较适合评估本方法整体代价；主表#Steps不能单独证明总执行便宜。Figure7 p.11的JobBench经验迁移到WorkBuddy，三个领域分别再提升0.6/0.5/2.9分，提供跨任务经验可用的证据。排除每题自己的条目却使用后续任务经验的实验是回顾性复用，不是严格在线结果。

App F p.29承认：额外试跑增加成本；对比受执行随机性与共享偏差影响；不保证正确与迁移。App G将经验库压缩、过期经验更新、适应性预算列为未来工作。不能把这些能力写成已完成机制。

**实际失败案例，Figure14 pp.25–26。** 一次selector面对95、85、85、80、55分的候选，选择了55分产物，理由是表面上更完整朴素；真实评分在事后才可见。另一次演化把按`id()`缓存当作足够方案，自写checker三次通过，隐藏测试却要求等价内容也命中，任务分数75→64。还有PDF填表流程确实验证了33个字段，但这些PDF不属于评分关注的交付，85/132步耗在无关工作上。这些案例分别暴露选择偏差、同源验证盲区和局部目标错位，不应统称为“模型偶尔发挥不好”。

**工程建议。** 用独立workspace、环境快照和只读材料做试跑。真实业务中的重试、建单、发信等有副作用动作必须能隔离或回放，否则多次Probe已改变环境，行为比较不再有效。这是从匹配环境要求推导的部署条件，非论文已经验证的生产保障。

## 5. Evo²：用 harness 演化经验训练“改进系统的人”

原文：[Evo²: Evolving the Evolver through Weight-Harness Co-Evolution](references/Evo_2_Evolving_the_Evolver_through_Weight-Harness_Co-Evolution.pdf)，arXiv2610.13025v1。

### 5.1 两个模型实例不能混淆

**论文机制，§3–4 pp.4–8。** 主实验的任务executor是固定Qwen3.8-27B，FP8、greedy decoding。evolver也从该基座起步，但它承担共享参数的Proposer和Reflector，接受EvoTIDE训练。

因此权重更新发生在演化器，executor保持冻结。名称中的weight-harness共演化是“更好的演化器造更好的harness，harness修改经验再训练演化器”，不是同步微调每条任务轨迹的执行模型。

### 5.2 搜索树和双角色闭环

**论文机制，§3.2 pp.4–5。**

1. 从有不同深度与分数的parent pool取一个harness。
2. Proposer TypeA自主诊断并写初始修改，形成$h_0$，执行外部评测。
3. Reflector读parent/child、diff、分数变化、成功与失败轨迹，选择revise、crossover或keep。
4. revise/crossover时，TypeB Proposer按directive修改，形成$h_1$，再次执行评测；keep不产生额外修改。
5. 候选加入树与pool，有用机制进入策略库，供其他分支适配。

crossover不是直接拼接两个文件。Reflector选donor机制并说明如何接入，TypeB根据recipient代码适配，再用执行评分判断兼容性。

parent pool保留多深度节点、强候选及其他可执行候选，root有固定份额。非root权重为 $\epsilon_p+|\widehat V(h)-0.5|$，故高分和低分节点都获得较高采样机会。意图是同时学增强强系统和修复弱系统；它不是按分数单调增加的“只挑赢家”。见§3.3.3 p.7。

### 5.3 反思质量由后续实现的结果定义

**论文奖励，§3.3.2 p.6。**

$$
r_P=\widehat V(h')-\widehat V(h),\qquad
r_R=\widehat V(h_1)-\widehat V(h_0).
$$

Proposer为自己的编辑增益获得奖励；Reflector为directive被实施后的额外增益获得奖励。keep奖励为0。格式错误、无法应用/启动、无效harness、no-op和无效crossover有惩罚。TypeB另检查是否触及directive指定文件。Reflector的正增益还需要轨迹显示新增机制确实执行，否则增益置0。

**教学推导。** 一段“分析很深刻”的反思若无法转成可执行修改，或改完没有效果，得不到相应执行奖励。这把反思从语言评价转为具有后果的决策。但Reflector奖励仍依赖Proposer的实现能力；它是“在当前搭档条件下有用的建议”，不是建议的纯粹内在正确性。

### 5.4 EvoTIDE：轨迹修复、SFT、交错GRPO

**论文机制，§3.3 pp.5–7。** edit extraction从没有最终edit action的记录中提取具体修改；prefix continuation保留截至最后一次成功应用的编辑的前缀，恢复该编辑之后的中间状态，再重新生成失败后缀。修复结果仍需通过应用、启动和任务评测，不能未经执行就进入成功数据。

先用按执行结果筛选的TypeA、TypeB、Reflector轨迹做平衡SFT。之后在每轮开始冻结当前policy快照作为counterpart：训练Reflector时，冻结快照负责实施directive；训练Proposer时，冻结快照提供所需指令。live policy在两种角色上交错更新，轮末再刷新快照。

冻结搭档减少了同一轮中评估目标不断变化的问题。它不会消除任务采样、执行随机性或跨轮分布漂移。

对同一role prompt采样$G$个回答，论文使用组均值基线：

$$
A_i=r_i-\frac1G\sum_jr_j.
$$

按固定$L_{max}$归一化token loss；截断回答从loss中mask。这里不要自动补成带组内标准差归一化的教科书GRPO公式，也不要自行补出未披露的KL、clip或学习率配置。

### 5.5 实验能支持什么

**论文报告，Table1 p.8。** 使用相同固定executor，完整方法Polyglot82.1（最强baseline62.6），SWE48.3（baseline41.0），LiveCodeBench58.0（baseline56.0）。完整比较同时包含训练过的evolver和不同搜索机制，不能将差值全部归因于某一个组件。

Table5 p.10较接近训练贡献隔离：固定搜索流程、executor和parent harness，untrained/trained evolver在Polyglot61.8/78.0、SWE46.0/51.0。Polyglot标$P=.001$，SWE标$.086$；后者不支持按0.05阈值声称显著。61.8→78.0按显示数相减16.2，表列16.3，可能来自未舍入值；保留其报告口径，不扩大精度。

Table2 p.9有六个跨coding benchmark迁移方向，方法在五个领先；Polyglot→LCB44.0低于DGM/GEA45.0。不要照摘要写“全部迁移第一”。memory实验在LoCoMo演化，转LongMemEval-S，分别60.4 F1与71.5 accuracy；二者是不同指标，不可做分数差解释。

**闭源设置的关键限定，Table3和§4.4 p.9。** GPT5mini和Haiku均固定权重，只运行双角色harness搜索；60题SWE子集、3次搜索。24.4是SICA对照结果，不是原始base；Evo²报告48.3。baseline取top1，Evo²取top2中较优，候选评估机会不一致。因此不能表述为“同一base通过同预算训练从24.4翻倍到48.3”。

Figure3和§4.6 p.10报告最终LCB harness约3.6K executor completion tokens/task、10.2次调用，优于若干更昂贵baseline。它没有计入EvoTIDE训练、搜索和全部评测成本。适合重复部署的离线优化是否摊得回，仍需算账。

**复现限制。** 12页PDF没有完整给出coding discovery/held-out各split规模与划分、训练超参数和统一总预算。本文未审计官方代码，不能补齐缺失参数或断言完全等算力。训练增量奖励也可能学会迎合有限评测器，RRSI式holdout和复杂度控制仍有价值。

## 6. OO-Harness：用程序层次管理特化，再根据运行证据选择

原文：[Object-Oriented Harness: Evolving Agent Harnesses through Object-Oriented Design](references/Object-Oriented_Harness_Evolving_Agent_Harnesses_through_Object-Oriented_Design.pdf)，arXiv2610.28380v1。

### 6.1 为什么更好的全局harness仍可能拖累一部分任务

**论文问题，§1–3 pp.1–5。** 不同任务可能共享某种失败模式，也可能需要冲突的策略。为复杂文档加多轮校验，对简单查找题可能只增加负担；工具错误恢复，对从未报错的任务没有同样价值。

OO-Harness用可执行类层次组织代码：child继承parent的机制，按需override或新增方法。每个节点是完整可执行harness，选择child后在一个实例里执行；不会先运行祖父agent，再运行父agent，最后运行childagent。

**教学伪代码，未执行；用于解释继承，不是论文接口。**

```python
class EvidenceHarness(BaseHarness):
    def before_finish(self, state):
        super().before_finish(state)
        verify_citation_locations(state)

class FinancialTableHarness(EvidenceHarness):
    def before_finish(self, state):
        super().before_finish(state)
        verify_period_and_units(state)
```

把共用行为显式继承，可以减少复制旧代码时遗漏已接受机制的机会。它也引入父类变动影响后代的风险；论文只支持所评测搜索中的收益，不能推为面向对象总比组合好。

### 6.2 task cluster与class tree是两种结构

**论文机制，§3.3–3.4 pp.4–5。** 先用base跑discovery tasks，根据执行需要分簇。簇可以是“未完成必要写入”“过度探索耗尽预算”之类失败模式，而非固定行业分类；也可以自然出现文档、幻灯片、表格等任务类型。

每轮选择目标簇和parent，写subclass，直接在目标簇评测，不经router。候选来源parent不必是当前该簇部署的class。只有目标簇分数严格改善并通过领域接受检查才保留；不要求每个候选提升全体任务。重复拒绝降低簇优先级，簇可根据新轨迹重分配、拆分或合并。

任务簇组织“哪些证据支持改什么”，类树组织“代码如何复用”。两者不必一一对应。执行记录保留成功与失败；design lessons指导修改，routing lessons指导选择。

### 6.3 测试时先跑base，再决定是否使用专门程序

**论文机制，§3.5 p.5。** 冻结类目录与经验；新任务先运行base。router读取任务、可观察base轨迹、class描述与冻结的routing lessons。如果选择base，复用其产物；若选specialist，执行一个专门harness。held-out grader分数、判定和隐藏答案都不提供给router。

因此这是trajectory-informed selection，不是只看用户输入的零执行成本router。所谓训练router，在这里主要是积累指导决策的经验，不是梯度更新router权重。

**工程成本推导。** 完整单任务成本应写为：

$$
C=C_{base}+C_{router}+\mathbf1[\text{specialist}]C_{specialist}.
$$

论文Table1的Steps只统计最终选择的那条轨迹，明确排除其他rollout与辅助选择调用。它不能证明端到端工具调用、token或延迟必然下降。

### 6.4 实验：部分完成分数与全任务成功要同时看

**论文报告，§4、Table1 pp.5–7。** AutomationBench300 discovery/300held-out；Workspace288/100；Toolathlon251/252。executor固定Gemini3.5Flash，evolution使用ClaudeOpus4.8，最多40轮；主结果为3次executor运行均值±标准差。

| benchmark | primary metric | Base | OO-Harness | 绝对变化 |
|---|---|---:|---:|---:|
| AutomationBench | Mean partial credit | 61.62 | 77.41 | +15.79 |
| Workspace-Bench | micro rubric pass | 25.45 | 39.48 | +14.03 |
| Toolathlon-GYM | strict PASS | 31.15 | 37.45 | +6.30 |

同一个Mean词在不同benchmark中含义不同。尤其Workspace的strict PASS只有3.67→8.33；39.48不是完整任务成功率。Toolathlon的Mean71.87→77.18与strict PASS31.15→37.45也不能混用。

Table2 p.7路由消融为单次运行：Automation task-only64.88，加入base轨迹77.52；Workspace40.03/40.56；Toolathlon strict PASS33.33/37.70。轨迹的价值依赖任务：输入要求能揭示文档类型，却不总能预知实际API错误或漏写行为。

Figure5 p.8的独立搜索比较：base-reset29.39、copy-based flat35.60、OO40.56。复用代码有用，继承组织在这次设置更好；但各自进行了独立搜索且单次测试，不能把4.96差值当成纯语言特性的因果收益。

Figure7 p.9构造应用族不重合的OOD49题，OO所有任务回退base，strict PASS保持59.18；Meta-Harness44.90。这里的成功是避免负迁移，不是specialist在OOD获得额外提升，也不是通用OOD检测保证。

**披露边界。** 主文p.6称router为Sonnet5；App A.4.2 pp.14–15列Automation检索/选择默认Sonnet5/Opus4.8，其他router还可用proposer默认值与override。本文不把它们合并成统一router模型。实际复现应检查各benchmark配置。

**工程建议。** 限制层次深度，给父类和后代绑定不可变版本；写清super调用协议与方法输入/输出；base永远保留为可选项；跟踪每类的覆盖、误路由和维护成本。若大量子类只有一行规则，可能更适合配置/组合；这是设计建议，非论文已经做过的比较实验。

**具体迁移陷阱，App B.3 p.20。** 一个已演化的百分比检查会对标签像百分比且数值在0与1之间的单元格建议乘100。它依赖任务要求以百分数数值保存20，而不是以比例0.2配百分比格式。把该规则直接移植到通用表格agent可能制造100倍误差。应该把值、单位和显示格式合起来判断；成功演化出来的检查仍带有适用条件。

## 7. 把四篇放进同一个工程决策中

以下是**基于论文机制的综合建议与未执行实验设计**，不是四篇作者共同提出或已验证的系统。

### 7.1 什么时候优先采用哪一种

- 有可信离线评测，evolve分数涨但部署迁移弱：先用RRSI式编辑纪律、成本门槛与holdout。
- 新任务缺答案，已有可隔离环境并允许额外试跑：试Harness²式对比更新，同时保留事实验证。
- 持续产生大量高质量“修改—执行—反馈”样本，有训练资源：考虑Evo²，训练编辑与诊断能力。
- 任务存在稳定异质性，全局改动互相牵制：考虑OO式specialist目录、共享代码和回退路由。

RRSI控制搜索怎么接受修改，OO控制修改如何组织和适用；两者可以互补。Harness²在线改进若要长期保留，也需要防止经验泄漏、过期与无效扩张。Evo²训练的evolver仍可提出不可靠代码，不能替代程序验证。这些组合目前只是合理实验方向。

### 7.2 最小可验证落地顺序

1. **建立冻结baseline。** 固定模型版本、工具协议、文档解析和随机参数；记录最终产物与完整轨迹。
2. **拆分反馈用途。** discovery/evolve用于改代码，validation用于选择/停止，最终holdout冻结；按文档、机构、仓库、时间等实体分组，避免同源chunk跨集合。
3. **一次只验证一个机制假设。** 如“结束前检查引用是否可定位”，先比原始base与单修改；不要同时换模型、检索、提示和预算。
4. **对照额外计算。** 设置同预算多次base、输出选择、harness修改三组，检验结构改动是否比多跑几次更值。
5. **异质性得到证据后再特化。** 按失败机制组织目录，对比task-only/trajectory-router/总是base/总是specialist。诊断用oracle router只可作为离线上界，不能进入真实部署。
6. **先离线验证经验库与训练数据。** 经验条目绑定代码、模型、工具和来源版本，记录失效条件。样本积累足够再比较固定evolver、SFT、SFT+RL，使用相同搜索评估预算。

这里的金融案例验收可以同时覆盖：出处可定位、数字/单位/期间准确、用户要求覆盖率、全任务通过、平均和尾部成本、失败恢复次数。不能只用“报告更长”“critic说更好”作为业务验收。

### 7.3 成本应按生命周期算

$$
C_{life}=C_{search}+C_{training}+N\,C_{deploy}+C_{maintenance}.
$$

某方法最终每题更省，但前期搜索贵，是否值得取决于部署次数$N$。若新harness每题节省$\Delta c>0$，仅从费用看需要约 $N>(C_{search}+C_{training})/\Delta c$ 才能摊平；质量增益另算。若每题更贵，就要用业务质量价值或节省人工时间证明增量成本合理。这是通用成本推导，没有用论文未披露的美元费用作估计。

## 8. 自测与参考答案

1. **RRSI接受一个涨0.2分的候选，是否违背稳定性原则？** 不必然。先看噪声带、全局地板和对应分支；微小涨分之外可能有成本下降或结构探索价值。
2. **Harness²两个probe得到一致结论，是否证明正确？** 否。它们可能共享错误假设。行为对比只帮助判断修改的后果，事实仍需独立证据。
3. **Evo²训练后的executor为何更强？** 问法应改为“训练后的evolver为何造出更强harness”。主实验executor权重冻结，增强来自它执行了更好的程序。
4. **为什么Reflector不能仅按反思文本打分？** 论文把奖励绑定到directive实施后的增量效果，迫使建议具有可执行后果；但搭档能力仍影响该奖励。
5. **OO的child继承3层，会运行4个agent吗？** 不会。它选择一个完整类实例执行继承方法；测试前base试跑是另一个成本来源。
6. **Workspace39.48是否约四成任务完全完成？** 否，是micro rubric pass；同表strict PASS为8.33。
7. **RRSI和OO能否直接用同一SWE/Workspace数字比较？** 不能。模型、任务、指标和预算不同，必须做共同评测。
8. **什么时候不应该启动更复杂的自演化？** baseline、反馈质量或可重复性还不可靠时。复杂搜索会放大错误信号，先修评测和隔离环境。

本次交付完成PDF下载、版本/页数/哈希登记、正文与关键附录核查、关键表图视觉检查和讲解写作。没有运行模型、训练、API或benchmark复现；示例代码为教学伪代码。

## 9. Harness² 与 DSPy 是否属于同一种思路

补充核查：2026-11-13。DSPy 官方 main 核查提交 `2c07ebbee3a66f6e04b71e141c6c198f1b31a129`，并非对用户已安装版本的检查。

**共同机制。** 二者都可利用执行反馈，提出系统修改，试跑并保留较好的方案。DSPy 是编程/优化框架，不是单一算法；比较时应具体到 BootstrapFewShot、MIPROv2 或 GEPA。GEPA 已包含轨迹反思、候选演化与合并，因此这些要素不是 Harness² 独有的新颖性。见 [优化器说明](https://github.com/stanfordnlp/dspy/blob/2c07ebbee3a66f6e04b71e141c6c198f1b31a129/docs/docs/learn/optimization/optimizers.md)、[GEPA说明](https://github.com/stanfordnlp/dspy/blob/2c07ebbee3a66f6e04b71e141c6c198f1b31a129/docs/docs/api/optimizers/GEPA/overview.md)。

**有意义的区别。** 典型 DSPy compile 使用 program、训练输入、metric，并通过验证数据选择可复用程序；输入可以没有标签，metric仍需提供优化信号。Harness² 的研究设定是在新任务到来时、没有外部正确性标签下，以参考/候选执行的行为对比完成 Propose–Probe–Compose，再把可执行组件及修改经验留给后续任务；下个任务仍从共同H0开始。两者的区别主要是优化时机、反馈组织与状态生命周期，不是“一个自动优化、另一个不会”。Harness² §§2.2–2.3 pp.4–7；Table4 p.19。

**不能绝对化的边界。** 当前 DSPy GEPA 源码已有 `dspy.Flex` 的 code proposer，可替换模块源码，因此“DSPy只能改prompt，Harness²能改代码”不是当前能力事实。见 [固定版本源码](https://github.com/stanfordnlp/dspy/blob/2c07ebbee3a66f6e04b71e141c6c198f1b31a129/dspy/teleprompt/gepa/gepa.py)。DSPy metric也可由规则或模型评判构造；没有标签不是 Harness² 的独占能力。Harness² 的具体贡献在于其无正确性标签的任务流设定与两层更新组合；论文未提供与当前DSPy等搜索空间、等反馈、等总成本的对照，不能由两套系统各自分数判断更强。

**工程推导。** 可以在DSPy程序内部接入类似Harness²的在线适配和经验库，也可以用DSPy优化Harness²某些提示组件；实现组合不代表已经复现论文增益。比较应同时对齐可编辑组件、评测反馈、基础模型、搜索/部署预算及数据隔离。

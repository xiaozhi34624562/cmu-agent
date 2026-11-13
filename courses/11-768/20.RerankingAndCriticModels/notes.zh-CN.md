# CMU 11-768 第 20 课：怎样从多次尝试中得到更可靠的答案

本课官网题目是 **Search 1: Reranking and Critic Models**，讲义封面是 **Search over Trajectories**，授课日期为 2026-11-12。目录里的 `20` 是本仓库的稳定课次编号。本文对应 [31 页主讲义](lecture-20-search-basics.pdf)，页码均为实际 PDF 页序，从 1 开始。

这节课要解决一个很实际的问题：你已经有一个能调用工具、修改代码、执行测试的 LLM Agent，但它一次运行并不总能成功。现在允许多花一些计算，应该让它多跑几次，让另一个模型挑答案，让它反思重做，还是修改控制它的程序？这些办法花的钱和解决的问题并不相同。

下面把你已有的 LLM 开发与 Java 后端经验作为起点。会直接使用“函数、测试、请求、日志、工作目录”这些概念；遇到轨迹概率、奖励模型、强化学习目标时，先解释它们在当前问题里是什么意思。主线沿讲义展开，四篇指定阅读负责补全关键机制，参考文献接在需要它们的地方。文中的 Java 任务和数值推导是教学例子；论文实验与工程建议分别标明。

## 1. 先把目标说清楚：多生成一个答案，为什么可能有用

**讲义主线：PDF 第 2–6 页。** 设想一个 Coding Agent 要修复下面的方法：输入非负 `int n`，返回不大于 `n` 的所有正偶数之和，返回类型为 `long`；负输入须抛出 `IllegalArgumentException`。`n=12` 时，正确结果是 $2+4+6+8+10+12=42$。

同一个模型运行三次，可能提出三种实现：

```java
// A：按定义累加。long 循环变量也避免大 n 时 i += 2 溢出。
static long inclusive(int n) {
    if (n < 0) throw new IllegalArgumentException("n must be nonnegative");
    long sum = 0;
    for (long i = 2; i <= n; i += 2) sum += i;
    return sum;
}

// B：一个常见错误，把“不大于”写成了“小于”。
static long exclusive(int n) {
    long sum = 0;
    for (long i = 2; i < n; i += 2) sum += i;
    return sum;
}

// C：利用 2 + 4 + ... + 2m = m(m + 1)。
static long formula(int n) {
    if (n < 0) throw new IllegalArgumentException("n must be nonnegative");
    long m = n / 2;
    return m * (m + 1);
}
```

A 和 C 在约定输入域内正确，B 在偶数边界上错了，且缺少负输入检查。问题在于：Agent 如果只试 `n=11`，三个实现都输出 30，B 看起来也成功了。即使候选集合里已经有正确实现，最终交付哪个仍是一个独立问题。

完整 Agent 的一次尝试不只是最后的代码字符串。它可能先读需求、搜索代码、修改文件、执行测试，再解释结果。把这串“行动以及行动后观察到的结果”称为一条 **trajectory（轨迹）**；从起点执行出一条轨迹的过程称为一次 **rollout**。一次 rollout 可以包含很多次模型调用。讲义第 4 页的并行采样，是从相同任务和初始环境启动多个这样的尝试，每个尝试得到自己的补丁和运行记录。

由此先区分三个问题：

1. **候选覆盖**：这些尝试里面有没有正确答案？
2. **候选选择**：系统能不能把正确答案选出来？
3. **经验再利用**：已有尝试能不能帮助下一次产生更好的答案？

最后还有一个更外层的问题：这些失败是否说明 Agent 的提示构造、工具接口、上下文管理等程序本身应该修改？本课后半段才进入这一层。

## 2. 多次采样提高的是“有解的机会”，还不是交付成功率

### 2.1 模型为什么会给出不同候选

**讲义第 3 页，概率前提的教学展开。** 模型在每个位置为候选 token 产生分数 $z_i$，称为 logit。采样时把这些分数变成概率：

$$
P(y=i)=\frac{\exp(z_i/T)}{\sum_j\exp(z_j/T)}.
$$

$T>0$ 是 temperature。分母使所有候选概率加起来等于 1。假设只考虑两个 token，它们的 logit 相差 2：$T=1$ 时较高分 token 的概率约为 0.881；$T=2$ 时约为 0.731。升温给较低分 token 更多机会，但没有增加模型知识，也没有保证新路径是有用的路径。

这里的概率发生在**逐个 token 的选择**上。整个程序是否正确，是许多 token、工具行为和环境状态共同作用的结果。不能把某个 token 的高概率直接解释成“这段代码有 90% 概率正确”。

实际服务也不一定允许自由调温。[Claude 文档归档](references/Extended_thinking.html)说明 thinking 模式与预算等接口约束；[固定提交的 DeepSeek-R1 README](references/code/DeepSeek-R1/README.md)在 Usage Recommendations 中推荐温度 0.5–0.7。它们提醒我们核对具体模型和模式，而不是由讲义的“某些推理模型固定温度”推出所有推理 API 都固定为 1。这里讨论的是本课归档版本，不是当前所有服务的调用指南。

### 2.2 用最小概率模型理解 pass@k

**讲义第 5–6 页。** 先只考虑一道固定的题。假设每次从头独立尝试，成功概率都等于 $p$。一次失败概率是 $1-p$；$k$ 次全部失败的概率是 $(1-p)^k$，所以至少一次成功的概率是：

$$
P(\text{至少一个正确候选})=1-(1-p)^k.
$$

若 $p=0.25$，尝试 1、4、16 次的覆盖概率分别为 25%、68.36%、99.00%。这个结果很诱人，但它包含一个关键前提：我们在计算“有没有正确候选”，尚未说明怎么识别它。能直接知道候选真假的理想裁判称为 **oracle**。`pass@k` 常用来描述这种有 oracle 时的候选覆盖上限。

同一个模型不等于“每次都会完全不同”。即使随机数独立，模型也可能反复采到同一种错误方案；这种集中已经体现在较低的 $p$ 和重复候选中。若尝试之间共享不断变化的记忆、互相复制答案、共享被修改的工作目录，条件独立和固定 $p$ 又可能失效。此时不能直接套上式。

还有一个更容易忽略的问题：真实数据集每道题的难度不同。假设两道题的单次成功率分别为 0.1 和 0.9，平均单次成功率是 0.5。每道题采两次，再平均覆盖率，得到 $(0.19+0.99)/2=0.59$；把平均 $p=0.5$ 直接代入则得到 0.75。两者不同。因此，必须先按题计算，再对题平均。

### 2.3 论文里怎样估计 pass@k

[Codex 原始论文 §2.1，PDF 第 3 页](references/Evaluating_Large_Language_Models_Trained_on_Code.pdf#page=3)给出常用估计式。对一道题先独立生成 $n$ 个候选，其中 $c$ 个通过评测，从中不放回地选 $k$ 个：

$$
\widehat{\operatorname{pass@k}}
=1-\frac{\binom{n-c}{k}}{\binom{n}{k}},\qquad k\le n.
$$

$\binom{n}{k}$ 表示从 $n$ 个对象里选 $k$ 个的组合数。分子只从错误候选里选，因此分式是“选到的全错”的比例；若错误候选不足 $k$ 个，该概率为 0。比如 $n=10,c=2,k=3$，估计值是 $1-56/120=53.33\%$。把经验成功率 $c/n=0.2$ 填入 $1-(1-p)^3$ 则是 48.8%。前者对应论文使用的无偏估计方法：如果反复采集这样的 $n$ 个独立候选并计算估计值，其平均不会系统性地高于或低于真实 `pass@k`。单次估计仍有随机误差，后一个简单代入也不能替代前者。

在 [Large Language Monkeys §3–4](readings/Large_Language_Monkeys_Scaling_Inference_Compute_with_Repeated_Sampling.pdf#page=4) 中，多次采样确实让数学、证明、代码任务的覆盖范围扩大。但 [PDF 第 10 页 Figure 7](readings/Large_Language_Monkeys_Scaling_Inference_Compute_with_Repeated_Sampling.pdf#page=10)同时显示：在其 GSM8K、MATH 设置中，oracle 覆盖继续提高时，投票或奖励模型选出的答案已经趋于饱和。不能把蓝色的覆盖率曲线当成真实可交付的最终准确率。

你可以把它理解成 Java 服务里的候选实现池：把 A、B、C 都生产出来，是生成器的能力；能识别 B 的边界错误，是选择器的能力。扩大候选池只完成了前一半。

## 3. 候选不够好时，应该增加怎样的多样性

**讲义第 7–8 页。** “再运行十次”可能得到十个几乎一样的实现。我们真正需要的是在有限预算内探索不同的有效解法，例如循环、数学公式、边界优先验证，或不同的仓库定位路径。这里要区分三个改变对象。

**第一层：改变一次调用怎样采样。** 温度改变 token 分布；[Verbalized Sampling §3–4，PDF 第 3–5 页](references/Verbalized_Sampling_How_to_Mitigate_Mode_Collapse_and_Unlock_LLM_Diversity.pdf#page=3)则让模型显式输出多个候选及其概率描述，试图恢复被偏好训练压缩的输出多样性。它给本课的启发是：请求“若干不同方案及其分布”与连续请求一个最佳答案不同。但模型写下的“概率 0.1”不是自动校准的正确率，也不是底层 token 概率；一次调用里列出五段代码，更不等于五个隔离环境中执行过的 Agent。

**第二层：改变解题模式。** 给某些尝试规定“先验证边界”，给另一些规定“先找调用链”，可能比只改随机种子更有意义。不过 [Mode-Conditioning §3–5，PDF 第 4–10 页](references/Mode-Conditioning_Unlocks_Superior_Test-Time_Scaling.pdf#page=4)研究的核心是先为训练数据区分模式，进行带模式信息的训练，再分配推理采样；模式可以来自已知搜索策略、教师身份，也可以通过训练梯度聚类发现。它不是只改一句提示就保证获得相同收益，论文还讨论了单纯用提示诱导模式的不可靠性。工程上要检查生成结果是否真的进入不同策略，而不是只在开头写了不同口号。

**第三层：改变模型权重。** 这里的强化学习可以先理解为：让模型尝试，根据是否成功给结果一个奖励分数，再调整参数，让有价值的行为更容易出现。所谓分布“锐化”，是概率越来越集中在少数输出上；“熵”则用来量化这种集中程度，熵越大通常意味着分布越分散。我们不必先推导整套 GRPO，就能看懂讲义列出的三项研究在改什么：

- [Rewarding the Unlikely §3–4，PDF 第 2–7 页](references/Rewarding_the_Unlikely_Lifting_GRPO_Beyond_Distribution_Sharpening.pdf#page=2)关注原本低概率的正确轨迹受到不足奖励的问题，重新分配正确样本的训练权重。它不是奖励所有罕见答案，更不奖励罕见的错误。
- [Differential Smoothing §3–4，PDF 第 3–6 页](references/Differential_Smoothing_Mitigates_Sharpening_and_Improves_LLM_Reasoning.pdf#page=3)分别对正确、错误输出的概率分布进行不同处理，目标是保留正确解法的多样性，同时抑制错误。不能简化成“让模型更随机就好”；理论分析还有奖励正确性与约束条件。
- [Maximum Likelihood RL §3–5，PDF 第 3–6 页](references/Maximum_Likelihood_Reinforcement_Learning.pdf#page=3)重新思考训练时对不同难度题目的权重。设题目 $x$ 的成功概率为 $p_\theta(x)$，最大化平均成功率 $\mathbb E_x[p_\theta(x)]$ 与最大化 $\mathbb E_x[\log p_\theta(x)]$ 不同：后者对低成功率题的提升更敏感。该论文用有限采样近似这种目标，实际估计器存在截断阶数等条件，并不是有限样本下精确优化完整最大似然。

最后一个式子里的 $\theta$ 是模型参数，$\mathbb E_x$ 可以读成“按题目分布求平均”，$\log$ 是自然对数。把一题的成功率从 0.1 提升到 0.2，与从 0.8 提升到 0.9，都增加了 0.1；但对应对数增量分别约为 0.693 和 0.118。这个小例子解释了为什么换目标会改变对难题的关注程度，并不意味着有限预算训练一定能找到这些改进。

这些训练方向说明，`pass@1` 提高和大预算 `pass@k` 提高并不必然同步。权重训练可能把质量集中到较少模式，也可能帮助模型跨过原本无解的题。判断时要画出不同 $k$ 的曲线，检查按题的成功分布。这些是阅读对讲义“多样性”问题的补充；本课的推理时选择算法本身不需要先实现这些 RL 训练方法。

## 4. 生成了候选之后，用什么证据判断它

**讲义第 10–12 页。** verifier 是判断候选是否满足要求的机制；critic 更强调评价和指出问题，可以输出分数，也可以输出文字。它们可能由测试程序实现，也可能由模型实现。这里的 critic 是广义评价者，不要求一定实现强化学习中的价值函数。名称里有“验证”不代表一定正确。

### 4.1 从外部事实到模型意见，证据强度会变化

回到 Java 例子，以下反馈不是同一种信息：

| 反馈 | 实际支持什么 | 不能据此断言什么 |
|---|---|---|
| 已知 `n=12` 应为 42，实际运行得到 30 | 发现了一个确定反例 | 还不知道所有缺陷在哪里 |
| 仅运行 `n=11` 得到 30 | 这个输入通过 | 所有边界和溢出都正确 |
| LLM 写测试，测试也期待 `n=12` 为 30 | 模型与自己的错误需求理解一致 | 有独立的正确性证据 |
| LLM 阅读补丁说“看起来正确” | 得到一个预测或意见 | 代码经过执行，更不等于通过完整验收 |
| 两个不同实现对大量输入结果一致 | 获得行为一致性证据 | 两者没有共享同一个错误 |

已知答案的测试、形式化证明检查器是很强的工具，但也有各自的规格边界。测试套件可能覆盖不足、依赖不稳定、预期结果有误；证明检查器保证的是某个形式化命题，命题本身仍可能没有表达真实需求。[Large Language Monkeys §4.2，PDF 第 10–11 页](readings/Large_Language_Monkeys_Scaling_Inference_Compute_with_Repeated_Sampling.pdf#page=10)专门用软件任务说明不完美测试可能产生误判。因此，测试失败时还要区分业务缺陷、测试缺陷和环境故障。

### 4.2 奖励模型怎样把一条轨迹变成一个分数

讲义第 11 页引用 [SWE-Gym §5.1.1，PDF 第 7 页；提示见附录 B.6，第 17 页](references/Training_Software_Engineering_Agents_and_Verifiers_with_SWE-Gym.pdf#page=7)。其 OpenHands outcome reward model 读入任务与完整交互轨迹，训练预测成功标签 `YES` 或失败标签 `NO`。训练数据包含不同来源的成功、失败轨迹，并平衡正负数量。

如果模型在这两个标签上的对数概率分别是 $\ell_Y,\ell_N$，归一化分数为：

$$
s(\tau)=\frac{e^{\ell_Y}}{e^{\ell_Y}+e^{\ell_N}}.
$$

这里 $\tau$ 表示一条轨迹。这个模型在训练时使用了实际结果标签，部署时根据轨迹预测结果。从这种输入形式推导，工程上可以让评价者检查“测试没执行”“异常后直接宣布完成”“只改了复现脚本”等信号；这不表示论文已证明模型总能识别这些具体错误，它也可能被漂亮的说明误导。

分数落在 0–1 之间，不代表已经校准为线上真实成功概率。训练集正负各半，而线上失败率可能不同；新的仓库、测试习惯、轨迹长度也可能不同。校准的意思是：在类似线上数据里，所有打 0.8 分的样本是否约有 80% 真正成功。排名有效与概率校准是两个不同要求。

**Best-of-N** 做的事很简单：先产生 $N$ 个候选，分别算分，返回分数最高的一个：

$$
\hat\tau=\arg\max_{\tau\in\{\tau_1,\ldots,\tau_N\}}s(\tau).
$$

SWE-Gym 的对应实验在 $N=16$ 时，候选覆盖 `pass@16` 为 42.8%，实际最高分候选的成功率 `Best@16` 为 32.0%（同一论文 PDF 第 7 页，指定 32B Agent/verifier 与 OpenHands 设置）。这个差值正是“池中有正确答案，但排序未能选中”的空间；不能把二者混成一个指标。

## 5. 没有可靠裁判时，为什么会想到投票

### 5.1 对最终答案投票，而不是对措辞投票

**讲义第 13 页，Self-Consistency 的机制。** 三条推导写法不同，最后都得到 42；另一条得到 30。如果任务答案能规范化成明确的数字，我们可以把通向相同答案的路径合起来。形式上，答案 $a$ 的概率是所有产生该答案的轨迹概率之和：

$$
P(a\mid x)=\sum_{\tau:\operatorname{answer}(\tau)=a}P(\tau\mid x).
$$

真正枚举所有轨迹做不到，因此 [Self-Consistency §2，PDF 第 2–3 页](references/Self-Consistency_Improves_Chain_of_Thought_Reasoning_in_Language_Models.pdf#page=2)采样多条推导，抽取最后答案，再用频率近似这个总概率。这不是挑模型概率最高的一条推导，也不是要求每一条推导的中间步骤相同。

投票前必须确定“相同答案”如何判断：`42`、`42.0` 在当前任务可归为一类；两个 JSON 对象字段顺序不同也可能等价；两个程序的代码字符串不同则往往无法直接比较。解析失败应单独记录，不能悄悄算作错误类别的多数票。

更根本的限制是，多数意见未必正确。如果输出是 `30,30,42`，覆盖率已经是 100%，多数票仍选错。增加采样可以更准确地估计模型最常给的答案，却不能自动把模型最常给的错误变成正确答案。

### 5.2 从多数票理解 Minimum Bayes Risk

**讲义第 13–14 页；下面公式是依据综述的教学写法。** Minimum Bayes Risk（MBR）不是另一种神秘模型。它问的是：如果把其他候选当作可能的参考，我应该交付哪个候选，才能让平均损失最小？

设 $L(a,b)$ 表示输出 $a$、参考为 $b$ 时的损失。对采到的 $N$ 个候选，使用等权近似：

$$
\hat a=\arg\min_{a\in\{a_1,\ldots,a_N\}}\frac1N\sum_{j=1}^N L(a,a_j).
$$

如果相同答案损失为 0，不同答案为 1，那么出现次数最多的答案与其他候选不一致的次数最少，MBR 就退化成多数票。[From Decoding to Meta-Generation §4.2.2，PDF 第 16–18 页](references/From_Decoding_to_Meta-Generation_Inference-time_Algorithms_for_Large_Language_Models.pdf#page=16)把这类选择放进更广的推理算法框架。这里的候选分布是模型产生的近似参考，不是真实答案分布已经可知。

对于程序，可以比较在一组输入上的执行结果。讲义第 14 页的思路对应 [Natural Language to Code Translation with Execution §3，PDF 第 3 页](references/Natural_Language_to_Code_Translation_with_Execution.pdf#page=3)：两段代码写法不同，但在测试输入上输出相同，就有行为接近的证据。该论文的一种执行损失会在测试集合中存在任一输出不一致时判为不一致。即使不知道正确输出，也能进行这样的候选间比较。

在 Java 例子中，如果只用输入 11，A、B、C 不可区分；加入 12，A、C 成为同一行为组，B 成为另一组。这里 A、C 的一致性提供了选择依据，但若两个候选都把 12 算成 30，多数行为仍错。测试输入的区分能力因此非常重要。结果一致也不表示成本一致：A 的循环次数随 $n$ 增长，C 只做固定次运算；正确性筛选之后，仍可以根据性能要求另作选择。

[AlphaCode §3.2，PDF 第 11–13 页](references/Competition-Level_Code_Generation_with_AlphaCode.pdf#page=11)进一步展示了另一种用法：大量生成，先用题目示例过滤，再按生成输入上的行为聚类，最后从不同大簇中选择有限次提交。它保留跨簇多样性以适应提交预算，不能简化成“只取最大簇的唯一答案”，也不能把它的大规模竞赛计算预算直接移植到交互式 Coding Agent。

## 6. 一个不完美的 verifier，为什么会让收益停在 76%

**讲义第 15 页；以下为同一过程的逐步推导。** 为了看清问题，先用固定的三个参数：

- $p$：生成的候选实际正确的概率；
- $q$：候选正确时，verifier 接受它的概率；
- $r$：候选错误时，verifier 仍接受它的概率，也就是误接受率。

算法最多生成 $k$ 个候选：遇到第一个被接受的候选就返回；如果前面都没被接受，最后直接返回第 $k$ 个。因此 $k=1$ 时就是直接返回一次生成结果。

一次尝试被接受，可能来自两种情况：正确且接受，概率 $pq$；错误却接受，概率 $(1-p)r$。总接受概率是：

$$
a=pq+(1-p)r.
$$

在“已经被接受”的候选中，真正正确的比例为：

$$
P(\text{正确}\mid\text{接受})=\frac{pq}{pq+(1-p)r}.
$$

讲义取 $p=0.25,q=0.95,r=0.10$。可以想象有一大批候选：25% 正确，其中 95% 被接受，贡献 23.75%；75% 错误，其中 10% 被接受，贡献 7.5%。在所有 31.25% 被接受的候选中，正确占 $23.75/31.25=76\%$。

如果不断尝试，最终几乎总能遇到某个被接受的候选。但它有可能是误接受，所以最终成功率趋近 76%，不会随 $k$ 增大而趋近 100%。注意这不是“verifier 准确率为 76%”，而是**在本组生成器和 verifier 参数下，被接受结果的正确率**。

把“最后一个兜底”也考虑进去，有限预算下的准确率是：

$$
S_k=\frac{pq}{a}\bigl[1-(1-a)^{k-1}\bigr]
+p(1-a)^{k-1},\qquad a>0.
$$

前一项对应前 $k-1$ 次内已经接受，后一项对应一直没接受、返回最后一次。若 $a=0$，永远不会提前接受，所以 $S_k=p$。若 $q=1,r=0$，得到完美识别，式子退化为 $1-(1-p)^k$。

这使“下一笔预算投哪里”变得具体：当 $p$ 很低时，多产生候选可能有帮助；候选已经很多但误接受率高时，更应改善 verifier 的证据、测试覆盖和校准。只要求 verifier 更宽松，会提高接受率，却可能恶化最终正确率。只追求拒绝所有东西，则又会退回最后一次兜底。

上述公式假设每次候选独立、$p,q,r$ 固定，不适用于所有 Best-of-N 排名器或会学习的多轮 Agent；它揭示一个机制，不是一条所有搜索系统的通用上限。对应的精确计算与随机模拟已在 [examples.py](examples.py) 中实际运行，结果见 [EXAMPLE_RUN.json](EXAMPLE_RUN.json)。

## 7. 从“挑一个”到“改好一个”：反馈究竟提供了什么

**讲义第 17–20 页。** 以上方法基本在现有候选里做选择。现在让后一次尝试看到前一次的经历，尝试修复错误。

### 7.1 先看一条能发生进步的反馈链

Agent 提交 B，只用输入 11 验证。外部测试运行输入 12，报告 `expected=42, actual=30`。critic 指出：循环条件漏掉偶数上界。下一次 Agent 把 `<` 改成 `<=`，加入 `n=0,1,2,11,12` 的检查。这个过程中新增的有用信息不是一句“请再想想”，而是一个能排除当前假设的反例。

随后 Agent 想优化成公式。若写成下面这样，又会出现新问题：

```java
long answer = (n / 2) * (n / 2 + 1); // 两个操作数还是 int，先溢出，再赋给 long。
```

`n=100000` 时，正确值是 2,500,050,000，但这行得到 -1,794,917,296。把 `m` 先声明为 `long` 才能修复中间乘法。这个例子说明：修复边界并不自动修复溢出；下一轮“更简洁”的实现也可能破坏已经正确的行为。这里两个 Java 错误都已在本机真实编译运行，并非模型预测执行结果。

### 7.2 Reflexion、Self-Refine 和 Self-Debug 各自改变什么

[Reflexion §2，PDF 第 3–4 页](references/Reflexion_Language_Agents_with_Verbal_Reinforcement_Learning.pdf#page=3)把执行、评价与反思分开：actor 完成尝试，evaluator 提供反馈，反思模型把经验写成自然语言，再帮助下一次尝试。所谓“verbal reinforcement learning”在这里主要是通过文字记忆改变后续行为，并不等于每轮都对模型权重做策略梯度更新。该论文不同任务可获得的反馈不同，例如带答案的成败反馈，与开放任务中模型猜测是否成功不能混为一谈。

[Self-Refine §2，PDF 第 2–4 页](references/Self-Refine_Iterative_Refinement_with_Self-Feedback.pdf#page=2)展示同一个模型生成、评价、再修改的循环。自反馈可能引导模型显式检查本来忽略的要求，但没有外部测试时，反馈本身仍是一个模型输出，需要验证。原方法把历次输出和反馈追加进提示，让模型看见此前的修改；这也会逐渐拉长上下文。停止条件也属于算法：固定轮数、模型说无需修改、外部检查通过，会带来不同成本和风险。下一节的 PDR 会进一步处理多分支与有限上下文的矛盾。

[Self-Debug §3，PDF 第 3–4 页](references/Teaching_Large_Language_Models_to_Self-Debug.pdf#page=3)把代码解释、执行信息和错误反馈接入修改过程。其中模型逐行描述程序行为的“trace”，不应一概当成真实运行产生的 trace。你在工程日志里必须区分“模型解释说得到 42”和“命令执行器实际打印 42”。真实 SQL 执行结果、真实单元测试、纯文本解释也有不同的证据强度。

### 7.3 自我修正为什么可能越改越差

[Large Language Models Cannot Self-Correct Reasoning Yet §2–3，PDF 第 2–5 页](references/Large_Language_Models_Cannot_Self-Correct_Reasoning_Yet.pdf#page=2)区分了无外部反馈的 intrinsic self-correction 与借助 oracle 的修正。其特定历史模型和任务实验表明，单纯让模型检查自身推理并不总能带来净提升，错误答案会变对，正确答案也会被改错。标题不是对未来所有模型和所有反馈机制的不可行性证明。

用一个教学计数看净效果：100 题原来答对 60 题；复核后修好了 12 道错题，却改坏了 15 道原本正确的题，最终只有 57 题正确。不能只展示 12 个成功修复案例。至少要同时记录“错→对”和“对→错”，并对比同预算的重新采样。

**由上述机制推导的工程建议：** 保留上一轮补丁与结果，把新旧版本在同一组测试上对照；失败反馈保存实际输入、预期、输出和环境信息；对“语气更有把握但没有新证据”的修改降低信任。保留旧候选也不能保证正确，只是为回退和最终选择留下机会。

## 8. Parallel–Distill–Refine：把多个尝试变成下一轮的有用上下文

**讲义第 21 页；指定阅读 Rethinking Thinking Tokens §3，PDF 第 5–6 页。** 只沿一个答案不断修改，称为 Sequential Refinement（SR，顺序改进），容易困在最初思路里；把所有历史完整塞回去，又会让上下文越来越长。PDR 同时处理这两个问题。

设 $x$ 是任务，$C^{(r-1)}$ 是上一轮留下的有限长度文本，$M_r$ 是本轮候选数。每一轮：

$$
S^{(r)}=\{s_i^{(r)}\leftarrow M_\theta(x,C^{(r-1)})\}_{i=1}^{M_r},
\qquad
C^{(r)}\leftarrow D(x,S^{(r)}),\quad |C^{(r)}|\le\kappa.
$$

$M_\theta$ 是模型，$\theta$ 表示其权重；$D$ 是从本轮候选构造下一轮上下文的操作；$\kappa$ 是文本预算。先 **Parallel** 产生多份候选，再 **Distill** 选取或压缩信息，下一轮据此 **Refine**。原论文的基础推理配置最后一轮只生成一个结果。

这里的 distill 首先是**文本层的提取、选择或压缩**，不是把大模型训练成小模型的知识蒸馏。PDR 推理阶段可以固定权重。论文 §3.3 还另行研究与这一接口一致的训练，那才涉及更新参数；不能因为同一篇论文同时谈训练，就说每次 PDR 总结都修改模型权重。

### 8.1 Java 例子里应该留下什么

第一轮的三个尝试分别发现：A 的循环实现通过小边界；B 的 `<` 在偶数上界失败；C 的公式方向正确，但若用 `int` 中间值则溢出。一个有用的下一轮文本可以是：

```text
已验证：n=11 应为 30，n=12 应为 42；“不大于”包含上界。
可复用思路：令 m=floor(n/2)，数学结果为 m*(m+1)。
已发现错误：int 乘法在 n=100000 时溢出；赋给 long 发生在乘法之后。
待验证：负输入契约、大输入、返回类型；不要声称未运行的测试已经通过。
```

这段是教学设计，并非论文原始 prompt。它有价值，是因为后一次不必重新发现同一个反例，而不是因为它写得简短。若压缩时把“公式的 int 实现溢出”变成“公式不可靠”，就会丢掉正确方法；若把“模型声称通过”变成“已经通过”，又会制造虚假证据。

原论文 [§3.2，PDF 第 6 页](readings/Rethinking_Thinking_Tokens_LLMs_as_Improvement_Operators.pdf#page=6)比较了不同构造方式：全局摘要、选取若干候选原文、随机取少量候选构造多个上下文。摘要节省上下文但可能失真；提取原文保真但更长；不同小集合有机会避免所有分支过早接受同一个错误共识。PDR 的工作区按轮重建，早期全文不持续重放，不能把它描述成跨任务永久累积的记忆数据库。

### 8.2 为什么论文要同时画两种预算

[Rethinking Thinking Tokens §3.1、§4，PDF 第 5 页及第 8–12 页](readings/Rethinking_Thinking_Tokens_LLMs_as_Improvement_Operators.pdf#page=5)区分：

$$
B_{\mathrm{total}}=\sum_{c\in\text{全部调用}}(\mathrm{in}_c+\mathrm{out}_c),
\qquad
B_{\mathrm{seq}}=\sum_{c\in\text{最终接受路径}}(\mathrm{in}_c+\mathrm{out}_c).
$$

前者包含被丢弃分支与摘要调用，作为总计算/成本的代理；后者是接受路径上的 token 量，作为延迟代理。并行生成八份候选，可能缩短相对串行的等待，但总工作量依然存在。`B_seq` 不是实测墙钟时间，更没有包含所有排队、容器、限流、网络和工具耗时。

该阅读的比较要分别看横轴：在总预算受限与可并行、延迟更重要的设置中，优选方案可以不同；一些设置下 SR 的总成本效率更好。论文中的多次评估平均准确率也不能自动解释为把这些评估再做一次多数投票后的准确率。没有一种“并行更快所以一定更省”的结论。

### 8.3 与 Recursive Self-Aggregation 的区别

[Recursive Self-Aggregation §2，PDF 第 3–4 页](references/Recursive_Self-Aggregation_Unlocks_Deep_Thinking_in_Large_Language_Models.pdf#page=3)从一个候选群体中抽取子集，让模型聚合生成新的候选，再反复进行。它强调不同候选之间的信息融合，聚合结果可以是新的答案。它不是下一节那种“每组只留下原有赢家”的淘汰赛。二者都利用候选间关系，但**创造新候选**与**选择旧候选**的错误来源不同：前者可能吸收优点也可能拼出新错误，后者不能创造集合里本来没有的正确答案。

## 9. 真正的 Coding Agent：几百步日志怎样拿来比较和复用

**讲义第 23–25 页；指定阅读 Scaling Test-Time Compute for Agentic Coding。** 短数学答案可以直接投票，长 Agent 轨迹却夹杂文件搜索、失败命令、环境修复和多次改动。最后一句“已修复”几乎没有足够信息；把所有原始日志给裁判，又可能超长、难以比较。

### 9.1 结构化摘要是比较接口，不只是省 token

该阅读 [§2.2–2.4，PDF 第 3–5 页](readings/Scaling_Test-Time_Compute_for_Agentic_Coding.pdf#page=3)为每个 rollout 生成结构化摘要，保留任务要求、关键发现、解决策略、代码改动、执行证据等。讲义第 23 页突出 `key_discoveries` 与 `solution_approach`：前者说明发现了什么，后者说明为什么这样改。

看其 [附录 G 的 SymPy 例子，PDF 第 49–53 页](readings/Scaling_Test-Time_Compute_for_Agentic_Coding.pdf#page=49)。任务是块矩阵计算出现类型错误。看起来都是“零”，但标量 `0` 没有矩阵的行列属性，`ZeroMatrix` 有形状。轨迹逐层追踪后发现，构造处理把一个人为的标量零放到了矩阵加法参数前面；化简时保留了这个标量，而不是矩阵零。候选修复是在没有非矩阵项时，不再插入那个标量。

从 Java 经验理解，这像是两个对象打印都显示 `0`，运行时类型和接口契约却不同：只比较 `toString()`，无法验证调用方随后要访问的结构。摘要若只写“修复零值计算”，就丢掉了导致错误的机制；下一轮很可能在错误层次打补丁。

这份原始轨迹还记录了依赖缺失、复现脚本、不同测试命令及其结果：矩阵表达式测试通过，与更大范围矩阵测试出现失败分别存在。学习时应保留这种区别，不能压成“所有测试通过”。这些是论文里的运行记录，本地本轮没有执行该历史 SymPy 仓库，也没有复现其 benchmark 成绩。

**由该接口推导的实现建议：** 摘要引用原始 `run_id`、补丁哈希、测试命令、返回码与日志位置；将“实际观察”与“Agent 的解释”放在不同字段。比较器需要细节时能回读日志。主论文使用摘要；这里进一步保留可回查指针，是为了减少摘要失真造成的错误传播，不是声称论文已经实证了这套字段设计。

### 9.2 Recursive Tournament Voting 为什么分小组

讲义第 24 页的 RTV 先把候选摘要分成小组，让模型比较每组哪个更可能成功，对同一组多次判断后投票，留下赢家，再递归比较。这样一次判断不用同时处理十六条长轨迹。

若有 16 个候选、每组 2 个、每组判断 8 次，完整二叉淘汰赛有 $8+4+2+1=15$ 次组间比较，共 $15\times8=120$ 个裁判调用，串行依赖为 4 轮。这里 8 个判断可以并行，但它们仍可能共享盲点；八次模型投票不是八份独立事实证据。

淘汰制还有路径依赖：一个正确候选可能在第一轮被错淘汰，后面无法恢复；候选顺序、分组、位置偏好和摘要遗漏都可能改变结果。用更小的组降低单次比较负担，不代表全局最优选择已经有保证。[原论文 §4.2，PDF 第 13–14 页](readings/Scaling_Test-Time_Compute_for_Agentic_Coding.pdf#page=13)也分别观察剩余候选的平均成功率与覆盖率：筛选可以提高平均质量，同时丢掉一些题唯一的正确候选。

### 9.3 把选择和再生成接起来

完整流程是：

```text
同一初始任务
  → N 个隔离环境中的独立 rollout
  → 每条生成结构化摘要
  → RTV 选择 K 份摘要
  → N 个重新初始化的环境，读取选中经验后重新尝试
  → 再次摘要与 RTV
  → 选中一条实际 rollout 及其补丁
```

来源是 [原论文 §2.5，PDF 第 5 页](readings/Scaling_Test-Time_Compute_for_Agentic_Coding.pdf#page=5)。下一轮是**新初始化的环境加文字经验**，不是默认继承上一轮文件系统、工具进程或未提交补丁。论文把复用持久工作产物列为后续方向；因此实现时不能一边共享目录，一边声称复现了隔离 rollout 设置。

### 9.4 认真读讲义第 25 页的表：它没有报告最终交付准确率

表中是 **100 个 SWE-bench 任务，在最终选择之前的平均 rollout 成功率**。以表中的 Claude-4.5-Sonnet 设置为例：初始 69.87%；使用单条经验后 70.87%；随机选多条摘要后 75.06%；选择多条摘要后 78.06%。它支持的是：在该消融设置中，多条经验有帮助，先选择经验进一步有帮助。78.06% 不能被写成完整系统最终选择出的成功率。[讲义第 25 页](lecture-20-search-basics.pdf#page=25)与[阅读 Table 1，PDF 第 8 页](readings/Scaling_Test-Time_Compute_for_Agentic_Coding.pdf#page=8)使用同一口径。

主实验的最终结果在阅读另一个表中，任务集合和阶段也不同，不能与这个 100 题消融表混拼。更值得理解的是 [§4.1，PDF 第 10–12 页](readings/Scaling_Test-Time_Compute_for_Agentic_Coding.pdf#page=10)揭示的两极分化：下一轮有更多题的候选几乎全对，也有一些本来有正确候选的题变成 0/16。结合摘要质量分组，作者将这种现象与选中经验的质量联系起来；不同难度的题也可能落在不同分组，不能把分组相关性单独当成排除了难度影响的因果实验。平均单次成功率提升，不保证覆盖率提升，更不保证每道题都改善。

因此，在自己的系统里至少同时观察：初始覆盖、初始平均质量、选中经验质量、下一轮覆盖、下一轮平均质量、最终选择成功率。还要保存每题的变化，才能发现总体平均掩盖的退步。

## 10. 反复失败的是同一种流程时，开始搜索 harness

**讲义第 27–29 页。** 如果 Agent 每次都忘记边界测试，不一定要无限重复同样的流程。可以改变包裹模型的程序：怎样组装提示、选择示例、调用工具、限制步数、保存状态、解析结果。这个程序就是本课语境中的 **harness**。

对于 Java 后端开发者，可以把它看成围绕模型服务的编排代码：模型是被调用的能力组件，harness 决定请求和反馈如何流动。改提示构造、工具适配器和结果解析器会改变系统行为，但不会自动修改模型参数。

### 10.1 先读一个小到能看懂的真实 harness

讲义链接的[固定提交 fewshot_memory.py](references/code/meta-harness/reference_examples/text_classification/agents/fewshot_memory.py)是分类基线，不是 Coding Agent。代码存储已经获得标签的例子；预测时抽取一部分示例，构造 prompt，调用模型，再解析标签；状态可以导出并恢复。`learn_from_batch` 在这里是把已标注例子加入存储，并没有反向传播。

这个小程序已经包含值得搜索的决定：用多少示例、怎样抽样、上下文怎样截断、标签怎样解析。固定文件中 `MAX_CHARS` 实际为 30,000，注释里的近似描述与此不完全一致；执行行为应以代码为准。字符预算也不是 token 预算，返回的存储示例数量不等于当前 prompt 实际注入数量。它说明观察 harness 时，不能只看类名叫“memory”就推断它做了复杂学习。

把它迁移到 Java 例子，等价的可编辑设计可能是：先从契约生成边界清单，再请求补丁，调用隔离测试执行器，最后要求报告未覆盖的情况。这是基于课程概念的工程设计，原始 few-shot 文件不包含这些步骤。

### 10.2 Meta-Harness 把“改程序”本身放进闭环

[Meta-Harness §3，PDF 第 4–5 页](readings/Meta-Harness_End-to-End_Optimization_of_Model_Harnesses.pdf#page=4)使用一个 proposer（提出修改的 Coding Agent），读取过去候选 harness 的代码、执行轨迹和分数，提出新程序，验证接口后运行评测，把结果再次保存到文件系统。

关键不只是“用模型写 prompt”，而是历史证据可查询。完整历史可能远超一个上下文窗口，所以 proposer 通过文件搜索和读取选择相关记录，而不是把所有历史一次塞进 prompt。某个提示改动使平均分下降时，可以追查哪些任务和哪些执行步骤变坏，再考虑保留有用部分。

这里至少有三个不同的状态：

1. 一次任务内的轨迹和工作目录；
2. harness 自己维护、按评测协议重置或更新的状态；
3. 外层搜索保存的候选代码与历史评测库。

把它们混为“记忆”，很容易造成数据泄漏或复现实验失败。例如不能让评测题的真实标签在预测之前进入示例存储；外层评测反复提供的反馈也会影响程序选择，即使基础模型权重完全冻结。

### 10.3 高分程序是否真的泛化

[Meta-Harness §4，PDF 第 6–9 页](readings/Meta-Harness_End-to-End_Optimization_of_Model_Harnesses.pdf#page=6)包含分类、数学、TerminalBench-2 等不同设置，不能把它们描述成同一种留出协议。分类和数学包含留出评估；TerminalBench-2 一节明确使用同一基准进行搜索与评估。后者的高分说明该基准上的搜索结果，不能直接充当未见任务泛化证明。

**工程建议，依据该阅读的搜索与评测机制：** 将搜索集、用于决策的验证集、只在最后使用的测试集分开；按仓库、题型或时间划分，避免同一个缺陷的近似复制跨集合。记录搜索了多少候选、选择了多少次、用了多少总调用和人工调整。反复看测试分数再选程序，测试集事实上就参与了开发。

阅读 [附录 D，PDF 第 24–25 页](readings/Meta-Harness_End-to-End_Optimization_of_Model_Harnesses.pdf#page=24)还有很实用的实施经验：先准备可靠基线与有区分力的小评测集；日志格式可查询；昂贵评测前检查导入、实例化和小样例；把评测放在 proposer 之外。论文明确把这些称为工程经验，而非每条都单独验证过的科学结论。

### 10.4 几种“自我改进”改的不是同一个对象

讲义第 29 页和相关参考，把范围扩展到权重与框架共同变化：

| 方法 | 更新对象 | 怎样继承经验 | 本课要分清的边界 |
|---|---|---|---|
| PDR | 当前任务候选与文本上下文 | 本轮候选提取/摘要 | 推理版本可冻结权重，按轮文本不等于永久记忆 |
| Meta-Harness | 模型外围可执行程序 | 历史代码、分数、轨迹文件 | 基础模型固定仍可能对搜索集过拟合 |
| WHALE | harness 与模型权重交替更新 | 当前 harness 下的成功轨迹用于训练，再搜索程序 | 不是对整个 Python 程序端到端反向传播 |
| Darwin Gödel Machine | Agent 的可执行代码 | 从归档中的候选继续演化，保留潜在跳板 | 基础模型冻结；实测改进不等于形式化证明 |
| Group-Evolving Agents | 多个 Agent 的框架代码 | 共享成功与失败、轨迹和代码修改经验 | 共享经验不是共享梯度或自动合并权重 |

[WHALE §3，PDF 第 3–5 页](references/WHALE_A_Simple_Recipe_for_Joint_Harness-Weight_Optimization.pdf#page=3)交替进行权重训练与 harness 搜索：程序固定时，从成功轨迹做训练；权重固定时，再寻找更合适的程序。一次阶段变了，另一阶段的输入分布也会变，因此评测时还要分别观察“只换程序”“只换权重”“两者都换”。这张表解释机制，不把其全部成绩等同于严格未见测试上的泛化结论。

[Darwin Gödel Machine §2–3，PDF 第 3–5 页](references/Darwin_Gödel_Machine_Open-Ended_Evolution_of_Self-Improving_Agents.pdf#page=3)保留一组历史 Agent，允许从不一定当前最高分的候选继续演化。原因是暂时退步的结构可能成为后续改进的跳板。“Gödel”这个名称不意味着每次代码修改都附带数学正确性证明；它主要依靠实际任务评测。

这类程序改进也有具体形态：该论文 [PDF 第 7–8 页](references/Darwin_Gödel_Machine_Open-Ended_Evolution_of_Self-Improving_Agents.pdf#page=7)描述了按行查看文件、字符串替换式编辑、生成多个补丁再选择等变化。它们改变 Agent 怎样使用已有模型能力，并不要求模型先重新学习 Java 或 Python 语法。

[Group-Evolving Agents §3，PDF 第 3–5 页](references/Group-Evolving_Agents_Open-Ended_Self-Improvement_via_Experience_Sharing.pdf#page=3)让一组 Agent 交换成功和失败经验，候选选择考虑性能与行为新颖性。新颖性用不同任务上的解题行为描述，而不只是代码字符串差异。一个程序把所有函数改名，不会因此成为有价值的新解题能力。

这些方法把优化对象从单个答案移到长期复用的系统。它们与“让这次回答再想一分钟”需要不同的数据隔离、版本记录和成本衡量。是否部署搜索出来的程序，也仍需独立的工程验证。

## 11. 把整节课变成一个能逐步实施的判断过程

**讲义第 30 页的预算问题，下面是基于前述机制的工程展开。** 先在一个固定任务集上跑单次基线，保存代码版本、模型版本、初始状态、候选产物、执行日志和成本。然后多采几次，分别测覆盖与最终选择准确率，再决定下一步。

| 观察到的现象 | 优先调查什么 | 值得尝试的改变 |
|---|---|---|
| 多采样仍几乎没有正确候选 | 任务是否可解、工具是否缺失、输入是否错误、策略是否重复 | 改善生成能力、可用信息或策略分配；不要只换排序器 |
| 池里有解，最终却经常选错 | verifier 是否只读自述、测试是否无区分力、摘要是否遗漏反例 | 加强独立证据、比较和校准，再评估更大 $N$ |
| 反思经常把正确改成错误 | 反馈是否提供新信息、停止规则、旧版本是否保留 | 记录转移矩阵，保留候选，加入实际反例 |
| 下一轮所有分支都犯同一错误 | 是否共享错误摘要或被一个方案过早锁定 | 保留分歧、构造不同小上下文，检查信息出处 |
| 同类流程缺陷反复出现 | 提示、工具、状态、解析等 harness 的责任 | 受控修改程序并做留出评测 |
| 分数提升但延迟或费用失控 | 总调用、关键路径、工具耗时、失败重试 | 同时比较质量、总成本与墙钟时间 |

### 11.1 一个渐进实现顺序

先做 4 个独立候选和确定性测试，把 `pass@4` 与真实选中结果分开。这一步能判断有没有生成与选择的差距。

离线评估时还要把开发反馈与最终判分分开：Agent 可以读取开发测试，最终覆盖和选择准确率使用预先保留的验收测试或独立人工审查来判定。这些验收证据不能在生成和选择时提前泄漏进去；也要注明它们仍只是所定义验收范围内的 oracle。

接着固定同一批候选，比较随机选择、测试过滤、模型评分或行为投票。候选池固定，才更容易把差异归因于选择器。给每个候选独立环境与固定测试，避免一个候选修改另一个候选运行的代码。

如果错误反馈足够具体，再增加一轮修改，并与同样总预算的重新采样比较；统计错→对、对→错以及按题覆盖变化。这里不应该只比较“1 次基础调用”与“16 次生成加很多裁判调用”的最终分数，然后把全部差异归因于精巧流程。

只有在长轨迹比较确实成为瓶颈时，才加入结构化摘要与 RTV；只有在跨任务出现重复流程缺陷时，才考虑外层 harness 搜索。每一步都回答一个可观察的问题，而不是一次把所有论文名都装进系统。

### 11.2 成本要算完整，也要量真正的等待时间

一个简单的记账方式是：

$$
C_{\mathrm{total}}=C_{\mathrm{rollout}}+C_{\mathrm{summary}}
+C_{\mathrm{judge}}+C_{\mathrm{tools}}+C_{\mathrm{retry}}.
$$

不同模型和工具的单价可能不同，所以它是成本分项，不是简单把所有 token 当作同价。墙钟时间还取决于并发限制、最长分支、测试运行、组间串行依赖与排队。PDR 的理论 token 代理只能帮助理解结构，生产实验仍应实际计时。

例如 16 个候选做二叉 RTV，8 票一组，选到 1 个需要 120 次裁判调用；先选到 4 个只需淘汰 12 个，需 96 次调用。若两轮流程都需要摘要、最后再选一次，不能只把“32 次 Agent rollout”写成全部费用。这个计数假设不重试、不缓存、每对只留一个，属于教学计算，不是论文实现的账单复现。

### 11.3 实验应该怎样设计，才知道真的学到了什么

以下实验尚未执行，作为实现后的验证设计：保留同一任务集、相同初始仓库、相同模型及工具版本；记录随机性；将候选生产成本与选择成本都计入。对比单次、同预算独立重试、独立重试加选择、单分支反馈修改、PDR，以及 PDR 加 RTV。按题报告覆盖、平均候选质量、选中成功率和退步数量，同时报告费用、延迟分位数、环境失败和解析失败。

若比较不同 judge，尽量让它们看到同一候选与同一证据，而不是一个判断自己容易的候选，另一个判断另一模型更难的候选。[Agentic Coding 原论文 PDF 第 14 页](readings/Scaling_Test-Time_Compute_for_Agentic_Coding.pdf#page=14)专门提醒其不同 judge 的原始组间准确率不构成这种受控对比。

最后再换仓库、换题型或改变预算测试泛化。一个方法在数学短答案上有利，不代表能原样用于修改文件、运行进程和涉及副作用的 Agent。

### 11.4 为什么下一课才进入树搜索

本课主要从起点生成完整轨迹，或让下一轮根据整段经验重新开始。[Tree Search for Language Model Agents §3，PDF 第 4–6 页](references/Tree_Search_for_Language_Model_Agents.pdf#page=4)则把中途状态作为搜索节点，为多个行动分支打分，维护待探索集合，再选择值得继续的状态。它是下一课的桥梁。

该阅读 [§5.4，PDF 第 11 页](references/Tree_Search_for_Language_Model_Agents.pdf#page=11)通过重置环境并重放行动序列实现回溯，也明确指出普通网页后退不足以恢复输入框、滚动等状态。由此推广到工具工程，“返回上一个节点”不能只改一条 Python 列表：文件写入和外部请求也可能已经改变世界，需要可恢复快照、受控重放或避免不可逆副作用。本文不把整套树搜索算法提前展开；先掌握候选、选择、反馈、状态与预算，才能理解为什么树搜索多了状态恢复这一层难题。

## 12. 自测：能解释这些问题，就掌握了本课的关键判断

**题 1。** 一个系统的 `pass@16=90%`，是否可以宣称它交付的答案有 90% 正确？

**答案。** 不可以。这说明在评测 oracle 判断下，16 个候选至少有一个正确的题目比例为 90%。实际交付还取决于选择器，必须另测选中答案的成功率。

**题 2。** Java 的三个实现只在 `n=11` 上运行并都输出 30，为什么不足以支持一致性选择？补哪种输入最直接？

**答案。** 当前输入没有区分 `<` 与 `<=` 的行为。增加偶数边界，例如 `n=12`，会得到 42、30、42。还应独立检查 0、小边界、负输入契约和大数溢出；多数一致仍不等于完整证明。

**题 3。** `long answer = (n / 2) * (n / 2 + 1)` 为什么仍会溢出？

**答案。** 乘法两边都是 `int`，先按 `int` 计算，再把已经错误的结果赋给 `long`。让中间操作数先成为 `long`，例如 `long m = n / 2; return m * (m + 1);`。对本例非负 `int` 输入，上界结果也在 `long` 范围内。

**题 4。** $p=0.25,q=0.95,r=0.10$ 时，95% 的正确答案都会被接受，为什么不断重试后仍只有 76% 左右正确？

**答案。** 因为错误候选占 75%，其中 10% 也会被接受。“正确且被接受”的概率为 0.2375，“错误但被接受”的概率为 0.075，所以被接受结果的正确比例为 $0.2375/(0.2375+0.075)=0.76$。95% 是在“候选已正确”条件下的接受率，不是接受结果的正确率。

**题 5。** PDR 里的 distill 与训练蒸馏有什么不同？下一轮是否自动接着上一轮的文件系统运行？

**答案。** 本课的基础 PDR 把候选变成有限长度文本上下文，权重可以不变；训练是原论文另一部分。Agentic Coding 的对应实现启动新环境，只带入选中的摘要，不自动继承文件系统。若要保留工作产物，需要另外设计状态复用协议。

**题 6。** 讲义第 25 页的 78.06 应该怎样描述？

**答案。** 它是该 100 题消融设置中，使用选择后的多条摘要进行下一轮生成、在最终选择之前的平均 rollout 成功率。不能叫完整系统最终准确率，也不能拿它和另一任务集的最终表格直接比较。

**题 7。** PDR 后平均候选成功率提高，但有更多题的 16 个候选全错，这矛盾吗？

**答案。** 不矛盾。一些题从少量成功变为几乎全对，抬高平均值；另一些题的正确候选被淘汰或错误摘要被传播，变为全错。平均质量与按题覆盖衡量不同方面，要分别记录。

**题 8。** Meta-Harness 没有更新模型权重，为什么仍可能过拟合？

**答案。** 多轮查看同一批题的结果，再据此修改和选择程序，已经把评测信息用于优化。程序、提示、检索策略、特殊分支都能适应该集合；是否更新权重不是判断数据泄漏或泛化的充分条件。

**题 9。** 八票选一个候选，与运行八份独立测试有什么区别？

**答案。** 八次判断可以降低某些采样随机性，但可能读同一份错误摘要、共享同一知识盲点。独立测试则应有明确的输入、预期与真实执行结果，也仍受测试覆盖约束。不能把投票次数当成独立事实证据数量。

**题 10。** 这一篇里的哪些结果实际运行过？

**答案。** 本地运行了组合数估计、固定错误率 verifier 的概率公式及随机模拟、合成反例计数，以及 Java 边界/溢出例子的编译执行。未运行 LLM、API、GPU、SWE-bench、TerminalBench、官方 harness 或历史 SymPy 实验。论文数据来自固定归档正文，PDR/RTV/harness 的工程实验方案仍未执行。

## 13. 来源地图与复查入口

以下不是要求先读完所有论文才开始学习，而是说明本文每一组解释由哪份材料支撑。主讲义决定顺序；指定 Readings 是四条主线的深入阅读；References 补概念、对照或实现。版本、来源 URL、取得或复用信息与 SHA-256 见 [REFERENCES.json](REFERENCES.json) 和 [SOURCES.md](SOURCES.md)。页段用于回查本文采用的机制与结论，不代表其余附录均逐页精读。

| 材料 | 本文作用与实际页段 | 使用边界 |
|---|---|---|
| [Large Language Monkeys: Scaling Inference Compute with Repeated Sampling](readings/Large_Language_Monkeys_Scaling_Inference_Compute_with_Repeated_Sampling.pdf) | §2、§4–6：PDF 4–12，采样覆盖、选择瓶颈、测试不完美 | 历史任务和模型；oracle 覆盖不等于最终准确率 |
| [Rethinking Thinking Tokens: LLMs as Improvement Operators](readings/Rethinking_Thinking_Tokens_LLMs_as_Improvement_Operators.pdf) | §8：PDF 2、5–12，有限上下文、PDR、两种预算、训练接口 | 文本蒸馏与参数更新分开；token 延迟代理不是实测时间 |
| [Scaling Test-Time Compute for Agentic Coding](readings/Scaling_Test-Time_Compute_for_Agentic_Coding.pdf) | §9、§11：PDF 3–15、49–53，摘要、RTV、PDR、消融与真实轨迹 | 阶段/任务集不能混用；论文执行记录不是本地复现 |
| [Meta-Harness: End-to-End Optimization of Model Harnesses](readings/Meta-Harness_End-to-End_Optimization_of_Model_Harnesses.pdf) | §10：PDF 2–10、24–25，文件历史、程序搜索、评测协议 | TerminalBench 同基准搜索评估；工程经验非独立因果实证 |
| [Evaluating Large Language Models Trained on Code](references/Evaluating_Large_Language_Models_Trained_on_Code.pdf) | §2：PDF 2–7，pass@k 估计与温度/采样关系 | 2021 论文，不是当前 Codex 产品能力说明 |
| [Verbalized Sampling: How to Mitigate Mode Collapse and Unlock LLM Diversity](references/Verbalized_Sampling_How_to_Mitigate_Mode_Collapse_and_Unlock_LLM_Diversity.pdf) | §3：PDF 3–5，分布式提示与多样性机制 | 口述概率不等于校准概率；同次列举不等于独立环境 |
| [Mode-Conditioning Unlocks Superior Test-Time Scaling](references/Mode-Conditioning_Unlocks_Superior_Test-Time_Scaling.pdf) | §3：PDF 4–12，模式覆盖、条件训练与自动模式发现 | 训练后的模式控制不能简化成通用 prompt 技巧 |
| [Rewarding the Unlikely: Lifting GRPO Beyond Distribution Sharpening](references/Rewarding_the_Unlikely_Lifting_GRPO_Beyond_Distribution_Sharpening.pdf) | §3：PDF 2–7，低概率正确轨迹与分布锐化 | 不奖励罕见错误；形式化任务与训练超参有条件 |
| [Differential Smoothing Mitigates Sharpening and Improves LLM Reasoning](references/Differential_Smoothing_Mitigates_Sharpening_and_Improves_LLM_Reasoning.pdf) | §3：PDF 2–6，正确/错误分布差异处理 | 不是无条件提高熵；依赖奖励质量 |
| [Maximum Likelihood Reinforcement Learning](references/Maximum_Likelihood_Reinforcement_Learning.pdf) | §3：PDF 2–6，平均奖励与似然目标差异 | 有限采样为截断目标估计；没有本地训练复现 |
| [Training Software Engineering Agents and Verifiers with SWE-Gym](references/Training_Software_Engineering_Agents_and_Verifiers_with_SWE-Gym.pdf) | §4：PDF 6–7、17–18，轨迹评分、标签概率与候选覆盖差距 | 训练平衡分布不自动带来线上校准；采样数 N=8 的图文数值有差异，本文只使用一致的 N=16 数值 |
| [Self-Consistency Improves Chain of Thought Reasoning in Language Models](references/Self-Consistency_Improves_Chain_of_Thought_Reasoning_in_Language_Models.pdf) | §5：PDF 2–3，对答案边缘化和投票 | 不是对推理文字投票；共享错误仍在 |
| [From Decoding to Meta-Generation: Inference-time Algorithms for Large Language Models](references/From_Decoding_to_Meta-Generation_Inference-time_Algorithms_for_Large_Language_Models.pdf) | §5：PDF 16–18，MBR 与候选选择框架 | 本文另行展开最小损失公式，未照搬抽取异常的符号 |
| [Natural Language to Code Translation with Execution](references/Natural_Language_to_Code_Translation_with_Execution.pdf) | §5：PDF 2–3，执行行为作为候选间损失 | 输入行为一致不等于已有正确输出 |
| [Competition-Level Code Generation with AlphaCode](references/Competition-Level_Code_Generation_with_AlphaCode.pdf) | §5：PDF 11–13，过滤、行为聚类与跨簇提交 | 大规模竞赛预算不直接外推到交互服务 |
| [Reflexion: Language Agents with Verbal Reinforcement Learning](references/Reflexion_Language_Agents_with_Verbal_Reinforcement_Learning.pdf) | §7：PDF 3–4、6，执行—评价—文字反思 | 文字记忆不是权重 RL；任务反馈条件不同 |
| [Self-Refine: Iterative Refinement with Self-Feedback](references/Self-Refine_Iterative_Refinement_with_Self-Feedback.pdf) | §7：PDF 2–4、9，自反馈、历史追加与迭代修改 | 自反馈不是外部正确性证明 |
| [Teaching Large Language Models to Self-Debug](references/Teaching_Large_Language_Models_to_Self-Debug.pdf) | §7：PDF 3–4，解释、执行信息、反馈 | 模型生成的解释 trace 与执行器 trace 分开 |
| [Large Language Models Cannot Self-Correct Reasoning Yet](references/Large_Language_Models_Cannot_Self-Correct_Reasoning_Yet.pdf) | §7：PDF 2–5，intrinsic/oracle 区分、正确改错 | 特定历史实验，不是所有未来模型的不可能定理 |
| [Recursive Self-Aggregation Unlocks Deep Thinking in Large Language Models](references/Recursive_Self-Aggregation_Unlocks_Deep_Thinking_in_Large_Language_Models.pdf) | §8：PDF 2–4，子集聚合产生新群体 | 生成新答案不等于 RTV 从旧答案里淘汰选择 |
| [WHALE: A Simple Recipe for Joint Harness-Weight Optimization](references/WHALE_A_Simple_Recipe_for_Joint_Harness-Weight_Optimization.pdf) | §10：PDF 3–5，权重/程序交替优化 | 不是对程序端到端求梯度；本文不混报不同评测阶段成绩 |
| [Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents](references/Darwin_Gödel_Machine_Open-Ended_Evolution_of_Self-Improving_Agents.pdf) | §10：PDF 3–8，候选归档、代码演化与工具改进 | 经验评测非形式化证明；外层搜索框架与基础模型不等同于被改代码 |
| [Group-Evolving Agents: Open-Ended Self-Improvement via Experience Sharing](references/Group-Evolving_Agents_Open-Ended_Self-Improvement_via_Experience_Sharing.pdf) | §10：PDF 3–5，群体经验与行为新颖性 | 经验共享不等于权重合并 |
| [Tree Search for Language Model Agents](references/Tree_Search_for_Language_Model_Agents.pdf) | §11：PDF 3–6、11，中间状态分支、搜索与环境重放 | 作为下课衔接；向其他工具的副作用恢复推广是工程推导 |
| [Extended thinking](references/Extended_thinking.html) | §2，归档文档中的模式与预算约束 | 不将某个版本的 API 参数限制推广到全部推理模型 |
| [DeepSeek-R1 usage recommendations](references/code/DeepSeek-R1/README.md) | §2，固定提交的 Usage Recommendations | 特定模型和提交的推荐，不是普遍最优温度 |
| [Meta-Harness fewshot baseline](references/code/meta-harness/reference_examples/text_classification/agents/fewshot_memory.py) | §10，完整固定代码的存储、构造、调用、解析与状态恢复 | 实际常量优先于注释；未执行官方模型调用 |

本地轻量例子可用 `python3 examples.py --output EXAMPLE_RUN.json` 重跑，需要 Python 3 和 JDK。运行脚本只验证本文标出的数值、合成反例与 Java 行为；它不验证论文结论，也不替代真实 Agent 评测。当前内容审核状态与最终文件校验值由课程 [REVIEW.json](../REVIEW.json) 统一登记。

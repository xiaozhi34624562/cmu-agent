# 第 9 周：模型演化（二）——把反馈变成训练，把训练接回系统

本课对应官网 **Week 9，2026-11-04，Model evolution 2**。本地材料是 19 页的 `lec6 - rl in practice.pdf`，教程标题页（PDF 第 2 页）使用 **Lecture 6: RL and Self-Distillation in Practice**。Week、PDF Lecture 编号和目录编号是不同的标识。本篇以这份讲义为主线，再接上本周三篇指定阅读中的自博弈。下文页码均为 PDF 文件从 1 开始的实际页序。

你已经做过 LLM 应用和 Java 后端，可以把这一课的起点放在一个熟悉的地方：请求进来，模型生成代码，测试给出结果。但这里还要多走一步——**下一次遇到类似请求时，模型为何会改变行为？究竟改了哪些状态？** 把报错放进下一轮 prompt，只改变当前请求的上下文；运行训练更新，才改变模型参数。两者都可能改善结果，成本、影响范围和验证方式却很不同。

贯穿本篇的是一个小任务：生成 `sum_even(n)`，返回从 0 到非负整数 `n` **包含端点**的所有偶数之和。对于 `n=4`，正确结果是 6。模型写成 `range(n)` 时会漏掉端点，得到 2。这个例子足够小，能让我们看清“失败了”“为什么失败”“该提高哪个 token 的概率”“如何验证改进”之间的区别。它是教学案例，不是论文的复现实验，也不表示真实代码训练只需要这几个测试。

阅读顺序如下。先理解训练信号，再看系统执行，最后看如何自动产生下一轮学习题目。

| 讲义位置 | 核心问题 | 本文对应部分 |
|---|---|---|
| pp.1–3 | 课程定位与本次教程的问题 | 本节 |
| p.4 | 一个完成结果怎样变成参数更新？ | 第 1–3 节 |
| pp.5–7、12–14 | 教师概率和额外上下文怎样提供更细的反馈？ | 第 4–6 节 |
| pp.8–11 | 数据、参数、显存和 batch 怎样流动？ | 第 7–9 节 |
| pp.15–17 | 怎样判断训练是否正常，并落实到 verl？ | 第 10–11 节 |
| pp.18–19 | 怎样把部署、观察和学习连接起来？ | 第 13 节 |
| 本周 Readings | 题目和监督是否也能由系统产生？ | 第 12 节：AZR、R-Zero、PSV |

## 1. 先把“模型会学习”拆成可观察的东西

**讲义主线：p.4；下面的小函数是教学展开。** LLM 并不是直接挑选一段完整代码。给定提示和已经生成的 token，它对下一个 token 给出概率，再从中采样。把模型写作 $\pi_\theta$：$\theta$ 是模型参数，$\pi$ 强调它是一套“在当前状态下怎样选择动作”的策略。

对于一次生成：

- 输入 $x$ 是函数要求；状态 $s_t=(x,y_{<t})$ 是要求加上已经生成的前缀。
- 动作 $a_t=y_t$ 是下一个 token。动作不限于工具调用；生成一个括号或数字也算一步。
- 轨迹 $y=(y_1,\ldots,y_T)$ 是整段输出。多轮 Agent 则还包括工具调用、观察和后续回答。
- 奖励 $R(x,y)$ 是外部评价。例如运行预先规定的测试，全部通过记 1，否则记 0。

训练需要把外部评价接到可微分的模型输出上。**可微分**的意思是：能计算某个参数稍微改变时，目标量会怎样变化。测试执行器通常不可微分；它只告诉我们结果，不会给出“第 37 层第 102 个参数应增加多少”。策略梯度正是连接两者的方法。

先给两个训练词一个落点。SFT（supervised fine-tuning，监督微调）拿到示范答案，逐 token 提高示范内容的概率；RL（reinforcement learning，强化学习）让模型先尝试，再利用结果反馈调整选择。一次从策略采样到完成输出或交互的过程称为 rollout。后文的 PPO（proximal policy optimization，近端策略优化）和 GRPO（group relative policy optimization，组相对策略优化）都是把反馈变成策略更新的具体方法。

先看模型内部的最小接口。它为候选 token 计算一组实数 $z_v$，称为 logits；再通过 softmax 变成概率：

$$
p_v=\frac{e^{z_v}}{\sum_u e^{z_u}}.
$$

这里 $v,u$ 遍历词表。提高一个 logit，会提高相应 token 的概率，也会改变其他 token 的概率，因为所有概率必须加起来等于 1。因此“奖励某个 token”是调整整个分布，不能理解为独立修改一个字的计数。

一段输出的概率，是各步条件概率的乘积；取对数后变成求和：

$$
\log\pi_\theta(y\mid x)
=\sum_{t=1}^T\log\pi_\theta(y_t\mid x,y_{<t}).
$$

后文的 `log_prob` 就是这些对数概率。使用对数既便于计算，也避免很多小概率相乘造成数值下溢。只保存最终输出文本不足以重建一次训练：还需要 token、有效位置掩码、生成时的策略版本，以及与这些 token 对齐的概率和反馈。

掩码 mask 可以先理解为与 token 对齐的一串 0/1：1 表示这处属于要学习的模型动作，0 表示填充位置或不参与该项损失的位置。前向计算产生概率与 loss；反向传播沿计算图求各参数对 loss 的影响；优化器才真正修改参数。一次前向评分本身不会把反馈学进权重。

Java 服务经验在这里很有用：一个训练样本也应有清楚的数据契约。不过，“一批响应”不是一个可以随意重新排序的字符串列表。同一道题的多个回答要保持组身份，反馈要绑定到生成它的版本，工具返回文本不能误当成模型亲自选择的动作来更新。后面会看到，这些关联错误会直接改变优化目标。

## 2. Reward、advantage、loss：三个不能混用的量

**讲义：p.4；机制补充见 [DeepSeekMath，PDF pp.11、13–14](references/DeepSeekMath_Pushing_the_Limits_of_Mathematical_Reasoning_in_Open_Language_Models.pdf#page=13)。**

奖励回答的是“这次结果怎样”。但同样得到 0.5 分，在大家都得到 0 分的题目上可能不错，在大家都得到 1 分的题目上则偏差。**优势 advantage** 回答的是“相对当前比较基准，这个选择好多少”。**损失 loss** 是优化器实际最小化的表达式，它把优势接到模型概率上。

### 2.1 用四个回答算出一次 GRPO 信号

对同一个 `sum_even` 要求生成四个回答，其中两个通过测试，两个失败：

$$
(R_1,R_2,R_3,R_4)=(1,0,0,1).
$$

平均奖励是 $\bar R=0.5$。为便于手算，暂用总体标准差 $\sigma=0.5$，即各奖励偏离均值的平方先取平均，再开平方。GRPO 的一种常见形式是：

$$
A_i=\frac{R_i-\bar R}{\sigma+\epsilon},
$$

$\epsilon$ 是防止除以零的小数。忽略它时，四个优势是 $(1,-1,-1,1)$。通过的回答得到正信号，失败的得到负信号。这里的组是“**同一道题的多个回答**”，不能把不同题目随意混成一组。

后文用 $G$ 表示组内回答数量，本例 $G=4$；$i$ 标记第几个回答，$t$ 标记回答中的第几个 token。这里和后面的概率公式使用自然对数。

本课 CPU 示例加入 $\epsilon=10^{-6}$，得到约 $\pm0.999998$。固定版本 verl 的 `compute_grpo_outcome_advantage` 使用 `torch.std`，其默认样本标准差以 $G-1$ 而不是 $G$ 作分母；同样四个数会得到约 $\pm0.866024$。两者方向相同、尺度不同。复现时必须匹配实现，不能只说“公式一样”。[固定源码，函数 `compute_grpo_outcome_advantage`](references/verl-ddf7007/core_algos.py)

如果四个回答全错，且奖励都为 0，那么均值也是 0，优势全部为 0。加入 $\epsilon$ 只能避免数值异常，**不能凭空创造正确方向**。四个回答全对时，结果奖励的组内信号也为 0。这解释了为什么过难和过易的题目都可能浪费采样预算，也解释了后文自博弈为什么关心难度。

这个结论限于这里的组相对结果奖励。若另外加入 KL、熵、过程奖励或教师监督，总损失未必没有梯度。单样本组还可能有实现特例，不能把 `rollout.n=1` 当成普通多样本 GRPO 的等价配置。

### 2.2 为什么正优势会让好答案更可能出现？

暂不加入裁剪和 KL，策略梯度常写成下面这个用于求梯度的损失：

$$
L_{\rm PG}(\theta)
=-\frac1G\sum_i\sum_t
\operatorname{stopgrad}(A_{i,t})
\log\pi_\theta(y_{i,t}\mid x,y_{i,<t}).
$$

`stopgrad` 表示本次反向传播把优势当成已算好的数，不沿优势的计算过程继续求导。正优势乘上负的 log probability，最小化损失会推动相应输出的概率升高；负优势则相反。参数更新大致形如 $\theta\leftarrow\theta-\eta\nabla_\theta L$，其中 $\eta$ 是学习率，梯度指示损失增加最快的方向，所以更新取反方向。实际 AdamW 还维护历史统计来调整各参数的步幅。

真正想优化的是“按当前策略反复采样时的平均奖励”，记为 $J(\theta)=\mathbb E_{y\sim\pi_\theta}[R(x,y)]$。$\mathbb E$ 表示按指定分布取平均。策略梯度利用 $\nabla\pi=\pi\nabla\log\pi$，把不可微的执行结果作为权重，乘上可微的 log probability 梯度；上面的 loss 是实现这种估计的代理表达式。为看清方向，这里对 token 直接求和，真实训练还要明确序列/全 batch 的归一化方式，第 10 节会说明它为什么影响长回答。

结果监督 GRPO 通常让同一回答的所有有效输出 token 共用同一个 $A_i$。因此，失败代码中的正确函数名也可能一起收到负信号。长期统计上，成功与失败回答的差异可以帮助学习；但这不是已经识别出了“漏掉 `+1` 才是根因”。**有训练信号不等于完成了精确的因果归责。**

### 2.3 PPO 为什么还要一个 critic？

GRPO 用同题其他回答作比较。PPO 的常见 actor–critic 实现则训练一个价值模型 $V_\psi(s_t)$，预测“从这个前缀继续生成，预计能拿多少回报”。Actor 是生成策略；critic 是估计基准的模型，参数 $\psi$ 与 actor 参数 $\theta$ 分开。

直观上，advantage 是“实际或估计的后续回报减去原先预期”。例如 critic 预测这个前缀成功率约 0.2，而最终通过测试得到 1，就有正的超预期信号。优势估计不必只依赖最终回报，可以把 critic 对后续回报的预测与实际奖励组合；这不改变本课同步流程中“先采样、再更新”的顺序。GAE 把不同长度的估计组合起来。先定义一步预测误差：

$$
\delta_t=r_t+\gamma V_\psi(s_{t+1})-V_\psi(s_t),
\qquad
\hat A_t=\sum_{l\ge0}(\gamma\lambda)^l\delta_{t+l}.
$$

$r_t$ 是当前步奖励，$\gamma$ 控制未来奖励的折扣，$\lambda$ 控制远处预测误差的权重；有限轨迹求和到终止位置，并正确处理终止价值。较长的回报估计较少依赖 critic 的准确性，却通常更嘈杂；较短的估计更依赖 critic。GAE 是这种取舍，不是“逐 token 自动知道谁导致成功”。[GAE，PDF pp.3–5，尤其式 16–19](references/High-Dimensional_Continuous_Control_Using_Generalized_Advantage_Estimation.pdf#page=5)

GRPO 省去这个单独训练的价值模型，减少模型状态和计算，却通常要为每题生成多个回答。不能只比较“少了一个模型”，还要算生成数量、长度以及有区分度的组所占比例。

## 3. Old policy、reference policy 与 PPO clipping

**讲义：pp.4、10–11、14；[PPO，PDF pp.2–4](references/Proximal_Policy_Optimization_Algorithms.pdf#page=3)。** 训练中会同时出现几份模型或概率。先区分它们的职责，公式就不容易混乱。

| 对象 | 用途 | 何时改变 |
|---|---|---|
| 当前 actor $\pi_\theta$ | 正在优化的生成策略 | 每次优化器更新 |
| old / behavior policy $\pi_{\rm old}$ | 产生本批回答的策略，作为概率比的基准 | 下一次采样使用新版本时改变；本批旧概率保持固定 |
| reference policy $\pi_{\rm ref}$ | 约束长期偏离的锚点 | 常在一段训练内冻结；有些算法外层迭代会刷新，要按配置记录 |
| critic $V_\psi$ | 估计价值，帮助计算 advantage | 使用 actor–critic 方法时单独更新 |
| teacher $q$ | 提供希望学生接近的分布 | 可能固定、跟随学生、用 EMA 平滑；第 5 节分别说明 |

同一初始 checkpoint 可以承担多个角色，但起始 checkpoint 相同，不代表职责相同。reference 是“别离某个锚点太远”，teacher 是“朝这个目标学习”；它们不能因为都参与 KL 就混为一个概念。

PPO 用概率比检查当前模型相对生成时改变了多少：

$$
\rho_t(\theta)
=\frac{\pi_\theta(y_t\mid s_t)}{\pi_{\rm old}(y_t\mid s_t)},
\qquad
J_t=\min\left(\rho_t A_t,
\operatorname{clip}(\rho_t,1-\varepsilon,1+\varepsilon)A_t\right).
$$

训练最小化 $-J_t$。设 $\varepsilon=0.2$，可以用下面四个数检查符号：

| 优势 | 概率比 | 未裁剪项 | 最终 $J_t$ | 含义 |
|---:|---:|---:|---:|---|
| $+1$ | 1.5 | 1.5 | 1.2 | 已经把好动作提高很多，再提高不继续获得这项收益 |
| $+1$ | 0.5 | 0.5 | 0.5 | 好动作被降低，仍保留纠正方向 |
| $-1$ | 1.5 | -1.5 | -1.5 | 坏动作被提高，仍保留纠正方向 |
| $-1$ | 0.5 | -0.5 | -0.8 | 已经把坏动作降低很多，不继续奖励这种降低 |

因此，clipping 不是把所有概率强行锁在旧值的 $[0.8,1.2]$ 倍。它是裁剪代理目标中“继续朝有利方向变化”的收益；共享参数、其他样本和其他损失项仍会推动概率改变。必须观察实际 KL、概率比和裁剪比例，不能仅凭设置了 clipping 就认定更新稳定。

reference KL 则比较整个分布与锚点分布的差异：

$$
D_{\rm KL}(p\|q)=\sum_v p_v\log\frac{p_v}{q_v}.
$$

对合法概率分布，完整 KL 非负，分布相同为 0；若目标分布不支持某些有正概率的事件，还可能为无穷大。单个采样 token 的 $\log p_v-\log q_v$ 可以为负，不能把一个 token 的这个数直接当成已经算出的完整 KL。实践中还会使用特定采样估计量，其名称、采样分布和梯度处理都要回查实现。

熵 $H(p)=-\sum_vp_v\log p_v$ 则衡量分布有多分散。提高熵可能保留探索机会，却不保证答案正确；降低熵也可能只是模型更确定地选择了正确答案。讲义提到推理 RL 经常关闭 reference KL，而 RLHF 常保留，这属于实践模式，不是算法定律。DAPO 的长推理训练确实移除了该项，但本课归档的 verl Qwen3 脚本显式开启 `use_kl_loss=True`，系数默认 0.001。应先说清任务和具体配置，再讨论需要多大约束。[DAPO，PDF pp.3–4](references/DAPO_An_Open-Source_LLM_Reinforcement_Learning_System_at_Scale.pdf#page=3)

## 4. OPD：让老师看学生真正会走到的前缀

**讲义：pp.5–6、12–13；机制由 [GKD，PDF pp.3–8](references/On-Policy_Distillation_of_Language_Models_Learning_from_Self-Generated_Mistakes.pdf#page=3) 和 [On-Policy Distillation 的 Method、Implementation](references/On-Policy_Distillation.html) 补充。**

如果只让学生模仿老师生成的完整正确代码，学生主要在“老师常走到的前缀”上学习。部署时学生自己早一步写错，后续前缀就偏离了训练样本。On-policy distillation（OPD）换了顺序：**学生先生成，老师再对学生的同一前缀给出下一个 token 的分布。** 学生在自己实际遇到的状态上获得指导。

这里要区分两条轴：

1. **谁产生前缀**：学生产生的是 on-policy 数据；固定教师答案提供的是另一种前缀分布。
2. **怎样计算监督**：可以用单个目标 token、教师全词表概率，或 top-k 概率加剩余概率质量。

所以“蒸馏一定是离线的”“on-policy 一定是 GRPO”都不成立。GKD 正是把数据来源比例和分布距离分开研究。其 T5 摘要、翻译和算术实验中，最佳 divergence 随任务和解码方式变化，不能从一项实验得出 reverse KL 永远更好。[GKD，PDF pp.5–8]

### 4.1 用两个候选 token 看清 reverse KL 的方向

设在一个固定前缀上，学生对两个候选项的概率是 $(0.5,0.5)$，老师是 $(0.8,0.2)$。把它们想成“正确处理端点”和“漏掉端点”的两个教学候选；真实 tokenizer 不一定把这些语义各编码为一个 token。

讲义采用的局部信号是：

$$
A^{\rm OPD}(v)=\log q(v\mid s)-\log p_\theta(v\mid s).
$$

两个候选分别约为 $\log1.6=0.4700$、$\log0.4=-0.9163$。老师比学生更支持的候选得到正信号，老师较不支持的得到负信号。这些数是相对概率信号，既不是测试分，也不证明某个 token 在语义上必然正确。

在**固定前缀、教师固定**的条件下：

$$
\nabla_\theta D_{\rm KL}(p_\theta\|q)
=-\mathbb E_{v\sim p_\theta}
\left[A^{\rm OPD}(v)\nabla_\theta\log p_\theta(v)\right].
$$

为何没有额外的常数项？对概率求导时出现的 $+1$ 项，乘上 $\nabla p_v$ 后求和为 $\nabla\sum_vp_v=\nabla1=0$。实现采样式代理损失时，$A^{\rm OPD}$ 需要停止梯度；若直接计算完整的可微 KL，则按完整表达式求导，不能又把同一项重复当奖励加一次。

本课 CPU 数值检查直接对两个 logits 求导，得到梯度约 $(-0.346574,0.346574)$，与有限差分的最大差异约 $6.4\times10^{-12}$。取学习率 0.1 更新后，第一个概率从 0.5 变为 0.517322，KL 从 0.223144 降为 0.199731。这验证的是这条**局部数学关系**，不是语言模型能力提升。

有限差分就是把参数分别增加、减少一个很小的量，用 loss 的变化除以参数变化来近似斜率。它提供了一个独立于解析推导的检查方式；真实模型仍会通过自动微分高效计算大量参数的梯度。

### 4.2 为什么“每 token 一个信号”仍有边界？

第一，前缀本身可能已经错了。老师在这个错误前缀后也可能偏好一个逻辑上顺接、却最终错误的答案。OPD 博客的真实例子中，最终错误答案未被强烈惩罚，因为错误已经在更早的决策发生。这提醒我们，teacher likelihood 不是外部正确性证明。[OPD 博客，Illustration]

第二，前面的 token 会改变后面遇到的状态。上面的公式固定了前缀；把每步局部 KL 加起来并忽略采样前缀分布的梯度，**不等于完整序列 KL 的精确梯度**。SDFT 附录 A.1 和 SDPO 附录 B 区分了这种局部估计与考虑未来状态影响的估计。讲义使用局部形式帮助理解，不应把这个简化升级成无条件的数学等价。[SDFT，PDF p.16](references/Self-Distillation_Enables_Continual_Learning.pdf#page=16)；[SDPO，PDF pp.29–32](references/Reinforcement_Learning_via_Self-Distillation.pdf#page=29)

第三，教师前向计算也要付钱。已知学生完整输出后，老师可以并行评分各位置，不必自己逐 token 生成另一条答案；但仍需要教师权重、前向计算和概率数据。全词表分布的存储与通信也可能很大。

讲义 p.6 用 $O(1)$ 与 $O(N)$ “bits” 对照结果反馈和逐 token 反馈，适合作为监督密度的直觉。它不是任意任务都成立的信息量定理，更不能直接推出节省 $N$ 倍算力。OPD 博客的 9–30 倍成本比较还涉及 SFT 曲线外推、是否计入教师生成成本；不能把这些估算写成本课系统的实测收益。

## 5. 自蒸馏：同源模型为什么还能教自己？

**讲义：pp.5、12–13；下面分别回到三篇论文的已归档版本。** 普通 OPD 可以让更大的模型当老师。Self-distillation 则让同源模型因拥有更多信息而形成教师分布。学生看 $x$，老师看 $x$ 加上额外上下文 $c$：

$$
p_\theta(y_t\mid x,y_{<t}),
\qquad q_\phi(y_t\mid x,c,y_{<t}).
$$

这不矛盾。你独立写函数，与已经看到失败测试后重新审视同一段代码，判断能力就不同。额外的信息来自示范、解答或环境反馈，不是由“自己教自己”这句话创造出来的。如果参数、输入、前缀和计算条件都相同，两个分布也相同，蒸馏不会凭空产生新知识。

训练时学生仍只看到普通输入；教师利用 $c$ 评分。训练成功的目标是：测试时拿掉 $c$，学生仍更容易做对。若评估时也给学生标准答案，就把学习效果与答案泄漏混在一起了。

### 5.1 三种额外信息，对应三种学习条件

| 方法及归档版本 | 教师多看什么 | 学生学什么 | 论文实际实现中的重要区别 |
|---|---|---|---|
| SDFT，2601.19897v2 | 专家示范；知识任务中还有原文与答案 | 吸收新技能或知识，同时尽量保留已有能力 | 默认教师使用学生参数的 EMA；实践部分选 forward KL，不应只照理论段落写 reverse KL |
| OPSD，2601.18734v3 | 数学问题的参考解答 | 把带答案时的推理判断转移到不带答案的学生 | 实验冻结初始教师；使用全词表 forward KL；学生 TM-off、教师 TM-on |
| SDPO，2601.20802v2 | 环境反馈，例如错误输出，也可包含组内成功解答 | 从自己的尝试及反馈中修正策略 | 教师需要稳定化；无反馈实验用 JSD / top-100，代码 rich-feedback 与测试时训练用 reverse KL / top-20，均保留 tail |

来源位置：[SDFT，PDF pp.3–4、17–21](references/Self-Distillation_Enables_Continual_Learning.pdf#page=4)；[OPSD，PDF pp.4–9、13–15](references/Self-Distilled_Reasoner_On-Policy_Self-Distillation_for_Large_Language_Models.pdf#page=6)；[SDPO，PDF pp.4–6、10–13、31、42–43](references/Reinforcement_Learning_via_Self-Distillation.pdf#page=42)。讲义采用 reverse KL 和同模型加上下文来统一介绍直觉；论文实现并不完全相同，这些区别会影响真正训练时的梯度和稳定性。

表中的 TM 是 thinking mode，即模型通过提示模板开启或关闭的思考模式；它不是换了模型大小。rich feedback 表示包含错误细节等内容的反馈，区别于单一分数。JSD 是 Jensen–Shannon divergence（JS 散度），tail 是未逐项保留的剩余 token 概率质量。

forward KL 指 $D_{\rm KL}(q_{\rm teacher}\|p_{\rm student})$，reverse KL 指相反方向。前者按照老师的概率加权误差，鼓励学生覆盖老师支持的候选；后者按照学生概率加权，重点处理学生实际会给高概率的候选。JSD 则通过混合分布度量两者差异。方向选择要看容量、任务和稳定性，不能仅凭“哪个更像 RL”决定。

EMA 是指数移动平均：每次把教师参数更新为 $\phi\leftarrow(1-\alpha)\phi+\alpha\theta$，其中 $\alpha$ 较小时教师变化较慢。它既跟随学生获得的新能力，又减小教师目标瞬间变化的幅度。**EMA 更新不等于反向传播进入教师**：当前一步仍把教师输出视为固定监督，之后才单独更新其参数。SDFT p.17 的消融中，直接用当前学生作为教师不稳定，固定初始教师又较弱；这提供了使用 EMA 的实证理由，而不是证明任何任务都该用 EMA。

OPSD 的 pointwise clipping 也不要与第 3 节的 PPO clipping 混淆。前者限制分布匹配中极端的逐 token / 词表贡献，后者裁剪相对旧策略的概率比代理目标。名称相似，所裁剪的对象不同。[OPSD，PDF pp.5、7–8]

### 5.2 把 SDPO 放回小函数例子

假设学生写出 `range(n)`，测试执行器返回“`n=4`，期望 6，实际 2”。纯结果 RL 可以把这段回答记为 0 分。自蒸馏则把反馈放入教师上下文，**仍在学生原先生成的各个前缀上评分**。教师看到端点错误后，可能提高包含端点的代码候选概率。这不是必须先生成一份完整修复答案，再把修复答案作为 SFT 标签。

如果另外一条学生回答恰好通过测试，也可以把它作为教师的示范。SDPO 的消融把“环境输出”“组内成功解答”“原始尝试”分开：环境输出和成功解答有互补作用；把整段原始尝试都塞进 reprompt 有时反而让教师过于依附原方案，降低多样性。[SDPO，PDF pp.12–13，Table 6]

top-k 蒸馏的作用是缩小要处理的概率向量，不是只保留 k 个 token 后假装概率总和仍为 1。SDPO 把其余 token 合并为 tail 类别，以保留剩余概率质量。不同方法的 top-k 选取方向和重归一化方式也可能不同，不能直接交换实现。

### 5.3 读实验时，先问“省了什么、保住了什么”

SDFT 的知识与技能实验支持较好的学习—遗忘取舍，但不是从此不会遗忘。例如其 p.22 Science Q&A 表中，旧任务平均分从初始 65.5 变为 SDFT 的 64.5；SFT 为 53.4。合理结论是该设置下 SDFT 保留得更好，不是所有旧能力逐项不降。论文还报告相对 SFT 的额外 rollout 成本，并提醒模型可能学到“根据上文”等教师上下文痕迹。[SDFT，PDF pp.9–11、22]

OPSD 的主实验给学生每题 1 条、上限 1024 token 的 rollout，而 GRPO 每题 8 条、上限 16000 token；二者有效问题 batch 一样，不等于生成预算一样。Table 2 的 OPSD 和 GRPO checkpoint 搜索步数也不同，评估使用 Avg@12。它说明所报告训练配方的效率与效果，不能直接解释为“相同所有条件下，换掉 loss 就必然获得同样收益”。[OPSD，PDF pp.6–7、13–14]

Avg@12 是多次采样正确率的平均；pass@k 问的是 k 次尝试中至少一次成功的概率。它们不是同一个指标：十次里只对一次，对平均正确率贡献 10%，对这十次“是否至少成功过”则是成功。greedy 是每步取最高概率 token 的解码策略，也与随机采样多次不同。后文看到这些指标时，都要连同预算一起读。

SDPO 在代码实验中把同一组 LCBv6 问题的测试划分用于训练反馈和验证，因此这里的表现不能描述成“完全未见过题目的泛化”。Table 5 的其他任务才用于观察保留能力。其测试时训练实验又是另一种协议：对单个难题不断尝试并更新权重，使用 discovery@k 衡量 k 次尝试内找到解的概率。作者筛选了 19 个 hard 和 9 个 very-hard 问题，结果只支持该筛选和预算下的结论。[SDPO，PDF pp.8–9、12、14–15]

“on-policy 往往更少遗忘”还有 [RL’s Razor](references/RL_s_Razor_Why_Online_Reinforcement_Learning_Forgets_Less.pdf) 的实证支持，但应保留其边界：论文比较了特定 LLM、机器人和简化分类任务；理论使用有限输出空间、可表示策略族及其他条件。其简化实验中，使用理想标签分布的 SFT 甚至优于 RL。对工程更有用的结论是：观察更新后的分布偏离和旧任务表现，而不是把算法名称当作免遗忘保证。[PDF pp.3–8]

## 6. RL 与蒸馏可以结合：反馈有两个用途

**讲义 p.7 的 OpenClaw-RL 案例；补充以 [OpenClaw-RL v2，PDF pp.5–16](references/OpenClaw-RL_Train_Any_Agent_Simply_by_Talking.pdf#page=5) 为准。** 用户或环境的下一条信息，可能同时告诉系统“这次不好”和“下一次具体应怎么改”。前者适合转成结果或过程分数，后者可以放入教师上下文形成蒸馏信号。

对小函数而言，`FAIL` 只有评价；“漏算了右端点，`n=4` 应为 6”还带有方向。一个混合训练目标可以由结果奖励的策略损失与反馈蒸馏损失加权组成。这是理解讲义的抽象；OpenClaw-RL v2 的实际方法进一步区分可评价的交互与有明确指导内容的交互，使用 PRM（process reward model，过程奖励模型）评分、提示选择和 log-probability-difference clipping，并不是把每一条聊天无条件加入训练。

为什么还要选择 hint（从反馈提取的提示）？有的反馈改变了话题，有的只要求语气，有的本身错误。把不适合当前生成前缀的 hint 强行当教师上下文，会得到非常极端的概率差。论文用教师与学生 top-k 分布的重叠帮助选择 hint，并限制过大概率差；这与 PPO 相对旧策略的 ratio clipping 仍是两件事。[PDF pp.7–9、13–14]

系统还把 serving、rollout、judging、training 分开执行。这里可以借用后端经验：请求可以继续被处理，评分和训练在旁路工作，但每份反馈必须能追溯到请求、策略版本和正确的交互步骤。异步不代表没有版本滞后，也不代表可以丢掉状态关联。

论文个人偏好实验 Table 3 中约 10.3 个 session 的数字，来自模拟用户、特定模型和三类偏好设置下的平均结果，不是对真实用户十轮聊天就能可靠学会任何偏好的承诺。部分一般 Agent 实验呈现训练集或训练滚动表现，也应与独立测试集指标分开。作者在结尾明确讨论错误或恶意反馈污染、个性化信息进入权重等限制。因此，“没有另找一个更大的蒸馏老师”也不等于“没有评判模型、没有数据治理成本”。[PDF pp.9–12、16]

## 7. 一个训练循环里，数据和参数怎样移动？

**讲义 pp.8、10、12、16；[HybridFlow，PDF pp.3–8](references/HybridFlow_A_Flexible_and_Efficient_RLHF_Framework.pdf#page=3) 补系统机制。** 可以把一个同步训练周期理解为下列数据流，但不要把所有箭头都理解成复制一份完整模型。

```text
题目 batch + 策略版本 k
  → rollout 引擎生成多条回答，记录 token / mask / 采样概率
  → 执行测试或评分，得到 reward；可选保存详细反馈
  → 计算 old/ref logprob、critic value 或 teacher distribution
  → 计算 advantage / distillation loss
  → 训练引擎分批前向、反向、优化器更新
  → 得到版本 k+1，保存 checkpoint，并把权重同步给 rollout 引擎
  → 下一批采样
```

这是教学流程图；可并行的阶段、概率是否重算、缓存如何存放，要由实际实现决定。reward 可以来自规则执行器，不一定是神经网络；GRPO 没有独立 critic；关闭 reference KL 时可能不需 reference 前向；自蒸馏则要增加带特权上下文的教师评分。

rollout 通常交给 vLLM、SGLang 等生成引擎，训练交给 FSDP 或 Megatron 等训练后端。原因不是模块名称不同，而是工作负载不同：生成要按新 token 逐步推进，关注 KV cache、并发和长尾；训练已知整条序列，需要保存或重算激活、反向传播，并维护优化器状态。相同参数可以采用不同的分片布局。

HybridFlow 把“模型之间的数据依赖”与“每个模型内部的分布式计算”分开。外层控制器表达先生成、再评分、再更新；内层 worker 处理 collective communication 和具体 GPU 计算。训练转生成时还要做参数重分片，不能只发一句“切换模式”就假定两边权重一致。论文的 3D-HybridEngine 是特定设计，不能据此推定任意 verl 配置都零复制或零通信。

从服务状态角度，需要保留三类不同东西：

| 状态 | 例子 | 作用与生命周期 |
|---|---|---|
| 本批经验 | token、组 ID、行为版本、reward、反馈、mask | 用于当前更新及定位训练问题；旧数据是否继续使用由算法规定 |
| 学习状态 | actor、critic、教师 EMA、优化器状态、随机数状态 | 决定恢复训练后是否真正在延续同一次过程 |
| 发布状态 | 服务当前模型版本、候选版本、评估结果 | 决定下一次用户请求究竟用了哪个版本 |

只导出推理权重足以部署某个模型，却通常不够精确恢复训练；只写下“step=100”也不足以知道实际服务已经切到哪个模型。这是从后端版本管理通往训练系统最直接的连接。

## 8. 为什么推理能放下，训练却 OOM？

**讲义 p.9 的数量级估计；[ZeRO，PDF pp.7–10](references/ZeRO_Memory_Optimizations_Toward_Training_Trillion_Parameter_Models.pdf#page=7)、[FSDP，PDF pp.3–7](references/PyTorch_FSDP_Experiences_on_Scaling_Fully_Sharded_Data_Parallel.pdf#page=3)、[PagedAttention，PDF pp.3–5](references/Efficient_Memory_Management_for_Large_Language_Model_Serving_with_PagedAttention.pdf#page=3) 补原理。**

### 8.1 先分清权重、激活和 KV cache

权重是模型长期学习到的参数；激活是这一批输入经过各层时产生的中间结果，反向传播会用到；KV cache 是生成过程中保存的历史 token 的 key/value，避免每生成一个新 token 都重算全部历史。它们不是同一种缓存，不能通过“清理 KV”解决所有训练显存问题。

在 attention 中，可以把 query 理解为当前要寻找的信息，key 帮助匹配历史位置，value 提供被聚合的内容；head 是并行计算的一组这类表示。GQA 让多个 query heads 共享较少的 KV heads，所以估算 cache 时要数 KV heads，不能直接填 query heads。OOM 是 out of memory，即内存分配失败。

讲义以约 8.2B 参数、每参数 2 bytes 的权重估计推理权重约 16.4 GB。这里 GB 使用十进制 $10^9$ bytes；显卡工具显示 GiB 时数字会不同。推理还需 KV cache、临时工作空间和运行时内存，因此 16.4 GB 不是完整服务最低显存保证。

对于普通 attention / GQA 架构，一个未分片、未压缩的 KV cache 可粗估为：

$$
\text{KV bytes}
\approx B_{\rm live}L\times2\times N_{\rm layer}
\times N_{\rm KVhead}\times d_{\rm head}\times b.
$$

$B_{\rm live}$ 是同时保留 cache 的序列数，$L$ 是平均已有 token 数，2 表示 key 和 value，$b$ 是每元素字节数。示意配置取 36 层、8 个 KV heads、head dimension 128、2 bytes，得到每 token 147456 bytes，约 0.15 MB。100 条各 4096 token 的独立序列就约 60.4 GB KV。共享前缀、分页、分片、量化会改变实际占用；不同模型结构也不能照抄该式的参数。

PagedAttention 用逻辑块到物理块的映射管理 KV，减少按最大长度预留和碎片造成的浪费，并支持适合的共享。它不会让已生成且仍需访问的所有 KV 在逻辑上消失。调大 rollout 数量或最大长度，仍可能把显存吃满。

### 8.2 训练的“16 bytes/参数”从哪里来？

讲义采用一种常见的混合精度 Adam 状态账本：低精度权重 2 bytes、梯度 2 bytes、FP32 主权重 4 bytes、Adam 一阶统计 4 bytes、二阶统计 4 bytes，共 16 bytes。于是 8.2B 参数约需 131.2 GB **模型训练状态**，还没计激活、通信 buffer、临时空间及其他模型。

这是一种配置下的估算，不能当作所有 BF16、优化器、LoRA、量化或 FSDP 实现的固定常数。比如实际梯度精度、是否单独保留主权重、哪些参数可训练，都会改变账本。

FSDP（fully sharded data parallel，完全分片的数据并行）的核心做法是让不同设备长期保留不同的参数、梯度与优化器状态分片。某层计算前通过 all-gather 临时收齐需要的参数，计算后释放其他分片；反向后通过 reduce-scatter 聚合并分配梯度。它依然为本地输入计算完整相关层，并不等同于 tensor parallel 把每个矩阵乘法拆开。

在理想的 8 路完全分片下，131.2/8=16.4 GB 是平均模型状态的示意值，**不是每卡峰值显存**。完整的当前 FSDP unit、激活、通信重叠 buffer，以及共置的其他模型都会占空间。unit 太大，峰值高；切得太小，通信次数增多。梯度累积若选择暂不通信，还可能保留未分片梯度而增加内存。[FSDP，PDF pp.3–7]

遇到 OOM 应先看发生阶段。生成阶段优先查活动序列、prompt/response 长度与 KV；反向阶段查 micro-batch、激活、重计算与分片；参数切换阶段查临时完整权重和副本是否释放。直接把总 batch 一路缩小，可能既没找到原因，又改变了学习行为。

## 9. Batch、mini-batch、micro-batch 是三个不同问题

**讲义 p.11 的算例。** 设每轮取 $B=1024$ 道题，每题生成 $n=5$ 条回答，训练数据共 5120 条。一次优化器更新使用 $M=256$ 道题对应的 1280 条回答，那么本轮共有 $B/M=4$ 次优化器更新。

若训练侧有 $D=8$ 个数据并行 worker，每个 worker 在一次更新中处理 $1280/8=160$ 条回答。若每次只放得下 $m=4$ 条，那么要累积 $160/4=40$ 个 micro-batch 的梯度，再执行一次 `optimizer.step()`。

$$
\underbrace{1024\times5}_{5120\text{ 条/采样批}}
\quad\longrightarrow\quad
\underbrace{256\times5}_{1280\text{ 条/更新}}
\quad\longrightarrow\quad
\underbrace{1280/8}_{160\text{ 条/worker}}
\quad\longrightarrow\quad
\underbrace{160/4}_{40\text{ 次累积}}.
$$

micro-batch 主要解决单次计算能否放入显存；mini-batch 决定多久更新一次参数；rollout batch 决定从哪批策略产生多少经验。若保持总有效 batch 不变且正确归一化，缩小 micro-batch、增大累积次数可近似保留同一次更新的目标，但通信、浮点运算顺序和吞吐仍可能变化。

两条工程边界尤其重要：

1. 上面的 8 是**训练的数据并行度**。若 8 张卡还分了 tensor / pipeline / sequence parallel，不能直接把物理 GPU 数代入。生成侧 tensor parallel=2 也不自动等于训练侧数据并行度为 4。
2. 讲义固定 `m=4` 是教学算例。归档的 `run_qwen3_8b_fsdp.sh` 当前内容采用 `use_dynamic_bsz=True` 和 token 上限，实际 micro-batch 会随长度变化，不能宣称该脚本默认恰好执行 40 次累积。[固定脚本](references/verl-ddf7007/run_qwen3_8b_fsdp.sh)

第一块 mini-batch 开始时，当前参数与采样参数相同；更新一次后，后面的 mini-batch 仍来自旧策略。讲义借此强调“严格当前分布”的区别。PPO 仍常被归类为 on-policy 方法，因为它主要使用最近策略采集的数据并控制有限复用；不能仅凭一轮内第二次更新就把它与任意历史经验回放算法完全等同。

最后，`global_step`、优化器 step 和 epoch 也要分开。一个外层采样周期可能包含多次优化器更新；epoch 表示遍历数据集的轮次。比较“训练了 100 step”前，先确认双方 step 的单位，否则既无法比较采样成本，也无法比较学习进度。

## 10. 六条训练曲线，要联合解释

**讲义 p.15。** 该页展示的是公开 verl DAPO 基线中 Qwen2.5-Math-7B / AIME24 的示例曲线，不是本篇运行的实验。图的价值是教我们把指标连起来看，而不是记住一组“健康数值”。

| 指标 | 能告诉我们什么 | 需要一起查看什么 |
|---|---|---|
| 训练 reward | 在当前训练样本和评分规则下表现怎样 | 独立验证、奖励解析成功率、题目难度是否变化 |
| validation accuracy | 在规定评估协议下是否进步 | 采样温度、预算、数据隔离、checkpoint 选择方式 |
| entropy | 输出分布是否逐渐集中或变得混乱 | 正确率、重复率、组内奖励方差；并非越大越好 |
| response length | 生成成本和推理行为是否变化 | 截断率、正确回答长度、无意义重复，而非只看平均值 |
| update KL / PPO KL | 相邻策略变化的程度 | old/reference/teacher 究竟比较谁、估计方式与分位数 |
| gradient norm | 一次更新的整体梯度尺度 | clipping 比例、异常值、loss 归一化、是否有有效 token |

讲义图中的 `actor/ppo_kl` 不应直接称作相对初始 reference 的长期 KL；图上约 $10^{-4}$ 的量级也不是所有模型都该遵守的阈值。批大小、词表、有效 token 数和算法都会影响曲线尺度。

用小函数任务来诊断三个常见现象：

**训练分数上升，隐藏测试不动。** 先检查是否记住可见输入、利用输出提取漏洞，或题目生成器越来越偏向容易题。假设只有 `n=5` 的测试，错误的 `range(n)` 也会通过；这种 reward 上升并不证明模型掌握了包含端点的要求。应补边界覆盖并隔离评估数据，随后重新比较。不能让模型自己改评估器并用新分数证明自己进步。

**所有组都没有奖励差异。** 统计全对组和全错组的比例：前者可能太容易，后者可能超出能力、奖励解析错误或测试环境异常。DAPO 使用动态采样过滤全对/全错组，但这会改变采样成本和保留的数据分布。不能丢掉 90% 数据后仍只报告剩余样本的“训练效率”。[DAPO，PDF pp.4–7]

**输出越来越长，分数先升后降。** 可能是更充分推理，也可能是重复、截断惩罚或序列归一化造成的偏向。每条回答先取 token 平均再平均，与全 batch 所有有效 token 一起平均，对长回答的相对权重不同。DAPO 专门讨论了这个区别以及过长输出的奖励噪声；不能把所有坏曲线都归因于学习率。[DAPO，PDF pp.6–7]

工程上至少同时记录：成功率、失败类别、总生成 token、教师前向 token、验证器时间、GPU 时间与端到端时长。增加 teacher 之后，即使达到同分数所需 optimizer step 减少，也可能把时间花到了别处。旧任务保留集还要覆盖原有指令遵循、工具调用格式等能力，否则“这个函数任务学会了”并不能支持“可直接替换服务模型”。

## 11. 从公式落实到 verl：先核对每个接口的意义

**讲义 pp.16–17；参考固定提交 `ddf7007` 的本地源码快照。** 本节是代码阅读和实现建议，没有启动分布式训练。上游文件可能与讲义截图的行号发生变化，因此下面按文件和函数定位。

另已核对讲义链接的 [GRPO 配置文档](references/Group_Relative_Policy_Optimization_GRPO_verl_documentation.html) 与 [PPO/GSM8K Quickstart](references/Quickstart_PPO_training_on_GSM8K_dataset_verl_documentation.html)，两者均为 2026-11-13 网页快照。文档解释配置用途，固定源码说明此版本的实际行为；Quickstart 使用的小模型 PPO 案例，不等于本课的 Qwen3-8B GRPO 脚本配置。

[`trainer_base.py`](references/verl-ddf7007/trainer_base.py) 的 `_step_once` 展示了真实的数据准备链：从 buffer 取 batch，按需要算 reward，平衡数据，计算 old log-prob、可选 reference log-prob、可选 critic values，然后计算 advantage，更新 critic 和 actor。[`trainer_sync.py`](references/verl-ddf7007/trainer_sync.py) 在初始化后和 step 结束时更新 rollout 权重，并在采样结束后让副本休眠以释放权重及 KV cache。这比“generate 后直接 loss.backward”多出来的部分，正是训练系统的状态管理。

这里的 `old_log_prob`、rollout engine 保存的 behavior log-prob、训练引擎重算的概率也不应凭名称认定完全相同。不同数值内核、温度处理、异步版本会产生差异。接入前应明确概率来自哪套引擎、哪个版本，以及是否使用重要性校正。本篇只核对已归档函数，不据此宣称所有后端已经执行一致性验证。

对于小函数任务，数据和奖励接口至少应表达下面这些内容。它是**基于讲义流程的工程建议**，并非复制自某个可直接运行的官方配置：

```text
任务记录：task_id、prompt、输入约束、训练用测试/规范、验证器版本
生成记录：task_id、group_id、policy_version、token_ids、response_mask、old_log_probs
反馈记录：测试是否执行成功、通过情况、编译/超时/异常类别、可用的错误说明
更新记录：使用了哪些样本、loss 配置、训练版本、评估版本、产生的 checkpoint
```

先写对 `compute_score` 的契约：它要从回答中稳定提取代码或答案，按照训练测试评分，区分“候选程序确实失败”和“评估基础设施未完成”。执行器崩溃不能默认返回正确，也不应无记录地混入普通错误奖励。训练时只开放训练测试，独立验证器中的隐藏用例不放入教师上下文。

讲义的 Parquet 数据、奖励函数和启动配置是三个连接点：Parquet 存可复现的任务输入与所需字段；评分函数把输出映射为信号；启动配置绑定模型、数据、采样数、算法和计算资源。实际字段必须匹配所固定版本的数据加载器与 reward manager，不能拿一个示意 JSON 就称为已可运行数据集。

原始启动脚本使用多 GPU 配置，并有推理后端、动态 token batch、模型缓存和数据路径前提。它在本仓库作为来源归档，未执行。真正落地时，适合先完成小规模闭环：固定少量任务和 seed，确认 group 与 mask 正确，检查一次更新前后概率比，确认新权重已经进入下一轮 rollout，再扩大采样和分布式规模。执行模型生成的代码应采用隔离环境、资源限额和明确的文件/网络权限；本课 CPU 示例只调用预先写好的函数，没有执行模型产出的任意代码。

保存训练 checkpoint 后，还需要按框架导出或合并成推理端能加载的格式，并用部署时同一 tokenizer、chat template 和生成配置做评估。模型文件成功加载只证明格式兼容，不能替代任务正确率和旧能力检查。

## 12. 指定阅读：当训练题目也开始自己产生

**本节是本周三篇指定阅读的展开，不是 19 页教程里已经完整讲过的内容。** 前面解释的是“拿到一道题及反馈，怎样更新模型”。自博弈再往外包一层：“接下来做什么题，谁来判断答案，题库怎么随能力改变？”

这层循环与 self-distillation 是不同维度。自蒸馏讨论监督分布从哪里来；自博弈讨论任务、角色和反馈怎样相互推动。自博弈可以使用策略梯度，也可以使用筛选后的监督学习。判断方法时，依次追踪 **题目 → 解答 → 验证 → 更新 → 下一轮题目**，不要只看论文名字里有没有 Zero 或 Self。

### 12.1 Absolute Zero Reasoner：用可执行程序同时制造题目与答案

来源：[Absolute Zero: Reinforced Self-play Reasoning with Zero Data，2505.03335v3](readings/Absolute_Zero_Reinforced_Self-play_Reasoning_with_Zero_Data.pdf)，主机制 PDF pp.4–8，实验 pp.8–14，相关附录 pp.23–28、34、41–46、51–52。

AZR 的关键对象是三元组 $(p,i,o)$：程序 $p$、输入 $i$、执行结果 $o=p(i)$。固定同一个三元组，可以遮住不同部分，得到三种题目。

| 任务 | 给 solver 什么 | 要 solver 产生什么 | 教学例子 |
|---|---|---|---|
| Deduction，演绎 | 程序和输入 | 输出 | 已知正确的 `sum_even` 和 `n=4`，推得 6 |
| Abduction，溯因 | 程序和输出 | 任一能产生该输出的输入 | 已知输出 6，`n=4` 和 `n=5` 都可接受 |
| Induction，归纳 | 部分输入输出与说明 | 能适用于保留输入的程序 | 根据若干例子推断“求不超过 n 的偶数和”并写函数 |

溯因不能强制匹配原始输入：函数不是一一映射，多个输入可能得到相同输出。归纳也不能只在给过的样例上判断，否则一串 `if n == ...` 就能冒充学会了规律。AZR 把部分输入输出提供给 solver，保留其他输入用于验证；它是执行测试意义上的验证，不是对所有输入的形式证明。[PDF pp.6–8]

AZR 用**同一个参数模型**扮演 proposer 和 solver，以不同提示区分角色。proposer 生成程序与输入，Python 执行器检查、运行并构造三元组；solver 完成被遮住部分；最后用两个角色的信号共同更新模型。历史有效题目进入 buffer，既为 proposer 提供参考，鼓励产生不同题目，也在新一轮有效题目不足时补齐 solver batch。

“Zero Data”的范围是没有人为整理的该轮推理训练题库。模型仍然有预训练能力、人工设计的任务接口和 prompt、程序执行环境，以及初始恒等程序 `f(x)=x` 的种子。它不是从随机权重和完全空白的知识开始学习。[PDF p.6，Figure 5；pp.41–46 提示模板]

**出题者为什么不一直出最难的题？** 如果 solver 一次都做不对，当前结果奖励可能无法提供有效方向。AZR 用多次尝试估计成功率 $\hat p$，基本 proposer reward 为：

$$
r_{\rm propose}=\begin{cases}
0,&\hat p=0,\\
1-\hat p,&\hat p>0.
\end{cases}
$$

这里最值得注意的不是“难度适中”四个字，而是公式形状：在非零区间，成功率越低，奖励越高。若以 8 次尝试估计，成功 1 次得到 0.875，成功 4 次得到 0.5；它并非在 50% 成功率达到最大值。有限采样下的 $\hat p=0$ 也只表示这几次没成功，不证明题目数学上不可解。实际算法还加入格式与错误惩罚。[PDF p.5，式 4–6；p.23 超参数]

训练算法使用 Task-Relative REINFORCE++，按照 3 种任务 × 2 个角色建立 6 个均值和标准差基准。它既不是把全部任务混算一个 baseline，也不是 GRPO 对每一道题的多个回答单独归一化。尽管两者都出现“减均值、除标准差”，比较集合不同，学习信号就不同。[PDF p.8]

**证据支持到哪里？** v3 的 Qwen2.5-7B-Coder 行中，代码平均从 56.6 到 61.6，数学平均从 23.9 到 39.1，总平均从 40.2 到 50.4。这里总平均是代码平均与数学平均的平均，不是把所有不同 benchmark 任意等权重混在一起。评估以论文规定的 greedy 协议为主，高预算 pass@k 是另一组实验。跨模型起点和其他方法训练数据不同，也不能用同一张排行榜孤立归因于算法。[PDF pp.8–10、12–13]

更有工程价值的是失败尝试：附录报告直接增加某些复杂度或多样性奖励没有显著收益；某些函数组合任务被简单恒等路径绕过；偏向近期题目的采样会导致塌缩；加入人工题种子可早期改善但后续平台化。这说明自动 curriculum 也会追逐容易获得奖励的结构，不能把“不断出新题”视作不断获得新知识。[PDF pp.51–52]

最后，论文用敏感包过滤和两次重复执行来近似检查程序安全与确定性。**黑名单不是安全沙箱，两次输出相同也不是确定性的证明。** 若实现这个思路，应把程序执行隔离作为环境责任，另外统计超时、非确定输出、重复题和验证绕过，不能把 prompt 中的“不要访问文件”当作权限控制。[PDF pp.7–8、24–28；此处隔离要求为工程推导]

### 12.2 R-Zero：没有执行器时，用答案一致性形成伪标签

来源：[R-Zero: Self-Evolving Reasoning LLM from Zero Data，2508.05004v4](readings/R-Zero_Self-Evolving_Reasoning_LLM_from_Zero_Data.pdf)，主文 PDF pp.1–10，训练与评估附录 pp.14–21。

R-Zero 维护两个独立模型角色：Challenger 出题，Solver 解题。训练 Challenger 时冻结 Solver，用后者对题目的反应形成 reward；训练 Solver 时固定当前出题机制和构造好的题集。两者交替更新，并不是同一个模型在一步里同时修改自己的问题和答案。

它与 AZR 最大的差别是：开放数学题没有可执行程序自然给出标签。R-Zero 让 Solver 对一个问题采样多个答案，用出现最多的答案当伪标签，用该答案占比估计一致性。比如答案为 $(4,4,4,4,2)$，众数是 4，一致性为 0.8；如果真实答案是 2，这个“很有把握的标签”仍然错。

因此，一致性 $\hat p$ 不是已经验证的准确率。Challenger 的基本难度奖励为：

$$
r_{\rm uncertainty}=1-2\left|\hat p-\frac12\right|.
$$

它在 $\hat p=0.5$ 时最大，与 AZR 的形状不同。完整奖励还包括重复题惩罚和格式要求。论文一次生成 8000 个候选题，对每题用 10 个回答估计一致性，保留众数次数为 3–7 的题目，再用众数答案训练 Solver。Challenger 与 Solver 的 GRPO 超参数也分别设置，不能把估计标签时的 10 次采样误当成 solver 训练的组大小。[PDF pp.3–4、14、19]

用 $p(1-p)$ 解释中间难度有更大的二元结果方差，可以帮助理解设计动机。但这里观测到的是一致性代理，题目是否清晰、标签是否正确、是否具备学习价值都未由这个方差公式保证。把“5 个答案赞同、5 个答案不赞同”叫作理想课程过于仓促：也可能是题目有歧义或模型共有盲点。[PDF p.18 的理论讨论]

**为什么会出现先升后降？** 图 3 在多轮训练后出现退化：其中 4B 曲线从初始约 42.58 升到 step 45 的 49.07，之后 step 60 降到 46.52。重复任务、伪标签噪声与分布收缩可能相互加强。论文在不同设置下用外部模型检查生成数据质量，但那是模型辅助估计，不是形式正确性验证；正文与附录还使用了不同 judge 和样本量，不能把它们拼成一条统一的标签正确率曲线。[PDF pp.7–9、17]

这里还有一个版本内事实需要保留：**v4 的摘要、部分正文描述与表格平均数不完全一致。** 例如摘要对 4B 的数学提升写 +6.49，而 Table 1 的平均列是 42.57→49.93，对应 +7.36；摘要的一般推理 +7.54，也不等于 Table 2 平均列的 26.34→31.15。本文保留原始 PDF，不替作者修表，不把这些数混成一个确定提升。讨论迭代风险时采用图 3 自身的曲线，讨论消融时按 Table 3 自身条件阅读。[PDF pp.1、5–7]

Table 3 中去掉重复惩罚或难度过滤都会影响结果，提示任务分布治理不是可有可无。附录还比较了更一般的出题提示，显示训练主题并非必须永远限定数学。但这些结果都依赖初始模型能力和伪标签质量。若没有可靠 judge，工程起点应是可审计的小题集、标签抽检、重复率与难度分布监控，而不是让模型无限自动自训。[PDF pp.6、20；后一句为工程建议]

### 12.3 PSV：用形式验证筛选解，用通过样本做 RFT

来源：[Propose, Solve, Verify: Self-Play Through Formal Verification，2512.18160v1](readings/Propose_Solve_Verify_Self-Play_Through_Formal_Verification.pdf)，主文 PDF pp.1–8，相关附录 pp.12–16。

PSV 把代码任务改为“给定形式规范，生成实现及足以让验证器接受的证明”。普通单元测试检查若干输入；形式规范则表达前置条件和后置条件，例如“输入是合法非负整数；返回值等于范围内偶数之和”。实现者还可能需要提供循环不变量，让验证器证明每次循环都维持必要关系。

先不用掌握 Verus 语法，也能理解一个不变量：处理到数字 $k$ 之前，累加器恰好等于已经遍历范围内偶数之和。初始为空范围时成立；处理下一个数后仍成立；终止时范围正好覆盖到 $n$，才得到后置条件。实际机器整数还必须处理溢出与范围约束，不能拿数学无限精度整数的论证直接替代真实代码证明。这段 `sum_even` 推导是教学示意，未运行 Verus 验证器。

PSV 的一轮循环是：

1. 从当前规范集合出发，Solver 对每题生成多个“实现 + 证明”候选。
2. Verus 验证，收集通过的候选，每题最多保留一个训练解。
3. 用这些通过样本做 rejection fine-tuning（RFT）：筛选成功样本后的监督微调。
4. 根据各题通过率标记 easy、medium、hard、impossible，放进 proposer 的上下文，让它生成不同难度的新规范。
5. 检查新规范的格式和合法性、去重，扩充题集，进入下一轮。

这几处实现细节决定了它不是“另一种 zero-data GRPO”：**有人工来源的种子规范；本实例的 proposer 通过上下文学习改变出题分布，不做 proposer 参数 RL；solver 使用 RFT；每轮训练按 Algorithm 1 从初始 solver 参数 $\theta_0$ 重新开始，利用当前收集的通过样本，而不是无条件接着上轮参数继续训练。** [PDF pp.4–5]

为什么只学通过样本？因为验证器是 sound 但不 complete：在其逻辑、规范和可信基成立时，通过支持正确性；未通过却可能只是缺少证明、证明器超时或找不到所需不变量，并不必然表示实现错误。若把全部失败都当负 advantage，可能惩罚本来正确但未证明成功的程序。RFT 只吸收有正面证据的样本，也有代价——没有通过样本的困难题无法直接贡献监督。[PDF p.4、附录 F pp.15–16]

规范自身也会出问题。比如前置条件永不成立，后置条件就可能空洞成立；或者规范表达了错误的需求。论文的 spec verifier 会忽略实现体来检查规范有效性，但这种检查不能独自证明“存在某个实现满足它”。附录 D 使用受信任的实现占位来检查规范，不能把这个占位通过误当成最终程序已经通过证明。最终验证还需排除 `assume(false)` 等信任逃逸，并审查规范确实表达目标。[PDF pp.13–14、16；对信任边界的解释为教学推导]

**实验怎么读？** 论文基于 Qwen2.5-Coder-3B-Instruct，区分两种协议：transfer learning 在 Dafny2Verus 题目上训练，再到保留的 MBPP-Verified / HumanEval-Verified 测试；test-time training 则用待解决数据集本身的规范启动自训练。后者允许利用测试题目进行适应，不能与前者混称未见题泛化。Table 1 使用 5 个 seed、每题 100 个评估采样估计 pass@1/5/10。[PDF p.5]

例如 transfer 的 MBPP-Verified pass@1 从 RFT 的 10.99 到 PSV 的 25.25；常见的约 9.6 倍说法则来自 **TTT** 中 MBPP-Verified 的 3.83→36.78，是另一个条件。跨协议挑最大增幅会误导选型。增加生成题目也不是所有指标都继续上升：附录 C 某些 HumanEval pass@1 近乎持平。固定题目数量比较多轮与少轮时，还要计算重复求解和训练次数，不能当作已固定总计算量。[PDF pp.5、7、12]

### 12.4 把三篇放在同一张机制表里，而非同一张分数榜里

| 要追踪的对象 | AZR | R-Zero | PSV |
|---|---|---|---|
| 题目起点 | 预训练模型、人工接口、恒等程序种子 | 预训练模型与人工出题提示 | 人工来源、经过转换的种子规范 |
| 正确性反馈 | 程序执行结果和保留测试 | 模型答案一致性产生伪标签 | Verus 对形式规范的验证 |
| proposer 改变什么 | 与 solver 共享的模型参数 | 独立 Challenger 参数 | 主要更新带难度示例的上下文 |
| solver 怎样更新 | TRR++ 策略梯度 | GRPO 策略梯度 | 通过样本的 RFT |
| 主要持久状态 | 参数、分任务题目 buffer | 两套参数、候选与过滤题集 | 参数版本、增长的规范集、验证结果 |
| 最需要防止的误读 | 测试通过等于普遍正确；零数据等于无先验 | 一致性等于正确率；迭代必然持续改善 | 形式验证等于需求正确；RFT 等于 GRPO |

在工程中，这张表首先帮助选择反馈来源。若能可靠执行任务，优先保留可复核的执行反馈；若只有模型共识，就要承担伪标签和共同错误的风险；若任务能写出可验证规范，形式验证提供更强的正确性依据，但规范、证明负担与工具能力成为约束。这是从三篇机制推出的选型原则，不是论文已经完成的跨方法公平竞赛。

## 13. 从训练脚本到持续学习服务：verl 与 Reef 的衔接

**讲义 pp.18–19；[Reef README 固定提交 b373872e22d6581d3cd53a6077c9180581d599b7](references/reef/b373872e22d6581d3cd53a6077c9180581d599b7/README.md)，2026-11-13 获取。** 讲义用 verl 的“准备数据、训练、部署”和 Reef 的“服务中收集反馈、学习、更新”形成对照。把它理解为关注层次不同更准确，不能由此断言训练框架完全没有异步功能，或 Reef 自己取代所有底层训练引擎。

Reef 的归档 README 把循环分成 Serve、Observe、Grow、Commit：服务记录交互；把反馈匹配到记录；从符合条件的样本产生候选更新；根据配置的评估与选择策略发布接受的版本。当前 README 还明确区分模型权重学习与 harness（提示、规则、skills 等）优化，所以“持续改善”不一定表示每次都更新模型权重。

在小函数服务中，一次请求返回代码，同时返回一个 interaction receipt。测试报告应引用这个 receipt，才能确认它评价的是哪次生成。Reef README 的接口使用 `x-reef-agent-record-id` 返回收据；后续 report 可带 score、feedback 和 references。recipe 由部署配置决定，请求不能随意选择另一种学习算法。这些细节把“反馈喂回去”变成了明确的服务协议。

候选 checkpoint 产生后，仍要经过配置的选择流程才能成为服务版本。实际产品可以同时验证新任务、旧能力、时延与格式契约，并记录被拒候选。这里的“可以”是工程设计建议：README 描述了组件与流程，并不证明任何默认配置已满足你的验收标准。该固定版本还提示正在进行 control plane + workers 重构，部分 recipe/example 可能失败。本篇只阅读归档 README，未安装 Reef、未调用服务、未确认训练或热更新成功。

从 Java 后端经验出发，可以把持续学习理解为带有明确数据血缘的候选版本生产与发布过程：请求成功、反馈匹配成功、训练成功、评估通过、版本被服务加载，是五个不同结果。把这些状态分开，才知道模型行为改变究竟来自参数更新、prompt 修改，还是恰好换了评估题。

## 14. 怎样把这课变成一个可解释的小实验？

### 14.1 本篇已经执行的 CPU 练习

运行入口是 [learning_signals.py](examples/learning_signals.py)，记录是 [RESULTS.json](examples/RESULTS.json)。仅使用 Python 标准库，执行日期 2026-11-13，Python 3.11.10。可在本课目录运行：

```bash
python3 examples/learning_signals.py
```

脚本实际检查了手写正确/错误函数的五组输入，计算两种标准差口径的组优势，对四种正负 advantage 与 ratio 组合验证 PPO surrogate，并用有限差分验证固定前缀 reverse KL 梯度。它还复算了讲义 batch 算例、示意显存账本，以及 AZR 与 R-Zero 的 proposer reward 形状。主要结果为：

| 检查 | 实际结果 |
|---|---|
| 端点错误 | `n=4` 时错误函数输出 2，正确函数输出 6；`n=5` 时两者都为 6 |
| 全错组 advantage | 四项均为 0 |
| KL 梯度 | 解析梯度与有限差分最大差异约 $6.4\times10^{-12}$ |
| 一次局部梯度下降 | KL 0.223144→0.199731 |
| batch | 5120 条/采样批，4 次更新，160 条/worker，40 次累积/更新 |
| 训练状态估算 | 8.2B × 16 bytes = 131.2 GB，不含激活等额外项 |
| proposer，$\hat p=0.125$ | AZR 为 0.875，R-Zero 基本不确定性项为 0.25 |
| proposer，$\hat p=0.5$ | AZR 为 0.5，R-Zero 基本不确定性项为 1 |

这是数学和状态账本的校验。没有调用 LLM、没有训练权重、没有 GPU 实验、没有运行不可信生成代码或 Verus；没有复现论文分数、吞吐、显存峰值或在线服务更新。

### 14.2 下一步模型实验应怎样设计——尚未执行

如果把本篇变成实际模型实验，先固定同一个模型初始化和一组不同的小函数任务，保留未用于训练的函数题目与边界测试。只用一个 `sum_even` 模板的不同数字，主要测的是同题适应，不能代表代码任务泛化。

然后分开验证两个问题。**第一组**比较学习信号：结果奖励、带反馈的自蒸馏、二者结合。固定任务和反馈获取渠道，分别报告生成量、教师计算、总时间，以及隐藏题的表现。**第二组**比较出题机制：固定题池与自动生成题池，固定总预算并记录有效题目、重复率、难度分布、伪标签误差；不要同时换模型、奖励和评估集，再把全部提升归给自博弈。

还需要一个很朴素的基线：不训练权重，只把失败测试放到下一轮上下文。这样才能判断，当前收益是否真的需要参数更新。评估时明确“新题不带反馈的一次生成”“同题多次尝试”“测试时更新参数”分别是什么协议，并给各协议相同且公开的预算。checkpoint 在验证集上选，最终测试集保留到比较方案确定后使用。

如果模型训练后的隐藏题表现不升，先检查前面各节的数据身份、奖励覆盖、教师能力和预算，再判断方法不适用。若只在训练用例提高、旧任务下降，则应保留失败记录与版本，不把训练 loss 下降当作完成学习。

## 15. 自测：能解释这些问题，才算接上了机制

先尝试口头回答，再看下面的答案。重点是能预测改动会怎样影响系统，而不是记住缩写。

1. 四个回答全错，GRPO 加一个更大的 $\epsilon$ 能不能教会模型正确解法？
2. 为什么同一段失败代码中，正确 token 也可能被结果奖励压低概率？自蒸馏解决了多少？
3. old policy、reference、teacher 可以来自同一个 checkpoint，为什么仍要分开记录？
4. 同一份权重能推理，却训练 OOM，至少有哪些新增内存？把 batch 切小能否解决全部问题？
5. 5120 条回答拆成 4 个 mini-batch 后，第 2 个 mini-batch 与采样策略是什么关系？
6. SDFT、OPSD、SDPO 是否都使用当前学生加上下文、reverse KL 和相同 top-k？
7. 一道 R-Zero 题有 80% 答案一致，能否说标签有 80% 概率正确？AZR 的“8 次全失败”又能否证明无解？
8. PSV 验证失败为什么不宜一律当作负样本？它是否从无人工任务开始并用 GRPO 更新两个角色？
9. “隐藏题 pass@1 上升”“同题 discovery@k 上升”“训练 loss 下降”，分别证明了什么？
10. Reef 产生新 checkpoint，是否意味着下一次请求已经使用这个版本？

**参考答案：**

1. 不能。全组奖励相同，减均值后仍是 0。$\epsilon$ 处理分母，不产生指导信息；需要有区分度的任务、反馈或其他监督。
2. 结果监督把一条回答的 advantage 广播到所有有效 token，没有局部因果定位。自蒸馏让不同位置或候选 token 得到不同监督，但仍依赖教师、前缀和反馈质量，不能保证定位真实根因。
3. 它们分别负责生成分布基准、长期偏离约束和目标分布。更新时机、使用的上下文和参数是否冻结都可能不同。
4. 梯度、优化器状态、主权重、激活与通信 buffer 等；还可能有 critic/teacher/reference。缩 micro-batch 主要减激活，不能自动消除模型状态或切换时副本峰值。
5. 第一次更新后当前参数已变，第 2 个 mini-batch 仍来自先前采样版本。old log-prob 保持固定，PPO 用 ratio 等机制控制有限复用；整个算法仍通常称为 on-policy。
6. 不是。要按第 5 节的版本表核对教师更新、KL 方向和具体实验配置。尤其 SDPO 无反馈与 rich-feedback 的配置不同。
7. 都不能。答案一致性可能是共同错误；有限次失败也不能证明不可解。两种观测所对应的可靠性不同。
8. sound 不等于 complete，正确程序可能因证明不足等未通过。PSV 有人工来源种子规范，proposer 主要通过上下文适应，solver 对通过样本做 RFT，并按原算法从初始参数重新训练。
9. 第一种在隔离和预算成立时支持新题泛化；第二种支持指定适应协议下更快找到解；第三种只说明优化了训练目标，不能单独证明能力提高。
10. 不能。还要核对评估和选择结果、发布状态，以及推理端实际加载的版本；完整训练链和服务链是不同的状态。

## 来源与阅读路径

本篇对照了 19 页教程、三篇指定阅读的正文与相关附录，以及下表中与讲义实质内容对应的一手材料。原始文件没有被翻译或改写；补充材料的版本、复用位置和 SHA-256 见 [REFERENCES.json](REFERENCES.json)，课程主来源见 [SOURCES.md](SOURCES.md)。来源页码用于支撑相邻机制与原文观察；本文的小函数、数值简化、排障与实验安排均在相应位置标为教学展开或工程建议。

| 材料 | 重点位置与在本课中的作用 |
|---|---|
| [RL and Self-Distillation in Practice](tutorials/lec6%20-%20rl%20in%20practice.pdf) | 全部 19 页；算法—训练循环—监控—verl—Reef 主线 |
| [前课 lec6 - training.pdf](../7.ModelEvolution1/slides/lec6%20-%20training.pdf) | 本课 p.4 的前置链接；核对 pp.7–20、24–27、37–39 的策略梯度、PPO/GRPO 和蒸馏衔接，未改写前课讲解 |
| [Absolute Zero: Reinforced Self-play Reasoning with Zero Data](readings/Absolute_Zero_Reinforced_Self-play_Reasoning_with_Zero_Data.pdf) | v3；正文 pp.1–14，算法/执行检查/提示及失败实验见 pp.23–28、34、41–46、51–52 |
| [R-Zero: Self-Evolving Reasoning LLM from Zero Data](readings/R-Zero_Self-Evolving_Reasoning_LLM_from_Zero_Data.pdf) | v4；正文 pp.1–10，附录 pp.14–21；机制、评估协议与多轮退化；保留数字冲突说明 |
| [Propose, Solve, Verify: Self-Play Through Formal Verification](readings/Propose_Solve_Verify_Self-Play_Through_Formal_Verification.pdf) | v1；正文 pp.1–8，附录 pp.12–16；RFT、规范检查、验证的正确性边界 |
| [Proximal Policy Optimization Algorithms](references/Proximal_Policy_Optimization_Algorithms.pdf) | v2，pp.2–5；概率比与 clipped surrogate |
| [High-Dimensional Continuous Control Using Generalized Advantage Estimation](references/High-Dimensional_Continuous_Control_Using_Generalized_Advantage_Estimation.pdf) | pp.2–5；价值基准、TD error 与 GAE |
| [DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models](references/DeepSeekMath_Pushing_the_Limits_of_Mathematical_Reasoning_in_Open_Language_Models.pdf) | v3，pp.11、13–14；GRPO 的组优势和 reference KL |
| [DAPO: An Open-Source LLM Reinforcement Learning System at Scale](references/DAPO_An_Open-Source_LLM_Reinforcement_Learning_System_at_Scale.pdf) | pp.3–7；动态采样、长度、熵与 loss 聚合；不把其训练曲线当本地复现 |
| [On-Policy Distillation of Language Models: Learning from Self-Generated Mistakes](references/On-Policy_Distillation_of_Language_Models_Learning_from_Self-Generated_Mistakes.pdf) | v3，pp.1–8；学生前缀、divergence 选择、实验任务边界 |
| [On-Policy Distillation](references/On-Policy_Distillation.html) | Thinking Machines 博客正文；局部 reverse KL、实现与成本口径。原文发表于 2025-10-27，归档含 2026-06 模型退役更新，旧模型实验不是当前 API 可用性承诺 |
| [RL’s Razor: Why Online Reinforcement Learning Forgets Less](references/RL_s_Razor_Why_Online_Reinforcement_Learning_Forgets_Less.pdf) | v1，pp.1、3–8；遗忘、KL 与 on-policy 数据的实证关系及理论条件 |
| [Self-Distillation Enables Continual Learning](references/Self-Distillation_Enables_Continual_Learning.pdf) | v2，pp.1–11、16–18、20–22；EMA、实际 KL 方向、知识/技能与遗忘 |
| [Self-Distilled Reasoner: On-Policy Self-Distillation for Large Language Models](references/Self-Distilled_Reasoner_On-Policy_Self-Distillation_for_Large_Language_Models.pdf) | v3，pp.2–9、13–15；固定教师、forward KL、style 与预算配置 |
| [Reinforcement Learning via Self-Distillation](references/Reinforcement_Learning_via_Self-Distillation.pdf) | v2，pp.1–15、29–32、42–43；rich feedback、局部/序列梯度、teacher、top-k 与分实验配置 |
| [OpenClaw-RL: Train Any Agent Simply by Talking](references/OpenClaw-RL_Train_Any_Agent_Simply_by_Talking.pdf) | v2，pp.5–16；混合信号、异步流程、hint 选择与模拟实验边界 |
| [OpenClaw-RL1 项目说明](references/OpenClaw-RL1.html) | 2026-11-13 网页快照；两类反馈及系统动机；正文实验以有版本的论文为准，不合并项目页早期实验数值 |
| [HybridFlow: A Flexible and Efficient RLHF Framework](references/HybridFlow_A_Flexible_and_Efficient_RLHF_Framework.pdf) | pp.3–8；跨模型数据流、分布式 worker、训练/生成重分片 |
| [PyTorch FSDP: Experiences on Scaling Fully Sharded Data Parallel](references/PyTorch_FSDP_Experiences_on_Scaling_Fully_Sharded_Data_Parallel.pdf) | pp.3–7；分片、all-gather、reduce-scatter、峰值内存与通信 |
| [ZeRO: Memory Optimizations Toward Training Trillion Parameter Models](references/ZeRO_Memory_Optimizations_Toward_Training_Trillion_Parameter_Models.pdf) | pp.7–10；模型状态与额外内存账本 |
| [Efficient Memory Management for Large Language Model Serving with PagedAttention](references/Efficient_Memory_Management_for_Large_Language_Model_Serving_with_PagedAttention.pdf) | pp.3–5；生成依赖、KV cache、分页与 batch 上限 |
| [verl trainer](references/verl-ddf7007/trainer_base.py)、[同步钩子](references/verl-ddf7007/trainer_sync.py)、[算法](references/verl-ddf7007/core_algos.py)、[配置](references/verl-ddf7007/run_qwen3_8b_fsdp.sh) | 固定 `ddf7007` 快照；只读核对训练链、组标准差与脚本实际默认值，未运行分布式任务 |
| [verl GRPO 文档](references/Group_Relative_Policy_Optimization_GRPO_verl_documentation.html)、[PPO Quickstart](references/Quickstart_PPO_training_on_GSM8K_dataset_verl_documentation.html) | 2026-11-13 网页快照；batch 单位、配置、数据/奖励/导出入口 |
| [Reef README](references/reef/b373872e22d6581d3cd53a6077c9180581d599b7/README.md) | 固定提交的系统入口说明；receipt、recipe、候选选择与发布；非完整源码审计或服务验收 |

讲义 p.15 的 W&B 链接本次工具未能取得运行详情，曲线解释依据已归档的讲义图，不宣称复核了完整在线日志。人物主页、社交账号与发布消息用于辨认讲者和项目，不作为算法效果证据。

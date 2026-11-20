# 推测解码 — 让目标模型一次核验多个 token

Harvard CS2680，2026 年 11 月 11 日。以下页码是 PDF 文件中从 1 开始的实际页序。有些页面右下角的编号与文件页序不同。首尾课程安排见课程课表。[教师原始讲义](12_llm_serving_spec_decoding.pdf) · [课程来源索引](SOURCES.md) · [课程课表](../COURSE_SCHEDULE.md)

假设你维护一个 Java 工单服务。它调用 LLM，把一段自由文本转成一个 `Ticket` 对象，例如 `{"category":"billing","priority":"normal"}`。请求需要等完整 JSON 到齐才能做 schema 校验并进入下一步。目标模型已经通过验收，换成小模型可能把问题分错。能否让小模型先猜后面几个 token，再让目标模型一次核验，少走几次串行推理？

这就是本讲的问题。答完还要追问两件事。一次核验省的是哪项资源？系统怎样保证最终交给 Java 业务代码的仍是目标模型的输出？

| 讲义实际页序 | 问题 | 本文位置 |
|---|---|---|
| [1–20](12_llm_serving_spec_decoding.pdf#page=1) | 逐个生成慢在哪里？怎样核验才能保持原分布？ | §1–3 |
| [21–46](12_llm_serving_spec_decoding.pdf#page=21) | 草稿从哪里来？怎样降低生成草稿的成本？ | §4 |
| [47–61](12_llm_serving_spec_decoding.pdf#page=47) | 如何并行核验一棵树？怎样区分精确验证与放宽规则？ | §5 |
| [62–75](12_llm_serving_spec_decoding.pdf#page=62) | 引擎怎样提交 token？什么时候开、减小或关闭推测？ | §6–8 |
| [76–78](12_llm_serving_spec_decoding.pdf#page=76) | 后续课次、可选的有损方向与收束 | §5.3、§8 |

## 1．串行限制在下一次输入，GPU 的瓶颈还要另算

**讲义主线**参见 [第 4–6 页](12_llm_serving_spec_decoding.pdf#page=4)。训练时，正确序列是已知的。一层内可以为多个位置同时算输出，用因果掩码限制每个位置只能看见自己和前面的输入。生成时，下一位置的输入包含刚刚产生的 token。你还没决定是 `billing` 还是 `technical`，就无法知道后面位置应在什么前缀下计算。硬件能并行算矩阵，仍不能提前获得这项输入。

生成有两个阶段。**Prefill** 处理已知的输入 token，计算各层的 Key、Value 并留下 KV cache，同时得到用于选择首个输出 token 的 logits，也就是词表各候选的原始分数。**Decode** 把已选 token 送回模型，用已有 K、V 和当前位置的查询做注意力，再得到下一个位置的 logits。可以把 KV cache 看成 prefix 每过一层留下的可复用数据。它减少对旧 token 的重复计算，读取它仍占显存带宽。模型权重是另一类数据，目标模型每次前向都需要使用它们。上一课的分页解决 KV 放在哪里，连续批处理解决每轮一起处理哪些请求，这里再加一个维度，每个请求本轮带几项以后可能有用的工作。[上一课资料](../12.EfficientLLMServingBasicsIII.BatchingPagingAndParallelism/SOURCES.md)

低并发时，稠密（dense）模型每步使用所有常规模型层的权重，一次 decode 往往只算少数 token，搬模型权重所需的时间却基本不跟着减少。讲义用 8B 参数、每个 FP16 参数 2 字节估出 16 GB。按 H200 的 HBM（GPU 上的高带宽显存）4.8 TB/s 计算，$16 / 4800$ 秒约为 3.33 ms。这是权重搬运的理想时间尺度，实际还受 KV 访问、算子调度、量化、通信等影响。若一次加载的权重可以供多个 token 的矩阵运算使用，就可能用接近同样的时间算更多位置。连续批处理把多个请求叠在一起。推测解码为单个请求凑出多个候选位置。两者会争用同一批 GPU 资源。[讲义第 5、14、64 页](12_llm_serving_spec_decoding.pdf#page=14)

讲义第 6 页的一轮可以读成三步。

1. 草稿器先产生 $k$ 个候选，例如猜完 `category` 的值和后面的分隔符。它可以是小模型、目标模型的轻量分支，也可以从已见文本中查找候选。
2. 目标模型在一个前向中计算各候选位置的分数。草稿使这段输入暂时已知，因果掩码依然保证后面的猜测不会反过来影响前面的 logits。
3. 从左到右决定可接受的前缀。如果某一位置被拒绝，在此处补一个正确分布的 token，把后续候选丢弃并结束本轮。如果所有候选都被接纳，可以再从目标模型已经算好的下一位置的分布采样一个 token。忽略结束标记与长度上限时，一轮能提交 1 到 $k+1$ 个 token。[讲义第 6、9 页](12_llm_serving_spec_decoding.pdf#page=9)

## 2．把被拒绝的概率补回去

### 2.1 接受率、剩余分布和一次手算

**讲义主线**参见 [第 7–13 页](12_llm_serving_spec_decoding.pdf#page=7)。先固定前缀 $h$，例如 JSON 刚写到 `"category":`。随机采样时，可先按温度缩放 logits，再用 softmax 将分数变成概率。如果用 top-p（nucleus），按概率从高到低保留累计质量达到阈值的候选，并重归一化。此时目标模型实际用于抽样的分布写作 $p(x\mid h)$，草稿器实际提议的分布写作 $q(x\mid h)$。下面省略固定的 $h$。概率必须落在同一个 token 空间。直接用两套 tokenizer 的同号 token，可能把不同字符串错当成同一个候选。

传统拒绝采样的图很好读。若要采出 $[0,1]$ 上密度为 $3x^2$ 的数，可先采均匀点 $x$，再以 $x^2$ 的概率留下它。留下来的密度与 $x^2$ 成比例，积分归一化乘 3。一般取覆盖目标的上界 $M q(x)\ge p(x)$，按 $p(x)/(M q(x))$ 接受，留下的概率密度就是 $p(x)/M$，拒绝则重试。推测解码也利用「被提出的概率乘上被接受的概率」来调整分布，不过被拒后立即补一个 token。第 8 页简写为从目标分布补采。精确算法使用第 9–13 页写出的**剩余分布**。直接重新从 $p$ 抽一次通常会偏离 $p$。[讲义第 8–13 页](12_llm_serving_spec_decoding.pdf#page=8) · [Leviathan 等，Algorithm 1](readings/Fast_Inference_from_Transformers_via_Speculative_Decoding.pdf#page=3) · [证明，附录 A.1](readings/Fast_Inference_from_Transformers_via_Speculative_Decoding.pdf#page=11) · [Chen 等，§2.3、Algorithm 2 和 Appendix A.1](readings/Accelerating_Large_Language_Model_Decoding_with_Speculative_Sampling.pdf#page=4) · [von Neumann 的历史参考](https://mcnp-green.lanl.gov/pdf_files/InBook_Computing_1961_Neumann_JohnVonNeumannCollectedWorks_VariousTechniquesUsedinConnectionwithRandomDigits.pdf)

对草稿抽到的 $x$，以 $\min(1,p(x)/q(x))$ 的概率接受。只有 $q(x)>0$ 的候选可能被提出。被接受并输出 $x$ 的联合概率因此是

$$
q(x)\min(1,p(x)/q(x))=\min(p(x),q(x)).
$$

某个 token 目标想要的比草稿给得多，缺口就是 $[p(x)-q(x)]_+$，其中 $[u]_+=\max(u,0)$。总接受率 $\alpha=\sum_x\min(p(x),q(x))$，所有缺口恰好加成 $1-\alpha$。在发生拒绝这个条件下，按 $r(x)=[p(x)-q(x)]_+/(1-\alpha)$ 采样它们。若 $\alpha=1$，拒绝事件不会发生，程序无需构造 $r$。去掉条件之后，补上的质量是 $(1-\alpha)r(x)$。加上先前留下的质量得到

$$
\Pr(\text{输出 }x)=\min(p(x),q(x))+[p(x)-q(x)]_+=p(x).
$$

**教学推导**将讲义第 10–12 页的数值换成三个工单类别。假定这三个类别在当前例子各占一个候选 token，真实分词时类别可能跨多个 token。

| $x$ | 目标 $p$ | 草稿 $q$ | 被提出后接受 | 提出且接受的概率质量 | 拒绝后最终补给该类的概率质量 |
|---|---:|---:|---:|---:|---:|
| `billing` | 0.6 | 0.3 | 1 | 0.3 | 0.3 |
| `technical` | 0.3 | 0.6 | 0.5 | 0.3 | 0 |
| `general` | 0.1 | 0.1 | 1 | 0.1 | 0 |

草稿每 100 次平均猜 60 次 `technical`，一半被拒。总共有 30 次需要补采，全部补成 `billing` 后，三类输出就回到 60、30、10。如果误用 $p$ 补采，只有 $30\times0.6=18$ 次补成 `billing`，最终分别是 48、39、13。重复调用看起来大多仍是合法 JSON，但你已经换掉了分类接口的统计行为。

### 2.2 为什么验完一个还可以继续，推测在哪些条件下保持精确

**讲义主线与阅读补充**参见 [第 9、13、17 页](12_llm_serving_spec_decoding.pdf#page=9)。将 $h$ 换成每个位置的输入前缀，沿着同一个在途草稿先计算 $p_i,q_i$。之前的候选全通过，当前位置的草稿前缀就是真正的输出前缀。这时可以继续用预先算出的分布。如果第 $i$ 项的候选被拒，按该位置的 $r_i$ 补出的 token 可能与草稿不同，第 $i+1$ 位置起的分布对应的是未发生的旧路径。因此保留通过前缀和补采项，下一轮从新前缀开始。每步在已提交前缀下都保持 $p$，逐步相乘便恢复目标模型的序列分布。若整段通过，额外一项直接用该前缀下的 $p_{k+1}$。

工程中要比对和使用被定义为基准的**实际**抽样策略。温度、top-p、惩罚项、schema 掩码和引擎的停止规则都必须在正确前缀上处理。目标 $p$ 可以是 schema 约束后的分布。草稿 $q$ 可以有自己的提议规则，但公式里的 $q$ 必须反映它实际怎样提出。普通链式算法不能拿一个没有按 $q$ 抽样的 top-k 列表随意计算 $p/q$。后面的树需要自己的验证规则。

在目标做确定性贪心时，可直接比较每个草稿是不是目标的 argmax，首个不匹配就输出目标选中的 token。与普通 greedy 的 token 等价还依赖同样的前缀、停止和并列分数处理，实际内核的舍入差异也可能使 argmax 改变。随机采样的精确性指分布一致。两个引擎即使用同一个 seed，也可能因消耗随机数的顺序不同输出不同样本。比较随机路径时应该查条件分布或多次抽样统计。[原论文对正确性及数值差异的说明](readings/Accelerating_Large_Language_Model_Decoding_with_Speculative_Sampling.pdf#page=6)

## 3．为什么接受得多还可能慢

**讲义主线**参见 [第 14–20 页](12_llm_serving_spec_decoding.pdf#page=14)。令 $A$ 为本轮从左开始通过的草稿长度。可以把 $A$ 写作 $k$ 个指示变量的和，第 $i$ 项在前 $i$ 个草稿全部通过时记 1。所以 $E=1+\sum_{i=1}^{k}\Pr(A\ge i)$ 是一轮平均提交的 token 数，这里忽略停止边界。若每一级在其前缀已通过的条件下都有近似恒定的接受率 $\alpha$，乘法法则把它简化为 $1+\alpha+\cdots+\alpha^k$。真实请求的分布随前缀变化，测到的总体 token 接受率不能直接当每一级的条件概率。部署上宜同时记录各深度的存活率。

把普通 decode 一步的时间记为 1。若验证一批草稿仍花 1 步，草稿器每提出一个 token 花 $c$ 步，那么速度比近似 $E/(1+kc)$。取讲义例子的 $\alpha=0.8,k=4,c=0.05$，$E=3.3616$，速度比约 $2.80$。这说明短草稿在权重读取主导时可能很值。若完整核验变成 3.5 个基准步，保持同样的 $\alpha,k,c$，分母变为 3.7，速度比约 $0.91$。在每级接受率固定且小于 1、草稿每步成本大于零的模型里，$k$ 增大时 $E$ 有上限而草稿时间继续增加。目标 FLOPs 按 $k+1$ 个查询位置近似计算时，平均每个输出 token 用了 $(k+1)/E$ 倍目标计算。取 $k=4,\alpha=.8$ 时约 $1.49$ 倍，还没算草稿器。第 52 页正是把这笔额外计算重新放回账里。[讲义第 15–16、52 页](12_llm_serving_spec_decoding.pdf#page=15)

课程用 roofline 把「平时验得快」量化。对一次核验的 $n$ 个查询位置，理想的权重内存时间为 $W/B$，矩阵乘算量对 FP16 权重近似取 $nW$ FLOP，因为按 2 字节参数与一次乘加约 2 次浮点运算粗估。整步耗时的近似值为两项的较大者 $\max(W/B,nW/F)$。这里 $W$ 是以字节计的权重大小，$B$ 是字节每秒的 HBM 带宽，$F$ 是每秒浮点运算数，$F/B$ 的单位是 FLOP/字节。课件按 H200 取 $989$ TFLOP/s 与 $4.8$ TB/s，约 206 个查询位置就越过这一教学模型的拐点。固定每请求草稿 $k$，近似 $n=\mathrm{batch}(1+k)$。这个加 1 将等待被前向处理的最后一个已选 token 计入 batch。单看草稿候选的数量会漏掉它。[讲义第 14、64–65 页](12_llm_serving_spec_decoding.pdf#page=64)

**论文证据**不能用一条速度倍数替代运行条件。讲义第 18–19 页对应 Leviathan 等的 T5X 实验。单 TPU v4、batch 1、WMT 英译德、11B T5-XXL 目标。贪心时，小、中、大草稿接受率分别为 0.75、0.80、0.82，但墙钟加速分别为 3.4、2.8、1.7 倍。温度 1 时对应是 2.6、2.4、1.4 倍，表里三个草稿使用的长度分别为 7、5、3，不能把讲义上的「7 降到 5」当成一条统一规则。Chen 等在 16 片 TPU v4 上用 70B Chinchilla 和专门训练的 4B 草稿，batch 1、$k=4$，在 XSum 的 nucleus 配置和 HumanEval 的 nucleus 配置分别给出 1.92 和 2.46 倍。两组实验各自证明这些组合有收益。比较大小模型时还要看拓扑与通信，小参数量并不自动换成较低延迟。[Leviathan 等，§4.1 Table 2](readings/Fast_Inference_from_Transformers_via_Speculative_Decoding.pdf#page=6) · [Chen 等，§4 Table 1](readings/Accelerating_Large_Language_Model_Decoding_with_Speculative_Sampling.pdf#page=6)

## 4．草稿方式不同，代价落在不同地方

**讲义主线**参见 [第 21–46 页](12_llm_serving_spec_decoding.pdf#page=21)。理解新方法时问三个问题。输入从哪里拿？草稿要做几次串行前向？为了让更多猜测通过，需要额外维护哪些权重、状态或训练数据？Java 接口接收完整的 `Ticket`，引擎内部才决定谁提出候选。

### 4.1 独立小模型、早退和预测头

独立小模型把 target 和 drafter 分成两个模型，能冻结大模型就地部署。服务要加载另一套权重，为每个请求保存草稿模型自己的 KV。每个候选还要经过草稿模型的串行 decode。DistillSpec 解释为什么「小模型在测试集上很强」与「它能猜中这位目标模型」是两回事。它从草稿模型自己会遇到的前缀收集蒸馏样本，用目标分布纠正它。若只用标准答案的干净前缀教学，就可能漏掉草稿器在实际 rollout 里偏离后遇到的输入。蒸馏的任务是减少 $p$ 和 $q$ 的差异，验证器承担精确性的保证。[讲义第 22–23 页](12_llm_serving_spec_decoding.pdf#page=22) · [DistillSpec，§2–3](readings/DistillSpec_Improving_Speculative_Decoding_via_Knowledge_Distillation.pdf)

LayerSkip 让同一模型的前 $\ell$ 层先猜，后续核验复用已经走过的前层计算状态。训练时让早层也能接到同一 LM head 做预测，同时使用随深度变化的 layer dropout，即训练时有意让某些层不参与该次前向。LM head 把某个位置的隐藏向量投影到词表 logits。直接在一个原本只训练最后一层输出的模型上提前取 logits，可能得到很差的草稿。验证用完整模型的路径，早退路径的权重、表示和 KV 何时能够复用由训练和实现决定。课件用 $k\ell/L+(1-\ell/L)$ 粗估相对深度，层成本和缓存调度在真实硬件上并不均匀。Draft & Verify、SWIFT 通过选择性跳层构建自草稿。SWIFT 在使用过程中根据输入调整跳过哪些层，保留完整路径用于核验。[讲义第 24–25 页](12_llm_serving_spec_decoding.pdf#page=24) · [LayerSkip，§3](readings/LayerSkip_Enabling_Early_Exit_Inference_and_Self-Speculative_Decoding.pdf) · [Draft & Verify](readings/Draft_Verify_Lossless_Large_Language_Model_Acceleration_via_Self-Speculative_Decoding.pdf) · [SWIFT，§3](readings/SWIFT_On-the-Fly_Self-Speculative_Decoding_for_LLM_Inference_Acceleration.pdf)

Medusa 在同一隐藏状态上加多个预测头，分别猜更远的位置。猜 `priority` 的头看到了当前前缀，但看不到中间的其他头选中了什么，因此可能产出不能同时成立的组合。把每个头的高分候选组装成树可覆盖多个组合。覆盖范围增大也意味着验证项增加。Medusa-1 冻结 backbone，Medusa-2 联合微调。核验用严格匹配还是放宽的 typical acceptance 应单看配置。另外，若联合微调改过目标权重，等分布的参照必须说清是哪一个目标 checkpoint。[讲义第 26–27 页](12_llm_serving_spec_decoding.pdf#page=26) · [Medusa，§2–3](readings/Medusa_Simple_LLM_Inference_Acceleration_Framework_with_Multiple_Decoding_Heads.pdf)

### 4.2 EAGLE 的四次改动分别解决什么

| 版本 | 观察和机制 | 需要核对的边界 |
|---|---|---|
| EAGLE | 目标隐藏特征给出比单个 token 更丰富的状态。草稿头先预测下一步特征，再用目标 LM head 得到 token。将已经选中的 token 一并输入，使下一特征知道当前究竟走了哪条分支。 | 较深草稿位置会收到草稿头自己的预测。上一位置的偏差会传到后面。 |
| EAGLE-2 | 用草稿置信度估计核验接受机会，沿路径相乘排序。展开高值节点再裁剪树，让可预测片段多猜几步，不确定处多留几种候选。 | 置信度近似依赖校准，部署域变化时应按深度测量真实接受率。路径乘积用于选择核验对象，输出仍要遵循验证规则。 |
| EAGLE-3 | 融合目标低、中、高层的特征，改用 token 预测损失，而非必须还原某层特征。在训练内让草稿头遇到自己的多步输出，贴近草稿阶段的输入。 | Training-time test 是训练时模拟推理路径，服务请求到达时不为这个机制在线更新权重。 |
| EAGLE-4 | 用硬件与负载曲线估核验代价，再结合接受置信度决定树深、树宽和总数。草稿 LM head 用低秩候选筛选后重算候选行，省掉每步全词表的大矩阵乘。 | 词表中的 token 都可能随上下文进入候选集，不代表每一步都为所有 token 计算精确 logit。作者报告的效率数据依赖具体硬件与负载。 |

以工单为例，常见模板里的标点会让 EAGLE-2 走得深，类别交界处有可能需要保留备选值。如果排队积压，即使很有把握也可能选择只核验一点。EAGLE-4 把核验成本直接加进决策，改变的是花多少资源验证。引擎从树中选择要核验的节点，核验器再按既定规则决定提交哪些 token。EAGLE-4 发布者用 Qwen3.8-27B 做的 GPU 比较采用 4 块 B300、SPEED-Bench、TP 4 且关闭 MegaKernel。文中的单并发和 512 并发数据对应两种工作负载，不能用单并发比值推高负载容量。[讲义第 28–36 页](12_llm_serving_spec_decoding.pdf#page=28) · [EAGLE，§3](readings/EAGLE_Speculative_Sampling_Requires_Rethinking_Feature_Uncertainty.pdf) · [EAGLE-2，§3–4](readings/EAGLE-2_Faster_Inference_of_Language_Models_with_Dynamic_Draft_Trees.pdf) · [EAGLE-3，§3](readings/EAGLE-3_Scaling_up_Inference_Acceleration_of_Large_Language_Models_via_Training-Time_Test.pdf) · [EAGLE-4 论文 §3–4、Table 2](references/EAGLE-4_One_Flexible_Drafter_for_All_Batch_Sizes_and_Hardware.pdf#page=9) · [作者技术说明](https://blog.eagle.ai/blog/introducing-eagle-4)

Meta 的部署研究说明，效果也取决于树注意力、批处理、GPU 中间步骤和通信开销。作者报告其 Llama 服务优化在生产规模负载下达到 1.4–2.0 倍加速，原因包含系统优化。Baseten 用 Qwen3-4B 讲怎么准备训练和部署资料，报告速度也只能按其 target 和负载来解读。两项工作分别提供系统实现和模型准备的参考。[Meta 论文摘要、Fig. 1](readings/Efficient_Speculative_Decoding_for_Llama_at_Scale_Challenges_and_Solutions.pdf) · [Baseten 工程说明](https://www.baseten.co/blog/how-to-train-custom-eagle-3-heads-for-speculative-decoding/)

### 4.3 原生多 token 预测与并行草稿

DeepSeek-V3 把 MTP 模块放进预训练。主干表示 $h_t$ 已能给 $t+1$ 的预测。当 $t+1$ 被选中，MTP 模块可以消费它的 embedding 和 $h_t$，预测 $t+2$，继续遵守因果条件。用模块为每轮多猜一项时 $E=1+\alpha$，按每轮提交数衡量其上限为 2。训练时预测未来 token 有额外监督信号，部署时能否加载该模块、能否按验证器要求采样、值不值额外算力，要分别核对。原报告 §5.4.3 的多种生成主题测试中，额外 token 的接受率为 85–90%，报告的速度为基线的 1.8 倍。[讲义第 37–38 页](12_llm_serving_spec_decoding.pdf#page=37) · [DeepSeek-V3 Technical Report，§2.2](readings/DeepSeek-V3_Technical_Report.pdf) · [DeepSeek 的硬件分析，§2.3.3](https://arxiv.org/html/2505.09343v2#S2.SS3.SSS3)

DFlash 的切入点是缩短草稿生成的关键路径。已知一个锚点后，把接下来的多个位置作为待预测占位，轻量 drafter 读取目标模型的多层特征，在一个前向里同时给出后续候选，目标模型照常做核验。课件以 16 token 的块大小说明并行性。原论文训练时把锚点放在块首，余下位置做预测，块大小和新增草稿数应按实现口径区分。一次前向的时间仍随块宽、注意力和显存变化。即使并行出候选，越靠后的 token 往往越依赖前面生成的值。例如多处字段的引号和分隔符要与已选值协调。

DSpark 在这种并行骨干之上加一个轻量的条件化预测头，让后面位置更能利用前面猜测，随后让置信度头估计能存活多长的前缀。scheduler 再按负载决定送几个位置去验。理解时把「草稿块已经算出来」和「目标真正核验了几项」分开。为了保住高并发的算力，后半块可以不进入目标 forward。若按请求负载先定长度，再按精确规则核验，动态减短只是少做推测。若看过尚未核验的草稿值再决定选哪项，就要让核验器反映筛选后的真实提议机制。直接用被筛之前的 $q$ 代入公式未必精确。[讲义第 39–42 页](12_llm_serving_spec_decoding.pdf#page=39) · [DFlash，§3](readings/DFlash_Block_Diffusion_for_Flash_Speculative_Decoding.pdf) · [DSpark，方法与系统实现](readings/DSpark_Confidence-Scheduled_Speculative_Decoding_with_Semi-Autoregressive_Generation.pdf)

**论文与工程证据**例子要看参照。DSpark 原文 §5.4 在 DeepSeek-V4 Flash 与 Pro 的预览版服务测了真实流量，报告相同总吞吐附近每用户生成速度比 MTP-1 快 60–85%。NVIDIA 的 5.8 倍是单块 B300、vLLM、Gemma 4 31B、并发 1 与自回归基线的 Math500 对比。同表 MT-Bench 是 3.0 倍。fal 的 prompt expander 为同一个目标任务重训了领域草稿，并修改引擎适配。其「超过 1000 token/s」来自 TP 4 的测试，生产选 TP 1，作者报告约 830 token/s。16 倍指在最低每用户交互速度 300 token/s 条件下同卡总吞吐相对起始配置的变化，指标和单请求倍率不同。[NVIDIA Table 2](https://developer.nvidia.com/blog/boost-inference-performance-up-to-15x-on-nvidia-blackwell-using-dflash-speculative-decoding/) · [fal 工程记录](readings/How_We_Achieved_1000_tok_s_and_16x_Throughput_with_DSpark_for_Ideogram_V4_Prompt_Expander.html)

### 4.4 输入里已有的内容，可以先拿来猜

Prompt Lookup 从当前请求中找匹配后缀并复制后续。REST 从存储的文本片段找候选。SuffixDecoding 在请求内和全局历史上查相似后缀，并用匹配长度和历史频数组织后续草稿。Lookahead Decoding 则在迭代中建立可用的 n-gram 候选，核验并行推进。它们说明草稿可以来自重复结构，例如工单 schema 的字段名或大量保持原样的文件片段。开销从 GPU 草稿模型转到 CPU 索引维护、查找、拷贝和目标核验。长字段有规律时可试，短请求或没有匹配时要有 $k=0$ 或其他草稿方案。应用使用共享文本索引时，按授权范围隔离和淘汰缓存属于实现设计，精确核验不负责跨租户数据隔离。[讲义第 43–46 页](12_llm_serving_spec_decoding.pdf#page=43) · [Prompt Lookup](readings/Prompt_Lookup_Decoding.html) · [REST](readings/REST_Retrieval-Based_Speculative_Decoding.pdf) · [SuffixDecoding](readings/SuffixDecoding_Extreme_Speculative_Decoding_for_Emerging_AI_Applications.pdf) · [Lookahead Decoding](readings/Break_the_Sequential_Dependency_of_LLM_Inference_Using_Lookahead_Decoding.pdf)

修改已有文件是「候选大多可以预测」的例子。Cursor 的文章解释了将原文件作为草稿对单点修改有什么收益。OpenAI 的 Predicted Outputs 指南展示了应用提交预测片段，以及如何读取接受和拒绝计数。服务接入时把它作为可选加速建议，业务的 JSON schema 校验照常执行。预测被拒也可能产生计费，读对应服务的使用明细再算成本。[Cursor 原文](readings/Editing_Files_at_1000_Tokens_per_Second.html) · [Predicted Outputs 指南](https://developers.openai.com/api/docs/guides/predicted-outputs)

## 5．树形验证、变长批处理和放宽规则

### 5.1 树共享前缀，掩码把不同分支隔开

**讲义主线**参见 [第 47–54 页](12_llm_serving_spec_decoding.pdf#page=47)。链的代价在于猜错了早期一项，后面的猜测整个失效。SpecInfer 将候选组成树，一起送进目标模型进行树注意力。看一个课堂图的工单版，公共前缀记为 `ctx`，三个步骤是选类别，然后选分隔符，最后进入下一字段。

```text
ctx
├─ 1 billing
│  ├─ 3 ,
│  │  └─ 6 "priority"
│  └─ 4 }
└─ 2 technical
   └─ 5 ,
```

将六个节点展开成一组 query，并为同一深度的节点分配相同逻辑位置。节点 6 的一行掩码只允许看见公共上下文、节点 1、3 及自己。它看不到邻接内存中的另一个逗号节点 5。这个逗号位于 `technical` 路径，两处 token 字符相同，隐藏状态取决于历史，不能交换 KV。节点前向返回的 logits 用来核验它的下一步，进入节点 1 的分数则由其父前缀给出。每条路径对应的目标条件概率因此和按该路径单独前向的语义一致。[讲义第 48–50 页](12_llm_serving_spec_decoding.pdf#page=48) · [SpecInfer，§4](readings/SpecInfer_Accelerating_Large_Language_Model_Serving_with_Tree-based_Speculative_Inference_and_Verification.pdf)

掩码解决的是怎样拿到正确分数。选择算法还要独立证明。贪心验证沿目标 argmax 从根向下走，一旦这一步的目标 token 没铺在树里，就输出这个 token 并结束本轮。随机采样时，不能把候选分支按模型打分选最长或最高分，也不能随便对每条兄弟枝套一遍链式 $p/q$。SpecInfer 用多步推测采样为候选和剪枝定义校验规则。Sequoia 的验证方法结合无放回采样和概率更新，避免重复试同一失败候选。Block Verification 则考虑整块决定能保留的前缀长度，仍给出不变分布的证明。一个简单而正确的**教学实现**是从每个真实前缀直接按目标 $p$ 抽一次，若抽中的 token 恰好是树中的孩子就沿用缓存继续走，否则提交该 token 并结束。本轮树的作用是多准备一些可能已算过的目标分布。它足以讲清树与输出策略的分工，但不等价于 SpecInfer 或 Sequoia 的多候选接受算法，接受长度也可能不同。[SpecInfer，§4.3、Algorithm 2](readings/SpecInfer_Accelerating_Large_Language_Model_Serving_with_Tree-based_Speculative_Inference_and_Verification.pdf) · [Sequoia，§3](readings/Sequoia_Scalable_Robust_and_Hardware-aware_Speculative_Decoding.pdf) · [Block Verification](readings/Block_Verification_Accelerates_Speculative_Decoding.pdf)

树怎么长又是一个问题。第 54 页把每个节点的路径接受机会近似成沿路置信度的乘积，再把树中各节点的这项数值相加，近似这一轮可利用的候选节点数量。父节点的值至少等于子节点的值，若按值选前 $m$ 个并在平分时优先父节点，就得到前缀闭合的候选集。Sequoia 则用分支接受机会和节点预算做动态规划，再用硬件测量决定深度和总规模。SGLang 的步数、分枝候选宽度、核验预算是三个参数，具体默认值与支持的 mode 应查看部署版本的文档。每请求草稿数量不同也能一起验证，例如 4、2、0 项草稿对应 5、3、1 个 query。将其展平后用偏移量 0、5、8、9 划回请求。树掩码管同一请求不同分支的可见性，偏移量和批处理掩码管不同请求的边界。[讲义第 51、53–54 页](12_llm_serving_spec_decoding.pdf#page=51) · [vLLM 架构说明](readings/Inside_vLLM_Anatomy_of_a_High-Throughput_LLM_Inference_System.html) · [SGLang 文档](https://docs.sglang.io/docs/advanced_features/speculative_decoding)

### 5.2 第一次拒绝后，引擎到底留下谁的 KV

**讲义主线**参见 [第 63 页](12_llm_serving_spec_decoding.pdf#page=63)。用「已对外提交」和「KV 已完成」两根位置指针解释这张图。在讲义的调度约定里，目标模型前一轮采出的最后一个 token $t$ 已经决定，本轮把 $t$ 作为 query 处理，对它的 KV 才补齐。候选输入是 $t,d_1,d_2,d_3,d_4$，$t$ 的 logits 评估 $d_1$，$d_1$ 的 logits 评估 $d_2$，依次类推。图上从 `The cat` 往后草稿 `sat on the mat`，前两项通过，第三项被拒并从剩余分布抽到 `a`。本轮新增输出为 `sat on a`。

| 项目 | 本轮状态变更 |
|---|---|
| 交给上层的序列 | 只发送已经决定的 `sat on a`。 |
| 目标 KV | 沿实际路径留下新计算的 `cat sat on`。以 `the mat` 为输入生成的 KV 无法给 `a` 这条路径复用。 |
| 下轮首个 query | `a` 已决定，本轮没用它做前向，下轮将它送入模型。全通过后额外采出的 token 也一样。 |
| 草稿模型 | 回到对齐的实际前缀，处理补采结果后再继续。树验证仅保留最终路径上的候选槽位。 |

**工程推导**可以借用 Java 的两阶段状态更新来理解。前向期间提前分配 slot，用 request id、当前前缀长度与本轮编号关联候选。采样完成再把被选分支变成下轮可读状态。引擎落地可以拷贝 KV，也可以更新映射，关键在于下轮可见性和序列位置保持一致。取消或超时时，结束本轮后按引擎的生命周期回收预留资源。计数需把 `drafted`、`verified`、`accepted` 和 `committed` 各自打点，因拒绝处的补采和全通过时的额外项都能增加 committed。指标语义在部署时以使用版本为准。vLLM RFC #64099 提议分别统计草稿模型提出、目标模型实际前向核验和目标接受的候选。设草稿提了 4 项，语法排除最后 2 项，最终接受 1 项。RFC 的同步调度示例是 4 / 2 / 1，异步示例是 4 / 4 / 1。两者接受数相同，异步示例在同一次目标模型前向中多处理两个候选位置。提交数还可能计入目标模型产生的补采 token。RFC 是提案，实际指标名和口径要查部署版本。[讲义第 63 页](12_llm_serving_spec_decoding.pdf#page=63) · [vLLM 架构说明](readings/Inside_vLLM_Anatomy_of_a_High-Throughput_LLM_Inference_System.html) · [vLLM RFC #64099](https://github.com/vllm-project/vllm/issues/64099)

### 5.3 放宽后的收益，需要重新定义可接受输出

**讲义主线**参见 [第 55–61、77 页](12_llm_serving_spec_decoding.pdf#page=55)。精确验证的问题是能否保持原目标的生成行为。如果应用只关心任务质量，可能愿意接纳不同措辞或相近的推理步骤来换速度。它修改了采样机制，需要新的质量验证。讲义逐一列出五种修改位置。

| 改在哪里 | 讲义举例 | 工单任务应观察什么 |
|---|---|---|
| 草稿粒度 | 草稿器给一整个推理步骤，目标或 judge 给步骤评分 | 多个局部合理步骤能否共同导出正确类别，是否有漏步骤 |
| 匹配定义 | 允许相似 token、组内替换 | 相似词替换能不能改变枚举值，例如 `billing` 变成近义但非法的值 |
| verifier | 用更便宜的目标近似，如稀疏 KV 或少量专家 | 长工单的关键信息被裁掉后，分类和置信策略是否退化 |
| 接受测试 | 放松接受阈值、typical acceptance | JSON 合法率可能没变化，类别比例和优先级错误是否漂移 |
| 额外 judge | 一个轻量分类器对严格拒绝的 token 再作判断 | 错误接受是集中在常见类，还是系统性漏掉少数紧急工单 |

Judge Decoding 学的是「这个拒绝对最终质量是否有害」，只能用训练及评测分布下的指标说明取舍。两篇 relaxed/lossy 阅读补充了放宽接受的不同机制和失败条件。看这些结果时，先核对基准、采样设置，再看统计质量有无漂移，最后观察自己任务的高成本错误。相比之下 MagicDec 的稀疏缓存只交给草稿，目标仍用完整路径作精确核验。区分谁使用近似比看方法名更重要。[Judge Decoding，§3–4](readings/Judge_Decoding_Faster_Speculative_Sampling_Requires_Going_Beyond_Model_Alignment.pdf) · [Revisiting Lossy Verification](readings/Revisiting_Lossy_Verification_in_Speculative_Decoding_Mechanisms_Trade-offs_and_Failure_Modes.pdf) · [Training-free Relaxed Decoding](readings/A_Practical_Investigation_of_Training-free_Relaxed_Speculative_Decoding.pdf)

## 6．同一个算法，为什么会随并发翻转

**讲义主线**参见 [第 62–68 页](12_llm_serving_spec_decoding.pdf#page=62)。现代引擎会在每步重新组 batch，请求结束或新请求到达时重新排队和分配 token 预算。每请求用统一的固定 $k$ 会把「多猜一点」的影响扩散给整批。对不同请求选不同的 $k_i$，目标模型的 query 数是 $\sum_i(1+k_i)$ 的近似，变长 batch 的布局前面已见过。硬件已很忙时，同一前向的额外 query 会占用别的请求本可使用的算力。

课件把 H200 权重模型带入 $k=4,\alpha=0.8$ 计算。下面是**课堂估算**，使用精确算出的 $E=3.3616$ 并忽略草稿开销、KV 读取和调度。

| Batch | 普通时的 query 数 | 推测时的 query 数 | 普通每用户输出 token/s | 推测每用户输出 token/s |
|---:|---:|---:|---:|---:|
| 16 | 16 | 80 | 约 300 | 约 1008 |
| 64 | 64 | 320 | 约 300 | 约 649 |
| 256 | 256 | 1280 | 约 241 | 约 162 |

计算第 3 行时，普通每步约耗 4.14 ms，只提交一个 token。推测每步约耗 20.71 ms，平均提交 3.36 个。接受率没变，核验每轮变慢得更多。即使接受率升高，容量也可能被草稿器显存、没被接纳的算力和长时间占用 batch 的请求吃掉。[讲义第 64–65 页](12_llm_serving_spec_decoding.pdf#page=64)

TurboSpec 把它变成一个反馈循环。引擎用已观察的接受长度估计每个请求选不同核验长度会推进多少 token，拟合整批前向时间，再在预算内选 $k_i$。讲义把这一局部优化写作 $\widehat{G}=\sum_i\widehat{E}_i(k_i)/\widehat{T}(k_1,\ldots,k_b)$。可以把它理解为这一步每秒真正推进的 token 数。TurboSpec 原文还区分草稿长度和核验长度，并用在线反馈按请求或引擎状态调整。不同工作的 goodput 定义会变化。比如业务也可定义为「每秒完成且满足 SLO（服务质量目标，如尾延迟阈值）的请求」，这需要网络、队列和首 token 延迟一起实测。包括 $k=0$ 允许调度器选择普通解码，预测误差和调整开销仍可能让当时的决策表现不佳。[讲义第 66–68、74 页](12_llm_serving_spec_decoding.pdf#page=66) · [TurboSpec 修订版，§3–5](readings/TurboSpec_Closed-loop_Speculation_Control_System_for_Optimizing_LLM_Serving_Goodput.pdf) · [AdaServe](readings/AdaServe_SLO-Customized_LLM_Serving_with_Fine-Grained_Speculative_Decoding.pdf)

## 7．长上下文与 MoE 改的是哪部分账

### 7.1 MagicDec 与长上下文的 KV 成本

**讲义主线**参见 [第 69–71 页](12_llm_serving_spec_decoding.pdf#page=69)。权重可以跨请求摊薄。一批不同会话的 KV 却各属于自己的前缀，batch 变大时读取的 KV 通常也变多。按讲义例子的 8B、32 层、每层 8 个 KV 头、头宽 128、每元素 2 字节，8K（8192）上下文的每请求 KV 尺寸约为

$$
2_{\text{K/V}}\times32\times8\times128\times2\times8192
=1\text{ GiB}.
$$

32 个不同请求大约产生 34.36 GB KV，加上约 16 GB 权重，此时「只算权重」的拐点不再描述整步。KV 的尺寸是粗估，实际读取次数还取决于 attention kernel、前缀共享、分页和缓存。GQA 使多个 query heads 共用一个 KV head。同一请求的多个 query 仍可复用读取的 KV，具体收益应看实现。MagicDec 用稀疏 KV 降低草稿成本，由保留完整 KV 的目标模型核验。StreamingLLM 变体保留开头的锚点与末尾的近期窗口。SnapKV 变体根据注意力选取前缀中值得保留的位置。若草稿遗漏了关键工单信息，候选可能更容易被拒绝。论文 Table 2 报告最高 2.51 倍的配置使用 SnapKV 自推测，条件为 LLaMA-3.1-8B、8 张 H100、100,000 个 prefill token、batch 41、草稿长度 11。讲义第 70–71 页的单 H200 字节例子说明机制。[MagicDec，§3、§5 与 Table 2](readings/MagicDec_Breaking_the_Latency-Throughput_Tradeoff_for_Long_Context_Generation_with_Speculative_Decoding.pdf#page=9)

### 7.2 Cascade 与专家路由

**讲义主线**参见 [第 72–75 页](12_llm_serving_spec_decoding.pdf#page=72)。MoE 层的路由器给每个 token 选择一小组专家（各有独立参数的子网络）。当一轮核验多个候选时，它们用到的专家并不总一样。一轮触达的专家多了，就要读更多权重，专家并行还可能增加通信。

**教学推导**用 $N$ 个专家、每 token 选择 $m$ 个、共验证 $n$ 个 query 来算。假设路由均匀且不同 token 独立，一个特定专家在单个 token 缺席的概率为 $1-m/N$。它在整批缺席的概率为 $(1-m/N)^n$，所以期望触达 $N[1-(1-m/N)^n]$ 个专家。课件的 Mixtral 例子取 $N=8,m=2,n=8$，约 7.2 个，对比单 token 时的 2 个约为 3.6 倍。实际相邻 token 经常共享专家，测量应考虑路由分布、权重缓存和网络。这是专家并集的估计，不能直接当延迟倍数。

Cascade 给每个请求短时间试几个 $k$，根据输出推进量和额外核验时间估计收益，随后在较长窗口用效果较好的取值，必要时关闭推测。保持 drafter 的 KV 跟进，以便后续恢复，在作者的方案仍约有 2–3% 的开销。论文报告的 5% 最坏减速和相对静态 $k$ 的 7–14% 吞吐改善对应其测试集、静态基线和输入设置。它的短时试验与 TurboSpec 的在线估计都在决定下一步投入多少，但目标函数和额外实验成本不同。[Cascade，Fig. 1、§3–5](readings/Utility-Driven_Speculative_Decoding_for_Mixture-of-Experts.pdf) · [讲义第 73–74 页](12_llm_serving_spec_decoding.pdf#page=73)

## 8．把它作为服务变更来上线和诊断

**工程建议**基于讲义第 75 页的三个杠杆。提高 $E$，降低草稿成本，控制目标核验成本。上一课解决了 batch、显存分页和并行度的基本问题。这里建议按下面顺序验收 Java 工单接口。

1. **先锁住正确性基线。** 使用相同目标 checkpoint、tokenizer、精度、schema、解码参数和停止规则。greedy 按基准核对 token 序列，定位分歧发生在哪个请求、前缀和位置。随机模式补条件概率小测试、重复采样统计和任务验收，例如 JSON 解析、类别、优先级一致性及错误分布。批内混合 schema 时每条请求都有自己的合法前缀与 mask。
2. **分清接口和引擎计时。** 记录客户端总时延与完整 JSON 可交付时间。端到端观测可分 TTFT（客户端发请求到收到首 token）、TPOT（首 token 后的平均生成耗时，仅在有后续 token 时）、相邻 token 或 stream chunk 的等待时间、端到端延迟 p50/p95/p99、并发下总 token/s 和满足 SLO 的请求/s。调度一次提交多个 token 时，TPOT 降低也可能出现更长的空档。对工单解析器来说，网络 stream 首包更快也不保证完整对象更快。
3. **给 A/B 足够可比的负载。** 用同一硬件和输入集合，交叉比较 $k=0$、短草稿、动态 $k$。单请求测最低延迟，再用低、中、重载测开始排队后的变化。服务记录输入/输出长度桶、实际 batch、每深度前缀存活率、草稿及核验时间、显存和回收、窗口内的拟合误差。长上下文、MoE 和不同解码模式单列。并发和请求到达速率不同，说明压测用的是固定并发还是固定到达率。
4. **看哪笔开销把收益吃掉。** 接受前缀短、草稿很耗时，先查 tokenizer/模板、checkpoint 对应关系和实际 workload，再试检索草稿或重新定预算。接受率高但核验时间随 batch 急升，先调小核验长度并保留 $k=0$。若核验快但端到端没变，拆开队列、prefill、重复调用、后端业务和网络。Greedy 基准明显分叉时先排查前缀状态、mask、KV 和采样配置，不拿速度解释质量变更。
5. **把训练当独立工作流。** 自训草稿时可比较固定 target 的输出蒸馏、让草稿在训练中看到自身推断、并行块的位置损失、以及目标特征缓存或流式传输。模型升级时要重新核对草稿适配与负载；线上适配还需要受控的数据与回滚。SpecForge、Speculators、TorchSpec 是不同训练或发布管线，说明训练数据处理如何接上服务配置，框架的默认选项和支持版本参见各自归档。[SpecForge](readings/SpecForge_A_Flexible_and_Efficient_Open-Source_Training_Framework_for_Speculative_Decoding.pdf) · [Speculators](readings/Speculators_A_unified_library_for_building_evaluating_and_storing_speculative_decoding_algorithms_for_LLM_inference_in_vLLM.html) · [TorchSpec](readings/TorchSpec_A_PyTorch_native_library_for_training_speculative_decoding_models.html)

**已执行的教学验证**是下面的 CPU 脚本。它用有理数枚举接受和补采两条路径，校验讲义的概率表，并用目标分布随前缀变化的两 token 例子检查联合分布。脚本还按上面公式计算课堂 roofline 数值。它不访问模型、GPU、JSON 接口或生产引擎，前五项服务验收是实验方案。[脚本](examples/speculative_sampling.py) · [本次运行记录](examples/RESULTS.json)

## 9．自测与参考答案

1. 对三个类别 $p=(0.6,0.3,0.1)$、$q=(0.3,0.6,0.1)$，已知草稿抽到第二项，它有多大概率被接纳？一旦被拒，替代 token 从哪里来？  
   **参考答案** 接受机会为 $0.3/0.6=0.5$。拒绝分布的全部质量都在第一项。无条件看，第一项来自本就接受的 0.3 和发生拒绝后补上的 0.3。第一项输出概率为 0.6。
2. 两个候选都叫逗号，但来自不同分类路径，缓存能否合并？如果在第三个草稿处补出新 token，下一轮 cache pointer 应放哪里？  
   **参考答案** 逗号的隐藏状态依赖祖先，两个版本分别核验。留到第二个成功草稿的目标 KV。补出来的 token 被提交为输出，但它的 KV 要等送入下一轮前向。
3. 草稿每层的接受概率条件相同，$\alpha=0.8,k=4$。普通步长 1，草稿共花 0.2，核验由 1 涨到 3.5。是接受率掉了还是服务账变了？  
   **参考答案** 平均提交数还约为 3.36。新速度比约为 $3.36/3.7=0.91$，原因是核验步长变长。记录实际 batch 和目标 step time 并比较更小的 $k$。
4. 能不能在树上选最长且语义合理的路径，然后声称输出分布一致？  
   **参考答案** 树掩码只得到各前缀的正确 logits。按长度或语义偏好选路径会改动各 token 的选择概率。贪心应沿每个真实前缀的目标 argmax，随机模式使用有分布保证的验证规则。
5. 长上下文 batch 很大，为什么仍可能得到加速？把稀疏 KV 用在 target 会怎样？  
   **参考答案** 权重读可由 batch 共用，长前缀的 K、V 访问仍重。一个核验步的多个查询可以利用同一请求的较长 KV，草稿只读定长稀疏 KV，便可能降低总成本。若用稀疏 KV 替代原目标的完整核验，条件分布也可能改变，需要重新定义质量和参照。
6. 两家厂商说各自 5 倍和 16 倍，哪家更适合工单接口？  
   **参考答案** 先对齐对照组、模型、硬件、并发和度量。相同并发下离线吞吐倍数、相同交互阈值下可服务容量倍数和用户完整 JSON 时延的倍数三者不能互换。按工单长度桶与到达负载做 A/B，核对应用验收及端到端 SLO 后决定。

## 阅读地图与版本

**阅读补充**下表每项都对应课程本地原件。有条件的数字回到使用的论文正文或工程原文，课程阅读页用来核对清单和分组。其中的自动摘要只作导航。预印本版本来自本地 PDF 标记，网页用课次归档快照。[课程阅读页](../site/readings/nov-11.html)

| 讲义问题 | 原件 | 读这项可以消除的疑问 |
|---|---|---|
| 起点与证明 | [speculative decoding](readings/Fast_Inference_from_Transformers_via_Speculative_Decoding.pdf)，2211.17192v2 | §2–4、附录 A.1 与 Table 2 给出链式算法、接纳长度模型及 T5X 对照 |
|  | [speculative sampling](readings/Accelerating_Large_Language_Model_Decoding_with_Speculative_Sampling.pdf)，2302.01318v1 | §2.3–4 与 Appendix A.1 复核随机采样、Chinchilla 配置及数值差异 |
|  | [blockwise parallel decoding](readings/Blockwise_Parallel_Decoding_for_Deep_Autoregressive_Models.pdf)，1811.03115v1 | 以跨步预测和验证引入较早的块式思路，和等分布随机算法分别读 |
| 草稿模型和训练 | [DistillSpec](readings/DistillSpec_Improving_Speculative_Decoding_via_Knowledge_Distillation.pdf)，2310.08461v2 | 对草稿实际遇到的前缀做蒸馏 |
|  | [self-speculative](readings/Draft_Verify_Lossless_Large_Language_Model_Acceleration_via_Self-Speculative_Decoding.pdf)，2309.08168v2 | 选择性跳层的自草稿和完整目标验证 |
|  | [LayerSkip](readings/LayerSkip_Enabling_Early_Exit_Inference_and_Self-Speculative_Decoding.pdf)，2404.16710v4 | 早退训练和前层 KV 复用 |
|  | [SWIFT](readings/SWIFT_On-the-Fly_Self-Speculative_Decoding_for_LLM_Inference_Acceleration.pdf)，2410.06916v2 | 按上下文适应跳层的代价 |
|  | [Medusa](readings/Medusa_Simple_LLM_Inference_Acceleration_Framework_with_Multiple_Decoding_Heads.pdf)，2401.10774v3 | 提前放多个预测头、树与 typical acceptance 的配置边界 |
|  | [EAGLE](readings/EAGLE_Speculative_Sampling_Requires_Rethinking_Feature_Uncertainty.pdf)，2401.15077v3 | 输入已采 token 以消除下一特征分支歧义 |
|  | [EAGLE-2](readings/EAGLE-2_Faster_Inference_of_Language_Models_with_Dynamic_Draft_Trees.pdf)，2406.16858v2 | 按置信度分配动态树 |
|  | [EAGLE-3](readings/EAGLE-3_Scaling_up_Inference_Acceleration_of_Large_Language_Models_via_Training-Time_Test.pdf)，2503.01840v3 | 多层特征、token 预测损失、训练中喂自身输出 |
|  | [EAGLE at Meta](readings/Efficient_Speculative_Decoding_for_Llama_at_Scale_Challenges_and_Solutions.pdf)，2508.08192v1 | 线上服务还优化 GPU 数据流、控制流与批处理 |
|  | [DeepSeek-V3 MTP](readings/DeepSeek-V3_Technical_Report.pdf)，2412.19437v2 | 原生 MTP 训练结构和额外一 token 的测量 |
| 整块草稿与扩展 | [DFlash](readings/DFlash_Block_Diffusion_for_Flash_Speculative_Decoding.pdf)，2602.06036v2 | 多层目标特征作为条件，一次提出整个块 |
|  | [Domino](readings/Domino_Decoupling_Causal_Modeling_from_Autoregressive_Drafting_in_Speculative_Decoding.pdf)，2605.29707v1 | 将块内因果建模和重型自回归草稿计算分开 |
|  | [DSpark](readings/DSpark_Confidence-Scheduled_Speculative_Decoding_with_Semi-Autoregressive_Generation.pdf)，2607.05147v1 | 并行预测加轻量条件化与核验长度调度 |
|  | [DFlash 2](readings/DFlash_2_Keep_Drafting_Parallel.html)，课程 HTML 快照 | 作者工程文章，查看并行块的后续改进及演示条件 |
|  | [DSpine](readings/DSpine_Draft_in_Parallel_Condition_Through_Depth_Adjacent_Causal_Injection_for_Speculative_Decoding.pdf)，2609.36173v2 | 利用深度方向的相邻因果注入改善块内协调 |
|  | [H-Spec](readings/H-Spec_Parallel_Speculative_Decoding_Without_a_Drafter-Side_KV_Cache.pdf)，2609.24197v1 | 探索避免另存草稿侧 KV 和相应的适配 |
|  | [Uno](readings/Unlocking_Lossless_Speedups_in_LLMs_via_Discrete_Diffusion.pdf)，2609.04010v1 | 离散扩散草稿结合精确核验 |
| 文本已有候选 | [REST](readings/REST_Retrieval-Based_Speculative_Decoding.pdf)，2311.08252v2 | 从数据存储检索后续候选 |
|  | [lookahead decoding](readings/Break_the_Sequential_Dependency_of_LLM_Inference_Using_Lookahead_Decoding.pdf)，2402.02057v1 | 从生成过程积累 n-gram 候选，不依赖辅助模型 |
|  | [prompt lookup](readings/Prompt_Lookup_Decoding.html)，课程 HTML 快照 | 从当前 prompt 匹配并复制 |
|  | [SuffixDecoding](readings/SuffixDecoding_Extreme_Speculative_Decoding_for_Emerging_AI_Applications.pdf)，2411.04975v3 | 本地、全局后缀树与重复的 agent 负载 |
|  | [speculative edits](readings/Editing_Files_at_1000_Tokens_per_Second.html)，课程 HTML 快照 | 厂商自述的重复文件编辑实践 |
| 验证路径和边界 | [SpecInfer](readings/SpecInfer_Accelerating_Large_Language_Model_Serving_with_Tree-based_Speculative_Inference_and_Verification.pdf)，2305.09781v4 | 树注意力、Greedy 与多步随机验证 |
|  | [Sequoia](readings/Sequoia_Scalable_Robust_and_Hardware-aware_Speculative_Decoding.pdf)，2402.12374v3 | 动态规划树、无放回采样和硬件 profiling |
|  | [SpecExec](readings/SpecExec_Massively_Parallel_Speculative_Decoding_for_Interactive_LLM_Inference_on_Consumer_Devices.pdf)，2406.02532v3 | 消费端参数 offload 场景的并行核验预算 |
|  | [block verification](readings/Block_Verification_Accelerates_Speculative_Decoding.pdf)，2403.10444v3 | 整块选择可保留长度的等分布验证 |
|  | [Judge Decoding](readings/Judge_Decoding_Faster_Speculative_Sampling_Requires_Going_Beyond_Model_Alignment.pdf)，2501.19309v1 | 用小分类器评判拒绝项对下游质量的影响 |
|  | [lossy verification](readings/Revisiting_Lossy_Verification_in_Speculative_Decoding_Mechanisms_Trade-offs_and_Failure_Modes.pdf)，2607.26627v2 | 放宽策略的结构、失败模式与分布偏移 |
|  | [relaxed acceptance](readings/A_Practical_Investigation_of_Training-free_Relaxed_Speculative_Decoding.pdf)，2607.08690v1 | 训练外放宽规则的速度/质量对照 |
| 系统与控制 | [vLLM anatomy](readings/Inside_vLLM_Anatomy_of_a_High-Throughput_LLM_Inference_System.html)，课程 HTML 快照 | 引擎 step、调度、KV 和推测解码集成 |
|  | [SmartSpec / TurboSpec](readings/TurboSpec_Closed-loop_Speculation_Control_System_for_Optimizing_LLM_Serving_Goodput.pdf)，2406.14066v3 | 当前本地 v3 为 TurboSpec，读调度控制与核验代价 |
|  | [MagicDec](readings/MagicDec_Breaking_the_Latency-Throughput_Tradeoff_for_Long_Context_Generation_with_Speculative_Decoding.pdf)，2408.11049v5 | 长上下文的稀疏草稿 KV 与核验模型 |
|  | [D-cut](readings/D-cut_Adaptive_Verification_Depth_Pruning_for_Batched_Speculative_Decoding.pdf)，2607.14647v1 | 根据高并发下的收益裁剪验证深度 |
|  | [Cascade](readings/Utility-Driven_Speculative_Decoding_for_Mixture-of-Experts.pdf)，2506.20675v1 | 在专家路由开销下试探不同长度并回退 |
|  | [mirror speculative decoding](readings/Mirror_Speculative_Decoding_Breaking_the_Serial_Barrier_in_LLM_Inference.pdf)，2510.13161v2 | 不同类型加速设备上的异构并行，属于超出讲义的实现路径 |
|  | [online spec decoding](readings/Online_Speculative_Decoding.pdf)，2310.07177v4 | 用实际查询分布适配草稿模型，属于训练扩展 |
|  | [AdaServe](readings/AdaServe_SLO-Customized_LLM_Serving_with_Fine-Grained_Speculative_Decoding.pdf)，2501.12162v2 | 根据不同服务目标分配细粒度推测预算 |
|  | [AgentSpec](readings/AgentSpec_Speculative_Decoding_for_Batch_Inference_of_LLM_Agents.pdf)，2608.24004v1 | 面向 agent 的 batch 与候选序列差异，属于负载扩展 |
| 工程与训练工具 | [SpecForge](readings/SpecForge_A_Flexible_and_Efficient_Open-Source_Training_Framework_for_Speculative_Decoding.pdf)，2603.18567v1 | 批量训练与部署 EAGLE-3 的开源训练流程 |
|  | [Speculators](readings/Speculators_A_unified_library_for_building_evaluating_and_storing_speculative_decoding_algorithms_for_LLM_inference_in_vLLM.html)，课程 HTML 快照 | 训练、评估和发布 draft adapter 的工程接口 |
|  | [TorchSpec](readings/TorchSpec_A_PyTorch_native_library_for_training_speculative_decoding_models.html)，课程 HTML 快照 | 分离生成目标特征和训练草稿的 worker |
|  | [fal](readings/How_We_Achieved_1000_tok_s_and_16x_Throughput_with_DSpark_for_Ideogram_V4_Prompt_Expander.html)，课程 HTML 快照 | prompt expander 的不同并发与交互约束下的倍率 |
|  | [D-PACE](readings/D-PACE_Dynamic_Position-Aware_Cross-Entropy_for_Parallel_Speculative_Drafting.pdf)，2605.18810v1 | 并行草稿学习随位置难度变化的损失权重 |

**讲义内嵌参考**另见 [REFERENCES.json](REFERENCES.json)。这些来源补传统抽样、模型架构、厂商 profile、引擎选项或指标定义，与上方指定阅读及性能主张各自对应。仅从线上页面核对或未能读取正文的来源已标明。

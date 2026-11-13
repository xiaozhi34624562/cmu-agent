# 从一次生成请求到整个推理集群：批处理、KV 分页与并行

本课对应 Harvard CS2680 **2026 年 11 月 4 日**的 *Efficient LLM serving basics III: Batching, paging, and parallelism*。[主讲义][slides]共 59 页；本目录的 12 是仓库稳定编号，原文件的 11 是官方 PDF 文件编号，两者都不是这里重新推算的授课顺序。11 月 2 日的 GPU 编程续讲归档在[目录 26](../26.AssignmentsFeedbackAndAgentPitfallsGPUProgrammingContinued/SOURCES.md)，是本课的背景，不是另一份“第 26 讲”。

这篇讲解面向做过 LLM 应用开发、也熟悉 Java 后端的读者。你已经知道请求队列、并发、缓存、线程池和服务延迟，但不需要预先掌握 GPU 核函数、分布式矩阵乘法或 KV 内存管理。我们会借这些工程经验建立入口，再解释类比在哪一步不再适用。

整课的问题不是“有哪些加速方法”，而是：**不同长度的生成请求一起到来，系统怎样安排计算、保存状态和交换数据，既让 GPU 做足有效工作，也让用户及时收到结果？** 学完应该能够沿一条请求时间线定位问题，解释一种优化为什么生效、付出了什么代价，并设计能检验这个解释的对照实验。

文中 PDF 页码均为阅读器中的实际页序，从 1 开始。讲义决定主线；论文补充机制和证据；标为“教学推导”的数字是便于手算的假设，标为“工程建议”的流程不是论文已验证的系统。末尾提供来源地图和可运行 CPU 算例。这里讨论归档论文的具体版本，不把旧版框架的实验结论当作今天软件版本的性能排名。

## 1. 三个请求为什么会把一个普通队列变复杂

**讲义主线：第 4–8 页；基础展开为教学推导。** 假设一个代码助手收到三个请求。为了讨论调度，先只保留长度和状态，不涉及特定业务。

| 请求 | 输入 token | 最终输出 token | 输入特点 |
|---|---:|---:|---|
| A | 128 | 20 | 一个短函数的解释 |
| B | 2,048 | 8 | 根据较长代码返回很短的分类结果 |
| C | 1,088 | 128 | 前 1,024 token 是重复的固定指令/示例，后 64 token 是新问题 |

输出长度是**事后观察值**。真实调度器通常只知道输入长度、最大输出限制和已经生成的 token，不能提前知道 B 只输出 8 个、C 会输出 128 个。将最大输出限制当作实际长度，会人为放大预留内存；把事后长度提供给调度器，则是在做带“先知”的实验。

如果这是普通 Java Web 服务，我们可能把三个任务交给线程池，每个任务执行完返回。生成模型有两点不同。第一，一个请求包含多次相互依赖的计算：得到第一个输出后，才能继续生成第二个。第二，已经运行的请求持有一份不断增长的 GPU 状态。暂停任务可以停止它继续消耗算力，但不会自动释放这份状态。

### 1.1 先把一次 Transformer 前向计算讲清楚

token 首先映射为向量，经过多层 Transformer，最后得到词表上各 token 的分数，再按采样规则选下一个 token。每层包含注意力和逐位置的前馈网络等计算。我们暂时省略归一化、残差及多头维度，只看一个位置的一次注意力：

$$
q=xW_Q,\quad k=xW_K,\quad v=xW_V,\qquad
\operatorname{Attention}(q,K,V)=\operatorname{softmax}\left(\frac{qK^T}{\sqrt d}\right)V.
$$

$x$ 是当前位置进入这一层的向量；$W_Q,W_K,W_V$ 是模型权重；$q$ 是当前要检索的 query，$K,V$ 收集允许访问的位置的 key 和 value；$d$ 是一个注意力头的维度。softmax 把相关性分数变成和为 1 的权重，再用它们加权求和 $V$。这里的“检索”是向量运算，不是向数据库发送查询。

因果模型中，一个位置只能看自己和更早的位置。已知完整输入时，这些位置仍可通过带因果遮罩的矩阵运算一并计算；“不能看未来”不等于“输入 token 必须逐个做前向”。而输出的下一个 token 尚未产生，无法预先把任意多个输出并行生成。

**Prefill** 处理已知输入，建立每层的 K、V，并产生第一个输出 token。**Decode** 把上一步产生的 token 作为新输入，结合已有 K、V，产生下一个输出。缓存的 K、V 就是 KV cache。在普通因果 Transformer、权重和位置规则不变时，历史位置的 K、V 不因尾部追加 token 而改变，因而可以复用。缓存的是每层的向量状态，不是字符串答案，也不是把整个历史重新送进前馈网络。

一个容易差一位的细节：处理完 A 的 128 个输入时，已有 128 个位置的 KV，并采样出第一个输出；这个输出自己的 KV，要在下一次前向中形成。讨论缓存长度时应区分“已处理位置数”和“已返回输出数”。[PagedAttention 第 3、5–6 页][paged]解释了这一执行过程。

### 1.2 KV 为什么会决定可并发多少请求

对每层拥有同样 KV 结构的模型，未分片、未量化 KV 的容量为：

$$
M_{KV}=2Lh_{KV}d\,b\,T.
$$

$L$ 是层数，$h_{KV}$ 是每层 KV 头数，$d$ 是头维度，$b$ 是每个元素的字节数，$T$ 是已经缓存的位置数，前面的 2 分别对应 K 和 V。结果单位是字节。GQA 让多个 query 头共享较少的 KV 头，因此这里用 $h_{KV}$，不能直接拿 query 头数代入。

取教学参数 $L=32,h_{KV}=8,d=128,b=2$，每个 token 占 $131,072$ 字节，即 128 KiB。B 的 2,048 个输入在这个模型里需要 256 MiB KV。32 个这样的请求仅输入 KV 就需 8 GiB，尚未计输出、权重、临时张量和分配损耗。这里不是某个部署模型的测量值，而是让你能检查量纲的计算。

因此服务至少要区分三类状态：不变的模型权重；每个活跃请求的 KV、已生成 token 和采样状态；等待调度的元数据。Java 对象表可以记录“请求 B 在运行”，真正占用大量容量的 KV 却在 GPU。一个线程退出、Future 被取消或 HTTP 连接断开，不代表 GPU 工作和 KV 引用已经安全释放。如何在迭代边界取消并回收，是后面缓存设计必须回答的问题。

### 1.3 为什么两阶段的瓶颈常常不同

Prefill 一次处理许多 token，矩阵乘法较大，较容易利用 GPU 的大量计算单元。单请求 decode 每步只处理一个新 token，却仍需要读取很多权重与历史 KV，容易受显存带宽限制。HBM 是 GPU 的高带宽显存；“容量足够”只说明装得下，“带宽足够”才决定数据能否及时送到计算单元。

用稠密模型的简化估算，每个 token 的权重相关运算约为 $2P$ FLOPs，$P$ 是参与运算的参数数，乘法和加法各算一次。若一个大小为 $N$ 的 batch 能共同摊销一次 $Pb$ 字节的权重读取（这里 $b$ 指权重每元素的字节数），权重部分的算术强度约为 $2N/b$ FLOPs/byte。$N$ 增大时，同一份权重带来更多计算。这是忽略了 KV、激活、缓存层次和具体算子效率的数量级估算，不能据此直接预测速度。

所以“decode 总是带宽瓶颈”过强。长上下文增加 KV 读取，大 batch 增加计算，GQA 又减少 KV，具体瓶颈会迁移。[Efficiently Scaling Transformer Inference 第 3–8 页][scaling]和历史归档 [NanoFlow 第 3–6 页][nanoflow]会在后文帮助修正这一初始直觉。

## 2. 先确定用户在等什么，再讨论吞吐量

**讲义主线：第 9–14 页；评测补充见 [On Evaluating Performance of LLM Inference Systems 第 2–9 页][evaluation]。**

设请求到达时刻是 $t_0$，第 $i$ 个输出 token 到达客户端的时刻是 $t_i$，总共输出 $n$ 个 token。统一时间单位后：

$$
TTFT=t_1-t_0,\qquad TBT_i=t_i-t_{i-1}\;(i=2,\ldots,n),
$$

$$
TPOT=\frac{t_n-t_1}{n-1},\qquad E2E=t_n-t_0=TTFT+(n-1)TPOT.
$$

TTFT 是用户看到第一个 token 前的等待，含排队及服务路径开销，不等于纯 prefill 计算时间。TBT 是每一个相邻输出间隔，描述中途是否卡顿；TPOT 是这些间隔的平均值。当 $n=1$ 时没有相邻输出间隔，TPOT 应记为不适用，而不是 0。若服务按多 token 一块发送，还要记录网络刷新行为，否则客户端 TBT 可能同时反映引擎和缓冲策略。

看一个教学时间线：TTFT 为 200 ms，随后五个间隔为 20、20、200、20、20 ms。TPOT 是 56 ms，E2E 是 480 ms。另一条时间线五个间隔都是 56 ms，TPOT 和 E2E 完全一样，用户看到的卡顿却不同。**平均生成速度不能说明最差的一次停顿。** 附带 CPU 算例会计算这两个序列，而不调用模型。

吞吐也至少有三个口径：每秒完成多少请求、每秒产生多少输出 token、每秒处理多少输入加输出 token。A、B、C 的工作量不同，三者不能互相替代。客户端每个请求的 token/s 也不能直接等同 GPU 总 token/s：单个用户可能变慢，但更多用户同时工作后，总吞吐上升。

当服务约定 TTFT 和生成间隔的上限时，可以定义 goodput，例如“每秒完成且满足本实验全部延迟条件的请求数”。这一定义必须同时给出 SLO（service-level objective，即服务预先设定的延迟等目标）、达标分位数和计数方式。P99 是第 99 百分位：约 99% 的测量不超过该值；对逐 token 间隔还是对每请求平均值取 P99，含义也不同。DistServe 用其 TTFT/TPOT 达标条件优化 goodput；Sarathi-Serve 强调尾部 TBT。两张都写“吞吐提高”的图，可能并非优化同一个目标。

评测论文检查 12 个系统的公开材料，提醒我们特别防范以下情况：短测试只观察到队列尚未积累的阶段；只报均值把尾部隐藏；不同系统使用不同注意力核却把收益都算给调度；用 E2E 除输出长度后把长时间 TTFT 稀释。它的推测解码案例还说明，一次验证批量吐出多个 token 会让大量 TBT 接近 0，中位数很好看，失败验证后的长停顿仍然存在。这是特定实验的现象，不是推测解码必然更差。

**工程建议。** 对 A、B、C 这类服务先画四条分布：排队时间、TTFT、逐 token TBT、E2E；同时记录已完成/未完成请求、到达率、输出长度和 KV 占用。在稳态与突发负载下分别看分位数。只有明确“B 的 prefill 插入时，A/C 的 TBT 尖峰上升”，我们才有证据进入下一节的调度问题。

## 3. Batch 的单位应该是一轮计算，还是整个请求

**讲义主线：第 15–19 页；机制来自 [Orca 第 5–10 页][orca]。**

传统静态 batch 的问题是：把 A、B 放进一批后，一直等这批所有生成完成，才能接收 C。B 已结束的槽位可能仍在等待 A；C 明明有机会提前计算，却被批次边界挡住。允许返回已完成结果能缓解客户端等待，但若引擎仍不能让新请求加入，就没有解决槽位闲置。

Continuous batching 把调度点放在每次模型迭代之间：移除完成请求，保留未完成请求，再加入满足计算与内存预算的新请求。它改变的是**每轮 batch 的成员**。请求内部的自回归依赖仍然存在。

先把 prefill 暂时排除，假设每轮耗时相同、最多两个请求同时 decode，三个教学任务分别还需 4、1、2 轮。静态批次先跑 `[A,B]` 四轮，再跑 `[C]` 两轮，共 6 轮。连续批处理第一轮跑 `[A,B]`，第二轮就用 C 替换 B，最终共 4 轮。这个例子验证空槽复用，不声称真实 GPU 延迟一定减少三分之一，因为真实 batch 大小、上下文长度和 prefill 都会改变每轮耗时。

### 3.1 长短输入不一样，怎样放进同一个矩阵

你可能想到先把输入 padding 到一样长。但 A 只有 128 个输入，B 有 2,048 个，补齐会引入大量无用位置。Orca 的 selective batching 区分两类运算：前馈、线性投影等逐位置运算可以把不同请求的有效 token 沿 token 维拼接；注意力必须保留各请求自己的序列边界、因果关系和 KV。

例如当前轮给 A、C 各执行一个 decode token，并给 B 执行 256 个 prefill token（下一节解释怎样把长输入切段），逐位置运算可以看到一个有 258 行的输入矩阵。之后注意力读取 A 的历史、B 的前缀和 C 的历史，不能让 A 看见 B 的 token。批处理共享的是权重与执行资源，不是三个请求的语义上下文。

GPU kernel 是提交给 GPU 执行的一段计算程序，thread block 是其中一组能够协作的线程；它们不是一条 HTTP 请求对应一个 Java 线程的关系。“注意力分别处理”指逻辑独立，不意味着必须启动三个独立 GPU kernel。Orca 的实现可以把独立请求的注意力放在同一个融合 kernel 的不同 thread block 中；现代实现也可使用带序列边界的批量接口。不要把“数学上不能把请求拼成一条序列”误读成“注意力无法批量执行”。

### 3.2 为什么调度优化仍需要内存管理配合

要让 C 插入，首先必须给 C 分配 KV。若系统已经为 A、B 的最大长度把显存全占完，空计算槽位也放不进新请求。Orca 原文保留了基于请求最大 token 数的内存预算，这正说明迭代调度解决了一类问题，后面的分页还要解决另一类问题。

Orca 的端到端比较使用 GPT-3 规格模型、A100、合成到达过程；175B 配置是 16 张 GPU，2 路层间并行乘 8 路层内并行。因没有真实权重与输入，实验固定生成长度并禁用提前 EOS，不能据此评价答案质量。论文相对当时 FasterTransformer 的大幅请求吞吐收益，混合了排队、批处理和引擎差异；不要将其移植为任意现代服务的预期倍数。其引擎微基准专门排除调度影响，才适合判断实现本身的效率。[Orca 第 11–14 页][orca]

## 4. 为什么连续批处理仍会让正在输出的用户卡住

**讲义主线：第 20–24 页；补充 [Sarathi-Serve 第 5–10 页][sarathi]。**

回到 A、B、C。A/C 正在以较短间隔输出，B 的长输入刚进入系统。如果为了降低 B 的 TTFT，立即执行 B 的完整 prefill，这轮计算可能很长，A/C 的下一个输出就迟到。反过来，一直优先所有 decode，持续到来的生成任务可能让 B 长时间不能开始。连续批处理提供了调度机会，并没有自动决定一个合理策略。

### 4.1 Chunked prefill：把长工作切成可插入的小段

将 B 的 2,048 个输入分成若干 chunk。每一轮先为已运行 decode 请求安排本轮工作，再用剩余 token 预算放入 prefill chunk。假设一轮的预算 $\tau=512$ 个**新处理 token**，A/C 各占 1 个，B 最多加入 510 个。预算是计算规模的代理，既不是 512 个请求，也不是 GPU 总 KV 容量。

B 的状态要保存“已处理到第几个输入 token”和已有 KV。下次继续处理后面的 chunk 时，新 token 仍然注意到 B 的全部必要历史，而不是把每个 chunk 当成独立文档。只有最后一段输入处理完成，才能从正确的完整输入上下文产生第一个输出。

Sarathi-Serve 的调度顺序是正在 decode 的请求、未完成的 prefill、再到新的 prefill，在预算内拼接。这使正在服务的 decode 不必因为一整个 prefill 而跳过若干轮。论文称其 stall-free scheduling；这里的意思是持续安排 decode，**不代表 prefill 对这轮延迟完全没有影响**。一个塞满 512 token 的迭代可能仍比纯 decode 迭代慢。

### 4.2 为什么 chunk 不能无限小

一个长度 100 的输入分成四段，每段 25。按“每段需要读到哪些旧 KV”的逻辑计数，后面三段分别涉及 25、50、75 个旧位置，合计 150 个旧位置访问机会。一次处理完整输入时，这个“跨 chunk 重读旧前缀”的项不存在。但这不是实际 HBM 字节测量：真实注意力核有 tiling 和缓存，输入自身的注意力运算也仍然存在。

除此之外，小矩阵可能不能充分利用 GPU，调度和 kernel 启动频率变高；较大 chunk 则有利于 prefill 效率，但拉长 decode 迭代。选择 chunk/token budget，就是在 TTFT、TBT 与总吞吐之间找符合服务目标的点，而不是寻找一个全球通用常数。

论文的一个直接对照很有教学价值：在 Yi-34B、两张 A100、128 个请求、token budget 1,024 的聊天设置中，只有混合 batching 时，median TTFT / P99 TBT 为 0.53 / 0.68 秒；只有 chunking 为 1.04 / 0.17 秒；二者结合为 0.76 / 0.14 秒。结合方案显著改善尾部间隔，但 TTFT 并非三者最低。这些是表 4 的特定实验，不是 1,024 永远最优的证据。[Sarathi-Serve 第 13 页][sarathi]

该论文的整体评测区分 Mistral-7B、Yi-34B、Llama2-70B、Falcon-180B 及不同 A100/A40 配置，输入还包含 ShareGPT 和更长的 arXiv 摘要负载，使用 P99 TBT 目标及排队约束。比较时要保留这些条件，不能把某一模型的宽松 SLO 下吞吐当作另一模型的交互体验。[第 10–13 页][sarathi]

## 5. 既然两阶段互相干扰，为什么不直接拆开

**讲义主线：第 25–27 页；机制与实验分别来自 [DistServe][distserve]、[Splitwise][splitwise]。**

PD disaggregation 将 prefill 和 decode 放在不同的执行资源上。B 的长 prefill 不再直接占用 A/C 的 decode GPU，可以分别扩容两个池、选择不同 batch 和并行度，甚至选择不同代际硬件。它与 chunking 不矛盾：前者主要隔离资源，后者控制每轮工作粒度。

但这不是把 HTTP 请求转发到另一台服务器就完成了。Decode 需要 prefill 已经建立的每层 KV，以及 token 位置、模型/适配器身份、采样状态和第一个输出等上下文。通常两个池各持有执行对应模型所需的权重，因而增加权重部署与资源碎片成本。

**教学状态机。** 可以将请求视为 `WAITING → PREFILL(partial) → KV_TRANSFER → DECODE → DONE`。单池运行可以没有转移阶段；抢占还会引入暂停/恢复。一次安全的转移至少涉及：目标端预留容量，源端传输带版本的状态，目标端确认可使用，路由切到目标，最后解除源端的必要引用。具体确认与重试协议是工程建议，不是两篇论文都已经实现的容错机制。DistServe 明确把 fault tolerance、preemption 等列为后续工作，不能将这张教学状态机说成其已具备的生产保证。[DistServe 第 8–9 页][distserve]

### 5.1 算一遍 KV 传输，才能判断“拆开值不值”

前面的 B 有 256 MiB KV。若链路有效带宽为 25 GB/s，纯搬运下界约为 $268,435,456/(25\times10^9)=10.7$ ms。若规格写的是 **25 Gbit/s**，理想字节带宽只有 3.125 GB/s，相同数据至少约 85.9 ms。这里还没算争用、协议和其他开销。GB、GiB、bit、byte 混用，足以让架构判断相差数倍。

PD 是否划算，可以先写成一个待测比较：减少的排队/干扰时间，是否超过新增转移、资源等待与重复部署成本。长输入让 prefill 隔离更有价值，也让 KV 更大；所以“输入长就一定适合跨机器 PD”仍缺一个带宽条件。若已经返回首 token，转移阻塞往往落在第一、第二个 token 的间隔上，单看 TPOT 可能把这一尖峰稀释。

### 5.2 DistServe：按 goodput 分配两阶段资源

DistServe 分别剖析 prefill 和 decode 的计算特点，在给定 TTFT/TPOT SLO 下寻找每 GPU goodput 合适的并行配置，再安排两池的副本数。高带宽下可以相对自由地分布两阶段；跨节点带宽低时，要让对应阶段的 KV 分片尽量留在同一节点，通过节点内互连传输。也就是说，网络拓扑会反过来约束模型分片和阶段布局。[DistServe 第 5–8 页][distserve]

其实际低带宽实验使用 32 张 A100、4 个节点，跨节点 25 Gbit/s，通过这种放置减少关键 KV 转移。实验模型为 OPT-13B/66B/175B，最大上下文受 2,048 限制；名为 LongBench 的输入在该实验中也受模型窗口约束，不能直接当作十万 token 长上下文结果。论文报告的大倍数收益、95% KV 转移少于 30 ms 等数字，都依赖其模型、负载、SLO 和放置策略；其中高带宽布局的部分研究使用模拟，不全是同样规模的实体部署。[第 9–13 页][distserve]

### 5.3 Splitwise：把硬件和功耗也纳入选择

Splitwise 通过 A100/H100 上的阶段剖析发现，所测 prefill 更受计算能力影响，decode 对显存容量/带宽更敏感，因此探索不同硬件与功耗上限的阶段组合。它保持 prefill、decode 和可动态转换的 mixed 池，用分层传输减少状态交接对关键路径的影响；在负载偏离预期时，mixed 池提供弹性。选择目标是吞吐、成本、功耗之间的组合，不只是一条延迟曲线。[Splitwise 第 3–8 页][splitwise]

论文既有少量实体 DGX 机器的剖析和传输验证，也有基于这些测量的大集群模拟；生产 trace 保留到达和输入输出长度，实验不等于重放真实文本及评测生成质量。其表述中的平均 TBT 实际相当于平均生成间隔，不能替代逐 token 尾部分布。混合代际高速互连的可用性也是原文讨论的部署限制。[第 8–12 页][splitwise]

对我们的三个请求，若低负载时一张 GPU 就能及时完成，拆出两个长期驻留池可能更贵。若 B 类长 prefill 持续压住 A/C，且有足够工作量填满两池，PD 才更可能创造稳定收益。这个结论是基于两篇机制的工程推导，必须通过实际工作负载验证。

## 6. 谁先运行：短任务优先和用户公平不是同一个问题

**讲义主线：第 28–31 页；阅读补充为 [Learning to Rank][ltr]、[FastServe][fastserve]、[VTC][vtc]。**

我们现在能在每轮选择请求，但该选谁？FCFS（first-come-first-served，先到先服务）容易解释，却可能让 B 的长输入挡住别人。理想的 shortest-job-first 在若干单机排队假设下能减少平均等待，但 LLM 的总工作量不仅取决于输出长度，还取决于输入、上下文、batch 和硬件；尤其总输出长度未知。调度论文是在这些限制下寻找可用近似，不是在恢复一个已知的任务时长。

### 6.1 Learning to Rank：不必准确猜到 128，也许先排对大小

C 最后输出 128 token，B 输出 8 token。如果能提前知道顺序，就有机会先完成短任务。Learning to Rank 用一个较小的模型从请求文本预测相对生成长度顺序，以排序损失训练，而不强求精确预测每个长度。

设一组请求的预测分数为 $s_i$，真实长度对应的排序是 $\pi$，ListMLE 一类目标可以写成：

$$
\mathcal L=-\sum_{k=1}^{m}\log\frac{\exp(s_{\pi_k})}{\sum_{j=k}^{m}\exp(s_{\pi_j})}.
$$

$m$ 是排序列表大小；将分数方向约定为“越应排前越大”。每一项要求当前真实排第一的请求，在剩余请求中有更大的选择概率。这解释了为什么排序模型不一定需要精确猜出“128”：只要在有意义的请求对之间减少次序错误，就可能减少短任务等待。

代价也随之出现。预测模型有额外 prefill、权重和运行成本；换模型、换任务分布后，文本到输出长度的关系可能改变；长期短请求涌入时，长请求会饿死。因此论文加入等待/抢占次数相关的优先级提升。其附录说明，已有请求的分数并不在每次生成后重新计算，不能将它说成精准估计“剩余长度”的 SRTF（shortest-remaining-time-first，最短剩余时间优先）。[Learning to Rank 第 3–6、15–18 页][ltr]

它的实验使用 vLLM 0.4.1、A100、Llama-3 的 8B/70B 模型等设置。部分图使用 E2E 除输出长度的 normalized latency，不能读作 TBT。论文“先得到一批合成数据”的大幅加速还包含了从 10,000 个请求中优先完成较短的 1,000 个；这改变了完成样本集合，可能影响数据长度分布，不能解释成相同全部任务都同比加速。[第 6–9 页][ltr]

### 6.2 FastServe：先给机会，再根据已经消耗的服务量降级

不知道未来长度时，可以用多级反馈队列 MLFQ。刚开始的请求进入较高优先级，消耗一个时间片还没完成，就移到更低优先级；较低级别有更大的时间片。这样短任务有机会尽快完成，长任务避免每一步都遭遇过密的调度开销。等待过久的任务再提升优先级，以缓解饥饿。

FastServe 进一步处理 LLM 的特殊性：长 prefill 本来就昂贵，不宜统一从最小时间片开始；它根据可估计的 prefill 工作选择初始队列，即 skip-join。暂停请求后，KV 还占显存，需要决定保留、换出到 CPU，还是丢弃后重算。换出会经过 PCIe 等链路，恢复又会阻塞；FastServe 根据预计再次服务时间提前换出/预取，使数据搬运尽可能与计算重叠。[FastServe 第 4–8 页][fastserve]

用 Java 线程调度理解“分时间片”有帮助，但不要把 KV 切换理解为保存几个寄存器。一个长请求的状态可能达到 GB 级。抢占策略、KV 管理和多 GPU 流水线中的在途工作必须一起设计，不能随时把一个运行到中间层的 token 当作已经安全暂停。

论文使用 OPT 模型、最多 16 张 A100，比较包含较旧的 vLLM 0.1.7 和 FasterTransformer。整体系统比较会混合引擎、并行和调度差异；其 FastServe-FCFS 消融更接近“只问多级队列值不值”。该文主要报告 normalized E2E、其尾部和相应 SLO，同样不能转述为逐 token 尾部收益。[第 9–13 页][fastserve]

### 6.3 VTC：公平首先要回答“按什么计服务”

假设用户甲不断发 A 类短请求，用户乙不断发 C 类长输出。每人每秒一个请求，并不表示占用相同 GPU 服务量；每人相同 token 总数也不一定相同成本，因为 prefill 与 decode 不同。

VTC 为每个客户端维护服务计数，使用可配置成本代理：

$$
W=w_p n_{input}+w_q n_{output}.
$$

$n_{input},n_{output}$ 是已计入的输入和输出 token 数；$w_p,w_q$ 是每 token 的服务单位权重，不是秒，也不是普适 GPU 成本。教学上取 $w_p=1,w_q=2$，A 完成后计 168 单位，B 计 2,064，C 计 1,344。B 输出很少，仍消耗较多 prefill 工作；按请求数量均分无法体现这一点。实际权重应由公平目标和负载剖析决定。

调度器在可加入 batch 时，优先服务计数较低的活跃客户端；随着实际生成推进，持续累加已获得的输出服务。新到或长期离开的客户端不能保留无限“欠服务额度”：counter lift 将其计数抬到适当的活跃基线，防止通过反复离开再返回获得不合理优先级。若客户有不同份额，则按份额归一化服务计数。

这套公平保证针对满足论文条件、持续有待服务请求的客户端。原文中的有界服务差涉及最大输入长度和可同时在系统中的 token 容量，不能推导成“所有用户 TTFT 相同”“高负载不会排队”。原始算法主要在新请求准入时作选择，已经在 batch 中的请求不是随时被抢占。公平与短任务优先优化的目标不同，必须公开服务目标后再组合。[VTC 第 4–8、18–24 页][vtc]

**工程建议。** 大规模客户端可以维护活跃客户端的有序结构/堆，按计数选择下一位，而不是每个 token 都全量轮询全部注册用户；实际还要处理注销、份额更新和懒更新。这是从 VTC 状态结构推出的实现方向，不是本笔记已实现的大规模调度器。

## 7. 空闲显存很多，为什么还可能放不进下一个请求

**讲义主线：第 32–35 页；机制来自 [PagedAttention 第 4–9 页][paged]。**

先区别三种浪费。为“可能达到的最大长度”提前保留空间，是未来预留；为某个实际长度分配的块尾部没用满，是内部碎片；很多空闲空间散在不同位置，不能满足一大段连续分配，是外部碎片。它们都可能降低有效并发，但修复方式不同。

PagedAttention 把请求的 KV 按固定 token 数分块：逻辑上仍是一条连续序列，物理上可放在显存池的任意可用块。每个请求保存 block table，将逻辑块号映射到物理块号。注意力 kernel 通过表找到对应 K/V。

取每块 4 token 的教学设置，A 已处理 7 个 token，逻辑块 `[0,1]` 可对应物理块 `[7,2]`；前 4 个位置在物理块 7，后 3 个在块 2。接下来处理一个新 token 可填满块 2；再处理下一 token 时才申请另一个空块，例如 9。不必为整条请求预留一段最大长度连续空间。

每个未共享序列在尾块最多浪费 3 个 token 槽位，实际系统还存在池、元数据、对齐等开销。块变小能减少尾部浪费，却增加查表、块元数据和 kernel 地址计算；块变大则相反。原文某个默认 block size 是当时实现的选择，不是所有模型都应使用的参数。

### 7.1 分页改变地址，不改变注意力数学

一个 query 仍要对所有允许访问的 key 计算分数，并做**全局**归一化。不能每块单独 softmax，再把各块结果取平均，否则可能让分数低的一块获得过多权重。

为了说明后面 context parallelism 的合并，我们用稳定 softmax 的分块形式。对块 $j$ 中分数 $s_i$ 和 value $v_i$，保存：

$$
m_j=\max_i s_i,\qquad l_j=\sum_i e^{s_i-m_j},\qquad u_j=\sum_i e^{s_i-m_j}v_i.
$$

合并时取 $m=\max_j m_j$，然后：

$$
l=\sum_j e^{m_j-m}l_j,\qquad u=\sum_j e^{m_j-m}u_j,\qquad o=u/l.
$$

$m_j$ 保证指数数值稳定，$l_j$ 是本块归一化所需的质量，$u_j$ 是未归一化加权和。各块可以分别计算，但必须携带这些统计量才能恢复同一个全局结果。后附算例验证 `[0,1]` 与 `[2,3]` 两块的合并等于直接计算，简单平均则不等价。这是教学推导，不是复现某个 CUDA kernel。

### 7.2 共享前缀为什么需要引用计数和写时复制

假设 C 的公共前缀已经缓存，另一个请求 C′ 使用相同前缀。完整且不可变的物理块可以共享，block table 都指向它，引用计数加一。某请求结束，只减少自己的引用，不能把另一个仍在读的块释放。

如果共享的最后一个块还没满，而 C 与 C′ 要追加不同 token，就会发生写冲突。写时复制 COW 的办法是：先复制有效内容到新块，再修改自己的映射并追加；另一个分支继续读取旧块。全满且不再修改的块无需复制。这与不可变对象共享相近，但释放时还要确保 GPU 中在途读写已经完成。

原始 PagedAttention 论文处理了并行采样、beam search 和预定义共享 prompt，也讨论请求被抢占后整体 KV 换出或重算。重算可以把原输入和已生成 token 拼起来做一次 prefill，并不需要按当初 decode 的慢路径逐 token 重演；是否比 CPU 换入快，取决于长度、计算能力及传输链路。[PagedAttention 第 6–9、13 页][paged]

其历史实验中，分页注意力核本身可能比对应非分页核慢约 20–26%，端到端系统却因减少浪费、增加有效 batch 而更快。这是本课很关键的因果：**局部 kernel 变慢，不等于整个服务变慢**。相反，若工作负载已偏计算瓶颈或 batch 无法再增加，内存节省也不一定带来同样吞吐收益。原文使用 OPT/LLaMA、A100、ShareGPT/Alpaca 长度和 Poisson 到达，其 Orca baseline 是作者重实现而非原始系统；比较要保留这些边界。[第 10–13 页][paged]

## 8. 从“能共享”到“下次真的命中”：前缀缓存、路由与公平

**讲义主线：第 36–40 页；补充 [SGLang 第 3–6 页及附录 A][sglang]、[DLPM 第 3–7 页][dlpm]。**

C 的 1,024 token 公共前缀若命中，可以减少重复 prefill；但 decode 仍然需要读取它的 KV，也仍会新增状态。缓存命中不意味着后续输出免费，更不等于直接复用以前的答案。

### 8.1 命中的条件是计算历史一致

因果注意力的某个位置依赖前面的全部必要上下文。两个请求中间都出现同一段文本，并不足以复用其 KV；前缀 token、模型权重、位置编码规则和其他会影响状态的配置要兼容。工程实现还应把适配器、相关多模态输入身份以及需要隔离的缓存域纳入身份判断。后者是正确性/隔离方面的工程建议，不是讲义给出的完整缓存键规范。

讲义第 38 页用链式块哈希表达依赖：

$$
h_i=H(h_{i-1},B_i),
$$

$B_i$ 是当前块的 token 内容，$h_{i-1}$ 代表全部前序块。只对 $B_i$ 自身哈希会错误共享“同样句子但前文不同”的 KV。哈希只是快速索引；碰撞处理和完整身份核验仍取决于实现。

### 8.2 Radix tree 为什么比一张“完整 prompt → KV”表灵活

C 和 C′ 可能共享 1,024 token，但 C′ 后面再分出不同后缀。Radix tree 把公共前缀压成共享路径，分歧处创建分支。查询时沿 token 前缀匹配，找到最长已缓存部分，再只 prefill 尚未命中的后缀。SGLang 原论文的 tree 元数据在 CPU，KV 在 GPU；压缩边可以包含多个 token，不能把树的一条边简单理解为一个固定大小 GPU 物理块。

活跃请求引用到的节点必须保留，已结束但可能复用的节点才可被淘汰。原文采用可淘汰叶子上的 LRU：先淘汰最久未使用、且没有活跃引用的后缀，必要时再向前收缩。它让同一缓存池同时承担活跃状态和可复用前缀，而不是无上限保存所有历史会话。

缓存还改变调度：优先选与现有缓存匹配更长的请求，可以减少新 prefill 并降低占用。SGLang 分析的最优缓存命中性质有离线已知请求及容量至少容纳最长请求等假设，不能当成任意在线流量下的全局最优性。原文也将 cache-aware scheduling 的饥饿问题列为未来工作。[SGLang 第 5–6、10、14–16 页][sglang]

SGLang 的完整系统还包括语言程序的 fork/join、异步执行和结构化输出的压缩有限状态机。压缩 FSM 能跳过确定的字符串片段，但要处理重新分词及概率偏差；这些是额外贡献，其最高吞吐倍数不能全部归给 RadixAttention。附录中的 prompt 重排为了扩大公共前缀，还可能改变语义，不能视为无损编译优化。我们的 C 案例只借用原样公共前缀，不擅自挪动用户指令。[第 7–9、17–20 页][sglang]

### 8.3 DLPM：不能让没有热门前缀的用户永远等着

设客户端甲不停提交同一个长公共前缀，乙每次提交全新输入。单纯 longest-prefix-match 会倾向甲，吞吐可能很高，乙却持续等待。VTC 又可能按公平顺序打散请求，使缓存局部性下降。DLPM 用 deficit counter 给每个客户端维护服务额度：在还有额度的客户端之间选择前缀匹配好的请求；执行后扣除本轮扩展输入和输出成本；合适时再补充额度。

这里的输入成本用的是 **extend tokens**，即本次需要新算的输入，不是客户端看到的整个输入长度。因此同样 1,088 token 的 C，命中 1,024 前缀后只剩 64 个新输入需要计入相应计算代理。原文有些图展示客户端感知的全部输入服务，另一些分析展示实际扩展工作，读图时要区分。

额度量子 $Q_u$ 大，调度器能在更长时间内追逐局部性，但允许的短期公平偏差变大；$Q_u$ 小，约束更紧，却容易失去前缀复用。论文的服务差界包含 $2(U+Q_u)$ 一类项，$U$ 由最大单次输入和系统中可处理 token 的上界构成。它解释的是有界成本差，而不是每个请求的排队延迟上界。[DLPM 第 4–6 页][dlpm]

多副本时还要决定请求送到哪台。每台机器本地公平并不推出全局公平，因为一个客户端可能在很多 worker 上都分得服务。D²LPM 同时维护跨 worker 的客户端服务与本地额度，在缓存命中、队列负载、客户端份额之间协调；缓存元数据的同步也有成本和时效问题。[第 6–7 页][dlpm]

论文在 A100/A10G、Llama-3 系列和多种共享前缀负载上测量，局部性与公平并非总能双赢：某些长上下文多 worker 配置中，更偏局部性的 baseline 有更高吞吐。跨客户端共享前缀的成本归属也仍被列为开放问题。[第 7–12、16–17 页][dlpm] 对实际服务而言，应该同时画按客户端的服务差、等待分布、命中率与吞吐，不能只用总 token/s 宣称公平调度已经成功。

## 9. 一个 KV 分页规则能覆盖所有模型吗

**阅读展开。** 讲义的分页与前缀复用主要建立在常规 Transformer 上；[JENGA][jenga]帮助我们识别其假设，[vAttention][vattention]则是本目录保留的历史阅读，用于比较不同内存实现层次，不计入当前 17 篇指定阅读。

### 9.1 JENGA：不同层可能保存不同大小、不同生命周期的状态

如果所有层的每个 token 都保存同样大小 KV，用统一页面很自然。但混合 full attention/sliding-window 层时，前者保留完整历史，后者只需近期窗口；Mamba 等状态空间层保存递推状态，不能把每个历史位置都当作普通 KV；视觉编码器输出和文本注意力 KV 的大小、使用时间也不同。

JENGA 先解决容量问题。假设两种状态的分配单位分别为 2 KiB、3 KiB，用两者最小公倍数 6 KiB 建立可交换大页，再按类型切成 3 个或 2 个小页。大页可在类型之间重新分配，小页服务对应状态。它还尽量让同一个请求的小页位于一起，因为请求完成时往往一起释放，更容易回收整个大页。这里 2/3/6 是教学例子，不是模型固定参数。[JENGA 第 5–6 页][jenga]

再解决命中正确性。某个前缀能否复用，要让**所有必要层类型的状态都可恢复**：full attention 需要该前缀所依赖的历史 KV；滑动窗口只需对应窗口；状态空间层需要合适位置的状态检查点。不能因为一类缓存命中就认定整个模型命中。各类型淘汰策略要对齐，否则甲层留着前缀 X、乙层留着前缀 Y，单看各自占用很高，合起来却复用不了。[第 7–9 页][jenga]

其评测建立在 vLLM 0.6.3 等版本、H100/L4 及多种异构模型上，收益依赖原始布局浪费程度；标准 Llama 一类模型的提升很小。更高内存效率也可能让 batch 变大，改善 TTFT/E2E 却增加 TPOT，不能只看最大吞吐倍数。对于私有 Character.ai 架构模式，作者采用可公开模型上的重建设置，不能写成实际私有权重的测量。[第 10–12 页][jenga]

### 9.2 vAttention：虚拟连续不意味着物理上提前占满

PagedAttention 在应用层维护块表，要求 kernel 支持这种寻址。vAttention 探索另一条路：预留一大段连续**虚拟地址**，再用 CUDA 虚拟内存接口按需映射物理显存。普通连续张量的注意力 kernel 仍看到连续地址，物理页可以不连续，也不必提前占满最大长度。

这与 Java 开发者熟悉的“对象地址与物理内存不是一回事”相通，但不是直接启用某个开关就完成 GPU 自动缺页调页。论文显式管理页映射，利用下一轮 KV 增长可预测的特征提前分配，并延迟回收以便后续请求复用；细粒度页方案还修改了驱动，另讨论依赖 stride 支持的张量切片替代方案。[vAttention 第 5–9、13–14 页][vattention]

该论文比较 vLLM 0.2.7 下不同注意力后端，使用 Yi/Llama 模型和 1–2 张 A100 等设置。最好的分页 decode kernel 已可接近非分页方案；收益较大的地方包括长 prefill、后端可移植性和特定布局开销。换 kernel 本身也能带来速度变化，因此不能把所有倍数算作“硬件分页天然更快”。保留这篇历史材料，是为了学会区分**内存抽象、kernel 接口、驱动开销和端到端调度**，不是给当前框架选型下定论。[第 10–14 页][vattention]

## 10. 一张 GPU 不够时，先弄清“分的是哪一个维度”

**讲义主线：第 41–56 页。** 到这里我们主要在同一执行组中调度请求。现在出现两个新限制：模型权重或 KV 装不下；单个 token 的计算/读取已经无法满足延迟。增加 GPU 后，可能复制模型服务更多请求，也可能让几张 GPU 合作完成同一个请求。这两种扩展解决的问题不同。

例如 70B 参数、每参数 2 字节，仅权重约 140 GB，尚不含 KV 与临时空间。即便权重能放进某张显卡，也不能据此推断有足够服务容量。若一次 decode 必须从 HBM 读取全部这些权重，简化读取下界为权重字节数除有效带宽；真实运行还要加入 KV、计算、调度和通信。这是讲义第 42 页的数量级思路，不是对某型号 GPU 的实测时延。

### 10.1 先认识通信动作，避免把 all-reduce 当成魔法

下面用 2 张 GPU 的小数组说明语义。它们不是 Java 集合的本地操作，传输会消耗网络/互连时间，也可能占 GPU 执行资源。

| 操作 | 两张 GPU 的输入与结果 | 在本课的意义 |
|---|---|---|
| send/recv | GPU0 把数组发给 GPU1 | 流水线相邻阶段传激活 |
| broadcast | GPU0 有完整数组，两张最后都有它 | 分发共同的数据/控制所需张量 |
| all-gather | GPU0 有 `[a,b]`，GPU1 有 `[c,d]`，最后都有 `[a,b,c,d]` | 拼回各自持有的分片 |
| reduce-scatter（求和） | 两者都有等长的部分结果，先逐位置相加，再各保留结果一段 | 合并部分和，同时保持分片 |
| all-reduce（求和） | `[1,2]` 与 `[10,20]` 最后都成为 `[11,22]` | 每张都需要同一个完整和 |
| all-to-all | 每张把自己的不同片段送往不同目标 | 按专家路由 token，再返回结果 |

All-gather 是拼接；all-reduce 是归约并让所有参与者得到结果，不能混用。对求和，reduce-scatter 后接 all-gather 可以实现 all-reduce 的语义。

[MPICH 论文第 2–11 页][mpich]用 $\alpha$ 表示一次通信启动时间，$\beta$ 表示每字节传输时间。令 $G$ 为参与者数、$n$ 为每张 GPU 的完整 all-reduce 输入字节数，理想 ring all-reduce 的通信部分可近似为：

$$
T_{AR}\approx 2(G-1)\alpha+\frac{2(G-1)}G n\beta.
$$

还应计本地归约成本，实际实现可能重叠传输和计算。式子解释了：小张量可能受启动延迟主导，大张量更在意带宽；更多 GPU 并非无条件更快。MPICH 原文研究的是较早的 CPU/Myrinet/IBM SP 等平台，提供的是集体通信语义和算法成本分析，不能将其中消息大小阈值直接当成今天 NCCL（GPU 集体通信库）的选择规则。

### 10.2 Data parallelism：复制完整服务能力

推理 DP 让不同副本处理不同请求。若两套完整模型实例分别服务 A 与 B/C，请求之间通常不需要逐层同步模型计算。它最直接地增加总服务容量，但每个副本都需要权重和自己的 KV。副本也可以内部再用 TP/PP，所以“副本”不一定是一张 GPU。

增加副本不会自动缩短一个已经分配给某副本的长请求的单步计算；它可能通过减少排队改善端到端延迟。前缀缓存也被分散：把 C′ 随机送到另一副本，可能失去 C 刚建立的缓存；固定粘在一个副本，又可能造成热点。第 8 节的局部性与公平路由因此与 DP 直接相关。

训练 DP 中需要同步梯度，而推理没有这种更新步骤。不能把 Megatron 训练架构图里的梯度 all-reduce 搬到推理 DP 中，声称每生成一个 token 都要同步所有副本权重。

### 10.3 Tensor parallelism：同一个矩阵乘法拆给几张卡

设 $X$ 的形状为 $N\times h$，$W_1$ 为 $h\times f$，$N$ 是本轮有效 token 数，$h$ 是隐藏维度，$f$ 是前馈中间维度。我们把 $W_1$ 按输出列拆成 $[W_1^{(0)},W_1^{(1)}]$，两张 GPU 各算一半中间特征：

$$
Z_0=\phi(XW_1^{(0)}),\qquad Z_1=\phi(XW_1^{(1)}).
$$

$\phi$ 是逐元素非线性。第二个矩阵 $W_2$ 为 $f\times h$，按相应输入行拆开，各算 $Y_0=Z_0W_2^{(0)}$、$Y_1=Z_1W_2^{(1)}$，再得到 $Y=Y_0+Y_1$。因此中间特征不必先 all-gather 成完整 $f$ 维，只在第二个线性层之后 all-reduce 部分和。这是 Megatron 的一项关键布局选择。[Megatron-LM 第 4–5 页][megatron]

为什么不能随便换拆法？如果先拆输入维度产生两个部分和，就必须先求和再应用非线性，因为通常 $\phi(a+b)\ne\phi(a)+\phi(b)$。例如 $\phi(x)=\max(0,x)$ 是 ReLU，取 $a=-1,b=2$，先相加再激活得到 1，分别激活后相加得到 2。把激活错误地提前到每个分片，输出数值就变了。附带 CPU 程序用具体矩阵验证正确拆分的等价性，并构造 ReLU 反例；这验证代数，不预测分布式性能。

注意力也可按头分片，输出投影再合并。典型 Megatron 稠密 Transformer 的前向有每层两次 all-reduce；不同模型结构和并行方案会改变它。更多 TP 卡减少每卡权重和计算，但每层都带来通信，并会把矩阵分得更小。若 KV 头数小于 TP 并行度，一些实现必须复制 KV 头，KV 容量不再按 $1/G$ 理想下降。[讲义第 46–49、55 页][slides]

[Efficiently Scaling Transformer Inference 第 4–8 页][scaling]进一步说明布局应随形状调整：小 batch 的低延迟路径与大 prefill 的高吞吐路径，最合适的权重/激活分片不同；在 MQA 下还可按 batch 分片 KV，通过额外交换 query 等数据避免 KV 复制。这里 MQA 是所有 query 头共用一组 KV 头的情况，是前述 GQA 的极端形式。其 PaLM-540B 结果使用 TPU v4，量化低延迟与高利用率 prefill 也不是同一配置。学习的是“数据规模决定搬哪种张量更划算”，不是照抄某个 GPU 数或把训练/TPU 数字当作当前 GPU 服务承诺。

### 10.4 Pipeline parallelism：把层分成几个阶段

PP 让 GPU0 执行前若干层，GPU1 执行后若干层。A 的一个 token 先经过阶段 0，再经过阶段 1，最终才能采样出下一个 token。阶段边界主要传隐藏向量，而不是每层都求和完整部分结果，因此跨节点通信次数可以较少。

代价是流水线空泡。如果只有一个请求，A 的下一个 token 仍要等当前 token 走完全部阶段；不能把尚未生成的未来 token 预先塞进去。为了填满流水线，需要其他独立请求或 microbatch 在不同阶段同时工作。

设有 $K$ 个等速阶段、$m$ 个独立 microbatch，每个阶段执行一个 microbatch 的时间相同且忽略通信。完成一轮前向需要 $m+K-1$ 个时隙，理想利用率为 $m/(m+K-1)$，相应空泡比例：

$$
\rho_{bubble}=\frac{K-1}{m+K-1}.
$$

$K=4,m=4$ 时空泡为 $3/7\approx42.9\%$；$m=16$ 时为 $3/19\approx15.8\%$。更多 microbatch 有助填满，但也可能增加请求等待、占用更多 KV，且真实阶段不一定等速。Prefill 与 decode 混用还会引入不均匀工作造成的空泡，Sarathi-Serve 对这点另有分析。

[GPipe 第 3–5 页][gpipe]提供分 microbatch、流水线和激活重算的经典机制，但它的主要实验是训练，涉及反向计算与梯度累积。这里的公式明确是平衡前向流水线教学模型；GPipe 的训练吞吐不能直接拿来证明在线自回归服务也有同样收益。其“每层必须装进单个分区”和负载平衡约束也不能忽略。

### 10.5 Expert parallelism：不是每个 token 都跑全部专家

MoE 层有多个前馈专家，router 为每个 token 选择 top-$k$ 个。EP 把专家放在不同 GPU：先将 token 的隐藏向量 dispatch 到所选专家，专家分别计算，再把结果送回并按路由权重 combine。数据交换往往表现为 all-to-all。

教学上有 8 个专家、4 张卡，每卡 2 个专家，1,024 个 token 都选 top-2。总计 2,048 次专家调用；只有路由完全均衡时，每卡约 512 次。实际可能集中到少数专家，使最忙的卡拖住整个批次。这里的平均值不是调度保证；容量限制、丢 token 或路由改变还可能影响模型行为，不能仅当作无损性能开关。

EP 的收益是让稀疏计算对应的专家权重分布到更多卡，代价是 token 搬运和负载不均。它可以与 attention 的 DP/TP 组合。长上下文、少 KV 头时，attention DP 加 EP 有机会避免高 TP 下 KV 复制；短请求下 all-to-all 启动和路由开销可能抵消收益。[讲义第 51、55 页][slides] 这是结构上的条件分析，未在本文运行 MoE 模型验证。

### 10.6 Context parallelism：把一个长序列的状态分开

C 的 1,088 token 还不很长；现在保持“同一请求、不同位置”的含义，把它扩展为 128K 输入。让四张卡各保存部分 token 的 KV，就能分担长上下文容量。Prefill 的每个 query 仍需要访问其允许的历史 key，不能把四段分别做独立注意力后直接拼接。

Ring attention 让各卡的 KV 块依次传给下一卡，本卡 query 逐步处理收到的块，并用第 7 节一类统计量合并全局结果；传输可与计算重叠。因果遮罩下，前半段 query 需要看的历史少、后半段多，按连续等长切分未必计算均衡，可以用更细粒度/交错布局改善。

讲义第 52 页的“helps prefill, not decode”适合作为这一简单 prefill 分片方案的直觉：普通 decode 每个请求只有一个新 query，直接照搬会遇到通信相对计算过大的问题。它不应解释为“所有上下文并行都不可能帮助 decode”。指定阅读 LoongServe 专门扩展了这个边界。

LoongServe 的 elastic sequence parallelism 动态改变一个请求占用的实例组；每个实例持有完整权重或一个 TP 执行组，改变的是序列/KV 的分布，不是每轮重新分发整套模型权重。Prefill 可以分散长序列；decode 中，主实例产生 query，其他实例对本地 KV 计算部分注意力，再正确合并。不同请求可使用不同主实例，使前馈等计算也分散，而不是永远由同一张卡成为瓶颈。[LoongServe 第 4–8 页][loongserve]

切换阶段会产生 KV 布局问题。原文利用 prefill 环形传输期间已有的 KV 流动，为后续 decode 提前保留所需状态，减少额外迁移；这不代表环形通信本身消失。缩小实例组可能要搬已有 KV，扩大时可让新实例承担后续新增 KV，是否值得伸缩需要比较预期收益和开销。[第 5–9 页][loongserve]

其长上下文实验用 LWM-1M-Text/Llama2-7B 规格、A800 集群及高速互连，负载覆盖从 ShareGPT 到数十万 token 的 LVEval。baseline 采用各自特定并行与 P/D 比例，部分在最长输入下 OOM；主图指标含 normalized E2E 及论文设定 SLO，不能等同所有在线服务的尾部 TBT 改善。该论文是“在这些条件下，动态序列并行能同时处理容量与服务调度”的证据，不是“任意 decode 分片必然更快”。[第 9–13 页][loongserve]

### 10.7 把“240 倍通信”按口径重算一遍

讲义第 53–54 页的数量级比较很有用，但应先写出计数对象。取隐藏维度 $h=8,192$、80 层、bf16 每元素 2 字节、4 路 TP，**每个全局 batch token、每张 TP GPU**的两次 ring all-reduce 发送量约为：

$$
80\times2\times\frac{2(4-1)}4\times(8192\times2)
=3,932,160\ \text{bytes}=3.75\ \text{MiB}.
$$

PP 的一个阶段边界发送一个隐藏向量，为 $8192\times2=16,384$ bytes，即 16 KiB；以上两个特定口径之比恰为 240。这里 PP 是**一次阶段边界**，并非整个集群所有边界的总量；ring 公式计算发送量，若同时累加收发字节还要一致地修改口径。通信时延还包含每次启动、拓扑和争用，不能只把总字节除带宽。

EP 那一行还需要多说一步。top-2、每层都有 MoE、均匀路由且有 $3/4$ 专家选择远端时，按“每张源 GPU 上一个本地 token”计算，dispatch 加 combine 的数据量为 $2\times2\times(3/4)\times h\times2$ bytes/层，80 层也得到 3,932,160 bytes。但如果比较的是相同的**全局 token 总数**且四张源 GPU 均匀分担输入，每卡平均只有四分之一的源 token，这个 EP 数还应除以 4。故讲义把 TP/EP 并列为相同 240 倍时，不能省略各自 token/batch 的归一化口径，更不能从表格推导任意 MoE 都恰好有同一倍数。

**工程推导。** 频繁、低延迟的 TP/EP 通信通常更需要快速节点内互连；较少阶段边界通信的 PP 更有机会跨节点。可是当模型已经装得下、请求足够多、跨节点网络强或 batch/context 改变时，DP、TP、PP 的最优组合都会变化。“TP 节点内，PP 节点间”是有依据的初始候选，不是无需测量的规则。

## 11. 最后一个反直觉：优化不是把所有资源同时拉满

**历史阅读补充：[NanoFlow 第 3–9 页][nanoflow]；不是当前官网新增指定阅读。** 前面把问题拆成计算、显存和网络，但一个真实推理迭代会交替执行偏计算、偏显存访问、偏通信的 kernel。某时刻 GPU 算力没满，不代表还可以随意叠加任务；另一个资源可能已经饱和。

NanoFlow 将 batch 再拆成 nano-batch，尝试让不同批次中依赖关系允许的计算、attention 和通信重叠。可重叠的前提是它们属于独立工作且数据准备完成；同一个 token 尚未完成上游线性层时，不能把依赖它的下游 attention 提前算。

“并发”还有资源竞争：两个 kernel 可能争抢 SM（GPU 的一组计算执行单元）、寄存器（线程使用的快速存储）、L2（共享缓存）或内存带宽，单独跑很快，重叠后都变慢。因此 NanoFlow 建立性能模型并通过剖析选择拆分和重叠配置。拆 batch 本身会增加权重读取、减小矩阵尺寸；论文消融中，仅拆分而无对应重叠反而退化约 13.2%，同引擎重叠收益约 1.07–1.17 倍，而系统相对不同 baseline 的总体倍数包含其他优化。[第 10–13 页][nanoflow]

其主要吞吐实验使用 8 张 A100、Llama2-70B 等，离线口径包含输入和输出 token；在线部分又使用平均 normalized E2E 目标。它提醒我们修正两种过度概括：大 batch decode 不一定始终整体受带宽限制；资源重叠也不自动带来更低交互延迟。把这些条件接回 A/B/C 时间线，比记住另一个系统名字更有用。

## 12. 怎样把本课变成可以诊断问题的工程能力

以下是依据本课机制提出的**工程实践顺序和未执行实验设计**，不是论文已证实的统一最优实现，也没有运行 GPU/模型实验。

第一步建立单个请求的状态与指标。记录到达、入队、首次运行、每轮阶段与处理 token 数、输出时间、KV 已用块和释放。保证 A/B/C 单独运行时数值/输出符合原模型语义，再谈并发；优化不能把不同请求的 attention 混在一起，或因缓存键不完整复用错误状态。

第二步固定模型、精度、kernel、硬件和相同请求集合，比较静态与连续 batching。观察空槽是否减少、队列是否缩短、KV 是否限制准入。此时不同时更换所有后端，否则不能把收益归因给调度。

第三步加入 B 类长输入，逐步改变 chunk budget，查看 A/C 的 P99 TBT 与 B 的 TTFT 如何互相影响。记录每轮有效 token、prefill/decode 比例及执行时间；只测总 token/s 无法解释长请求是否饿死。

第四步分别开启分页、前缀缓存、局部性调度。先在相同 batch 观察 kernel/元数据开销，再允许利用腾出的容量增大 batch，分清“单轮更快”和“能装更多工作”。设置有共享/无共享前缀、冷/热缓存、连续/突发到达和取消/超时场景。检查 C/C′ 的引用计数、COW 和淘汰，而不只看命中率。

第五步再评估 PD 与多 GPU。测量真实 KV 字节及有效转移带宽，比较相同 GPU 预算下不同阶段比例和 DP/TP/PP 布局；记录权重复制、空泡、collective、跨节点流量。新增 GPU 的收益应拆成排队改善、计算缩短和容量增加，避免“机器更多所以架构更好”的结论。

| 观察到的现象 | 本课提供的优先排查方向 | 还不能直接下的结论 |
|---|---|---|
| TTFT 好、输出中间偶发长停顿 | 长 prefill 插入、KV 转移、抢占恢复、网络缓冲 | 平均 TPOT 好就说明用户不卡 |
| 显存占用高但活跃请求少 | 最大长度预留、尾块、不可淘汰缓存、引用未释放 | 只要减少权重就一定解决 |
| 缓存命中很高但新用户等待很久 | locality 调度饥饿、客户端份额与路由 | 高命中率意味着调度公平 |
| GPU 增加，单 token 更慢 | collective 启动、小矩阵、拓扑、流水线空泡 | 并行实现一定有 bug |
| 总吞吐变高，单用户更慢 | batch 增大、TPOT/尾部变化、容量换延迟 | 优化一定失败；需看既定 SLO |
| 某论文倍数无法重现 | 版本、输入输出分布、baseline kernel、SLO、统计口径 | 论文机制完全无效 |

### 12.1 已实际运行的轻量示例

[examples.py](examples.py) 仅依赖 Python 标准库。运行：

```bash
python3 courses/2680/12.EfficientLLMServingBasicsIII.BatchingPagingAndParallelism/examples.py
```

运行记录保存在 [EXAMPLE_RUN.json](EXAMPLE_RUN.json)，记录代码校验值、Python 版本、时间和各项输出。示例覆盖：TTFT/TPOT 与间隔尖峰；静态/连续批处理槽位；chunk 的旧前缀读取计数；KV 容量与 bit/byte 传输换算；引用计数及尾块 COW；TP 的矩阵等价性与错误非线性反例；分块 softmax 的正确合并；理想 PP 空泡和 TP/PP 通信数量级。

这些程序验证教学例子的算术、状态隔离和代数性质。它们没有实现真实 Transformer、CUDA kernel、GPU 调度、网络传输或论文系统，不能用 CPU 输出声称复现任何论文加速比。进一步模型实验应遵循上面的对照设计，并保存模型版本、请求轨迹和未完成请求信息。

## 13. 自测：能解释原因，才算掌握方法

1. **B 只有 8 个输出，为什么仍可能让 A 卡住？** B 有 2,048 个输入，长 prefill 可占据一次较长迭代。输出短不等于当前计算少；应区分输入阶段的干扰与后续 decode。
2. **TPOT 从 60 ms 降到 50 ms，能否断言体验更好？** 不能。还要看 TTFT、逐 token TBT 分布和发送缓冲；少数长停顿可能被平均掩盖。
3. **Continuous batching 为什么不等于“所有请求都按时得到一个 token”？** 它提供迭代级成员变化，不保证准入、公平、每轮耗时或足够 KV。未完成 prefill 的请求也不能每轮产出一个正确输出。
4. **Chunk 从 512 减成 32，为什么未必更好？** 较短迭代可能改善 decode 间隔，但小矩阵效率、反复读旧 KV、调度和启动开销会恶化 prefill/吞吐；需要按 SLO 选预算。
5. **PagedAttention 能减少注意力需要看的历史 token 吗？** 对本课全注意力模型不能。它改变存储/寻址和共享，不改变语义；减少历史依赖是另一种模型或算法改变。
6. **两个请求结尾相同，为什么不能只按这段结尾缓存 KV？** 该位置的状态受前缀影响。必须保证计算历史和模型配置兼容，链式哈希包含前序身份。
7. **共享一个未填满尾块后，两条分支追加不同 token，应该怎样做？** 写者先复制有效内容并更新自己的 block table；完整不可变块仍共享；正确维护引用和 GPU 生命周期。
8. **PD 下 TTFT 很好，但第二个 token 很晚，可能是什么？** KV 转移或 decode 端准入阻塞。先单独记录交接和首个间隔，不能用平均 TPOT 排除这一问题。
9. **为什么 TP 的第一个线性层按列分、第二个按行分有价值？** 中间逐元素非线性可各自完成，第二层产生可求和部分结果，避免中间全量拼接；错误地对线性部分和分别做非线性会改变结果。
10. **为什么 PP 不能让同一个请求的未来输出提前同时生成？** 下一个 token 依赖上一个 token 的最终输出；流水线需要其他独立请求/microbatch 填空，不能创造不存在的数据。
11. **VTC 的公平保证为什么不是“每个请求同样快”？** 它按客户端的可配置服务成本及持续有工作等假设限制服务差，输入长度、已运行任务和全局负载仍会造成不同延迟。
12. **为什么全局请求数不变时，不能直接把讲义 EP 和 TP 的每 token 字节数都套成 3.9 MB？** TP 中每张卡处理同一全局 token 的分片；EP 的示例按每张源卡的本地 token 计搬运。先统一 token、卡、层和收发计数，再比较。

## 14. 讲义覆盖与阅读地图

以下地图说明每份资料在正文中承担的作用。论文实验只支撑其报告的模型、版本、负载与预算；本篇已核对正文机制与核心实验/限制，未复现论文性能。当前 17 篇指定阅读与两篇历史材料的身份分开保留。

| 主讲义实际页序 | 本文对应问题 |
|---|---|
| 1–3 | 课程身份、目标及课堂安排；安排不扩写成技术内容 |
| 4–8 | 第 1 节：请求、两阶段与 KV 的前提 |
| 9–14 | 第 2 节：用户指标、吞吐与评测错误 |
| 15–19 | 第 3 节：连续与选择性 batching |
| 20–24 | 第 4 节：阶段干扰和 chunked prefill |
| 25–27 | 第 5 节：PD 的状态、网络及资源配置 |
| 28–31 | 第 6 节：未知长度调度；第 13 节自测 |
| 32–35 | 第 7 节：容量浪费、分页和共享 |
| 36–40 | 第 8 节：前缀身份、哈希与 radix；第 13 节自测 |
| 41–56 | 第 10 节：集体通信、DP/TP/PP/EP/上下文并行及边界 |
| 57–59 | 第 12–14 节：综合实践、回顾与阅读组织 |

| 材料及本地全文 | 核对范围与本篇贡献 | 使用边界 |
|---|---|---|
| [On Evaluating Performance of LLM Inference Systems][evaluation] | 第 1–9、12–17 页：指标、公开评测审计、推测解码例子和附录清单 | 2507.09019v1；区分作者公开材料审计与独立重跑 |
| [Orca: A Distributed Serving System for Transformer-Based Generative Models][orca] | 实际第 2–14 页：迭代调度、选择性 batching、KV 预算、引擎与端到端实验 | 第 1 页为出版封面；补充 PDF 是正文，原 readings HTML 为会议页面；2022 系统比较 |
| [Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve][sarathi] | 第 1–14 页，重点 §3–5：stall、chunk、混合 batch、PP 和消融 | 2403.02310v3；P99 TBT 与具体预算/硬件，不与 TPOT 混用 |
| [DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving][distserve] | 第 1–13、17–18 页：阶段剖析、布局算法、传输及 goodput 实验 | 2401.09670v3；OPT 窗口、模拟部分、容错未实现 |
| [Splitwise: Efficient Generative LLM Inference Using Phase Splitting][splitwise] | 第 1–12 页：硬件/功耗剖析、池和转移、trace 与模拟 | 2311.18677v2；实体剖析与大集群模拟分开，平均 TBT 口径 |
| [Efficient LLM Scheduling by Learning to Rank][ltr] | 第 1–10、14–18 页：排序损失、优先级、预测成本、域变化、附录实现 | 2408.15792v1；固定预测分数不是精确剩余时长；部分完成任务集合会变化 |
| [Fast Distributed Inference Serving for Large Language Models][fastserve] | 第 1–13 页：skip-join MLFQ、KV 换出/预取、并行与消融 | 2305.05920v3；历史 baseline、normalized E2E 与队列消融 |
| [Efficient Memory Management for Large Language Model Serving with PagedAttention][paged] | 第 1–14 页：块表、COW、抢占、分布式、内存与 kernel 消融 | 2309.06180v1；原文共享 prompt 与后续自动前缀缓存不同 |
| [JENGA: Effective Memory Management for Serving LLM with Heterogeneity][jenga] | 第 1–13 页：异构布局、两级分配、类型依赖、模型/负载实验 | 2503.18292v1；缓存命中需所有必要类型成立，吞吐不等于 TPOT 改善 |
| [SGLang: Efficient Execution of Structured Language Model Programs][sglang] | 第 1–10、14–20 页：radix、调度条件、结构化程序及附录 FSM/编译限制 | 2312.07104v2；系统收益不全属 KV 复用；prompt 重排可能改变语义 |
| [Fairness in Serving Large Language Models][vtc] | 正文第 1–14 页及附录第 18–24 页：成本、counter lift、公平条件与实验 | 原文可配置服务代理不等于精确 GPU 时间或延迟保证 |
| [Locality-aware Fair Scheduling in LLM Serving][dlpm] | 第 1–12、16–17 页：额度与局部性、多节点公平、负载结果和界 | 2501.14312v1；extend 输入与客户端可见输入区分，跨用户共享成本未完全解决 |
| [Optimization of Collective Communication Operations in MPICH][mpich] | 第 1–16 页：通信语义、算法成本与旧平台实验 | 2005 年论文；成本模型用于理解，具体阈值不移植到 NCCL |
| [Efficiently Scaling Transformer Inference][scaling] | 第 1–11、15–18 页：张量布局、MQA、算力/通信模型、TPU 实验 | 2211.05102v1；低延迟/高吞吐/量化设置不可混成同一次运行 |
| [Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism][megatron] | 第 1–9、11–15 页：列/行分片、attention 头、DP 与训练实验 | 1909.08053v4；借用代数和布局，不把训练扩展效率说成推理结论 |
| [GPipe: Easy Scaling with Micro-Batch Pipeline Parallelism][gpipe] | 第 1–9 页：microbatch、空泡、重算和实验 | 1811.06965v5；训练系统，本文另限定前向理想模型 |
| [LoongServe: Efficiently Serving Long-Context Large Language Models with Elastic Sequence Parallelism][loongserve] | 第 1–13 页：ESP、KV 管理、分布式 decode、调度和长上下文实验 | 2404.09526v2；不等于任意短 decode 都值得分片 |
| [NanoFlow: Towards Optimal Large Language Model Serving Throughput][nanoflow] | 第 1–14 页：资源模型、nano-batch、重叠与同系统消融 | **历史保留**；2408.12757v2，不计当前指定阅读；离线吞吐与交互 SLO 分开 |
| [vAttention: Dynamic Memory Management for Serving LLMs without PagedAttention][vattention] | 第 1–14、18 页：VMM、页映射、后端比较、限制与复现实验说明 | **历史保留**；2405.04437v3/ASPLOS 2025；驱动/后端版本条件不推到当前软件 |
| [官网本课阅读说明](../site/readings/nov-04.html) | 完整核对主题分组、论文入口与思考题 | 组织阅读顺序；具体机制和数字回到论文正文 |

[slides]: 11_llm_serving_basics_3.pdf
[evaluation]: readings/On_Evaluating_Performance_of_LLM_Inference_Systems.pdf
[orca]: references/Orca_A_Distributed_Serving_System_for_Transformer-Based_Generative_Models.pdf
[sarathi]: readings/Taming_Throughput-Latency_Tradeoff_in_LLM_Inference_with_Sarathi-Serve.pdf
[distserve]: readings/DistServe_Disaggregating_Prefill_and_Decoding_for_Goodput-optimized_Large_Language_Model_Serving.pdf
[splitwise]: readings/Splitwise_Efficient_Generative_LLM_Inference_Using_Phase_Splitting.pdf
[ltr]: readings/Efficient_LLM_Scheduling_by_Learning_to_Rank.pdf
[fastserve]: readings/Fast_Distributed_Inference_Serving_for_Large_Language_Models.pdf
[paged]: readings/Efficient_Memory_Management_for_Large_Language_Model_Serving_with_PagedAttention.pdf
[jenga]: readings/JENGA_Effective_Memory_Management_for_Serving_LLM_with_Heterogeneity.pdf
[sglang]: readings/SGLang_Efficient_Execution_of_Structured_Language_Model_Programs.pdf
[vtc]: readings/Fairness_in_Serving_Large_Language_Models.pdf
[dlpm]: readings/Locality-aware_Fair_Scheduling_in_LLM_Serving.pdf
[mpich]: readings/Optimization_of_Collective_Communication_Operations_in_MPICH.pdf
[scaling]: readings/Efficiently_Scaling_Transformer_Inference.pdf
[megatron]: readings/Megatron-LM_Training_Multi-Billion_Parameter_Language_Models_Using_Model_Parallelism.pdf
[gpipe]: readings/GPipe_Easy_Scaling_with_Micro-Batch_Pipeline_Parallelism.pdf
[loongserve]: readings/LoongServe_Efficiently_Serving_Long-Context_Large_Language_Models_with_Elastic_Sequence_Parallelism.pdf
[nanoflow]: readings/NanoFlow_Towards_Optimal_Large_Language_Model_Serving_Throughput.pdf
[vattention]: readings/vAttention_Dynamic_Memory_Management_for_Serving_LLMs_without_PagedAttention.pdf

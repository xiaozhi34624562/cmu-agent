# 第 11 课：LLM 服务基础 II——从 GPU 的吞吐机器到可验证的性能优化

> 课程日期：2026-10-21。材料核查：2026-10-26。主讲 Juncheng Yang。本文以 [10_llm_serving_basics_2a.pdf](10_llm_serving_basics_2a.pdf) 全部 41 页为主线，L p.x 均是 **PDF 实际页序，从 1 开始**，不沿用跳号的页脚号。  
> 课程 [SOURCES.md](SOURCES.md) 中有 14 项已归档 reading 文件，另有 Roofline 与 PyTorch 2 的在线来源。本文补存 [Berkeley Roofline 技术报告](references/Roofline_An_Insightful_Visual_Performance_Model_for_Floating-Point_Programs_and_Multicore_Architectures.pdf) 与 [PyTorch 2 原论文](references/PyTorch_2_Faster_Machine_Learning_Through_Dynamic_Python_Bytecode_Transformation_and_Graph_Compilation.pdf)，版本和获取信息见 [REFERENCES.json](REFERENCES.json)。没有实际运行 GPU、CUDA 或论文性能实验；CPU 教学示例的验证范围单独说明。

## 0. 本课的中心问题：为什么算力没有变成速度

上一课把模型分成权重、计算与 KV 状态。本课进一步问：这些工作落到 GPU 后，为什么标称每秒近千万亿次运算，生成一个 token 仍要数毫秒？答案不能只用一句“decode memory-bound”概括。必须分清：要传多少字节、能同时发出多少请求、从哪一级内存传、实际指令依赖、并行工作是否足够、host 是否及时提交，以及用户请求是否还在队列里。

本课有三个观察尺度。**内核尺度**研究一个 attention 或 GEMM 怎样使用 Tensor Cores、寄存器、shared memory、L2 和 HBM；**模型一步尺度**研究几十层、通信、采样与许多 kernel 怎样串起来；**服务尺度**研究连续批处理、KV 布局、不同请求长度、编译与队列怎样影响实际时延和吞吐。某个尺度的最优结果不能自动跨尺度成立。

学完应能用 roofline 给出性能上界，用 Little 定律解释带宽为何需要并发，用在线 softmax理解 FlashAttention，用 Amdahl 定律限制端到端加速想象，并设计能确认“瓶颈真的转移了”的实验。

### 0.1 材料地图

| 讲义实际页 | 内容 | 本文与补充 |
|---|---|---|
| L pp.1–6 | 课程范围、作业说明、GPU 形态与图片 | 第 1 节；本笔记不代做要求独立提交的作业 |
| L pp.7–12 | 吞吐取舍、warp、SIMT、分支 | 第 1–3 节；CUDA Guide |
| L pp.13–22 | 峰值/容量/带宽、算术强度、batch/context、roofline | 第 4–7 节；Roofline、making DL go brrr |
| L pp.23–28 | SM、Tensor Cores、内存层级 | 第 2–3、8 节；CUDA、FlashAttention 系列 |
| L pp.29–33 | bytes in flight、异步复制、TMA、TMEM、双 SM MMA | 第 8–10 节；FA3/4、B200 walkthrough |
| L pp.34–35 | 多 GPU 互连、架构演进 | 第 11–12 节；FLUX、编译与运行时 |
| L pp.36–37 | 下一课与选读结束页 | 实验方法及第 13–16 节 |
| L pp.38–41 | AMD、TPU、Trainium、片上 SRAM 加速器 | 第 14 节；Ragged Paged Attention |

## 1. GPU 为什么像车队：吞吐、并行与单任务延迟

L pp.7–8 将 CPU 和 GPU 对比。CPU 花较多面积与功耗做强单线程：分支预测、乱序执行、大缓存能让一个复杂控制流尽量快地前进。GPU 则用大量执行单元、许多常驻线程和宽 HBM 接口，追求整个芯片每秒完成的总工作。这个取舍特别适合大量相似、相互独立的矩阵乘。

“GPU 简单核心”不是说没有缓存、调度或复杂硬件；而是单线程优化与全芯片吞吐的预算不同。一个高度串行的小程序搬到 GPU，可能增加启动与传输成本，却没有足够并行工作。模型含很多矩阵并不保证每个实际矩阵形状都足够大。

L p.8 的 64-core CPU 与 H200 数字也不能当作精确同精度跑分：CPU 行是 FP32，GPU 峰值行是 BF16 Tensor Core。其目的在于说明执行结构、线程和带宽量级，不能由这两行除出“GPU 比 CPU 快 198 倍”的普适倍数。

一次 warp 等待内存时，SM 可以选择另一个就绪 warp 执行。等待并没有消失，仍由该 warp 承担；被隐藏的是执行单元原本可能空闲的时间。如果所有 warp 同时卡在同一个长依赖，或没有足够就绪工作，切换也救不了吞吐。若整个 kernel 只启动几个 block，很多 SM 根本没有工作。

### 1.1 延迟隐藏不等于降低延迟

假设一次 HBM 访问要约 250 ns。增加 warp 能让 GPU 在这 250 ns 内服务其他工作，但并不把该数据的返回时间改成 25 ns。单个长依赖链仍可能慢，整体吞吐却会高。反过来，减少串行依赖可能显著改善一个 kernel，即使其总 FLOPs 和总字节完全不变。

因此排障要分别问：某条请求为什么慢，是执行链长还是竞争与排队？整个 GPU 为什么不忙，是工作太少、依赖太强还是指令发不出？整台服务为什么吞吐不高，是 GPU、CPU、通信还是请求量限制？“利用率”一词如果没有指标定义，几乎无法回答这些问题。

## 2. 从 thread 到 SM：编程模型和物理执行如何对应

CUDA 程序通常按 grid → thread block → thread 组织。每个 thread 以自己的索引处理数据；一个 block 的线程可以通过 shared memory 与 barrier 协作。block 通常被安排在一个 SM 上执行，grid 中许多 block 分布到多个 SM。普通 block 间不能假设固定调度顺序，也不能随意用互相自旋等待实现全局同步，否则可能等到尚未获调度的 block 而死锁。

硬件将同一 block 中连续线程编为 32-thread warp。Warp 是主要指令调度群组，32 个 lane 使用各自寄存器、地址与谓词，执行共同指令。CUDA thread 不等于一个固定独占的“CUDA core”；多条 warp 指令会在物理执行单元与流水线中推进。SM 是调度与资源域，FP32 core 是运算通路，Tensor Core 是矩阵专用单元，它们不能用数量一一互换。

L pp.24–25 用 H200 例子：132 个 SM，共享 L2/HBM；一个 SM 示意为四个分区，每个分区有 warp scheduler、寄存器与运算单元。最多 64 个常驻 warp、2048 线程是讲义针对这些具体 NVIDIA 架构的资源上限，不是所有 GPU 的跨代定律。真正能驻留多少还受每 block 线程数、寄存器、shared memory、block 数量上限等约束。

### 2.1 Occupancy 是资源比例，不是速度本身

Occupancy 常指常驻 warp 数占硬件上限的比例。高 occupancy 为隐藏延迟提供候选工作，但不保证每周期有足够 ready warp，也不保证 Tensor Cores 已经高效运行。一个大量等待 barrier 的 kernel 可以高 occupancy、低吞吐；一个寄存器较多、occupancy 较低但复用极好的 matmul，也可以更快。

扩大 tile 能减少重复 HBM 读取，却需要更多寄存器和 shared memory。资源一旦跨过某个阈值，SM 可驻留 block 从 2 降到 1，或寄存器 spill 到 local memory，速度反而下降。调参不能只追求最大 tile，也不能只追求 100% occupancy；应同时看复用、并发、spill、执行时间和实际形状。

L p.12 的“满占用约每线程 240 bytes”是资源预算的量级直觉，不能拿它当语言层面每线程固定堆空间。寄存器分配以架构粒度和编译器分配为准；local memory 虽然名字有 local，通常位于 device memory，并不等于低延迟片上私有 SRAM。

### 2.2 一个最小 kernel 的思路

向量加法可以让线程 `i=blockIdx.x*blockDim.x+threadIdx.x` 处理 `C[i]=A[i]+B[i]`，并在 i<N 时执行。最后不足一个 block 的尾部必须有边界检查。若 shared-memory 算法需要整个 block 的 `__syncthreads()`，不能让部分线程在 barrier 之前提前返回；应使所有需要参与的线程到达同步点，用谓词保护数据访问。

这些约束是正确性条件。一个偶尔快但存在 race 的 kernel 不算优化成功；随机输入误差检查无法证明没有同步问题，实际 GPU 实现还应使用相应 memory/race 检测工具与不同边界形状。

## 3. SIMT、分支与 Tensor Cores：算术不是同一类资源

L pp.10–11 的 SIMT 意味着一个 warp 共同执行指令，各 lane 持有自己的标量状态。若同一 warp 的 8 个 lane 走 f、24 个 lane 走 g，硬件通常分时执行两条路径，用 active mask 关闭不属于当前路径的 lane。总成本更接近两条路径工作之和，而非按 8/32 与 24/32 完全免费并行。

若所有线程都走相同分支，没有这种 warp 内分歧。若编译器把极短分支改成 predication，实际指令形式又可能不同。现代 independent thread scheduling 提供更细执行能力，但不能假设它使 warp divergence 免费，也不能省掉跨线程通信所需的显式同步。

分支还可能来自 ragged 输入：不同请求有不同序列长，某些 lane 在末页越界而被 mask。把相似长度分组或设计更合适的 tile 可以减少空工作，但过度分组也会增加调度开销和请求等待。服务层数据布局与 kernel 执行效率在这里相遇。

### 3.1 矩阵乘为什么适合专用单元

Tensor Core 以 tile 为单位计算 `D=A×B+C`。L p.26 的 16×16 乘 16×8 对每个输出累加 16 项，总计 16×8×16=2048 个 multiply-add；若乘与加各计一 FLOP，则是 4096 FLOPs。讲义“一次 MMA 相比 FMA 的 64×工作”对应它选定的 warp/指令与 lane 口径，不能混成“所有 MMA 指令都只有同一固定形状或同一周期数”。实际 PTX/硬件指令支持的 shape、类型和吞吐各不相同。

专用矩阵通路能复用操作数并摊薄指令控制。较低输入精度可提高吞吐、降低搬运量，累积常用更高精度。但 softmax、归一化、指数、地址计算、掩码与同步并不都由同一个 Tensor Core 执行。即便 matmul 占绝大部分 **FLOPs**，也不意味着它占同样比例的 **时间**。

这正是 FlashAttention-2 减少非 matmul FLOPs、FlashAttention-4 处理指数单元瓶颈的原因。用 BF16 Tensor Core 峰值给 softmax 的指数运算估时间，会得到不可能的乐观值。一个完整 kernel 可以有多个资源 roofline，而不只有 HBM 和 Tensor Core 两条界线。

## 4. 三张账本：容量、带宽和算力

L p.13 列 H200 141 GB、4.8 TB/s、989 TFLOP/s 等值。容量决定权重、KV、工作区能否容纳；带宽决定单位时间能搬多少字节；算力决定单位时间可完成多少对应精度的运算。三者量纲不同，增加容量不会自动提高带宽，降低参数量也不会自动缩短 host 调度等待。

本课后续示例使用讲义的 H200 SXM 理论 dense BF16 数字作为演算常数。它们不是本机检测结果。具体 SKU、功耗、频率、ECC、时钟限制、热状态、内核访存模式与软件版本会影响持续可达性能。不同图表若采用不同精度或 sparse 峰值，不能直接横向比较。

令 kernel 工作为 F FLOPs、从 HBM 传输 Q bytes，理想下界可写：

$$
T\ge \max(F/P_{\mathrm{peak}},\ Q/\mathrm{BW}_{\mathrm{HBM}}).
$$

这是假定计算和搬运能充分重叠的资源下界。如果复制与计算串行、还存在额外同步，实际时间会更长。一个完整模型多 kernel 的执行时间通常是各阶段沿依赖路径组合，不能把全模型 F、Q 一起取 max 就保证所有时间都能重叠。

### 4.1 对照 L p.14 的 8B 示例

约 8B BF16 权重占 16 GB。batch 1 decode 对这些线性权重约做 16 GFLOPs：读取时间 16GB/4.8TB/s≈3.33ms，理想矩阵计算时间 16GFLOPs/989TFLOP/s≈0.016ms。于是即便满带宽，Tensor Core 峰值利用比例也不到 1%。这说明算力峰值不是这个形状的主约束，不说明 kernel 已经真的达到 4.8TB/s。

若 2048 个 prompt token 同时复用权重，线性层算量约 32.8 TFLOPs，对应约 33ms 的计算下界。权重读取仍约 3.33ms，但还应加 attention、激活读写与其他操作。这是 prefill 更容易 compute-bound 的原因，不能据此说“prefill 的 HBM 全程闲着”。

## 5. Roofline：算术强度的分母必须说清

定义 HBM 算术强度 I=F/Q，单位 FLOP/byte。可达到的算术吞吐上界为：

$$
P_{\mathrm{attainable}}\le\min(P_{\mathrm{peak}},\mathrm{BW}_{\mathrm{HBM}}I).
$$

横轴为 I，纵轴为 FLOP/s。在 log-log 图上，带宽线斜率为 1，计算上限是一条水平线，交点 ridge 为 I*=Ppeak/BW。H200 BF16 代入为 989/4.8≈206.04 FLOP/B。左边增加复用可提高上界，右边继续减少 HBM 流量未必改善时间。

[Roofline 原始技术报告](references/Roofline_An_Insightful_Visual_Performance_Model_for_Floating-Point_Programs_and_Multicore_Architectures.pdf) 特意将 operational intensity 定义为缓存过滤后主存的流量；它区别于处理器和 cache 之间的流量。现代 GPU 文献常宽泛使用 arithmetic intensity，因此每次必须写明分母是 HBM、L2 还是 shared memory 字节。一个数据块从 HBM 进 L2 一次，被很多 SM 重读，HBM 强度高，不代表 L2 强度也高。

原模型还提出“ceiling”：指令混合、向量化、并行、实际可持续带宽等限制可把理想屋顶往下压。测得性能远低于斜线不表示模型理论失效，可能说明尚未满足并发、访存合并或有效指令吞吐等条件。Roofline 是资源边界和假设检验工具，不是自动给出 root cause 的分类器。

### 5.1 四种操作的强度推导

假设每元素 b bytes，忽略缓存和额外临时量，使用相应理想流量口径：

| 操作 | FLOPs | 传输量 | 近似 I |
|---|---:|---:|---:|
| 向量加法，N 个元素 | N | 读两写一，3Nb | 1/(3b) |
| N×N GEMV | 2N² | (N²+2N)b | 大 N 时约 2/b |
| 方阵 GEMM | 2N³ | 最小读 A/B 写 C，3N²b | 2N/(3b) |
| 单 query attention 读 n 个 K/V，head dim d | 约 4nd | 约 2ndb | 约 2/b |

GEMM 行假定 tile 复用足够好，每输入仅按最低流量计，不保证实际只读一次。GEMV 行忽略重复读取 x 等，实际内存访问可更差。若 C 还需要原值以做 beta C，读写量也要修正。Attention 行只比较两个乘法主项与 K/V 流量，softmax 和 query/output 等对小 n 可能不再可忽略。

BF16 b=2，因此单 query 的 attention 和大 GEMV 都约 1 FLOP/B。此时即便 HBM 达峰，也仅约 4.8 TFLOP/s，对 989 TFLOP/s 是约 0.485%。这个利用比例是数学上界演算，不是对真实 profiler 的 SM utilization 读数。

### 5.2 为什么不同层级会给不同答案

假设一个 tile 的 K/V 从 HBM 读一次，被同组 8 个 GQA query head 在片上复用。以 HBM 流量为分母，强度可提高；若实现把 K/V 为每个 query head 重读，收益就消失。对 shared memory 而言，重复片上读取仍消耗带宽，因此 Tensor Cores 还可能等 shared-memory 通路。

同样，L2 命中率高不等于访存免费：L2 有有限带宽与延迟。FP8/FP4 提高 Tensor Core 峰值后，I* 可能大幅右移；虽然压缩输入也减少 Q，提高 I，但两种变化要同时计算。只说“精度更低一定从 memory-bound 变成 compute-bound”或反过来，都不够严谨。

## 6. Batching 与 context：为什么一个改善强度，一个常只增加流量

把 B 个独立 query 组成一次权重矩阵乘，线性层约做 2BN FLOPs，权重可共享读取 Nb bytes。忽略激活后 I≈2B/b，BF16 时约 B。这是 L p.17 的权重曲线从 1 随 batch 上升到 256 的直觉。接近 H200 的 206 FLOP/B ridge 时，计算可能逐渐成为约束，但实际激活、tile 与其他操作让转折不是精确整数 206。

不同请求的 KV 一般不共享。B 变大，每步 KV 计算和读流量同时约放大 B，因此 **跨独立序列 batching 本身** 不提升这部分强度。GQA query 组内复用、共享前缀、多 token query、speculation 会改变条件，不能把“attention 始终1 FLOP/B”当作所有 decode kernels 的定律。

上下文增长则更直接地增加每请求要读的 K/V。单 query 对每一条新增历史做的算术与字节保持近似比例，所以更长 n 通常让时间变长，却不让强度自动跨过 ridge。KV 在总流量里的占比还会逐步超过权重，于是“batch 足够大，权重已摊薄”后仍可能被长上下文拖慢。

### 6.1 复算 L p.18 的长上下文例子

Llama 3 8B 的 L=32、Hkv=8、dk=128、BF16，则 CKV=2×32×8×128×2=131072 bytes/token，即 128 KiB。B=16，n=32768 时，KV 约 68.72 GB；加讲义权重 16.1 GB，本步约读 84.82 GB。除以 4.8 TB/s 得 17.67 ms，和讲义 17.7 ms 一致。

这里 32K 按 32768 处理；若使用 32000 就会得到不同结果。1K 同理采用 1024，读流量约 18.25 GB、约 3.8 ms。这个模型忽略已在 cache 的部分、组内复用的具体实现、输出写入、通信和 host 开销，也没有声称所有流量都真正达到峰值。

调度层看到的 ITL 还可能包括这一批的其他 kernel、prefill 插入、不同长度负载与队列。不能把 17.7 ms 算式与端到端 p99 直接比较，然后断言剩下的差值全是“框架浪费”。应按实际执行时间线分解。

### 6.2 什么时候 batching 会适得其反

对单请求，batch 增大可能延长每步时间；对系统，总 tokens/s 可能上升。到达率低时，为凑大 batch 主动等待会恶化 TTFT；长短序列混合会造成工作不均；超出容量会抢占或重算；更大 batch 还可能改变图捕获与内核选择。

因此部署目标可以定义为“满足 p99 TTFT 和 TPOT 的最大有用吞吐”，而不是只看某一最大 batch 的速度。比较两种配置时固定输入/输出长度与到达过程，报告拒绝和失败请求。GPU 更忙并不自动意味着用户更满意。

## 7. Roofline 的三个常见误读与修正

**误读一：memory-bound 就是 HBM 满了。** 算术强度低只说明资源上界倾向带宽；实际还可能受内存延迟、缺少独立访存、地址计算、L2、同步或短 kernel 约束。先看实际 DRAM bytes/s、ready warps、load stalls 与时间线，再决定怎样优化。

**误读二：FLOPs 占比就是时间占比。** Tensor Cores 做矩阵很快，softmax 指数、归约与同步的 FLOPs 少，可能仍耗大量周期。针对错的运算单元计算 MFU，会掩盖问题。

**误读三：kernel 更快同倍数等于服务更快。** 若 attention 仅占端到端 30%，将它加速 2 倍，Amdahl 上界为 `1/(0.7+0.3/2)≈1.176`，而不是 2 倍。若优化影响 scheduler、显存余量与 batch，还会有系统级二阶效应，需要重新测量。

L p.21 的未来硬件表包含 preliminary 项。本文保留其“算力、HBM 与其他单元不同比例增长”的设计结论，不把 Rubin、不同厂商或不同 SKU 的讲义数字当作当前采购规格或实测。硬件演进趋势也不保证每两代 I* 都单调右移；必须按具体 precision、dense/sparse 和带宽重算。

## 8. 内存层级与 Little 定律：让管道有足够在途字节

L p.28 从寄存器、shared/L1、L2、HBM 到 host/peer 列出容量、延迟与带宽。离执行单元越近的存储通常更快、更小，但用途与管理方式不同。寄存器保存每线程 live values；shared memory 是 block 可编程的协作存储；L1/L2 是硬件缓存；HBM 保存权重与大状态。Shared/L1 共享物理池不意味着两者可同时独立占满标称容量。

讲义中的 cycle/ns 数是架构与微基准量级，而非所有 load 指令的固定延迟。Cache hit、依赖链、bank conflict、请求大小、频率都会影响结果。NVLink 的双向总带宽与单向带宽也要区分：表中 900GB/s 总量和450GB/s each way是同一口径的不同表达，不应再次相加两遍。

### 8.1 用水管模型推导 in-flight 需求

稳态下 Little 定律给出平均在途数据 Qflight = BW×latency。H200 若想在约250ns的读延迟下持续达到4.8TB/s，需要全芯片约1.2MB在途，平均每132个SM约9091 bytes，即约9KB。这不是每SM额外分配9KB缓存的意思，而是尚未完成的有效内存请求所代表的数据量。

L p.29 的示例 `32 warps×32 threads×4B` 是4096B=4KiB。用它除250ns并乘132个SM，得到约2.16TB/s，解释图中约2.2TB/s。单位与并发是关键：增加“线程数”如果没有带来更多独立未完成 load，也不一定增加有效在途字节。

可以让每线程发16-byte vector load，或多条独立load，或用TMA搬大tile，提高每条指令对应的在途工作。但这受对齐、寄存器、队列、地址与依赖限制；不对齐的向量load可能拆分，更多并发也可能使cache污染或resource pressure上升。Little定律给必要量级，不保证这些字节一定均匀分布、没有冲突。

### 8.2 Coalescing、bank conflict 与异步复制分别修什么

Coalescing 让warp相邻lane访问相邻地址，合成较少且有效的内存事务。讲义“32×4B合成128B”是对齐连续访问的简化；现代实际sector/transaction粒度取决于架构与cache策略。跨跨度访问可能为了少量有效数据搬来许多sector，这时“逻辑bytes”小，物理流量却大。

Shared memory bank conflict 则发生在片上并行访问映射到相同bank等情况下，不是HBM coalescing。改变tile布局或swizzle可以减少冲突，但必须保持计算语义。把两种问题都称“访存不连续”会导致优化错层级。

Ampere 的cp.async支持global→shared异步复制，避免先把中间数据放进普通寄存器；Hopper的TMA用描述符与硬件地址生成搬整个tile，并能配合barrier。异步不是可以随便读尚未到达的数据；producer提交、完成通知、consumer等待以及buffer复用必须遵循正确协议。双缓冲用更多shared memory换重叠空间，若因此occupancy下降，收益要实测。

### 8.3 TMA multicast 和 Blackwell TMEM

L p.32 的cluster multicast可将同一数据服务到cluster内多个block的shared memory，减少某些重复L2访问。Cluster共调度与可移植大小等条件来自硬件/编程模型，不是任意8个SM在任何时刻都能自动共享一次读。缓存、同步和block布局需要一起设计。

L p.33 展示Blackwell将矩阵累积结果移到tensor memory，并提供跨两个SM协作的MMA。TMEM缓解寄存器压力，较大协作tile能摊薄某些数据访问；它不是把所有寄存器替换掉，也不是透明扩充HBM。端到端收益来自新的数据通路与pipeline设计，不能把Hopper kernel编译到新卡就假设自动使用所有能力。

## 9. FlashAttention：保持数学 attention，改变 IO 顺序

标准attention先物化S=QKᵀ，再softmax成P，再算PV，会反复写读n×n中间矩阵。FlashAttention把Q/K/V分块，在片上处理一块score后立刻更新归一化统计与输出，不把完整S/P写到HBM。它是精确attention的IO优化，除浮点顺序外不引入稀疏/低秩近似；其dense算术量仍随n²增长。

### 9.1 在线softmax为什么可以跨tile精确合并

对一行score，维护已见最大值m、归一化和ℓ，以及未除以ℓ的加权value向量u。新tile有scores s和values v，更新：

$$
m'=\max(m,\max_j s_j),\quad a=\exp(m-m'),
$$
$$
\ell'=a\ell+\sum_j\exp(s_j-m'),\quad
u'=a u+\sum_j\exp(s_j-m')v_j.
$$

最终输出u/ℓ。旧贡献乘a，是把旧基准m转换到新基准m'；若只把新tile概率加上去而不重缩旧贡献，答案会错。初始化m=-∞、ℓ=0、u=0；对完全mask的tile或空行需要额外处理，不能直接执行∞相减。

举例先看到scores `[0,ln2]`，m=ln2、ℓ=1.5；再看到score ln4，新m=ln4，a=1/2，于是总ℓ=1.75，对应原始指数和7除4。这个算法只需要逐行统计和输出累积，适合tile遍历。反向传播可以使用保存的归一化统计重算局部score，用额外计算换低HBM流量与较小保存状态。

[FlashAttention原文](readings/FlashAttention_Fast_and_Memory-Efficient_Exact_Attention_with_IO-Awareness.pdf) Algorithm 1与IO分析给出分块/重算的机制。它还另有block-sparse扩展，那个扩展改变访问模式，与“精确dense FlashAttention”分开。论文BERT、GPT-2、LRA训练加速来自具体模型、序列与基线；不能把训练端到端3×当作现代decode服务的普适数值。

### 9.2 FlashAttention-2：更好的工作划分

[FA2](readings/FlashAttention-2_Faster_Attention_with_Better_Parallelism_and_Work_Partitioning.pdf) 除减少non-matmul工作，还把单head沿query序列分到更多block，避免batch×head较小时SM不足。块内重新划分warp负责的query，减少shared-memory交换和同步。优化对象从“避免巨大中间量”进到“这些tile由谁来做”。

增并行不总是免费。沿K/V split会产生partial softmax结果，需要额外合并；沿Q split较独立，但每block可能重复读K/V。FA2的设计利用具体shape与硬件平衡这种关系。论文在A100报告50–73%峰值、GPT训练225TFLOP/s/A100是kernel与模型级各自的指标，不能混为服务吞吐。

### 9.3 FlashAttention-3：Hopper的异步不是一句“多线程”

[FA3](readings/FlashAttention-3_Fast_and_Accurate_Attention_with_Asynchrony_and_Low-precision.pdf) 让producer warps负责TMA搬运，consumer warps负责WGMMA/softmax等，交错不同tile的matmul与softmax，把本来串行的不同功能单元工作重叠。Producer与consumer通过barrier和buffer阶段配合，而不是无约束同时访问同一地址。

FP8路径另用block quantization与incoherent processing减少outlier问题；性能提升和数值精度要一起验证。论文H100 FP16最高740TFLOP/s、FP8近1.2PFLOP/s是不同precision，2.6×更低误差也相对它定义的FP8 baseline，不是“比FP16更精确”。论文§4.2固定{batch=4,seqlen=8448,heads=16,dim=128}做pipeline消融；这样的受控对照才说明异步机制贡献，跨GPU最大数值不能替代它。

### 9.4 FlashAttention-4：谁没有随Tensor Core一起变快

[FA4](readings/FlashAttention-4_Algorithm_and_Kernel_Pipelining_Co-Design_for_Asymmetric_Hardware_Scaling.pdf) 面向Blackwell不对称扩展：矩阵通路变快，shared-memory带宽和指数等单元没有按同比例增长。它重新安排更大tile和全异步pipeline，用软件模拟部分指数、条件性softmax rescaling等减轻非matmul瓶颈，并利用TMEM与2-CTA MMA。速度来自整体平衡，不是简单把softmax删掉。

有一个必须保留的版本问题：本地论文摘要/主要图写B200、BF16最高1613TFLOP/s、约71%利用率；但PDF p.20 Appendix A.1写“B100 180GB SXM6 (1000W)”，同页又写March 2025并列出CUDA13.1、PyTorch2.10等软件。已目视核对原页，确是原文件内部表述不一致。本文将峰值仅作为**论文自报且硬件设置待澄清**的结果，不把它当可精确复现的独立硬件基准，也不自行替作者改名或改日期。

论文相对cuDNN9.13和Triton的最高倍数依赖shape、causal与前后向；cuDNN后续版本也吸收相近技术。不能把论文的最大加速迁移到任意当前库版本。编译时间20–30×是相对具体C++模板路径的开发成本，不是运行时模型吞吐。

## 10. 从统一tile到真实服务：FlashInfer与B200逐步优化

[B200 walkthrough](readings/FlashAttention-4_from_Scratch_to_Near-SOTA_in_60_Diagrams_CUDA_PTX.html) 在固定dense non-causal BF16、head dim128、4K/8K/16K等shape上逐步改14版kernel，以同机FA4为参考，最终达到约94.4%的相对表现。它是作者公开的工程过程，不是同行评议论文，也不能外推到causal、decode或paged/ragged全部负载。

它的价值在因果顺序：先修shared-memory layout，再增加query tile复用，再做load/compute pipeline和指数通路优化。某一步单独看几乎无收益，仍可能为后续pipeline创造条件。不能把14步的单项百分比相加成总加速；最初和最终的瓶颈不同，收益互相依赖。

### 10.1 Ragged、paged与共享prefix改变接口

服务batch里的请求长度各异，KV在页表指向的不连续block里；请求结束、新请求加入，逻辑形状持续变化。Padding到最长序列会浪费算术与带宽；每请求单独launch又增加小kernel与host开销。一个只对均匀连续KV很快的attention kernel，不一定适合服务。

[FlashInfer](readings/FlashInfer_Efficient_and_Customizable_Attention_Engine_for_LLM_Inference_Serving.pdf) Figure 1与§3用统一block-sparse视角表达不同KV布局，JIT生成不同attention变体，并把动态长度信息交给load-balanced runtime。它把“做什么attention”“KV怎么存”“这些tile怎样分工作”明确分开。部分计划可放CPU侧，执行形状配合CUDA Graph，让动态工作不必每次重建整个launch路径。

这不等于所有layout没有成本差异。页表读取、短页尾、split-KV合并、共享前缀复用和workspace都有开销；调度plan也要计时。对head dim、query group与序列分布的kernel选择是性能的一部分。

### 10.2 如何正确引用FlashInfer实验

原文§4的实验硬件是A10040GB SXM与H10080GB SXM，CUDA12.4、PyTorch2.4、f16。在线服务比较包含SGLang0.3.4的Triton3.0后端与FlashInfer0.2、ShareGPT和512–2048均匀长度Variable等负载，并调整请求率使p99 TTFT低于200ms。29–69% ITL降低因此是特定条件结果，不是对所有生产服务的平均收益。

例如更换attention后端同时改变可持续请求率，ITL与TTFT的解释需要同时看负载与约束。长上下文、parallel generation等实验又是另外的设置，不能把28–30%和13–17%当作可以叠乘到同一个请求上的独立收益。

## 11. 多GPU：互连不是另一块等速HBM

L p.34 区分scale-up的NVLink/NVSwitch与scale-out的网络。讲义H200例中HBM4.8TB/s、NVLink总900GB/s、400Gb/s网卡约50GB/s是不同链路、不同口径的数量级。数据跨卡时不能继续按HBM带宽估算。Gb/s与GB/s差8倍；双向总带宽不等于单向有效payload。

Tensor parallel把权重和矩阵工作分到多卡，但每层可能需要collective。延迟可粗略分为启动/同步α与消息量S除有效带宽β：`Tcomm≈α+S/β`，实际collective还取决于算法与拓扑。Decode的小消息常被α主导，卡越多并不意味着α按卡数下降。Prefill的大矩阵更容易摊薄通信，但仍要看分片与network。

### 11.1 FLUX：从整层等待变成细粒度重叠

[FLUX](readings/FLUX_Fast_Software-based_Communication_Overlap_on_GPUs_through_Kernel_Fusion.pdf) 把通信和计算细分，再融合到同一kernel：已有tile可发送时不必等整个GEMM结束；接收一部分tile后也可启动对应计算。它不消除依赖，只利用不同tile之间允许重叠的空间。同步、SM分配、通信primitive和matmul效率需要一起平衡。

原文区分8-GPU推理和128-GPU训练；最高96%通信隐藏是相应fused操作的指标。1.66× prefill、1.30× decode相对vLLM，以及训练相对Megatron-LM1.24×，属于不同实验。把“隐藏96%”直接读成整个模型通信成本只剩4%或总速度25×，都会错。

部署时先确认通信在critical path上占多少，再考虑融合。某些collective已很短，融合增加寄存器压力、占SM或调度复杂度可能不值得。更大batch、不同TP degree与跨节点拓扑也会改变最佳方案。

## 12. 编译与运行时：减少launch、搜索schedule、改变计算边界

很多小kernel之间的CPU dispatch、参数准备、launch与同步会形成GPU空洞。[making DL go brrr](readings/Making_Deep_Learning_go_Brrrr_From_First_Principles.html) 把问题分成compute、memory和overhead三类，适合用来提出初步假设，但仍要用trace确认，不能单凭Python代码长度推断overhead。

### 12.1 Fusion到底省了什么

例如先算y=x+a，再算z=relu(y)，两个kernel需要写y到HBM再读回。融合可让y保留在寄存器，减少中间流量与launch。若后续有很多consumer或不同最佳tile，过度融合可能增加重复计算和live values，造成spill或低occupancy。融合不是算子越多越好。

CUDA Graph记录一段操作与依赖，实例化后重复launch，主要减少重复host提交工作；它不会自动把每个kernel内部算术变快，也不自动等于fusion。图内仍可以有多个kernel与内存操作。

### 12.2 CUDA Graph并非“指针与shape永远不能更新”

本地[CUDA Guide](readings/CUDA_C++_Programming_Guide.pdf) §6.2.8.7、PDF pp.73–82明确有whole graph / individual node update，以及具体限制。稳定拓扑下部分参数可以更新；新增任意操作或改变不受支持属性则可能需要重捕获/实例化。许多serving实现使用固定batch capture list、padding和稳定buffer，是为了降低动态更新成本及满足其实现约束，不能写成CUDA API根本不允许任何指针或参数变化。

本地Guide封面Release13.4、2026-09-15，同时正文说明这一份CUDA C++ Programming Guide已成为legacy、从CUDA13.0起不再更新。本文据它核查基本语义与所载API，不把封面新版本自动等同所有内容代表最新编程建议。实际部署还应查所用runtime的对应文档。

### 12.3 TVM：计算定义和schedule分开

[TVM](readings/TVM_An_Automated_End-to-End_Optimizing_Compiler_for_Deep_Learning.pdf) 将张量表达“算什么”与schedule“怎样tile、重排、vectorize、放在哪级存储”分开，并用cost model与实际测量搜索。对不同hardware可以保持计算语义，换schedule。图级fusion与算子级优化都需要，单独有graph IR不保证矩阵内部高效。

原文跨CPU、移动GPU、serverGPU、FPGA验证可移植性，不能把2018年库比较当作2026年LLM服务排行。学习其抽象边界比记住某个当年最大倍数更有价值。Tuning本身有编译与测试成本，shape变化频繁时需考虑摊销。

### 12.4 Mirage：同时搜索多个层级的等价程序

[Mirage](readings/Mirage_A_Multi-Level_Superoptimizer_for_Tensor_Programs.pdf) 用μGraphs统一kernel、thread-block、thread层，联合代数变换与schedule变换。它不只是对原图每个算子挑一个tile，而是搜索新的等价区域实现。等价验证有适用的tensor program/代数范围与概率保证，不应描述成任意Python或任意浮点程序的全功能证明。

本地v3原文§8评估GQA、QKNorm、RMSNorm、LoRA、GatedMLP等；相对基线的最高3.3×来自相应operator/shape与GPU条件，不能直接称整个LLM服务提升3.3×。有的benchmark它也并非最优，表明搜索空间、成本与操作结构会限制收益。

### 12.5 MPK：把调度搬入persistent kernel

[MPK](readings/MPK_A_Compiler_and_Runtime_for_Mega-Kernelizing_Tensor_Programs.pdf) 将整段多GPU推理编成SM级task graph，以kernel内部scheduler调度worker，减少每operator的launch边界并表达跨operator/通信pipeline。它比CUDA Graph更深入：不只批量提交已有kernel，而是改变运行时执行单位。

原文§6.2用A100/H100/B200，给scheduler保留4个SM、共16个scheduler warp，其他SM当worker。这个资源不是免费；模型编译、task graph、shared-memory page与物理SM数有对应关系。kernel长驻后，公平性、抢占与和其他任务共存也成为部署问题。

最高约1.7×较低端到端推理latency的评估使用**离线batched inference**，每请求prompt64、生成1024，BF16，vary maximum batch，比较vLLM/SGLang。它排除了在线到达不足的server-side stall，不能当作真实互联网到达下p99改进的直接证据。把continuous batching开启与在线load generation混为一谈，会误读这项实验。

### 12.6 PyTorch2：guard决定编译假设何时还成立

[PyTorch2原文](references/PyTorch_2_Faster_Machine_Learning_Through_Dynamic_Python_Bytecode_Transformation_and_Graph_Compilation.pdf) 的TorchDynamo拦截Python bytecode提取FX图，附带guard；后续状态满足guard则复用，不满足就重新分析、编译或回落。TorchInductor进一步生成GPU Triton或CPU C++等实现。图捕获失败、graph break、动态shape和Python副作用决定实际覆盖率。

原文A100、180多真实模型上的几何平均2.27× inference、1.41× training属于框架benchmark；本文未把它外推到continuous-batched LLM serving。Serving需要观测compile/recompile次数、warm-up成本、缓存命中、guard触发的shape，以及冷启动与稳态差异。一次静态batch跑得快，不证明在线多长度不会反复编译。

## 13. 用测量闭合推理：characterization论文提供什么证据

[LLM inference characterization](readings/A_Systematic_Characterization_of_LLM_Inference_on_GPUs.pdf) §3在A100服务器与Jetson AGX Orin上，用vLLM0.9.2、BF16、固定离线request batches，比较Llama3-8B、Qwen2.5-7B/32B与Qwen3-30B-A3B等模型，覆盖Chat、Summary、Translation、Code、Story。它把阶段时间、kernel mix、roofline、warp stalls与访存联系起来。

论文测到prefill/decode都可以有很高stall比例，但stall原因不同。不能从“stall70–80%”推出GPU整体70–80%时间什么都没做：统计的分母可能是warp/issue周期，多warp可在同一时间互相隐藏等待，必须读具体counter定义。

§6的并行对照里，summary场景TP让prefill由1.24s降至0.66s，而decode可能因通信与同步变差；它支持“按阶段分析并行度”，不支持“TP永远只适合prefill、singleGPU永远最适合decode”的普遍结论。权重是否容纳、KV容量、batch、互连、模型规模都可能让结论改变。

该论文离线固定batch有利于隔离执行因素，但不覆盖在线排队。Jetson的共享资源和带宽也不同于数据中心GPU，因此同一个roofline概念可复用，具体ridge、stall结构与优化优先级必须重测。

### 13.1 一次完整优化实验的执行顺序

先建立正确输出基线与shape集合，再计时并收集trace。Warm-up使JIT、显存池、autotuning与graph capture完成；稳态和冷启动分别报告。GPU异步执行时，CPU调用返回不代表工作完成；需用合适device events或同步包围测量范围，避免把launch时间误当kernel执行时间。

记录GPU型号、SKU、功耗/频率、驱动/CUDA、框架/内核revision、precision、mask、head dimension、GQA group、batch/长度分布与cache layout。性能对照固定这些条件，只改一个主因素；多次测量报告分布，不挑最快一次。极短kernel需避免计时工具开销比目标工作还大。

再用counter检查假设：若说HBM-bound，确认实际bytes/s与访存效率；若说occupancy不足，查资源与eligible warp而非只看GPU利用率；若说SFU瓶颈，查相应pipeline吞吐；若说host-bound，检查kernel间gap与CPU trace；若说通信瓶颈，分离collective时间、消息大小与等待。

优化后除了时间，还要重新做正确性、数值误差、边界长度和目标任务质量。低precision不能只测随机均匀输入，需包括outlier、长序列和真实激活分布；race与同步问题也不能用一次成功运行消除。最后回到模型和在线服务层验证SLO，避免把benchmark局部胜利写成业务收益。

## 14. 非NVIDIA硬件：哪些算法思想可迁移，哪些必须重写

L pp.38–41是选读，不需要记下所有硬件规格。AMD的wavefront、ROCm/HIP，TPU的systolic array与XLA/Pallas，Trainium的Neuron/NKI、显式SRAM与DMA，片上SRAM芯片的容量/互连约束，都说明程序员看到的执行模型会改变。

TPU上没有CUDA warp，并不意味着无法做FlashAttention或paged KV。能迁移的是分块、在线softmax、逻辑页表、ragged遍历与流水线的算法需求；哪些tile形状、怎样搬运、用什么barrier、如何利用矩阵阵列，则由硬件决定。把CUDA kernel逐行翻译很难保留性能。

### 14.1 Ragged Paged Attention的具体分界

[RPA](readings/Ragged_Paged_Attention_A_High-Performance_and_Flexible_LLM_Inference_Kernel_for_TPU.pdf) 使用Pallas/Mosaic，结合细粒度tile、fused KV update、软件pipeline与按分布编译不同decode/prefill/mixed变体。原文在TPU7x Ironwood、Llama3-8B配置、BF16及128/256 head dim、不同causal设置下评估，报告最高86% MBU与73% MFU。

这些两个百分比属于不同资源分母和阶段，不能相加、也不能声称同一时刻“两种利用率全都满”。§4的decode吞吐设置还用128序列、同一context length，以控制实验；它不是所有生产ragged分布都达到86%。原文还通过关闭KV更新、DMA或attention部分做分解，帮助确认pipeline重叠与真正主瓶颈。

Systolic array让数据按规律在阵列中复用，省指令与寄存器往返；但动态索引、小矩阵、ragged shape和非矩阵操作仍有成本。软件管理SRAM让搬运更显式，也把排布和pipeline责任交给编译器/内核作者。大规模scale-up或片上SRAM降低某些访问成本，同时带来容量、跨芯片和开发工具限制。

本课讲义的其他加速器规格随版本变化，本文不作为采购表。部署选型至少需要相同模型/precision、相同业务质量、相同长度/到达分布，以及实际整机价格和可用性；峰值PFLOPs相近不能代替TCO比较。

## 15. 最小实现与排障：把概念落到可检查对象

[examples/roofline_online_softmax.py](examples/roofline_online_softmax.py) 在CPU上做两类验证：计算H200演算常数与Llama8B流量下界；用17个随机score、5维value，比较整行stable softmax与tile大小1/2/4/8/17的在线合并。它没有生成或运行GPU kernel，也没有测量HBM带宽。

```bash
python3 examples/roofline_online_softmax.py
```

[RUN.json](examples/RUN.json) 的实际结果：ridge约206.0417FLOP/B，batch1权重GEMV理论峰值比例约0.4853%，在途全GPU约1.2MB、每SM约9091B；batch16、32768context的理想流量下界约17.6707ms；online softmax对照最大绝对误差不超过1.67×10^-16。误差范围只对应本脚本双精度与有限输入，不是FP16/FP8实现的误差承诺。

故意去掉旧u和ℓ的rescaling，就能得到反例；把tile边界换成不整除长度，可检查尾块；增加outlier score检验减最大值是否必要。但全mask行、NaN/Inf和实际attention mask没有由此完整覆盖。真实GPU实现需要额外处理这些输入与同步规则。

### 15.1 按证据分流的故障表

| 现象 | 优先假设 | 要取得的证据 | 合理下一步 |
|---|---|---|---|
| HBM低、FLOPs低、kernel很短 | launch/host或工作不足 | CPU/GPU时间线、block数量 | graph/fusion、增加有效工作 |
| 长load stall、HBM没满 | 在途请求不足或依赖强 | eligible warps、load依赖、事务效率 | 独立load、vectorize、异步搬运 |
| HBM高、TensorCore低 | 低I或流量膨胀 | 实际bytes与理论最低bytes | 复用、减少中间量、量化/缓存 |
| HBM低、shared-memory压力高 | 片上瓶颈 | bank conflict、shared吞吐 | swizzle、改变tile和pipeline |
| 高occupancy仍慢 | ready不足、barrier/SFU等 | stall分项、功能单元吞吐 | 改工作划分或减少非matmul路径 |
| tile扩大后回归 | register/shared阈值或spill | 编译资源、local流量、residentblocks | 缩tile、改live range/缓冲 |
| 单kernel快、端到端不变 | 占比小或其他阶段变慢 | phase时间与Amdahl预算 | 查真正criticalpath，服务层复测 |
| 在线时延抖动 | 编译/graph shape miss、排队、长短混合 | recompile计数、队列、p99 | shape策略、准入/调度、warmup |
| 新GPU提升远低于峰值比 | 非对称硬件扩展 | 各单元roofline与指令路径 | 针对新架构重排，而非盲改blocksize |

注意“下一步”只是待验证优化假设。Vectorize可能受对齐限制，fusion可能引发spill，量化可能损质量，graph可能因动态行为回落。应每次保留可回退基线和变更记录，最后只接受在目标负载上验证有效的结果。

### 15.2 优化过程里的反馈与状态

模型权重不一定改，kernel schedule、编译cache、graph实例和memory pool却会更新。这些是服务的持久/半持久状态。只测第二次运行与第一次运行不同，可能只是编译cache变热，不能直接归因某条优化。

反馈闭环应存每个候选的源码/revision、编译参数、shape集、正确性结果、warm/cold timing和counter。若自动搜索kernel，也不能只奖励最小latency，必须先通过语义与数值约束；否则搜索可能通过省略某些mask、忽略尾块或降低精度“作弊”。这和Agent harness优化的共同点是：评价器与约束定义了什么改进可以被接受。

## 16. 自测与答案

1. **GPU切换warp能否把一次250ns HBM访问变成25ns？**  
   不能。它让其他工作利用等待时间，改善吞吐，单条访问延迟仍存在。
2. **高occupancy是不是越高越快？**  
   不是。它只是常驻warp比例，ready工作、复用、spill和功能单元可能更关键。
3. **H200 BF16 ridge为什么约206，而batch1 GEMV利用峰值不到1%？**  
   989TFLOP/s÷4.8TB/s≈206FLOP/B；GEMV约1FLOP/B，只能在满带宽时达到约4.8TFLOP/s，即0.485%。
4. **Memory-bound且HBM没满是否矛盾？**  
   不矛盾。可能受延迟、依赖、并发、事务效率或另一级memory约束；低I只描述资源边界。
5. **不同请求batch为什么主要提升权重强度，未必提升KV强度？**  
   权重可共用，KV通常各自独立，计算与KV流量同增；GQA或共享prefix另有条件性复用。
6. **4.8TB/s与250ns意味着多少在途数据？**  
   1.2MB全芯片，132SM平均约9.09KB/SM；是未完成请求量，不是额外分配缓存大小。
7. **FlashAttention不保存n×n score是否把denseattention算量变成O(n)？**  
   没有。它改变IO和中间量；精确denseattention仍有平方算术工作。
8. **Online softmax遇到更大最大值时为什么要乘a？**  
   所有旧指数贡献必须换到新基准，否则不同tile的概率分母与加权和不在同一尺度。
9. **FA3比FA2快的关键是否“更多warps”四字就够？**  
   不够。Producer/consumer分工、TMA/WGMMA异步、matmul/softmax交叠与正确barrier协议共同作用。
10. **CUDA Graph能否替代所有fusion？**  
    不能。它减少重复提交并表达依赖，通常仍有多个kernel；fusion能减少中间访存，目标不同。
11. **为什么MPK1.7×不能直接承诺线上p99提升1.7×？**  
    其报告采用离线固定请求批、prompt64/output1024等条件，不包含线上到达、队列和多种服务干扰。
12. **Attention占30%、kernel快2倍，端到端理想最多多快？**  
    约1.176倍；若其他阶段不变，这是Amdahl估算。容量与调度改变时需重新测完整系统。
13. **如何处理FA4本地文件中的B100/B200不一致？**  
    保留版本证据并明确硬件设置待澄清，只把峰值作为作者自报结果，不自行改原文后声称可复现。
14. **同一个pagedattention算法迁移TPU时保留什么？**  
    页表、逻辑块、ragged访问、在线归一化等算法内容可保留；warp、tile、搬运、barrier与代码生成必须适配。

## 17. 全部来源与建议精读顺序

| 官方reading/补充文件 | 定位 | 支持什么，不支持什么 |
|---|---|---|
| [CUDA Guide](readings/CUDA_C++_Programming_Guide.pdf) | 本地Release13.4；§5、§6.2.8.7，PDF pp.27–36、73–82 | CUDA模型、cluster与graph更新；正文legacy标记需保留，不是所有GPU通用模型 |
| [Roofline技术报告](references/Roofline_An_Insightful_Visual_Performance_Model_for_Floating-Point_Programs_and_Multicore_Architectures.pdf) | Berkeley EECS-2008-134，PDF pp.3–8 | DRAM operationalintensity、ceilings；与官网2009期刊DOI版本分开 |
| [making DL go brrr](readings/Making_Deep_Learning_go_Brrrr_From_First_Principles.html) | compute/memory/overhead | 第一性分解思路；博客示例不是LLM服务统一跑分 |
| [FA1](readings/FlashAttention_Fast_and_Memory-Efficient_Exact_Attention_with_IO-Awareness.pdf) | §3、Algorithm1、IO分析、§4 | exactattention的tile/online/recompute；block-sparse扩展另分 |
| [FA2](readings/FlashAttention-2_Faster_Attention_with_Better_Parallelism_and_Work_Partitioning.pdf) | §3–4、工作划分图 | non-matmul、block/warp划分、A100测量 |
| [FA3](readings/FlashAttention-3_Fast_and_Accurate_Attention_with_Asynchrony_and_Low-precision.pdf) | §3–4、§4.2消融 | Hopper异步与FP8；精度和kernel/模型指标分开 |
| [FA4](readings/FlashAttention-4_Algorithm_and_Kernel_Pipelining_Co-Design_for_Asymmetric_Hardware_Scaling.pdf) | 算法/pipeline章节、AppendixA.1 PDFp.20 | Blackwell不对称扩展；硬件/日期内部不一致已注明 |
| [B200 walkthrough](readings/FlashAttention-4_from_Scratch_to_Near-SOTA_in_60_Diagrams_CUDA_PTX.html) | 14个版本，固定non-causalBF16/dim128 | 优化顺序与依赖；作者工程文章，非任意shape统一结论 |
| [FlashInfer](readings/FlashInfer_Efficient_and_Customizable_Attention_Engine_for_LLM_Inference_Serving.pdf) | Figure1、§3–4；本地v2 | ragged/paged/变体与动态调度，SGLang指定后端对照 |
| [RPA](readings/Ragged_Paged_Attention_A_High-Performance_and_Flexible_LLM_Inference_Kernel_for_TPU.pdf) | §3–4、PDFp.12以后评估 | TPU7x原生实现，MBU/MFU分母与阶段分开 |
| [FLUX](readings/FLUX_Fast_Software-based_Communication_Overlap_on_GPUs_through_Kernel_Fusion.pdf) | §2–5，2024-10-25稿 | 细粒度通信融合；8卡推理/128卡训练不能混为一项 |
| [TVM](readings/TVM_An_Automated_End-to-End_Optimizing_Compiler_for_Deep_Learning.pdf) | compute/schedule、costmodel与评估 | 图/算子两级和性能可移植性，不是当前LLM排名 |
| [Mirage](readings/Mirage_A_Multi-Level_Superoptimizer_for_Tensor_Programs.pdf) | 本地v3；μGraphs、verification、§8 | 多层搜索与适用范围等价验证；operator速度不等于服务速度 |
| [MPK](readings/MPK_A_Compiler_and_Runtime_for_Mega-Kernelizing_Tensor_Programs.pdf) | SMtaskgraph、runtime、§6.2–6.3 | persistentkernel与离线模型对照，scheduler资源有成本 |
| [PyTorch2](references/PyTorch_2_Faster_Machine_Learning_Through_Dynamic_Python_Bytecode_Transformation_and_Graph_Compilation.pdf) | §3–4及evaluation，ASPLOS2024 | bytecode/guard/Inductor；180+模型几何平均不代替线上压测 |
| [inference characterization](readings/A_Systematic_Characterization_of_LLM_Inference_on_GPUs.pdf) | §3–6 | 特定模型、vLLM0.9.2、离线batch与设备对照；counter分母必须核查 |

建议先掌握第4–8节的资源和流量账，再按FA1→FA2→FA3→FA4理解瓶颈如何迁移；随后以FlashInfer/RPA检查算法怎样适应真实KV布局，最后用FLUX、编译器和persistentkernel理解跨kernel边界。每次读性能数字都先找硬件、precision、shape、基线、计时层级与失败边界，才有资格把它变成下一次优化假设。

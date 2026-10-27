# 第 10 课：LLM 服务基础 I——从一个请求到模型的计算、状态与成本

> 课程日期：2026-10-19。材料核查：2026-10-26。主讲 Juncheng Yang。本文依据 [9_llm_serving_basics_1.pdf](9_llm_serving_basics_1.pdf) 的全部 36 页组织；目录号 10、文件号 9 与讲义页脚编号不是同一套编号。下文 L p.x 一律指 **PDF 实际页序，从 1 开始**。  
> 阅读材料见 [SOURCES.md](SOURCES.md)。本文中的算式和 CPU 示例是教学推导；论文性能数字只对应各自的原始条件。没有运行真实模型、GPU 服务或论文实验。

## 0. 学这课究竟要获得什么能力

Agent 一轮工作可能调用几十次模型；模型服务不是一块只有“参数量”标签的黑盒。相同模型遇到短输入、长输入、多用户、长输出，瓶颈会落在不同资源上。长输入通常增加首 token 时间，长输出增加串行生成步数，多用户能共享一次权重读取，却各自占用不断增长的状态。理解这些关系，才能解释为什么一个“更小”的模型仍可能耗尽显存，为什么更快的 GPU 不一定改善聊天体验，以及为什么让 Agent 少说几步有时比换内核更有效。

本课的核心问题是：**给定模型结构与请求分布，哪些东西需要计算，哪些东西需要保存，哪些东西必须串行等待？** 机制链条为：文字经过分词变成长度 → 调度决定本步同时处理多少 token → Transformer 对这些 token 做投影、注意力与 FFN → 过去的 K/V 被缓存 → 下一步继续读取权重与缓存 → 输出采样和停止条件决定整条链执行多久。

学完应能自己推导参数量、KV 字节数、粗略 FLOPs 和理想资源下界；能区别 dense、MoE、GQA、MLA、线性注意力、循环深度与扩散模型实际改变的对象；能提出一个可证伪的服务优化假设，而不是只把某个架构名称当作性能答案。

### 0.1 讲义与阅读的路线图

| 讲义实际页 | 主线 | 阅读补充及本文位置 |
|---|---|---|
| L pp.1–3 | 课程安排与范围 | 本课只建立架构和服务直觉，不是完整部署指南 |
| L pp.4–10 | 请求生命周期、分词、批处理、prefill、decode、采样、流式输出 | 第 1–3 节；BPE、inference arithmetic |
| L pp.11–14 | 符号、Transformer block、RMSNorm、残差 | 第 4 节；Transformer、RMSNorm、Llama 3 |
| L pp.15–20 | Q/K/V、causal mask、多头、复杂度 | 第 5 节；Illustrated / Annotated Transformer |
| L pp.21–24 | GQA、Llama 70B 参数、KV、计算估算 | 第 6–8 节；Llama 3、inference arithmetic |
| L pp.25–26 | MoE、总参数与激活参数 | 第 9 节；Switch、Mixtral、DeepSeekMoE、DeepSeek-V3 |
| L pp.27–34 | 窗口、MLA、线性、SSM、稀疏、循环、扩散 | 第 10–12 节；recurrent depth、LLaDA、Dream |
| L pp.35–36 | 下课与选读结束页 | 第 13–16 节串起实验、实现、排障、自测 |

## 1. 一个请求的时间线：先区分等待、计算与呈现

L p.4 把请求拆成 tokenize、schedule、prefill、decode、detokenize、stream 六阶段。L p.8 又把 sampling 单独画出来，导致展示编号与总览不完全一致；它们是同一条链的不同粒度。采样发生在模型给出 logits 之后，detokenize 是把 token ID 还原为文本，stream 是把可显示文本发给客户端。

假设用户让一个检索 Agent 总结 20 页研报。模型输入并不只有用户那一句话，还包括系统说明、工具定义、检索段落、历史对话、格式要求和已有中间结果。分词后长为 n；服务端把请求排入队列；轮到它后，prefill 同时处理提示词中的位置，建立每层的 K/V；最后位置的输出分布给出第一个生成 token。后续每一步只为新位置执行一次模型前向，同时读取此前的位置状态。停止符、输出上限、用户取消、连接策略等决定何时结束。

把接收请求到第一个可见输出的时间称作 TTFT。它通常包括分词、排队、prefill、采样、传输与缓冲，不能把它直接等同于某个 prefill kernel 的执行时间。相邻输出 token 的时间差可记 ITL；平均每输出 token 的时间常记 TPOT，但是否排除首 token、怎样处理长度为 1 的回答，必须在报告中写清。一个请求输出 m 个 token，粗略可以写：

$$
T_{\mathrm{request}}\approx T_{\mathrm{queue}}+T_{\mathrm{prefill}}
+\sum_{j=2}^{m}T_{\mathrm{decode},j}+T_{\mathrm{other}}.
$$

如果首 token 已由 prefill 末尾的 logits 采样，就不应再人为多加一次“第一步 decode”。若实现把 sampling、拷贝等计入 prefill 边界，计时字段又会不同。对优化有效的做法是画实际时间线，而不是只比较名称。

流式输出改善感知延迟，但没有消除计算依赖。模型还未生成第 100 个 token 时，网络不能替它先把第 100 个 token 发出去；若代理必须先生成完整 JSON 并通过验证，流式 token 也未必能提前变成用户可用结果。Agent 的端到端体验还包括工具、检索、校验以及多轮模型依赖，因此应同时记录模型时间与整个任务时间。

### 1.1 吞吐与单请求速度不是同一件事

同一步处理 32 个请求，可能每步从 10 ms 变成 15 ms；单请求 token 间隔变差，却每秒产出更多 token。服务通常同时追求有用吞吐、TTFT 和 TPOT 约束。报告“tokens/s”至少要说明是单请求、整个副本、输入还是输出，以及是否只计成功且满足时延要求的请求。

请求长度分布尤其重要。均匀 128-token 输入的压测不能代表带长文档的 Agent；长尾输入会改变 prefill 工作量，长尾输出会让 KV 长时间不释放。相同平均长度也不保证相同时延，因为排队、峰值和调度取决于分布而非仅仅均值。

## 2. 分词：长度从何而来，为什么会影响所有后续预算

L p.5 的要点是 token 不等于词。展示的“Serving is hard”被切为四个片段只是示意，不是所有 tokenizer 都会给出同样结果。ID 也只在相应词表与版本里有意义。讲义“约 3–4 个字符一个 token”是英语直觉，不能用来承诺中文、代码、数字、URL、表格或混合语言的计费长度。

BPE 的训练不断选择频繁相邻符号对，将它们合并成新符号。以 `l o w` 和 `l o w e r` 为例，若 `l o`、`lo w` 依次很频繁，会得到 `low`，再将新词表示成已有片段。一个更大的词表可能让常见文本序列变短，同时使 embedding 与输出词表投影更大。究竟是否划算，要看实际语言分布、模型维度与训练/服务目标。

这里有一个来源差异：[BPE 论文](readings/Neural_Machine_Translation_of_Rare_Words_with_Subword_Units.pdf) §3.2 的 NMT 实现以字符与词尾符号初始化，并且不跨词合并；L p.5 讲的是现代 **byte-level BPE** 的 256-byte 起点。后者在具有完整 byte 回退等相应实现条件时能表达任意字节序列，不应把“没有未知 token”倒推成原始论文的所有字符配置也天然具有此性质。两者共享频繁对合并思想，工程边界不同。

[Llama 3](readings/The_Llama_3_Herd_of_Models.pdf) PDF p.7、Table 3 与邻近正文说明词表扩至约 128K，并报告样本英语压缩从 Llama 2 的 3.17 字符/token 到 3.94。这是指定样本的统计，不是所有语言的固定换算率。更好的分词能让固定上下文窗口装下更多原文，也会改变相同文本的注意力计算和缓存长度，因此跨模型“每千 token 速度”未必对应相同字数工作量。

### 2.1 编码、模板与特殊 token 是正确性的一部分

用户看到的文字进入模型前通常还经过 chat template。角色分隔符、工具 schema、开始/结束符、图片占位和多模态编码都可能占用 token。比较两次运行时，应固定 tokenizer revision、模板、特殊 token 行为和输入归一化。否则既不能严谨比较模型输出，也不能解释输入长度为什么改变。

流式解码还必须缓冲不完整字符。一个 token 可以对应一个 UTF-8 字节片段，收到 ID 后立即用替换字符强行输出，可能让中文或 emoji 损坏。停止字符串还可能横跨多个 token；安全取消、终止检测与 detokenize 缓冲必须配合。对用户而言是一个“停”按钮，对服务而言是释放仍占用 KV 与调度槽位的控制事件。

工程上先记录实际 token 数，再考虑压缩历史、删去重复 schema、检索更精确的片段。压缩降低成本的前提是保住任务所需证据；若摘要遗漏数字或法律限定，模型调用便宜了，业务答案却可能更差。应以任务成功率和整体成本一起比较。

## 3. 调度与两阶段计算：为什么 KV 内存参与准入

L p.6 的 continuous batching 图让已结束请求离开、新请求加入，不必等一整批最慢请求结束。图上某一步的空格不是内存真正不存在，而是逻辑上可以供其他请求使用的容量。真实引擎还要管理 KV 页、请求状态、prefill token 预算和不同阶段的资源竞争。

Prefill 的新 token 数通常很大，权重能被许多位置复用，矩阵乘更容易高效。Decode 的每个请求每步只增加一个位置，batch 1 时大量权重只服务一个 token，因此常受权重读取带宽限制。L pp.7–8 的 compute-bound / bandwidth-bound 是典型工作区间的直觉；很短 prefill、极大 decode batch、长上下文注意力、通信或 host 调度都可能改变瓶颈，下一课的 roofline 会把这个条件量化。

KV 缓存是每个活跃请求各自持有的状态。模型权重能跨请求共享，但“甲对话中第 80 个 token 的 K/V”不能直接当作“乙对话第 80 个 token”的状态。只有输入前缀、模型版本及缓存语义等条件确实一致时，前缀缓存才有复用机会；相同文本出现在不同前文之后通常不足以复用。

容量不够时可以排队、抢占、卸载或重算，每种方式都有代价。排队增 TTFT；抢占可能增加后续恢复时间；CPU 卸载要付 PCIe 或其他互连开销；重算要再做 prefill。只看 GPU 满载会忽略用户已经等了很久。准入控制应预留工作区、通信缓冲与增长空间，不能把“所有剩余字节”承诺给当前 prompt。

### 3.1 为什么输出长度也是输入侧决策

设当前上下文 n，计划最多再生成 m token。若只按 n 分配并发，后续请求一起增长便会耗尽内存。完全按 n+m 预留又可能在许多请求早停时浪费容量。分页与动态管理缓解了分配浪费，但没有让实际已存在的 K/V 免费。

采样策略影响停止分布。温度、top-k、top-p 改变候选 token，可能改变模型是否尽早输出结束符、是否重复和推理链长度。因此同一模型的两个 serving 配置若用了不同采样参数，输出 tokens/s 与总耗时不能直接当作纯系统性能差异。做性能对照应固定输入和生成预算，另做质量评测来解释预算变化。

### 3.2 从 logits 到 token：温度、截断与停止

模型输出的是词表上每个候选的实数分数 z。正温度 τ 下，概率为 `p_i=exp(z_i/τ)/Σ_j exp(z_j/τ)`。τ 小会放大最高分与其他项的差距，τ 大会让分布更平；τ=0 通常作为 API 的 greedy 特殊约定，即选 argmax，并不是把公式真的除以零。浮点相等时还需要固定 tie-breaking；greedy 也不保证答案正确。

Top-k 保留分数最高的固定 k 个候选，其他概率归零后重新归一化。Top-p 先按概率排序，保留累计概率达到阈值 p 的最短前缀，故确定性很高的分布可能只留一个，平坦分布则会保留许多候选。若两个策略一起用，执行顺序、是否保留至少一个候选与温度应用位置会影响结果，比较框架时应核对实现。讲义默认值是说明采样方式的例子，不是质量最优配置。

采样本身还有系统成本：大词表 logits 读写、排序/选择、随机数和 CPU/GPU 同步都可能显现于短步骤。很多引擎会融合操作，避免复制整份 logits 到 CPU。若服务需要 logprobs、多个候选或复杂约束解码，它的成本也不等于只取 argmax 的基准。停止 token 与 max output 限制必须在 cache 与请求状态里同步处理，否则界面停止了，GPU 仍可能继续做无效工作。

## 4. Transformer block：从 ID 到分布，各模块负责什么

L pp.12–14 采用 Llama 3 70B 为贯穿例子。符号为层数 L、模型宽度 d、query heads H、KV heads Hkv、单头维度 dk、FFN 宽度 dff、词表 V、并发 B、当前序列长 n、参数 N。本文用 b 表示每个数的字节数，避免把批大小 B 与 byte 混为一谈。不同论文把层数或长度也写 N，因此读公式前先对符号。

一个 token ID 先查 embedding，得到 d 维向量。每层注意力负责在位置之间交换信息，FFN 负责对每个位置的特征做非线性变换。最后归一化与 LM head 将隐藏向量映射到词表 logits。Softmax 是把 logits 变为分布的数学函数，具体采样还需要策略和随机数。

L p.13 的“identical blocks”应理解成结构相同；常规 Transformer 各层权重不同。第 12 层学到的投影矩阵不是自动等于第 13 层。L p.33 的 recurrent depth 才专门复用同一组块权重，这个区别直接决定总参数和测试时计算是否绑定。

### 4.1 残差为什么像一条持续更新的工作区

L p.14 的 pre-norm block 可写成：

$$
h=x+\operatorname{Attn}(\operatorname{RMSNorm}(x)),\qquad
 y=h+\operatorname{FFN}(\operatorname{RMSNorm}(h)).
$$

每个子层先观察经过归一化的输入，再向残差流加更新。可将残差流想成每个 token 的特征工作区：注意力加入从其他位置读来的信息，FFN 再重组这些信息。这个比喻帮助理解数据流，不意味着某一个维度必然对应可读的人类概念。

RMSNorm 对单个位置的 d 个分量做：

$$
\operatorname{RMSNorm}(x)_i=
\frac{x_i}{\sqrt{d^{-1}\sum_j x_j^2+\epsilon}}g_i.
$$

它没有像 LayerNorm 那样先减均值。g 是可学习增益，ε 防止分母数值不稳定。统计在特征维度内进行，不是在 batch 或不同 token 之间混合。实现常用更高精度做平方和，以避免低精度溢出；使用什么累积精度与融合内核是工程选择。

[RMSNorm 原文](readings/Root_Mean_Square_Layer_Normalization.pdf) §4–6 从去掉 re-centering 的假设出发，比较翻译等任务，报告特定模型的速度改善。它不证明所有架构换成 RMSNorm 必然更好，也不授权把已训练的 LayerNorm 权重任意替换后期待输出相同。架构、训练与 checkpoint 是配套的。

### 4.2 SwiGLU：三个矩阵与逐元素门控

L p.23 用 `3*d*dff` 计算 FFN 参数，隐含的是现代三矩阵门控 FFN，而非原始 Transformer 的两矩阵 ReLU FFN。忽略 bias 后：

$$
\operatorname{FFN}(x)=
\left[\operatorname{SiLU}(xW_g)\odot(xW_u)\right]W_d,
\qquad \operatorname{SiLU}(z)=z\sigma(z).
$$

Wg、Wu 形状 d×dff，Wd 是 dff×d。门控先决定哪些中间特征通过，再投回 d 维。它不是 token 路由器：所有中间通道的矩阵计算通常仍执行，只是结果逐元素相乘。MoE 则真的选择若干专家矩阵，计算图稀疏性不同。

[SwiGLU 论文](readings/GLU_Variants_Improve_Transformer.pdf) PDF pp.2–3 在 T5 风格 encoder-decoder、C4 span-filling 预训练与下游微调中比较门控变体。为保持参数与算量相等，把门控版 dff 从 3072 改成 2048。若自己只加第三个矩阵而保持 dff 不变，就同时加了容量与计算，不能用这个对照证明收益来自激活函数。论文 held-out log-perplexity 与下游指标是质量证据，不是 Llama 服务速度的直接测量。

## 5. 注意力逐步推导：先看一个 head，再看多头

对一层输入 X∈R^(n×d)，单头有：

$$
Q=XW_Q,\quad K=XW_K,\quad V_m=XW_V,
\quad Q,K\in\mathbb R^{n\times d_k},\quad
V_m\in\mathbb R^{n\times d_v}.
$$

这里把 value 矩阵写 Vm，避免和词表大小 V 混淆。Q 表达当前位置要读什么，K 表达每个位置怎样被匹配，Vm 是实际混合的内容。Q/K/V 都从同一个输入投影出来，但使用不同权重，因此角色不同。

打分矩阵 S=QKᵀ/√dk，Si,j 表示位置 i 查询位置 j。Causal mask 在 j>i 时加入负无穷，softmax 后这些未来位置的概率为 0。每一行沿 key 位置归一化，再乘 Vm，得到该 query 的加权内容。L pp.15–17 的图应从一行读：例如第 4 行只能取前四个位置，行和为 1；图中的颜色不是对所有层都适用的真实解释。

为什么是除 √dk，而不是 dk？在分量近似独立、零均值、方差为 1 的启发条件下，点积是 dk 项之和，方差约 dk，标准差约 √dk。缩放减少维度增大时 logits 过大、softmax 饱和的问题。真实激活不必满足这些理想假设；这是设计动机，不是对所有训练阶段的严格分布定理。[Transformer 原文](readings/Attention_Is_All_You_Need.pdf) §3.2 给出同样动机。

### 5.1 一个手算例子

设某 query 对前面三个位置的缩放分数为 `[0, ln(2), 0]`。指数是 `[1,2,1]`，权重为 `[0.25,0.5,0.25]`。若三个 value 是 `[2,0]`、`[0,4]`、`[2,2]`，输出就是 `[1,2.5]`。如果第三个位置是未来 token，mask 后只剩 `[1/3,2/3,0]`，输出为 `[2/3,8/3]`。可见 mask 不只是把某个输出分量清零，它改变整行概率的分母。

实现 softmax 时先减行最大值，防止指数溢出。全部位置都被 mask 的行需要单独定义处理；默认让负无穷减负无穷会产生 NaN。正常 causal self-attention 通常允许位置看自己，但 padding、分块与自定义 mask 组合仍可能出现空行。

### 5.2 位置不是注意力公式自动具备的能力

只给无位置信息的内容投影，注意力无法直接知道 token 的顺序。原始 Transformer 加 sinusoidal positional encoding；Llama 3 使用 RoPE。RoPE 对 Q/K 的二维分量对按位置旋转，使它们的点积带有相对位置结构。它不要求给 value 同样旋转，也不意味着增加 context 上限只需把一个整数调大。

讲义基础图省略位置编码以强调矩阵形状，真正部署必须遵守 checkpoint 的 RoPE 配置。位置偏移、缓存重用、prefix 长度与扩展策略错一位，即便 Q/K/V 形状正确也可能让长文检索失效。缓存量化错误和位置错误的表现有时相似，排障时应先用短而可手查的序列验证。

### 5.3 多头怎样改变表达，而不自动减少总算量

H 个 head 各自投影、做注意力，拼接后乘 Wo：

$$
\operatorname{MHA}(X)=\operatorname{Concat}(\mathrm{head}_1,\ldots,
\mathrm{head}_H)W_O.
$$

在 Hdk=d、dv=dk 的常见形状下，拆成多头并没有把总宽度缩小：64×128=8192。它让不同子空间学习不同匹配模式。L p.20 中“看上一个词”“看第一个词”等是教学示意，不是保证每个 head 有固定语言学职责。也不能据此把“没有清晰可解释模式”的 head 任意删除而保证质量。

## 6. KV cache：缓存的是什么，为什么不缓存所有 Q

当前生成位置 t 的 Q 只用于计算当前位置的输出；下一位置有自己的 Q，不需要重用历史 Q。历史 K/V 则是每个新 query 都会读到的固定内容，所以保存它们避免重复投影及重跑历史层。缓存是激活状态，不是模型参数，不经过跨请求共同训练更新。

对于标准 causal decoder、固定权重、正确位置编号且关闭 dropout，已知前缀位置不会受未来 token 影响，因此历史 K/V 可以原样复用。在每一步只处理新 token 与“把完整前缀再跑一遍”之间，应得到数值容差内相同的最后位置输出。混合精度、算子顺序会造成微小差别；错误的 mask、位置或缓存写入会产生结构性差别。

每 token 的 KV 字节数为：

$$
C_{\mathrm{KV}}=2LH_{kv}d_kb.
$$

第一个 2 是 K 和 V 两份；L 是每一层都持有自己的缓存；Hkv 而不是 H 决定实际存多少 K/V head；b 是精度字节数。总缓存约为 Σr nr CKV，而不是在 ragged batch 下强行假设所有序列等长。分页还有元数据、末页浪费与对齐，量化则有 scale / zero-point 等额外开销。

### 6.1 MHA、GQA、MQA 分别共享什么

MHA 的每个 query head 有独立的 K/V head；MQA 的所有 query heads 共享一个 K/V head；GQA 在中间，每一组 query heads 共用一份 K/V。注意共享的是 K/V 投影和存储，query 仍然不同，因此各 query head 的注意力分数一般不同。

L p.21 的玩具图从 8 query / 8 KV 变成 8 / 2 和 8 / 1，缓存分别为原来的 1、1/4、1/8。Llama 3 70B 是 64 query / 8 KV，因此相对于同宽 MHA，缓存缩小 8 倍。它没有让 query heads 也减少到 8，更没有把所有注意力 FLOPs 都减少 8 倍。

训练时学到的共享结构不能通过服务端少存几份 cache 免费获得。把一个 MHA 模型临时平均 K/V head，会改变模型函数。GQA 的质量与训练过程需要具体实验评估；本课用 Llama 配置做成本计算，不单独证明 GQA 的能力取舍。

### 6.2 确切复算 Llama 3 70B 的状态

按 L p.12 与 p.21 的数值，L=80、Hkv=8、dk=128、b=2：

$$
C_{\mathrm{KV}}=2\times80\times8\times128\times2
=327{,}680\ \mathrm{bytes}=320\ \mathrm{KiB}.
$$

**讲义写“320 KB”采用了口语近似；精确单位是 320 KiB。** 80,000-token 一个请求缓存约 26.2144 GB，即 24.4141 GiB。64 个同长度请求约 1,677.72 GB 仅用于 KV。这里长度是 80,000，而不是 80×1024；单位的每次转换都要保持一致。

模型权重用讲义近似 70.6B×2=141.2 GB，则一个请求的权重加 KV 为 167.4144 GB，64 请求为 1,818.9216 GB。L p.24 的 167 / 1779 GB 是粗略展示，后者把每 token 当成 320,000 bytes 近似；它与精确 327,680-byte 公式并不完全一致。本文保留讲义原数作为来源说明，容量规划使用精确公式，并再加运行时余量。

## 7. 参数量与 FLOPs：把“70B”拆开

L pp.22–23 给出 d=8192、dff=28672、H=64、Hkv=8、dk=128、L=80、词表 128256。忽略 bias 与少量 norm 参数，attention 每层包括 Q 与 O 两个 d×d 矩阵，以及 K/V 两个 d×(Hkv dk) 矩阵：

$$
N_{\mathrm{attn}}=2dH d_k+2dH_{kv}d_k.
$$

FFN 三矩阵参数为 3ddff。输入 embedding 与独立 LM head 为 2Vd。代入得到每层 attention 约 151M、FFN 约 705M，总计约 70.55B，再加小项与模型标称取整便是约 70.6B。若模型绑定 embedding 与 head 权重，就只能算一份 Vd；不能把这个参数账本机械套到所有 checkpoint。

一枚权重在矩阵乘中通常对应一次乘和一次加，因此粗略线性层算量为每 token 2N FLOPs。这个式子把 embedding 查表等也粗略包含在参数总数内，忽略相对较小的 norm、激活、softmax，并且不包括注意力跨 token 计算。它是预算式，不是精确指令数。

### 7.1 为什么 prefill 有平方项，decode 单步有线性项

完整 attention 的 QKᵀ 和 AV，两次矩阵乘合计每层约 4n²d FLOPs；这是对完整 n×n 网格的计算估算。Causal 三角区域只需大约一半有效元素，利用三角掩码跳过工作后，常用近似是 2n²d。实际边界 tile、实现和硬件决定节省是否完整实现。

Prefill 的粗略总算量因此可以写：

$$
F_{\mathrm{prefill}}\approx B(2Nn+2Ldn^2)
$$

采用的是 causal 有效工作约定。若用 4Ldn²，也能作为未跳过上三角的估算，但必须说明约定，不能一边引用完整矩阵算量、一边声称已经包含因果节省。

生成时对当前单个 query，读取 n 个历史 key/value，attention 约 4Lnd FLOPs，外加线性层约 2N。因而 **单步** 随当前上下文长度线性增长；若从头累计生成很长的输出，所有步骤的上下文越来越长，累计注意力仍可能呈平方增长。缓存消除的是历史激活的重复计算，不是让历史长度对成本永远没有影响。

### 7.2 讲义的 690 GB 应如何理解

L p.18 计算 8192²×64×80×2 bytes≈690 GB，精确十进制约 687.2 GB。这个数把 **所有层、所有 head 的完整分数矩阵同时保留**。它用于展示潜在的平方存储规模，不能当作标准逐层推理必然需要的 attention 峰值。

常规推理层间可释放临时分数矩阵，单层同样形状约 8.59 GB；是否保存 score、softmax、dropout mask、反向图取决于实现和训练/推理模式。FlashAttention 不把完整分数矩阵写到 HBM，用分块与在线归一化减少 IO 与临时内存，但保持 softmax attention 的数学结果，不把精确 dense attention 的算术复杂度直接降为线性。下一课会具体推导在线 softmax。

## 8. 从算量变成时间：下界能回答什么

L p.24 以两张 H200、BF16 dense 峰值合计 1,978 TFLOP/s、9.6 TB/s、容量 282 GB 估算。将 N=70.6B、n=80,000 代入上一节式子，prefill 理想计算下界约 9.95 s。它假设两卡完美分工、始终达到峰值、没有通信、调度、采样或非矩阵操作损耗。这不是用户实际会看到的 TTFT。

64 个 80K 请求的算量在同一硬件上约放大 64 倍，理想总处理时间约 637 s；但它们所需 KV 已超出两卡容量，不能把这个表格当作一个现实中可直接运行的 batch。若把请求分批执行，总耗时与每请求等待又会由调度决定。

Decode 可以先用读取下界做估算：

$$
T_{\mathrm{step}}\gtrsim
\max\left(\frac{F_{\mathrm{step}}}{P},
\frac{W+\sum_r n_r C_{\mathrm{KV}}}{\mathrm{BW}}\right).
$$

W 为本步实际需要从相应存储层读入的权重字节，P 是相应精度的有效计算能力，BW 是对应层级带宽。缓存、GQA 的组内复用、模型切分和融合会改变真实流量；跨卡还要加不可隐藏通信下界。把所有项压成一个 max 只是高度理想的重叠模型，不能假设串行独立阶段永远完全重叠。

### 8.1 研究者的算术文章怎样正确使用

[inference arithmetic](readings/Transformer_Inference_Arithmetic.html) 以 2022 年硬件、dense MHA 和特定 tensor parallel 假设构建直觉。文中示例里容量公式存在明显的量级排版问题，诸如 52B 参数应为 52×10^9，而不是把 B 误写成 10^12。学习时重算单位，不能因来源有公式就照抄。

文章提出小 batch 下可能用重算换缓存等直觉，不能直接转成现代服务的通用建议。长前缀、现有优化内核、GQA、真实 KV 访问和请求到达会改变取舍。应测量“重算整个历史”和“读取历史 K/V”的真实成本，并把峰值内存、吞吐和单请求延迟一起记录。

本课下界主要有两个用途：先排除不可能的容量承诺，再发现明显低于理论资源利用率的工作区间。实测接近下界，可能需要改变模型、精度或资源；远高于下界，则继续查小 kernel、通信、访存、host gap、队列和错误的计时边界。

## 9. MoE：少算若干专家，不等于只存激活参数

L p.25 把 dense FFN 换成 router 与专家集合。对位置向量 x，router 算 logits，只保留 top-k 专家并形成权重：

$$
y=\sum_{e\in\operatorname{TopK}(r(x))}g_e(x)E_e(x).
$$

每个专家常是独立 SwiGLU FFN；注意力与残差仍在。这个“专家”是模型内部参数模块，不是能读邮件或调用工具的 Agent。router 的选择通常按 token、按层发生，也不保证专家天然对应某个可命名学科。

把参数分成 Nshared 与 E 个专家每个 Ne，dense 之外的总参数约 Nshared+E Ne，而每 token 激活约 Nshared+k Ne。因此小 k 能降低每 token FLOPs，却所有专家通常仍要驻留在整个服务集群，或者付卸载/读取代价。单个请求可能只用部分专家，下一请求可能选择另外的专家。

### 9.1 四篇 MoE 阅读各补哪一环

[Switch Transformer](readings/Switch_Transformers_Scaling_to_Trillion_Parameter_Models_with_Simple_and_Efficient_Sparsity.pdf) §2 使用 top-1 路由降低复杂度，讨论 capacity factor、路由负载不均和训练稳定性。它是 T5 风格、TPU 等条件下的训练研究，论文“7×+ pre-training speedup”是达到给定训练质量的特定对照，不是任意 decode 都快 7 倍。

[Mixtral](readings/Mixtral_of_Experts.pdf) PDF pp.2–3 的 Figure 1、Table 1、§2.1 展示每层 8 选 2，并明确不同 token 分给不同专家导致 grouped/sparse matmul 与负载均衡问题。论文使用自己统一重跑的 Llama 对照，通用、数学、代码、多语言任务均有具体 shot 和评测设置。其“8×7B”不等于八份完整 7B Transformer，因为 attention 等部分共享。

[DeepSeekMoE](readings/DeepSeekMoE_Towards_Ultimate_Expert_Specialization_in_Mixture-of-Experts_Language_Models.pdf) §2–4 将专家切细，并隔离始终启用的 shared experts。更细切分在保持激活计算近似不变时允许更丰富组合；共享专家承载共性，减少各 routed expert 重复学相同内容。论文关于知识混合与冗余是设计动机，实验通过小规模对照与消融支持，不能把“专家一定完全独立”当作已经证明。

[DeepSeek-V3](readings/DeepSeek-V3_Technical_Report.pdf) §2 将 MLA、DeepSeekMoE、负载平衡与多 token 预测组合。其 671B 总参数、约 37B 激活参数说明算量与存量确实分离；但这不是单独 MoE 一个因素的消融。质量还受到数据、训练、后训练和架构其他部分影响。

### 9.2 服务层必须补上的三个成本

第一是专家之间的通信。Expert parallel 把专家分到不同 GPU，token 要 dispatch 到对应设备，再 combine 回来，存在 all-to-all 通信与同步。第二是小矩阵效率：某个专家若只接到一两个 token，理论 FLOPs 很少，硬件利用率也可能很差。第三是负载长尾：最忙的专家决定该步结束时间，平均负载很好不代表 p99 很好。

L p.26 用 2×active params 估 GFLOPs/token，并对照 BF16 总权重。这是架构预算图，不能只凭“Mixtral 约 1/5 FLOPs”承诺同质量、同硬件、同 batch 下 5 倍端到端加速。尤其 dense 与 MoE 来自不同训练过程，“same quality”只应理解为论文指定评测上的相近水平。

选择 MoE 时先问集群是否容得下总权重、互连是否足够、请求量是否能给每个专家形成有效 batch、当前框架是否支持该路由形状。低并发单机可以优先试较小 dense 模型；大吞吐场景才可能把 MoE 的算量优势转成经济收益。这个选型是工程推导，需要本地数据验证。

## 10. 长上下文架构：读哪些历史、存什么历史是两件事

L pp.28–32 连续展示多种路径。共同优化对象是“每个新 token 从过去获得信息的方式”，但它们分别改访问范围、存储表示或状态更新，不能用一个“线性复杂度”标签合并。

### 10.1 Sliding window：只允许看最近 w 个位置

若某层完全采用局部窗口，旧于 w 的 K/V 不再会被该层未来位置读取，可以逐出，从而单层状态约 O(w) 而不是 O(n)。但局部层堆叠能间接传播远程信息，不等于保留任意远处原文的精确随机访问能力。若模型同时含全局层，这些层仍需保存长历史。

L p.28 的 Gemma 3 是五个局部层配一个全局层的示意。简单估算每六层缓存比例为 `(5w+n)/(6n)`。n≫w 时接近 1/6；若 n 不比 w 大，就不能声称节省 6 倍。Mistral 与 Gemma 各版本窗口与层模式不同，讲义列举是架构案例，服务引擎也必须真的启用匹配的逐出策略才会得到容量收益。

### 10.2 MLA：缓存压缩潜变量，不是删去历史 token

L p.29 的图从隐藏向量压成 c，再还原 K/V。DeepSeek-V3 §2.1.1、Figure 2 给出更准确的结构：缓存联合 KV latent，同时保留 decoupled RoPE key 等位置相关部分。不能说“所有模型只缓存一个 c，绝无额外状态”。

忽略位置分支，若 K=Wuk c，则 qᵀK=qᵀWuk c=(Wukᵀq)ᵀc，可以把 key 上投影吸收到 query 侧；value 上投影也可移到加权求和之后。由此 decode 不必为每个历史 token 显式重建并保存完整所有 head K/V。讲义的“重建细节”应理解为数学上可恢复相关表示，优化实现会通过矩阵吸收避免大规模物化。

MLA 改变每历史 token 存多少 bytes，仍可能读完整历史。讲义提到 DeepSeek-V2 相对 DeepSeek 67B 的 KV/吞吐数字，原始比较不等于固定其他条件的纯 MLA 消融；本课不把它外推到任意模型。使用 MLA 还需要支持其 absorb / non-absorb 路径的内核，不能把普通 GQA cache layout 原样套上。

### 10.3 Linear attention：把历史压成固定大小状态

忽略归一化的一种教学形式是：

$$
S_t=S_{t-1}+k_tv_t^\top,\quad o_t=q_t^\top S_t.
$$

这里约定 k 为 dk 维列向量、v 为 dv 维列向量，因此 S 是 dk×dv。若采用相反方向存储，公式也应相应转置。固定状态累积了历史统计，下一步无需读取每个 token 的独立 K/V。标准带核特征与归一化的 linear attention 还需要归一化状态；上述裸式不等于 softmax attention 的精确替代。

L p.30 的 Gated DeltaNet 不是简单把“累加”前面乘一个 gate 就讲完。它加入衰减与基于当前 key 的预测误差修正，近似可以把更新理解为“先遗忘，再写入当前 value 与旧状态预测之差”。这种覆盖能力缓解仅累加的干扰，但仍存在固定状态容量、训练适配与信息遗忘的取舍。讲义 p.31 并列的门控线性式是概念比较，不应误称完整 DeltaNet 更新公式。

混合架构只让部分层持有固定状态，global attention 层仍持有 KV。L p.30 的 3:1 模式意味着四分之三层的状态不随上下文增长，不代表整个模型总内存恒定。固定状态还要按 batch 分配，并在分叉、回滚、speculative decoding 等场景处理状态复制。

### 10.4 State-space models：递推状态与硬件扫描

L p.31 写 `h_t=Abar_t h_(t-1)+Bbar_t x_t`，突出 selective 状态转移会随输入改变。一个小向量递推能保留历史摘要，decode 期间空间不随 n 增长；prefill 则可利用 scan 或结构化矩阵计算获得并行性。Mamba 与 Mamba-2 的精确离散化和结构不同，本课不把这条简写公式当作完整实现。

固定状态并不意味着无限长文无损记忆。对于“找到第 3 页一串随机合同编号”的精确检索，显式保留 token 与固定容量压缩的能力边界不同。适合流式处理与大上下文的架构，需要在目标任务上检查选择性回忆、复制、顺序变化与长度外推，而不是只比较显存曲线。

### 10.5 Sparse attention：少读并不自动少存

L p.32 的 DeepSeek-V3.2 稀疏案例先用 indexer 打分，选择 top-k 历史位置，再做主 attention。主注意力只读所选项，但为了将来选择任意位置，历史状态通常仍保留。Indexer 也有打分、top-k、读索引和存储成本，所以“每 token 总成本严格封顶 2048”并不成立；封顶的是图中主 attention 的选中历史数量。

因此三种方案应分开问：窗口限制哪些位置可能被访问；MLA 改每个位置的表示字节数；稀疏检索限制本次实际访问哪些位置。它们可以组合，但不能把一个方案的缓存下降当成另一个方案已经获得的收益。讲义仅列出架构趋势；本地 Readings 没有对应每个趋势的完整原始论文，因此本文对未单独归档的模型只解释讲义机制，不补造实验结论。

## 11. 测试时计算的另一维：循环深度与多 token 预测

L p.33 的 recurrent depth 复用块 R。令 e=P(x)，s0 为初始 latent，再反复计算 si=R(e,s(i-1))，最后用 C(sr) 输出分布。输入 e 在每轮重新注入，使状态更新持续受当前输入约束，而不只是任意自由迭代。

[recurrent depth 论文](readings/Scaling_up_Test-Time_Compute_with_Latent_Reasoning_A_Recurrent_Depth_Approach.pdf) §3、Figure 2 的模型把 prelude、recurrent block、coda 分开；大型实验中是 2、4、2 层，r=32 时展开深度是 2+4×32+2=132，但物理独立权重只有 8 层。训练抽取不同迭代次数，并采用截断反向传播，测试时加循环不是把普通 Transformer 随便多跑几次。

论文 3.5B、800B-token 的 proof-of-concept 显示部分推理任务随着迭代数上升改善，而不同任务的收益饱和点不同。它不保证任意增加 r 都改善，也不等同“3.5B 获得任意 50B 模型能力”。Materialized parameters 是展开计算的比较标尺，不是新增驻留权重。

服务权衡是：权重小，但串行循环增加延迟与算量；若不同请求选择不同 r，还产生调度与负载差异。重复 depth 的 KV 在不同循环位置怎样维护，必须遵照模型实现，不能因为“复用同一权重”就认为所有循环共享同一份 K/V 状态且输出严格不变。

多 token 预测则改变训练目标或预测头。DeepSeek-V3 §2.2 顺序预测额外未来 token，用共享/连接结构提供训练信号；推理中辅助模块可以丢弃，也可作为 speculative decoding 的 draft。多预测几个 token 不表示主模型能无校验地把它们全部直接提交。接受率、验证开销和输出分布保持由具体解码算法决定，本课只指出架构接口，后续 speculative decoding 课再深入。

## 12. 扩散语言模型：并行填充为何仍要反复前向

L p.34 用被 mask 的回答序列展示逐步填充。自回归分解是 `p(x)=Πt p(xt|x<t)`；masked diffusion 从被破坏的整段文本出发，多次预测缺失位置。每次前向可同时给许多位置的分布，但这些位置对彼此的约束要靠多轮 refinement 建立。

[LLaDA](readings/Large_Language_Diffusion_Models.pdf) PDF pp.3–5、§2 令 t∈(0,1) 是 mask 比例，独立将 token 替换成 M，并用只在 masked 位置计算的交叉熵训练：

$$
\mathcal L(\theta)=
-\mathbb E_{t,x_0,x_t}\left[\frac1t\sum_i
\mathbf1[x_t^i=M]\log p_\theta(x_0^i\mid x_t)\right].
$$

t 大时输入信息少；t 小时仍需学会完成少量缺口。`1/t` 是该目标的权重，不应把它理解成解码温度。SFT 中提示词保持已知，主要对 response 做掩码。推理从全 mask 的回答开始，预测后按策略保留或重新 mask 某些位置，直至完成。

LLaDA 8B 原文报告从零训练、2.3T token、后续 SFT 与多类 benchmark。它与 Llama 3 8B 在若干评测上竞争是可行性证据；数据、训练规模、解码步数与评测协议不同，不能读成同预算下扩散已全面替代自回归。论文也用自建 ARM、相同训练数据与不同规模进行更受控的 scaling 对照，应与公开模型横向比较区分。

[Dream 7B](readings/Dream_7B_Diffusion_Large_Language_Models.pdf) §3–5 用现成 AR 模型初始化，结合 context-adaptive token-level noise rescheduling。这个路径与 LLaDA 从零训练不同：能力来源、训练成本与归因不能合并。Dream 本地文件封面日期与 arXiv 提交日期不同，引用时采用本地 PDF 的 arXiv:2508.15487v1 标识，不能只凭封面 April 日期推断归档版本。

### 12.1 为什么“少几步”不等于免费更快

自回归输出 m token 通常要约 m 个序列依赖步骤，但缓存只对新位置做投影。扩散若用 s 次全序列前向，每次可能对整个候选回答重算双向表示；其大矩阵有更高并行性，也可能做更多总 FLOPs。哪个快取决于长度、s、内核、硬件和质量容忍度，而非只比较“m vs s”。

少轮去噪可以提高速度，却可能损害推理、格式一致性与细节。输出尚可被后续修订，也让流式展示和稳定提交边界不同于 AR。Bidirectional attention 下已生成位置会受后续修改影响，标准 AR KV cache 不能原封不动沿用。若使用块式扩散、近似缓存或专门服务算法，需要单独检查其误差与成本。

在 Agent 中，工具调用 JSON 一旦执行就有外部副作用。扩散过程中一个半完成、未来还会修改的字段不能当作已承诺工具调用执行。因此评估除 token throughput 外，还应看“首次完整可验证动作时间”和整体任务成功率。

## 13. 把架构选型还原成资源与任务问题

| 主要约束 | 首先核查 | 可能候选 | 必须同时检查的代价 |
|---|---|---|---|
| 权重装不下 | 总参数、精度、切分后余量 | 小 dense、权重量化、模型并行 | 质量、通信、量化支持 |
| 长上下文 KV 装不下 | Hkv、实际长度、并发、缓存精度 | GQA/MLA 模型、局部/混合状态、KV 量化 | 训练兼容、检索质量、内核支持 |
| batch 1 decode 慢 | 权重/缓存实际读取、host gaps | batching、较小激活参数、减少输出 | 单请求时延、MoE 通信、任务质量 |
| 长 prompt TTFT 高 | prefill FLOPs、排队、prefix 命中 | 精确检索、prefix cache、prefill 优化 | 缓存失效、证据遗漏、decode 干扰 |
| 长输出导致任务慢 | 串行步数与停止分布 | 更短输出、speculation、研究新生成范式 | 接受率、质量、动作提交时机 |
| 精确长文回忆差 | 架构状态与训练长度 | 保留全局注意力、改检索 | 缓存和 IO 上升 |

这张表是基于机制的工程建议，不是来源论文的统一排行。尤其“更省 KV”的两个模型可能质量差异很大；“active params 更少”的模型可能总内存更大。生产决策应在固定任务集、服务预算和硬件条件下，画质量、时延、吞吐、成本的 Pareto 边界。

以研报 Agent 为例，先保留相同检索与答案评测，比较三种改变：删重复模板、缩检索到最相关段落、换 GQA 模型。前两个改变主要缩 n；第三个改变 CKV 并且换了整个模型能力。实验分开做，才知道节省来自上下文、架构还是能力退化。不要一次同时改检索、模型、采样和并发后，只用总耗时给某一个因素归功。

## 14. 最小可运行检查：用 CPU 验证账本和 cache 语义

本目录 [examples/inference_basics.py](examples/inference_basics.py) 只使用 Python 标准库，包含两部分：第一部分按本课公式复算 Llama 70B 参数、KV、显存与理想 prefill 时间；第二部分对 6 个四维 token，用固定随机投影做单头 causal attention，逐步缓存 K/V，再与每次重新投影完整前缀比较最后位置输出。

运行方式：

```bash
python3 examples/inference_basics.py
```

[实际运行记录](examples/RUN.json) 保存了本次结果：去除 norm 的参数约 70.552B，KV 为 327680 bytes/token，一个 80K 请求的权重加 KV 为 167.4144 GB，64 个为 1818.9216 GB，理想 prefill 为约 9.9518 s，单头 cache 对照误差为 0。误差为 0 是这个纯 Python、相同计算顺序例子的结果，不是对真实 BF16 内核逐 bit 一致的保证。

它没有 embedding、RoPE、多头、多层、真正 tokenizer、采样或服务调度，因此不能证明 Llama 实现正确，更不能用 CPU 运行时间验证 GPU 速度。它验证的是两个具体命题：公式的单位是否自洽，以及 causal 前缀不受未来影响时缓存 K/V 的语义是否成立。

可以自行改一个反例：把旧 K 的位置编号错移一步，或在完整前缀注意力中取消 causal mask，再比较中间位置。若测试还声称相同，就说明比较对象选错了。再将 Hkv 改成 64，观察 KV 放大 8 倍但 FFN 参数不变；这能直观看到“少 KV head”与“整个模型缩小”之间的区别。

## 15. 设计性能实验与排障：先确定谁变了

一个有用的实验最少固定：模型及 revision、tokenizer/模板、精度、内核后端、GPU/互连、输入/输出分布、并发/到达率、采样、prefix 命中和是否 warm-up。记录 OOM、拒绝、超时与取消，而不是从吞吐分母里悄悄删去失败请求。单测固定 batch 是 kernel/模型层实验；在线到达压测还包含排队，两者都需要，但回答的问题不同。

| 现象 | 可验证假设 | 下一步证据 | 常见误判 |
|---|---|---|---|
| prompt 变长后首 token 激增 | 注意力平方项、prefill 队列或缓存 miss | 按 n 分桶的 kernel/queue 时间 | 一律归为网络慢 |
| 输出越久越慢 | KV 读流量随上下文增长 | 每步 n、attention 时间、HBM 流量 | 认为缓存使长文完全免费 |
| 加并发吞吐高但体验差 | batch 改善复用但步长/排队变长 | p50/p95 TTFT、ITL、到达率 | 只报总 tokens/s |
| 小模型仍 OOM | KV/工作区而非权重主导 | 内存分项、活跃总 token | 只按参数量算显存 |
| MoE FLOPs 少却不快 | 小专家矩阵、all-to-all 或负载偏斜 | 专家 token 直方图、通信时间线 | 假定 active ratio=加速倍数 |
| cache 后答案改变 | 位置、mask、写入或批重排错误 | 小序列逐层/逐步数值比较 | 先怪采样随机性 |
| 局部 attention 没省内存 | 服务还在保存不能再访问的旧页 | 每层保留长度、缓存管理策略 | 只读 config 不查实际分配 |

对模型质量，至少有固定 seed / greedy 的确定性小集，以及真实业务长度和语言的任务集。系统优化可能改变浮点归约顺序，通常允许数值容差；但函数近似、量化、删上下文、换架构则需要重新做任务质量评估。不能因为 JSON 仍能解析，就认为研报中的数字、引用和结论都正确。

### 15.1 成本、反馈与持久状态

部署这类服务时，模型参数通常是固定持久状态；请求 KV 是短期状态；prefix cache 可跨请求存活但有失效条件；Agent memory 是另一个应用层持久状态。它们的生命周期、租户隔离与正确性条件不同。不能因为模型 checkpoint 没变，就认为缓存和记忆从来无需清理。

反馈也分层：硬件计数器告诉你资源使用；服务指标告诉你排队和吞吐；用户任务评分告诉你有没有正确完成任务。只优化其中一层容易产生反效果。例子是强行降低 max output：TPOT 和总成本看似改善，却因工具参数被截断让 Agent 重试更多次，最终任务更贵。

最终成本可以按 GPU 时间、API 费用和工程维护计，也应加失败重试。对于 MoE、MLA 或扩散等新路径，内核与框架成熟度是现实成本；一张漂亮的理论表不足以说明团队应该立刻迁移。先做能隔离因素的小试验，再逐步扩大真实流量。

## 16. 自测与参考答案

1. **80K prompt 做完 prefill 后，生成第一个 token 是否还必需再跑一次整个模型？**  
   不必。标准路径可用最后 prompt 位置的 logits 采样第一个输出。后续再把新 token 输入模型；具体计时边界依实现。
2. **为什么 KV 有一个 2，却没有历史 Q？**  
   2 对应 K 和 V。未来位置会读取历史 K/V，而历史 Q 只用于其自己的输出，不再需要。
3. **64 query / 8 KV heads 的模型是否 attention FLOPs 也自动减少 8 倍？**  
   不是。64 个 query heads 仍产生不同注意力输出；主要直接节省 K/V 投影、缓存与可复用流量，FFN 也不因此缩小。
4. **327680 bytes 为什么不是精确 320 KB？**  
   320×1024=327680，是 320 KiB；320 KB 按十进制是 320000。容量规划必须固定单位。
5. **讲义 690 GB 能否证明 8K Llama 推理必然需要近 700 GB 临时 attention 显存？**  
   不能。它把全部层的完整 score 同时保留。逐层推理可释放临时量，FlashAttention 更避免物化完整 score。
6. **把 70B 换成 37B active 的 MoE，显存一定减少吗？**  
   不一定。必须看总参数、KV 与运行时；DeepSeek-V3 的总参数远大于 37B。
7. **Sparse attention 只读 top-2048，是否可以只存最后 2048 个历史 token？**  
   一般不行。选择可能指向任意更旧位置；读多少与保留多少是独立问题，indexer 也有开销。
8. **为什么 linear attention 的固定状态不等于无限精确记忆？**  
   有限维状态压缩历史，可能产生干扰和遗忘；它改变函数族与信息访问方式，需做具体回忆任务评测。
9. **循环块加倍迭代为什么权重不变、延迟却可能增大？**  
   复用参数仍需按依赖顺序再执行计算；额外深度消耗算力与串行时间，且需要模型被训练为可迭代。
10. **扩散一次预测许多 token，为何未必比 AR 更便宜？**  
    每轮可能重算全候选序列，轮数、质量、缓存与输出长度共同决定实际成本，不能只比较轮次数。
11. **Prefill 一定 compute-bound、decode 一定 HBM-bound 吗？**  
    不是。它们是典型区间。小形状、通信、host、长上下文和大 batch 都可能改变约束，应测资源与时间线。
12. **给长上下文服务扩容前，至少应有哪三张账本？**  
    权重与持久状态容量账、prefill/decode FLOPs 与流量账、请求分布和 SLO 账；还要在实际部署中加工作区、碎片、通信和失败余量。

## 17. 阅读资料、版本与结论边界索引

以下保留官网全部 15 项 Readings。链接均指本课原始归档；网页解释用于直觉，论文承担方法与实验归因。原始 Transformer 是 encoder-decoder、post-norm、ReLU 等配置，不能把本文 Llama 风格 block 误称它的原样实现。讲义高级架构所列但本地未逐篇归档的趋势，本文只在讲义范围内解释，不补报未经核实的性能。

| 材料 | 精读定位 | 本文用途与边界 |
|---|---|---|
| [BPE](readings/Neural_Machine_Translation_of_Rare_Words_with_Subword_Units.pdf) | §3.2、Algorithm 1、§4，PDF pp.3–5；本地 v5 | 原始字符 BPE 与词表/长度权衡；原实验为 WMT NMT，不是现代 LLM byte tokenizer benchmark |
| [Transformer](readings/Attention_Is_All_You_Need.pdf) | §3、Figure 1–2、§4–6 | attention、mask、多头、位置、复杂度；WMT 实验不能作为 Llama serving 测量 |
| [Illustrated Transformer](readings/The_Illustrated_Transformer.html) | self-attention、multi-headed attention 图解 | 辅助理解数据流；示意头模式不是因果解释证明 |
| [Annotated Transformer](readings/The_Annotated_Transformer.html) | attention / MultiHeadedAttention / masks / positional encoding | 原始架构代码路径；训练教学代码不等于现代服务引擎 |
| [RMSNorm](readings/Root_Mean_Square_Layer_Normalization.pdf) | §4–6、Table 1 | 去均值与缩放差别、跨任务对照；不把速度范围外推到本课所有模型 |
| [SwiGLU](readings/GLU_Variants_Improve_Transformer.pdf) | PDF pp.1–3、Eq.6、Table 1 | 三矩阵 FFN、等参数/等算量对照 |
| [Llama 3](readings/The_Llama_3_Herd_of_Models.pdf) | §3.2、Table 3，PDF pp.6–8 | 配置、词表、RoPE、GQA；具体精确词表值结合讲义配置 |
| [inference arithmetic](readings/Transformer_Inference_Arithmetic.html) | KV / capacity / model parallelism / latency | 2022 年预算思维；硬件与若干排版量级须重算 |
| [Switch Transformer](readings/Switch_Transformers_Scaling_to_Trillion_Parameter_Models_with_Simple_and_Efficient_Sparsity.pdf) | §2、路由与 capacity、实验 | top-1、负载平衡、训练成本；不冒充 decode 加速 |
| [Mixtral](readings/Mixtral_of_Experts.pdf) | §2–3、Figure 1、Table 1 | 8 选 2、总/激活参数、同管线模型对照 |
| [DeepSeekMoE](readings/DeepSeekMoE_Towards_Ultimate_Expert_Specialization_in_Mixture-of-Experts_Language_Models.pdf) | §2–4、细粒度与共享专家消融 | 专家组合与冗余；同语料 dense 比较优于跨来源直接归因 |
| [DeepSeek-V3](readings/DeepSeek-V3_Technical_Report.pdf) | §2.1–2.2、Figure 2、§3 | MLA/MoE/MTP 组合；训练成本不含先前研发与消融，不能当作部署成本 |
| [recurrent depth](readings/Scaling_up_Test-Time_Compute_with_Latent_Reasoning_A_Recurrent_Depth_Approach.pdf) | §3–5、Figure 1–3 | recurrent 权重共享、随机深度训练与测试计算；任务收益有差异 |
| [LLaDA](readings/Large_Language_Diffusion_Models.pdf) | PDF pp.3–6、§2–3；本地 v3 | masked diffusion、目标、从零训练与受控 ARM 对照 |
| [Dream 7B](readings/Dream_7B_Diffusion_Large_Language_Models.pdf) | §3–5；本地 arXiv v1 | AR 初始化、噪声日程、质量/步数；与 LLaDA 训练路径分开 |

复习顺序建议是：先用第 1–8 节讲清一个普通 GQA decoder，再比较 MoE 改了哪个 FFN、MLA 改了哪个状态、稀疏/窗口改了哪个访问范围，最后理解循环和扩散为何改变测试时计算。能够把这些变化分别落到公式、状态生命周期和实验条件上，才算真正获得了服务系统设计的基础。

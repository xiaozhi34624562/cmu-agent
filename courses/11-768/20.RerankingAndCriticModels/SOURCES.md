# Search 1: Reranking and Critic Models

- 课程：CMU 11-768；官方条目标识 CMU-12b。
- 官网日期：2026-11-12；PDF 讲者：Daniel Fried。
- 官网课表题目：**Search 1: Reranking and Critic Models**；PDF 封面题目：**Search over Trajectories**。
- 材料同步日期：2026-11-13（Asia/Shanghai）。
- [当前官方课表](https://www.cmu-agents.com/#/schedule) · [本次课表原件](../../syllabus-snapshots/2026-11-13/cmu/schedule.json) · [完整本地课表](../COURSE_SCHEDULE.md)。

## 主讲义与中文讲解状态

- [Search over Trajectories · Lecture 20 · 31 页](lecture-20-search-basics.pdf)；原文件名及原始字节保留。
- Source: https://www.cmu-agents.com/slides/lecture-20-search-basics.pdf
- SHA-256：`7ef0f29b2c1067258914c786f088326013f423c17a284ffe33069c7983a38c0f`。实际取得时间、页数与来源见 [MATERIALS.json](MATERIALS.json)。
- [完整中文讲解：怎样从多次尝试中得到更可靠的答案](notes.zh-CN.md)：沿主讲义的采样、验证、选择、反馈修改、PDR、长轨迹摘要/RTV 与 harness 搜索展开，结合全部 4 篇 Readings 与 23 项 References 的相关机制和边界。面向有 LLM 开发与 Java 后端经验的读者，包含概率推导、Java 边界/溢出贯穿例子、真实 SymPy 轨迹、成本与故障诊断、自测及答案。
- [轻量教学例子](examples.py)与[实际运行记录](EXAMPLE_RUN.json)：概率公式、合成反例与本地 Java 编译运行。未调用模型/API/GPU，未复现论文基准。内容审核状态及最终讲解版本由课程 [REVIEW.json](../REVIEW.json) 统一登记。

## 指定 Readings

固定版本与官网一致。Meta-Harness 从仓库既有正文按精确版本复用，其他三篇本轮取得；复用不记作新下载。

| 阅读完整标题 | 本地正文 | 版本 / 页数 | 官方来源 |
|---|---|---|---|
| Large Language Monkeys: Scaling Inference Compute with Repeated Sampling | [readings/Large_Language_Monkeys_Scaling_Inference_Compute_with_Repeated_Sampling.pdf](readings/Large_Language_Monkeys_Scaling_Inference_Compute_with_Repeated_Sampling.pdf) | 2407.21787v3 / 27 | https://arxiv.org/abs/2407.21787v3 |
| Rethinking Thinking Tokens: LLMs as Improvement Operators | [readings/Rethinking_Thinking_Tokens_LLMs_as_Improvement_Operators.pdf](readings/Rethinking_Thinking_Tokens_LLMs_as_Improvement_Operators.pdf) | 2510.01123v1 / 21 | https://arxiv.org/abs/2510.01123v1 |
| Scaling Test-Time Compute for Agentic Coding | [readings/Scaling_Test-Time_Compute_for_Agentic_Coding.pdf](readings/Scaling_Test-Time_Compute_for_Agentic_Coding.pdf) | 2604.16529v1 / 70 | https://arxiv.org/abs/2604.16529v1 |
| Meta-Harness: End-to-End Optimization of Model Harnesses | [readings/Meta-Harness_End-to-End_Optimization_of_Model_Harnesses.pdf](readings/Meta-Harness_End-to-End_Optimization_of_Model_Harnesses.pdf) | 2603.28052v1 / 26 | https://arxiv.org/abs/2603.28052v1 |

## 官方 References

与指定阅读分开登记。官网简称保留为 REFERENCES.json 的 `official_label`，论文使用正文完整标题命名。以下 20 篇为论文 PDF；未标版本的官方 arXiv 链接记录本次实际返回版本，不将不同版本混同。

| 参考论文完整标题 | 本地正文 | 版本 / 页数 | 官方来源 |
|---|---|---|---|
| Evaluating Large Language Models Trained on Code | [references/Evaluating_Large_Language_Models_Trained_on_Code.pdf](references/Evaluating_Large_Language_Models_Trained_on_Code.pdf) | 2107.03374v2 / 35 | https://arxiv.org/abs/2107.03374v2 |
| Verbalized Sampling: How to Mitigate Mode Collapse and Unlock LLM Diversity | [references/Verbalized_Sampling_How_to_Mitigate_Mode_Collapse_and_Unlock_LLM_Diversity.pdf](references/Verbalized_Sampling_How_to_Mitigate_Mode_Collapse_and_Unlock_LLM_Diversity.pdf) | 2510.01171v4 / 83 | https://arxiv.org/abs/2510.01171v4 |
| Mode-Conditioning Unlocks Superior Test-Time Scaling | [references/Mode-Conditioning_Unlocks_Superior_Test-Time_Scaling.pdf](references/Mode-Conditioning_Unlocks_Superior_Test-Time_Scaling.pdf) | 2512.01127v1 / 16 | https://arxiv.org/abs/2512.01127v1 |
| Rewarding the Unlikely: Lifting GRPO Beyond Distribution Sharpening | [references/Rewarding_the_Unlikely_Lifting_GRPO_Beyond_Distribution_Sharpening.pdf](references/Rewarding_the_Unlikely_Lifting_GRPO_Beyond_Distribution_Sharpening.pdf) | 2506.02355v2 / 12 | https://arxiv.org/abs/2506.02355v2 |
| Differential Smoothing Mitigates Sharpening and Improves LLM Reasoning | [references/Differential_Smoothing_Mitigates_Sharpening_and_Improves_LLM_Reasoning.pdf](references/Differential_Smoothing_Mitigates_Sharpening_and_Improves_LLM_Reasoning.pdf) | Official proceedings PDF / 33 | https://proceedings.mlr.press/v306/gai26a.html |
| Maximum Likelihood Reinforcement Learning | [references/Maximum_Likelihood_Reinforcement_Learning.pdf](references/Maximum_Likelihood_Reinforcement_Learning.pdf) | Official proceedings PDF / 56 | https://proceedings.mlr.press/v306/tajwar26a.html |
| Training Software Engineering Agents and Verifiers with SWE-Gym | [references/Training_Software_Engineering_Agents_and_Verifiers_with_SWE-Gym.pdf](references/Training_Software_Engineering_Agents_and_Verifiers_with_SWE-Gym.pdf) | 2412.21139v2 / 21 | https://arxiv.org/abs/2412.21139v2 |
| Self-Consistency Improves Chain of Thought Reasoning in Language Models | [references/Self-Consistency_Improves_Chain_of_Thought_Reasoning_in_Language_Models.pdf](references/Self-Consistency_Improves_Chain_of_Thought_Reasoning_in_Language_Models.pdf) | 2203.11171v4 / 24 | https://arxiv.org/abs/2203.11171 |
| From Decoding to Meta-Generation: Inference-time Algorithms for Large Language Models | [references/From_Decoding_to_Meta-Generation_Inference-time_Algorithms_for_Large_Language_Models.pdf](references/From_Decoding_to_Meta-Generation_Inference-time_Algorithms_for_Large_Language_Models.pdf) | 2406.16838v2 / 53 | https://arxiv.org/abs/2406.16838v2 |
| Natural Language to Code Translation with Execution | [references/Natural_Language_to_Code_Translation_with_Execution.pdf](references/Natural_Language_to_Code_Translation_with_Execution.pdf) | Proceedings of EMNLP 2022, pages 3533–3546 / 14 | https://aclanthology.org/2022.emnlp-main.231/ |
| Competition-Level Code Generation with AlphaCode | [references/Competition-Level_Code_Generation_with_AlphaCode.pdf](references/Competition-Level_Code_Generation_with_AlphaCode.pdf) | 2203.07814v1 / 74 | https://arxiv.org/abs/2203.07814 |
| Reflexion: Language Agents with Verbal Reinforcement Learning | [references/Reflexion_Language_Agents_with_Verbal_Reinforcement_Learning.pdf](references/Reflexion_Language_Agents_with_Verbal_Reinforcement_Learning.pdf) | 2303.11366v4 / 19 | https://arxiv.org/abs/2303.11366 |
| Self-Refine: Iterative Refinement with Self-Feedback | [references/Self-Refine_Iterative_Refinement_with_Self-Feedback.pdf](references/Self-Refine_Iterative_Refinement_with_Self-Feedback.pdf) | 2303.17651v2 / 54 | https://arxiv.org/abs/2303.17651v2 |
| Teaching Large Language Models to Self-Debug | [references/Teaching_Large_Language_Models_to_Self-Debug.pdf](references/Teaching_Large_Language_Models_to_Self-Debug.pdf) | 2304.05128v2 / 78 | https://arxiv.org/abs/2304.05128v2 |
| Large Language Models Cannot Self-Correct Reasoning Yet | [references/Large_Language_Models_Cannot_Self-Correct_Reasoning_Yet.pdf](references/Large_Language_Models_Cannot_Self-Correct_Reasoning_Yet.pdf) | 2310.01798v2 / 17 | https://arxiv.org/abs/2310.01798 |
| Recursive Self-Aggregation Unlocks Deep Thinking in Large Language Models | [references/Recursive_Self-Aggregation_Unlocks_Deep_Thinking_in_Large_Language_Models.pdf](references/Recursive_Self-Aggregation_Unlocks_Deep_Thinking_in_Large_Language_Models.pdf) | 2509.26626v2 / 23 | https://arxiv.org/abs/2509.26626v2 |
| WHALE: A Simple Recipe for Joint Harness-Weight Optimization | [references/WHALE_A_Simple_Recipe_for_Joint_Harness-Weight_Optimization.pdf](references/WHALE_A_Simple_Recipe_for_Joint_Harness-Weight_Optimization.pdf) | 2609.00196v1 / 28 | https://arxiv.org/abs/2609.00196v1 |
| Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents | [references/Darwin_Gödel_Machine_Open-Ended_Evolution_of_Self-Improving_Agents.pdf](references/Darwin_Gödel_Machine_Open-Ended_Evolution_of_Self-Improving_Agents.pdf) | 2505.22954v3 / 72 | https://arxiv.org/abs/2505.22954v3 |
| Group-Evolving Agents: Open-Ended Self-Improvement via Experience Sharing | [references/Group-Evolving_Agents_Open-Ended_Self-Improvement_via_Experience_Sharing.pdf](references/Group-Evolving_Agents_Open-Ended_Self-Improvement_via_Experience_Sharing.pdf) | 2602.04837v1 / 18 | https://arxiv.org/abs/2602.04837v1 |
| Tree Search for Language Model Agents | [references/Tree_Search_for_Language_Model_Agents.pdf](references/Tree_Search_for_Language_Model_Agents.pdf) | 2407.01476v4 / 25 | https://arxiv.org/abs/2407.01476 |

### 文档与代码参考

以下三项不是额外论文或视频；代码仅归档官网引用文件，不冒充完整仓库快照，不执行其模型或评测逻辑。

| 官方入口 | 本地文件 | 类型与范围 | 来源 |
|---|---|---|---|
| Claude: extended thinking and sampling settings | [references/Extended_thinking.html](references/Extended_thinking.html) | 官方文档正文 HTML 快照 | https://platform.claude.com/docs/en/build-with-claude/extended-thinking |
| DeepSeek-R1 usage recommendations | [references/code/DeepSeek-R1/README.md](references/code/DeepSeek-R1/README.md) | 固定提交的原始 README，含 usage recommendations；commit `0cf78561f1d51c84a21b2190626b21116d5c68bb` | https://github.com/deepseek-ai/DeepSeek-R1 |
| Meta-Harness: few-shot text-classification baseline | [references/code/meta-harness/reference_examples/text_classification/agents/fewshot_memory.py](references/code/meta-harness/reference_examples/text_classification/agents/fewshot_memory.py) | 固定提交的原始 Python 文件；官方链接指向 L92–L99；commit `f805ad3aa4ada290458c1e0deadbe132fbbdea4e` | https://github.com/stanford-iris-lab/meta-harness/blob/main/reference_examples/text_classification/agents/fewshot_memory.py#L92-L99 |

## 来源与验证边界

[REFERENCES.json](REFERENCES.json) 对 4 篇 Readings 和 23 项 References 逐项记录 URL、角色、完整标题、实际版本、文件路径、页数和 SHA-256。5 篇按精确版本复用既有归档，保留 `reused_from`、复用时间和原文件名；其余 22 项本轮实际取得。

资料归档检查覆盖主讲义和 24 份论文 PDF 的正文标识、页数、版本及全部页面可解析性；网页检查文档正文，代码按固定上游提交取得并保持原名及路径。新增讲解另行依据完整主讲义、各项资料的机制/实验/限制相关正文与必要附录核查，具体采用页段和用途见讲解末尾的来源地图；不把资料可解析性检查当成研究结论验证，也不声称所有长附录逐页精读。原始资料字节未改写。未下载视频，未运行模型/API/GPU、论文基准或所归档代码；实际运行范围限于新增的轻量教学例子。

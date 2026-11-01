# 3. Agent Capabilities 2: Context Management for Long-Context Agents

- Date: Tue, Sep 1

## Slides

- [Lecture 3 slides](lecture-03-long-context.pdf)
  - Source: https://www.cmu-agents.com/slides/lecture-03-long-context.pdf

## Course Video

- [Lecture 3 official video](https://www.youtube.com/watch?v=AiwCCvFW1uE&list=PLSN0qpDfUvTM&index=3)
  - Source: https://www.youtube.com/watch?v=AiwCCvFW1uE&list=PLSN0qpDfUvTM&index=3
  - Checked: 2026-10-28 (Asia/Shanghai); linked from the official course schedule.
  - Status: 仅登记官方视频入口；未下载视频或字幕，未将视频内容作为本轮讲解核验依据。

## Readings

- None

## References

- [DistServe](references/DistServe_Disaggregating_Prefill_and_Decoding_for_Goodput-optimized_Large_Language_Model_Serving.pdf)
  - Source: https://arxiv.org/abs/2401.09670

- [Needle in a Haystack](references/002_Needle_in_a_Haystack.md)
  - Source: https://github.com/gkamradt/LLMTest_NeedleInAHaystack

- [Attention Is All You Need](references/Attention_Is_All_You_Need.pdf)
  - Source: https://arxiv.org/abs/1706.03762

- [Longformer](references/Longformer_The_Long-Document_Transformer.pdf)
  - Source: https://arxiv.org/abs/2004.05150

- [Transformers are RNNs](references/Transformers_are_RNNs_Fast_Autoregressive_Transformers_with_Linear_Attention.pdf)
  - Source: https://arxiv.org/abs/2006.16236

- [Linear Transformers Are Secretly Fast Weight Programmers](references/Linear_Transformers_Are_Secretly_Fast_Weight_Programmers.pdf)
  - Source: https://arxiv.org/abs/2102.11174

- [Gated Delta Networks](references/Gated_Delta_Networks_Improving_Mamba2_with_Delta_Rule.pdf)
  - Source: https://arxiv.org/abs/2412.06464

- [Kimi Linear](references/Kimi_Linear_An_Expressive_Efficient_Attention_Architecture.pdf)
  - Source: https://arxiv.org/abs/2510.26692

- [DeepSeek Sparse Attention](references/DeepSeek-V3.2_Pushing_the_Frontier_of_Open_Large_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2512.02556

- [Grouped-Query Attention](references/GQA_Training_Generalized_Multi-Query_Transformer_Models_from_Multi-Head_Checkpoints.pdf)
  - Source: https://arxiv.org/abs/2305.13245

- [DeepSeek-V2](references/DeepSeek-V2_A_Strong_Economical_and_Efficient_Mixture-of-Experts_Language_Model.pdf)
  - Source: https://arxiv.org/abs/2405.04434

- [RoFormer](references/RoFormer_Enhanced_Transformer_with_Rotary_Position_Embedding.pdf)
  - Source: https://arxiv.org/abs/2104.09864

- [NoPE Length Generalization](references/The_Impact_of_Positional_Encoding_on_Length_Generalization_in_Transformers.pdf)
  - Source: https://arxiv.org/abs/2305.19466

- [Position Interpolation](references/Extending_Context_Window_of_Large_Language_Models_via_Position_Interpolation.pdf)
  - Source: https://arxiv.org/abs/2306.15595

- [YaRN](references/YaRN_Efficient_Context_Window_Extension_of_Large_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2309.00071

- [Qwen3.8-Flash-Next（网页壳归档，未取得正文）](references/016_Qwen3.html)
  - Source: https://qwen.ai/blog?id=qwen3.8-flash-next
  - Status: 本地 HTML 只有页面壳；不能作为已获取的模型说明正文。

- [GLM-5](references/GLM-5_from_Vibe_Coding_to_Agentic_Engineering.pdf)
  - Source: https://arxiv.org/abs/2602.15763

- [GLM-5.3-Flash](references/018_GLM-5.html)
  - Source: https://huggingface.co/zai-org/GLM-5.3-Flash

- [Kimi K3](references/Kimi_K3_Open_Frontier_Intelligence.pdf)
  - Source: https://arxiv.org/abs/2607.24653

- [Nemotron 3 Ultra](references/Nemotron_3_Ultra_Open_Efficient_Mixture-of-Experts_Hybrid_Mamba-Transformer_Model_for_Agentic_Reasoning.pdf)
  - Source: https://research.nvidia.com/labs/nemotron/files/NVIDIA-Nemotron-3-Ultra-Technical-Report.pdf

- [Inkling](references/021_Inkling.html)
  - Source: https://thinkingmachines.ai/news/introducing-inkling/

- [DeepSeek V4](references/DeepSeek-V4_Towards_Highly_Efficient_Million-Token_Context_Intelligence.pdf)
  - Source: https://arxiv.org/abs/2606.19348

- [Ring Attention](references/Ring_Attention_with_Blockwise_Transformers_for_Near-Infinite_Context.pdf)
  - Source: https://arxiv.org/abs/2310.01889

- [Megatron Context Parallelism](references/024_Megatron_Context_Parallelism.html)
  - Source: https://docs.nvidia.com/megatron-core/developer-guide/latest/user-guide/features/context_parallel.html

- [Prompt Cache](references/Prompt_Cache_Modular_Attention_Reuse_for_Low-Latency_Inference.pdf)
  - Source: https://arxiv.org/abs/2311.04934

- [Can I Buy Your KV Cache?](references/Can_I_Buy_Your_KV_Cache.pdf)
  - Source: https://arxiv.org/abs/2606.13361

- [DeepSeek API Pricing](references/027_DeepSeek_API_Pricing.html)
  - Source: https://api-docs.deepseek.com/quick_start/pricing/

- [Z.AI API Pricing（历史快照）](references/028_Z.html)
  - Source: https://docs.z.ai/guides/overview/pricing

- [Kimi K3 Pricing](references/029_Kimi_K3_Pricing.html)
  - Source: https://www.kimi.ai/resources/kimi-k3-pricing

- [OpenAI Model Pricing](references/030_OpenAI_Model_Pricing.html)
  - Source: https://developers.openai.com/api/docs/models/compare

- [Anthropic Prompt Caching](references/031_Anthropic_Prompt_Caching.html)
  - Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

- [PagedAttention / vLLM](references/Efficient_Memory_Management_for_Large_Language_Model_Serving_with_PagedAttention.pdf)
  - Source: https://arxiv.org/abs/2309.06180

- [SGLang / RadixAttention](references/SGLang_Efficient_Execution_of_Structured_Language_Model_Programs.pdf)
  - Source: https://arxiv.org/abs/2312.07104

- [SGLang Cache-Aware Load Balancing](references/034_SGLang_Cache-Aware_Load_Balancing.html)
  - Source: https://lmsys.org/blog/2024-12-04-sglang-v0-4/

- [MemGPT](references/MemGPT_Towards_LLMs_as_Operating_Systems.pdf)
  - Source: https://arxiv.org/abs/2310.08560

- [LongLLMLingua](references/LongLLMLingua_Accelerating_and_Enhancing_LLMs_in_Long_Context_Scenarios_via_Prompt_Compression.pdf)
  - Source: https://aclanthology.org/2024.acl-long.91/

- [Codex](references/037_Codex.md)
  - Source: https://github.com/openai/codex

- [OpenCode](references/038_OpenCode.md)
  - Source: https://github.com/anomalyco/opencode

- [Pi](references/039_Pi.md)
  - Source: https://github.com/badlogic/pi-mono

- [Hermes Agent](references/040_Hermes_Agent.md)
  - Source: https://github.com/NousResearch/hermes-agent

- [OpenHands](references/041_OpenHands.md)
  - Source: https://github.com/All-Hands-AI/OpenHands

- [ReSum](references/ReSum_Unlocking_Long-Horizon_Search_Intelligence_via_Context_Summarization.pdf)
  - Source: https://arxiv.org/abs/2509.13313

<!-- BEGIN LOCAL LEARNING -->
## 中文学习讲解

- [完整课程讲解](long_context_lecture03_integrated_notes.md)
<!-- END LOCAL LEARNING -->

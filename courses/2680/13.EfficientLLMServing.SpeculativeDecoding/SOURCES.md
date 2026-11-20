# 13. Efficient LLM serving: speculative decoding

- Date: 2026-11-11

## Slides

- [Lecture slides](12_llm_serving_spec_decoding.pdf)
  - Source: https://cs2680.com/slides/12_llm_serving_spec_decoding.pdf
  - 编号说明：目录 13 是本仓库稳定编号；文件名前缀 12 是官网原始讲义编号。内容按本课日期与主题核对，保留原文件名。

## Readings

- [speculative decoding](readings/Fast_Inference_from_Transformers_via_Speculative_Decoding.pdf)
  - Source: https://arxiv.org/abs/2211.17192
- [speculative sampling](readings/Accelerating_Large_Language_Model_Decoding_with_Speculative_Sampling.pdf)
  - Source: https://arxiv.org/abs/2302.01318
- [blockwise parallel decoding](readings/Blockwise_Parallel_Decoding_for_Deep_Autoregressive_Models.pdf)
  - Source: https://arxiv.org/abs/1811.03115
- [DistillSpec](readings/DistillSpec_Improving_Speculative_Decoding_via_Knowledge_Distillation.pdf)
  - Source: https://arxiv.org/abs/2310.08461
- [self-speculative](readings/Draft_Verify_Lossless_Large_Language_Model_Acceleration_via_Self-Speculative_Decoding.pdf)
  - Source: https://arxiv.org/abs/2309.08168
- [LayerSkip](readings/LayerSkip_Enabling_Early_Exit_Inference_and_Self-Speculative_Decoding.pdf)
  - Source: https://arxiv.org/abs/2404.16710
- [SWIFT](readings/SWIFT_On-the-Fly_Self-Speculative_Decoding_for_LLM_Inference_Acceleration.pdf)
  - Source: https://arxiv.org/abs/2410.06916
- [Medusa](readings/Medusa_Simple_LLM_Inference_Acceleration_Framework_with_Multiple_Decoding_Heads.pdf)
  - Source: https://arxiv.org/abs/2401.10774
- [EAGLE](readings/EAGLE_Speculative_Sampling_Requires_Rethinking_Feature_Uncertainty.pdf)
  - Source: https://arxiv.org/abs/2401.15077
- [EAGLE-2](readings/EAGLE-2_Faster_Inference_of_Language_Models_with_Dynamic_Draft_Trees.pdf)
  - Source: https://arxiv.org/abs/2406.16858
- [EAGLE-3](readings/EAGLE-3_Scaling_up_Inference_Acceleration_of_Large_Language_Models_via_Training-Time_Test.pdf)
  - Source: https://arxiv.org/abs/2503.01840
- [EAGLE at Meta](readings/Efficient_Speculative_Decoding_for_Llama_at_Scale_Challenges_and_Solutions.pdf)
  - Source: https://arxiv.org/abs/2508.08192
- [DeepSeek-V3 MTP](readings/DeepSeek-V3_Technical_Report.pdf)
  - Source: https://arxiv.org/abs/2412.19437
- [DFlash](readings/DFlash_Block_Diffusion_for_Flash_Speculative_Decoding.pdf)
  - Source: https://arxiv.org/abs/2602.06036
- [Domino](readings/Domino_Decoupling_Causal_Modeling_from_Autoregressive_Drafting_in_Speculative_Decoding.pdf)
  - Source: https://arxiv.org/abs/2605.29707
- [DSpark](readings/DSpark_Confidence-Scheduled_Speculative_Decoding_with_Semi-Autoregressive_Generation.pdf)
  - Source: https://arxiv.org/abs/2607.05147
- [DFlash 2](readings/DFlash_2_Keep_Drafting_Parallel.html)
  - Source: https://inco.ai/blog/dflash2/
- [DSpine](readings/DSpine_Draft_in_Parallel_Condition_Through_Depth_Adjacent_Causal_Injection_for_Speculative_Decoding.pdf)
  - Source: https://arxiv.org/abs/2609.36173
- [H-Spec](readings/H-Spec_Parallel_Speculative_Decoding_Without_a_Drafter-Side_KV_Cache.pdf)
  - Source: https://arxiv.org/abs/2609.24197
- [Uno](readings/Unlocking_Lossless_Speedups_in_LLMs_via_Discrete_Diffusion.pdf)
  - Source: https://arxiv.org/abs/2609.04010
- [REST](readings/REST_Retrieval-Based_Speculative_Decoding.pdf)
  - Source: https://arxiv.org/abs/2311.08252
- [lookahead decoding](readings/Break_the_Sequential_Dependency_of_LLM_Inference_Using_Lookahead_Decoding.pdf)
  - Source: https://arxiv.org/abs/2402.02057
- [prompt lookup](readings/Prompt_Lookup_Decoding.html)
  - Source: https://github.com/apoorvumang/prompt-lookup-decoding
- [SuffixDecoding](readings/SuffixDecoding_Extreme_Speculative_Decoding_for_Emerging_AI_Applications.pdf)
  - Source: https://arxiv.org/abs/2411.04975
- [speculative edits](readings/Editing_Files_at_1000_Tokens_per_Second.html)
  - Source: https://cursor.com/blog/instant-apply
- [SpecInfer](readings/SpecInfer_Accelerating_Large_Language_Model_Serving_with_Tree-based_Speculative_Inference_and_Verification.pdf)
  - Source: https://arxiv.org/abs/2305.09781
- [Sequoia](readings/Sequoia_Scalable_Robust_and_Hardware-aware_Speculative_Decoding.pdf)
  - Source: https://arxiv.org/abs/2402.12374
- [SpecExec](readings/SpecExec_Massively_Parallel_Speculative_Decoding_for_Interactive_LLM_Inference_on_Consumer_Devices.pdf)
  - Source: https://arxiv.org/abs/2406.02532
- [block verification](readings/Block_Verification_Accelerates_Speculative_Decoding.pdf)
  - Source: https://arxiv.org/abs/2403.10444
- [Judge Decoding](readings/Judge_Decoding_Faster_Speculative_Sampling_Requires_Going_Beyond_Model_Alignment.pdf)
  - Source: https://arxiv.org/abs/2501.19309
- [lossy verification](readings/Revisiting_Lossy_Verification_in_Speculative_Decoding_Mechanisms_Trade-offs_and_Failure_Modes.pdf)
  - Source: https://arxiv.org/abs/2607.26627
- [relaxed acceptance](readings/A_Practical_Investigation_of_Training-free_Relaxed_Speculative_Decoding.pdf)
  - Source: https://arxiv.org/abs/2607.08690
- [vLLM anatomy](readings/Inside_vLLM_Anatomy_of_a_High-Throughput_LLM_Inference_System.html)
  - Source: https://vllm.ai/blog/2025-09-05-anatomy-of-vllm
- [SmartSpec / TurboSpec](readings/TurboSpec_Closed-loop_Speculation_Control_System_for_Optimizing_LLM_Serving_Goodput.pdf)
  - Source: https://arxiv.org/abs/2406.14066
- [MagicDec](readings/MagicDec_Breaking_the_Latency-Throughput_Tradeoff_for_Long_Context_Generation_with_Speculative_Decoding.pdf)
  - Source: https://arxiv.org/abs/2408.11049
- [D-cut](readings/D-cut_Adaptive_Verification_Depth_Pruning_for_Batched_Speculative_Decoding.pdf)
  - Source: https://arxiv.org/abs/2607.14647
- [Cascade](readings/Utility-Driven_Speculative_Decoding_for_Mixture-of-Experts.pdf)
  - Source: https://arxiv.org/abs/2506.20675
- [mirror speculative decoding](readings/Mirror_Speculative_Decoding_Breaking_the_Serial_Barrier_in_LLM_Inference.pdf)
  - Source: https://arxiv.org/abs/2510.13161
- [online spec decoding](readings/Online_Speculative_Decoding.pdf)
  - Source: https://arxiv.org/abs/2310.07177
- [AdaServe](readings/AdaServe_SLO-Customized_LLM_Serving_with_Fine-Grained_Speculative_Decoding.pdf)
  - Source: https://arxiv.org/abs/2501.12162
- [AgentSpec](readings/AgentSpec_Speculative_Decoding_for_Batch_Inference_of_LLM_Agents.pdf)
  - Source: https://arxiv.org/abs/2608.24004
- [SpecForge](readings/SpecForge_A_Flexible_and_Efficient_Open-Source_Training_Framework_for_Speculative_Decoding.pdf)
  - Source: https://arxiv.org/abs/2603.18567
- [Speculators](readings/Speculators_A_unified_library_for_building_evaluating_and_storing_speculative_decoding_algorithms_for_LLM_inference_in_vLLM.html)
  - Source: https://github.com/vllm-project/speculators
- [TorchSpec](readings/TorchSpec_A_PyTorch_native_library_for_training_speculative_decoding_models.html)
  - Source: https://github.com/torchspec-project/TorchSpec
- [fal](readings/How_We_Achieved_1000_tok_s_and_16x_Throughput_with_DSpark_for_Ideogram_V4_Prompt_Expander.html)
  - Source: https://blog.fal.ai/how-we-achieved-1000-tok-s-and-16x-throughput-with-dspark-for-ideogram-v4-prompt-expander/
- [D-PACE](readings/D-PACE_Dynamic_Position-Aware_Cross-Entropy_for_Parallel_Speculative_Drafting.pdf)
  - Source: https://arxiv.org/abs/2605.18810

## Local study notes

以下为本地中文学习笔记，文件名保留现有名称；教师原始讲义见上方 Slides。

- [notes.zh-CN.md](notes.zh-CN.md)

## References

- [Course reading notes](../site/readings/nov-11.html)
  - Source: https://cs2680.com/readings/nov-11.html

## Supplemental primary sources

以下为中文讲解补充的一手资料；与上方官网指定 Readings 分开登记。版本、获取状态与校验值见 [REFERENCES.json](REFERENCES.json)。

- [Various Techniques Used in Connection With Random Digits](https://mcnp-green.lanl.gov/pdf_files/InBook_Computing_1961_Neumann_JohnVonNeumannCollectedWorks_VariousTechniquesUsedinConnectionwithRandomDigits.pdf)（已在线核对正文，未另存原件）
  - Source: https://mcnp-green.lanl.gov/pdf_files/InBook_Computing_1961_Neumann_JohnVonNeumannCollectedWorks_VariousTechniquesUsedinConnectionwithRandomDigits.pdf
- [Introducing EAGLE-4: One Flexible Drafter for All Batch Sizes and Hardware](https://blog.eagle.ai/blog/introducing-eagle-4)（已在线核对正文，未另存原件）
  - Source: https://blog.eagle.ai/blog/introducing-eagle-4
- [EAGLE-4: One Flexible Drafter for All Batch Sizes and Hardware](references/EAGLE-4_One_Flexible_Drafter_for_All_Batch_Sizes_and_Hardware.pdf)
  - Source: https://github.com/eagle-hq/EAGLE-4/blob/main/EAGLE4_Paper.pdf
- [How to train custom EAGLE-3 heads for speculative decoding](references/How_to_train_custom_EAGLE-3_heads_for_speculative_decoding.html)
  - Source: https://www.baseten.co/blog/how-to-train-custom-eagle-3-heads-for-speculative-decoding/
- [Insights into DeepSeek-V3: Scaling Challenges and Reflections on Hardware for AI Architectures](https://arxiv.org/html/2505.09343v2)（已在线核对正文，未另存原件）
  - Source: https://arxiv.org/html/2505.09343v2
- [Boost Inference Performance up to 15x on NVIDIA Blackwell Using DFlash Speculative Decoding](references/Boost_Inference_Performance_up_to_15x_on_NVIDIA_Blackwell_Using_DFlash_Speculative_Decoding.html)
  - Source: https://developer.nvidia.com/blog/boost-inference-performance-up-to-15x-on-nvidia-blackwell-using-dflash-speculative-decoding/
- [Predicted Outputs](references/Predicted_Outputs.html)
  - Source: https://developers.openai.com/api/docs/guides/predicted-outputs
- [Speculative Decoding - SGLang Documentation](references/Speculative_Decoding_-_SGLang_Documentation.html)
  - Source: https://docs.sglang.io/docs/advanced_features/speculative_decoding
- [[RFC]: Consistent semantics for drafted, verified and accepted spec decode tokens](https://github.com/vllm-project/vllm/issues/64099)（已在线核对正文，未另存原件）
  - Source: https://github.com/vllm-project/vllm/issues/64099

# 15. Efficient LLM serving: pruning and quantization

- Date: 2026-11-11

## Slides

- No slides linked on the course website as of 2026-10-23.

## Readings

- [mixed precision](readings/Mixed_Precision_Training.pdf)
  - Source: https://arxiv.org/abs/1710.03740
- [FP8 formats](readings/FP8_Formats_for_Deep_Learning.pdf)
  - Source: https://arxiv.org/abs/2209.05433
- [INT vs FP](readings/INT_v.s._FP_A_Comprehensive_Study_of_Fine-Grained_Low-bit_Quantization_Formats.pdf)
  - Source: https://arxiv.org/abs/2510.25602
- [microscaling FP4](readings/Bridging_the_Gap_Between_Promise_and_Performance_for_Microscaling_FP4_Quantization.pdf)
  - Source: https://arxiv.org/abs/2509.23202
- [LLM.int8()](readings/LLM.int8_8-bit_Matrix_Multiplication_for_Transformers_at_Scale.pdf)
  - Source: https://arxiv.org/abs/2208.07339
- [SmoothQuant](readings/SmoothQuant_Accurate_and_Efficient_Post-Training_Quantization_for_Large_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2211.10438
- [ZeroQuant](readings/ZeroQuant_Efficient_and_Affordable_Post-Training_Quantization_for_Large-Scale_Transformers.pdf)
  - Source: https://arxiv.org/abs/2206.01861
- [GPTQ](readings/GPTQ_Accurate_Post-Training_Quantization_for_Generative_Pre-trained_Transformers.pdf)
  - Source: https://arxiv.org/abs/2210.17323
- [AWQ](readings/AWQ_Activation-aware_Weight_Quantization_for_LLM_Compression_and_Acceleration.pdf)
  - Source: https://arxiv.org/abs/2306.00978
- [OmniQuant](readings/OmniQuant_Omnidirectionally_Calibrated_Quantization_for_Large_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2308.13137
- [SqueezeLLM](readings/SqueezeLLM_Dense-and-Sparse_Quantization.pdf)
  - Source: https://arxiv.org/abs/2306.07629
- [KIVI](readings/KIVI_A_Tuning-Free_Asymmetric_2bit_Quantization_for_KV_Cache.pdf)
  - Source: https://arxiv.org/abs/2402.02750
- [KVQuant](readings/KVQuant_Towards_10_Million_Context_Length_LLM_Inference_with_KV_Cache_Quantization.pdf)
  - Source: https://arxiv.org/abs/2401.18079
- [ZipCache](readings/ZipCache_Accurate_and_Efficient_KV_Cache_Quantization_with_Salient_Token_Identification.pdf)
  - Source: https://arxiv.org/abs/2405.14256
- [QServe](readings/QServe_W4A8KV4_Quantization_and_System_Co-design_for_Efficient_LLM_Serving.pdf)
  - Source: https://arxiv.org/abs/2405.04532
- [Atom](readings/Atom_Low-Bit_Quantization_for_Efficient_and_Accurate_LLM_Serving.pdf)
  - Source: https://arxiv.org/abs/2310.19102
- [SageAttention3](readings/SageAttention3_Microscaling_FP4_Attention_for_Inference_and_An_Exploration_of_8-Bit_Training.pdf)
  - Source: https://arxiv.org/abs/2505.11594
- [Tilus](readings/Tilus_A_Tile-Level_GPGPU_Programming_Language_for_Low-Precision_Computation.pdf)
  - Source: https://arxiv.org/abs/2504.12984
- [QLoRA](readings/QLoRA_Efficient_Finetuning_of_Quantized_LLMs.pdf)
  - Source: https://arxiv.org/abs/2305.14314
- [BitNet b1.58](readings/The_Era_of_1-bit_LLMs_All_Large_Language_Models_are_in_1.58_Bits.pdf)
  - Source: https://arxiv.org/abs/2402.17764
- [BitNet b1.58 2B4T](readings/BitNet_b1.58_2B4T_Technical_Report.pdf)
  - Source: https://arxiv.org/abs/2504.12285
- [ParetoQ](readings/ParetoQ_Improving_Scaling_Laws_in_Extremely_Low-bit_LLM_Quantization.pdf)
  - Source: https://arxiv.org/abs/2502.02631
- [Quartet](readings/Quartet_Native_FP4_Training_Can_Be_Optimal_for_Large_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2505.14669
- [NVFP4 pretraining](readings/Pretraining_Large_Language_Models_with_NVFP4.pdf)
  - Source: https://arxiv.org/abs/2509.25149
- [stable FP4 training](readings/Stable_FP4_Training_via_Transposition-Invariant_Block_Quantization.pdf)
  - Source: https://arxiv.org/abs/2607.24953
- [reliability scaling](readings/Reliability_Scaling_Laws_for_Quantized_Large_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2607.10855
- [silent failures](readings/Silent_Failures_in_Quantized_LLM_Reasoning_A_Taxonomy-Based_Analysis_of_Hollow_Convergence_and_Failure_Mode_Shifts.pdf)
  - Source: https://arxiv.org/abs/2607.09999
- [QuIP#](readings/QuIPSharp_Even_Better_LLM_Quantization_with_Hadamard_Incoherence_and_Lattice_Codebooks.pdf)
  - Source: https://arxiv.org/abs/2402.04396
- [QuaRot](readings/QuaRot_Outlier-Free_4-Bit_Inference_in_Rotated_LLMs.pdf)
  - Source: https://arxiv.org/abs/2404.00456
- [SpinQuant](readings/SpinQuant_LLM_Quantization_with_Learned_Rotations.pdf)
  - Source: https://arxiv.org/abs/2405.16406
- [block rotation MXFP4](readings/Block_Rotation_is_All_You_Need_for_MXFP4_Quantization.pdf)
  - Source: https://arxiv.org/abs/2511.04214
- [SparseGPT](readings/SparseGPT_Massive_Language_Models_Can_be_Accurately_Pruned_in_One-Shot.pdf)
  - Source: https://arxiv.org/abs/2301.00774
- [Wanda](readings/A_Simple_and_Effective_Pruning_Approach_for_Large_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2306.11695
- [LLM-Pruner](readings/LLM-Pruner_On_the_Structural_Pruning_of_Large_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2305.11627
- [ProxSparse](readings/ProxSparse_Regularized_Learning_of_Semi-Structured_Sparsity_Masks_for_Pretrained_LLMs.pdf)
  - Source: https://arxiv.org/abs/2502.00258
- [beyond FLOPs](readings/Beyond_FLOPs_Benchmarking_Real_Inference_Acceleration_of_LLM_Pruning_under_a_GEMM-Centric_Taxonomy.pdf)
  - Source: https://arxiv.org/abs/2606.09080

## References

- [Full course reading list](../site/readings.html)
  - Source: https://cs2680.com/readings.html#nov-11

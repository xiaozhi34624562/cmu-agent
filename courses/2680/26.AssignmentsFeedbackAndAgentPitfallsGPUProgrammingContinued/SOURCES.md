# 26. Assignments feedback and agent pitfalls, GPU programming (cont.)

- Date: 2026-11-02

## Slides

- [assignment](feedback_assignment.pdf)
  - Source: https://cs2680.com/slides/feedback_assignment.pdf
- [gpu](10_llm_serving_basics_2b.pdf)
  - Source: https://cs2680.com/slides/10_llm_serving_basics_2b.pdf
  - 编号说明：目录 26 是本仓库稳定编号；文件名前缀 10 是官网原始讲义编号。内容按本课日期与主题核对，保留原文件名。

## Readings

- None listed for this meeting.

## Local study notes

以下为本地中文学习笔记，文件名保留现有名称；教师原始讲义见上方 Slides。

- [notes.zh-CN.md](notes.zh-CN.md)

## References

- None listed.

## Supplemental primary sources

以下为中文讲解补充的一手资料；与上方官网指定 Readings 分开登记。版本、获取状态与校验值见 [REFERENCES.json](REFERENCES.json)。

- [FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](../11.EfficientLLMServingBasicsII.IntroToGPUs/readings/FlashAttention_Fast_and_Memory-Efficient_Exact_Attention_with_IO-Awareness.pdf)
  - Source: https://arxiv.org/abs/2205.14135
- [FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning](../11.EfficientLLMServingBasicsII.IntroToGPUs/readings/FlashAttention-2_Faster_Attention_with_Better_Parallelism_and_Work_Partitioning.pdf)
  - Source: https://arxiv.org/abs/2307.08691
- [FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision](../11.EfficientLLMServingBasicsII.IntroToGPUs/readings/FlashAttention-3_Fast_and_Accurate_Attention_with_Asynchrony_and_Low-precision.pdf)
  - Source: https://arxiv.org/abs/2407.08608
- [FlashAttention-4: Algorithm and Kernel Pipelining Co-Design for Asymmetric Hardware Scaling](../11.EfficientLLMServingBasicsII.IntroToGPUs/readings/FlashAttention-4_Algorithm_and_Kernel_Pipelining_Co-Design_for_Asymmetric_Hardware_Scaling.pdf)
  - Source: https://arxiv.org/abs/2603.05451
- [FlashInfer: Efficient and Customizable Attention Engine for LLM Inference Serving](../11.EfficientLLMServingBasicsII.IntroToGPUs/readings/FlashInfer_Efficient_and_Customizable_Attention_Engine_for_LLM_Inference_Serving.pdf)
  - Source: https://arxiv.org/abs/2501.01005
- [FLUX: Fast Software-based Communication Overlap on GPUs through Kernel Fusion](../11.EfficientLLMServingBasicsII.IntroToGPUs/readings/FLUX_Fast_Software-based_Communication_Overlap_on_GPUs_through_Kernel_Fusion.pdf)
  - Source: https://arxiv.org/abs/2406.06858
- [The Llama 3 Herd of Models](../10.EfficientLLMServingBasicsI.IntroToLLMs/readings/The_Llama_3_Herd_of_Models.pdf)
  - Source: https://arxiv.org/abs/2407.21783
- [DeepSeek-V3 Technical Report](../10.EfficientLLMServingBasicsI.IntroToLLMs/readings/DeepSeek-V3_Technical_Report.pdf)
  - Source: https://arxiv.org/abs/2412.19437
- [CUDA C++ Programming Guide](../11.EfficientLLMServingBasicsII.IntroToGPUs/readings/CUDA_C++_Programming_Guide.pdf)
  - Source: https://docs.nvidia.com/cuda/cuda-c-programming-guide/
- [MPK: A Compiler and Runtime for Mega-Kernelizing Tensor Programs](../11.EfficientLLMServingBasicsII.IntroToGPUs/readings/MPK_A_Compiler_and_Runtime_for_Mega-Kernelizing_Tensor_Programs.pdf)
  - Source: https://arxiv.org/abs/2512.22219v2
- [PyTorch 2: Faster Machine Learning Through Dynamic Python Bytecode Transformation and Graph Compilation](../11.EfficientLLMServingBasicsII.IntroToGPUs/references/PyTorch_2_Faster_Machine_Learning_Through_Dynamic_Python_Bytecode_Transformation_and_Graph_Compilation.pdf)
  - Source: https://pytorch.org/assets/pytorch2-2.pdf
- [Stream-K: Work-centric Parallel Decomposition for Dense Matrix-Matrix Multiplication on the GPU](references/Stream-K_Work-centric_Parallel_Decomposition_for_Dense_Matrix-Matrix_Multiplication_on_the_GPU.pdf)
  - Source: https://arxiv.org/abs/2301.03598
- [KernelBench: Can LLMs Write Efficient GPU Kernels?](references/KernelBench_Can_LLMs_Write_Efficient_GPU_Kernels.pdf)
  - Source: https://arxiv.org/abs/2502.10517
- [AutoMegaKernel: A Statically-Checked Agent Harness for Self-Retargeting Megakernel Synthesis](references/AutoMegaKernel_A_Statically-Checked_Agent_Harness_for_Self-Retargeting_Megakernel_Synthesis.pdf)
  - Source: https://arxiv.org/abs/2606.09682
- [ThunderKittens: Simple, Fast, and Adorable AI Kernels](references/ThunderKittens_Simple_Fast_and_Adorable_AI_Kernels.pdf)
  - Source: https://arxiv.org/abs/2410.20399
- [TileLang: A Composable Tiled Programming Model for AI Systems](references/TileLang_A_Composable_Tiled_Programming_Model_for_AI_Systems.pdf)
  - Source: https://arxiv.org/abs/2504.17577
- [Reducing Activation Recomputation in Large Transformer Models](references/Reducing_Activation_Recomputation_in_Large_Transformer_Models.pdf)
  - Source: https://arxiv.org/abs/2205.05198
- [PaLM: Scaling Language Modeling with Pathways](references/PaLM_Scaling_Language_Modeling_with_Pathways.pdf)
  - Source: https://arxiv.org/abs/2204.02311
- [Making AI Less “Thirsty”: Uncovering and Addressing the Secret Water Footprint of AI Models](references/Making_AI_Less_Thirsty_Uncovering_and_Addressing_the_Secret_Water_Footprint_of_AI_Models.pdf)
  - Source: https://arxiv.org/abs/2304.03271
- [Look Ma, No Bubbles! Designing a Low-Latency Megakernel for Llama-1B](references/Look_Ma_No_Bubbles_Designing_a_Low-Latency_Megakernel_for_Llama-1B.html)
  - Source: https://hazyresearch.stanford.edu/blog/2025-05-27-no-bubbles
- [Flash-Decoding for long-context inference](references/Flash-Decoding_for_long-context_inference.html)
  - Source: https://crfm.stanford.edu/2023/10/12/flashdecoding.html
- [Programmatic Dependent Launch and Synchronization — CUDA Programming Guide](references/Programmatic_Dependent_Launch_and_Synchronization_CUDA_Programming_Guide.html)
  - Source: https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/programmatic-dependent-launch.html
- [CUDA C++ Best Practices Guide](references/CUDA_C++_Best_Practices_Guide.html)
  - Source: https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html
- [NVIDIA DCGM Profiling](references/NVIDIA_DCGM_Profiling.html)
  - Source: https://docs.nvidia.com/datacenter/dcgm/latest/learn/modules/profiling.html
- [Nsight Compute Profiling Guide](references/Nsight_Compute_Profiling_Guide.html)
  - Source: https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html
- [Nsight Systems User Guide](references/Nsight_Systems_User_Guide.html)
  - Source: https://docs.nvidia.com/nsight-systems/UserGuide/index.html
- [LLM Inference Performance Engineering: Best Practices](references/LLM_Inference_Performance_Engineering_Best_Practices.html)
  - Source: https://www.databricks.com/blog/llm-inference-performance-engineering-best-practices
- [NVIDIA HGX Platform: Data Center Physical Requirements Guide](references/NVIDIA_HGX_Platform_Data_Center_Physical_Requirements_Guide.html)
  - Source: https://intuitionlabs.ai/articles/nvidia-hgx-data-center-requirements
- How I Used Claude Code（未获取正文）
  - Source: https://how-i-used-claude.cs2680.com/
- [CUTLASS Overview](references/CUTLASS_Overview.html)
  - Source: https://docs.nvidia.com/cutlass/latest/overview.html
- [CuTe Layouts](references/CuTe_Layouts.html)
  - Source: https://docs.nvidia.com/cutlass/latest/media/docs/cpp/cute/01_layout.html
- OpenXLA architecture（未获取正文）
  - Source: https://openxla.org/xla/architecture
- [Triton Vector Addition](references/Triton_Vector_Addition.html)
  - Source: https://triton-lang.org/main/getting-started/tutorials/01-vector-add.html
- [CUDA Tile Programming Model](references/CUDA_Tile_Programming_Model.html)
  - Source: https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/writing-tile-kernels.html
- [NVIDIA CUDA Compiler Driver](references/NVIDIA_CUDA_Compiler_Driver.html)
  - Source: https://docs.nvidia.com/cuda/cuda-compiler-driver-nvcc/index.html
- [Triton Documentation](references/Triton_Documentation.html)
  - Source: https://triton-lang.org/main/index.html
- [DeepEP: an efficient expert-parallel communication library](references/code/DeepEP/README.md)
  - Source: https://github.com/deepseek-ai/DeepEP

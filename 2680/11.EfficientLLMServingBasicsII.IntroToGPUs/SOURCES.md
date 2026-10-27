# 11. Efficient LLM serving basics II: intro to GPUs

- Date: 2026-10-21

## Slides

- [Lecture slides](10_llm_serving_basics_2a.pdf)
  - Source: https://cs2680.com/slides/10_llm_serving_basics_2a.pdf
  - 编号说明：目录 11 按课表日期排序；文件名前缀 10 是官网原始讲义编号。内容按本课日期与主题核对，保留原文件名。

## Readings

- [CUDA programming guide](readings/CUDA_C++_Programming_Guide.pdf)
  - Source: https://docs.nvidia.com/cuda/cuda-c-programming-guide/
- roofline — [online source](https://doi.org/10.1145/1498765.1498785)
  - Source: https://doi.org/10.1145/1498765.1498785
- [making DL go brrr](readings/Making_Deep_Learning_go_Brrrr_From_First_Principles.html)
  - Source: https://horace.io/brrr_intro.html
- [FlashAttention](readings/FlashAttention_Fast_and_Memory-Efficient_Exact_Attention_with_IO-Awareness.pdf)
  - Source: https://arxiv.org/abs/2205.14135
- [FlashAttention-2](readings/FlashAttention-2_Faster_Attention_with_Better_Parallelism_and_Work_Partitioning.pdf)
  - Source: https://arxiv.org/abs/2307.08691
- [FlashAttention-3](readings/FlashAttention-3_Fast_and_Accurate_Attention_with_Asynchrony_and_Low-precision.pdf)
  - Source: https://arxiv.org/abs/2407.08608
- [FlashAttention-4](readings/FlashAttention-4_Algorithm_and_Kernel_Pipelining_Co-Design_for_Asymmetric_Hardware_Scaling.pdf)
  - Source: https://arxiv.org/abs/2603.05451
- [B200 attention kernel](readings/FlashAttention-4_from_Scratch_to_Near-SOTA_in_60_Diagrams_CUDA_PTX.html)
  - Source: https://iaroslavelistratov.github.io/b200-attention
- [FlashInfer](readings/FlashInfer_Efficient_and_Customizable_Attention_Engine_for_LLM_Inference_Serving.pdf)
  - Source: https://arxiv.org/abs/2501.01005
- [ragged paged attention](readings/Ragged_Paged_Attention_A_High-Performance_and_Flexible_LLM_Inference_Kernel_for_TPU.pdf)
  - Source: https://arxiv.org/abs/2604.15464
- [FLUX](readings/FLUX_Fast_Software-based_Communication_Overlap_on_GPUs_through_Kernel_Fusion.pdf)
  - Source: https://arxiv.org/abs/2406.06858
- [TVM](readings/TVM_An_Automated_End-to-End_Optimizing_Compiler_for_Deep_Learning.pdf)
  - Source: https://arxiv.org/abs/1802.04799
- [Mirage](readings/Mirage_A_Multi-Level_Superoptimizer_for_Tensor_Programs.pdf)
  - Source: https://arxiv.org/abs/2405.05751
- [MPK](readings/MPK_A_Compiler_and_Runtime_for_Mega-Kernelizing_Tensor_Programs.pdf)
  - Source: https://arxiv.org/abs/2512.22219
- PyTorch 2 — [online source](https://doi.org/10.1145/3620665.3640366)
  - Source: https://doi.org/10.1145/3620665.3640366
- [LLM inference characterization](readings/A_Systematic_Characterization_of_LLM_Inference_on_GPUs.pdf)
  - Source: https://arxiv.org/abs/2512.01644

## Local study notes

以下为本地中文学习笔记，文件名保留现有名称；教师原始讲义见上方 Slides。

- [notes.zh-CN.md](notes.zh-CN.md)

## References

- [Course reading notes](../site/readings/oct-21.html)
  - Source: https://cs2680.com/readings/oct-21.html

## Supplemental primary sources

以下为中文讲解补充的一手资料；与上方官网指定 Readings 分开登记。版本、获取状态与校验值见 [REFERENCES.json](REFERENCES.json)。

- [Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures](references/Roofline_An_Insightful_Visual_Performance_Model_for_Floating-Point_Programs_and_Multicore_Architectures.pdf)
  - Source: https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-134.pdf
- [PyTorch 2: Faster Machine Learning Through Dynamic Python Bytecode Transformation and Graph Compilation](references/PyTorch_2_Faster_Machine_Learning_Through_Dynamic_Python_Bytecode_Transformation_and_Graph_Compilation.pdf)
  - Source: https://pytorch.org/assets/pytorch2-2.pdf

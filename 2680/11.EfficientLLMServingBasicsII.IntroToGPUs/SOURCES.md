# 11. Efficient LLM serving basics II: intro to GPUs

- Date: 2026-10-21

## Slides

- [Lecture slides](10_llm_serving_basics_2a.pdf)
  - Source: https://cs2680.com/slides/10_llm_serving_basics_2a.pdf
  - 编号说明：目录 11 按课表日期排序；文件名前缀 10 是官网原始讲义编号。内容按本课日期与主题核对，保留原文件名。

## Readings

- [CUDA programming guide](readings/001_CUDA_programming_guide_d2a9bf.pdf)
  - Source: https://docs.nvidia.com/cuda/cuda-c-programming-guide/
- roofline — [online source](https://doi.org/10.1145/1498765.1498785)
  - Source: https://doi.org/10.1145/1498765.1498785
- [making DL go brrr](readings/002_making_DL_go_brrr_48f2c0.html)
  - Source: https://horace.io/brrr_intro.html
- [FlashAttention](readings/003_FlashAttention_5727fe.pdf)
  - Source: https://arxiv.org/abs/2205.14135
- [FlashAttention-2](readings/004_FlashAttention_2_0927a2.pdf)
  - Source: https://arxiv.org/abs/2307.08691
- [FlashAttention-3](readings/005_FlashAttention_3_4791e2.pdf)
  - Source: https://arxiv.org/abs/2407.08608
- [FlashAttention-4](readings/006_FlashAttention_4_d76220.pdf)
  - Source: https://arxiv.org/abs/2603.05451
- [B200 attention kernel](readings/007_B200_attention_kernel_3b0706.html)
  - Source: https://iaroslavelistratov.github.io/b200-attention
- [FlashInfer](readings/008_FlashInfer_5d1291.pdf)
  - Source: https://arxiv.org/abs/2501.01005
- [ragged paged attention](readings/009_ragged_paged_attention_22be22.pdf)
  - Source: https://arxiv.org/abs/2604.15464
- [FLUX](readings/010_FLUX_f1a3cb.pdf)
  - Source: https://arxiv.org/abs/2406.06858
- [TVM](readings/011_TVM_a5558d.pdf)
  - Source: https://arxiv.org/abs/1802.04799
- [Mirage](readings/012_Mirage_1abd0e.pdf)
  - Source: https://arxiv.org/abs/2405.05751
- [MPK](readings/013_MPK_fdd519.pdf)
  - Source: https://arxiv.org/abs/2512.22219
- PyTorch 2 — [online source](https://doi.org/10.1145/3620665.3640366)
  - Source: https://doi.org/10.1145/3620665.3640366
- [LLM inference characterization](readings/014_LLM_inference_characterization_bc759f.pdf)
  - Source: https://arxiv.org/abs/2512.01644

## Local study notes

以下为本地中文学习笔记，文件名保留现有名称；教师原始讲义见上方 Slides。

- [notes.zh-CN.md](notes.zh-CN.md)

## References

- [Course reading notes](../site/readings/oct-21.html)
  - Source: https://cs2680.com/readings/oct-21.html

## Supplemental primary sources

以下为中文讲解补充的一手资料；与上方官网指定 Readings 分开登记。版本、获取状态与校验值见 [REFERENCES.json](REFERENCES.json)。

- [Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures (Berkeley technical report, 2008)](references/roofline-EECS-2008-134.pdf)
  - Source: https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-134.pdf
- [PyTorch 2: Faster Machine Learning Through Dynamic Python Bytecode Transformation and Graph Compilation (ASPLOS 2024)](references/pytorch2-asplos2024.pdf)
  - Source: https://pytorch.org/assets/pytorch2-2.pdf

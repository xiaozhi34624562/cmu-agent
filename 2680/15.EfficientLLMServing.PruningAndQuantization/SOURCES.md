# 15. Efficient LLM serving: pruning and quantization

- Date: 2026-11-11

## Slides

- No slides linked on the course website as of 2026-10-23.

## Readings

- [mixed precision](readings/001_mixed_precision_1718c4.pdf)
  - Source: https://arxiv.org/abs/1710.03740
- [FP8 formats](readings/002_FP8_formats_0b72db.pdf)
  - Source: https://arxiv.org/abs/2209.05433
- [INT vs FP](readings/003_INT_vs_FP_914bc6.pdf)
  - Source: https://arxiv.org/abs/2510.25602
- [microscaling FP4](readings/004_microscaling_FP4_db60aa.pdf)
  - Source: https://arxiv.org/abs/2509.23202
- [LLM.int8()](readings/005_LLM_int8_5bd418.pdf)
  - Source: https://arxiv.org/abs/2208.07339
- [SmoothQuant](readings/006_SmoothQuant_4deb70.pdf)
  - Source: https://arxiv.org/abs/2211.10438
- [ZeroQuant](readings/007_ZeroQuant_7db96e.pdf)
  - Source: https://arxiv.org/abs/2206.01861
- [GPTQ](readings/008_GPTQ_d01b1d.pdf)
  - Source: https://arxiv.org/abs/2210.17323
- [AWQ](readings/009_AWQ_9d933c.pdf)
  - Source: https://arxiv.org/abs/2306.00978
- [OmniQuant](readings/010_OmniQuant_bfaef8.pdf)
  - Source: https://arxiv.org/abs/2308.13137
- [SqueezeLLM](readings/011_SqueezeLLM_dcfe54.pdf)
  - Source: https://arxiv.org/abs/2306.07629
- [KIVI](readings/012_KIVI_3ab07c.pdf)
  - Source: https://arxiv.org/abs/2402.02750
- [KVQuant](readings/013_KVQuant_2ad745.pdf)
  - Source: https://arxiv.org/abs/2401.18079
- [ZipCache](readings/014_ZipCache_bd18e9.pdf)
  - Source: https://arxiv.org/abs/2405.14256
- [QServe](readings/015_QServe_8adf7e.pdf)
  - Source: https://arxiv.org/abs/2405.04532
- [Atom](readings/016_Atom_457eaa.pdf)
  - Source: https://arxiv.org/abs/2310.19102
- [SageAttention3](readings/017_SageAttention3_11d141.pdf)
  - Source: https://arxiv.org/abs/2505.11594
- [Tilus](readings/018_Tilus_3d5dc3.pdf)
  - Source: https://arxiv.org/abs/2504.12984
- [QLoRA](readings/019_QLoRA_2e95ee.pdf)
  - Source: https://arxiv.org/abs/2305.14314
- [BitNet b1.58](readings/020_BitNet_b1_58_ea6cd9.pdf)
  - Source: https://arxiv.org/abs/2402.17764
- [BitNet b1.58 2B4T](readings/021_BitNet_b1_58_2B4T_b37179.pdf)
  - Source: https://arxiv.org/abs/2504.12285
- [ParetoQ](readings/022_ParetoQ_1cbc40.pdf)
  - Source: https://arxiv.org/abs/2502.02631
- [Quartet](readings/023_Quartet_8e192b.pdf)
  - Source: https://arxiv.org/abs/2505.14669
- [NVFP4 pretraining](readings/024_NVFP4_pretraining_513aa5.pdf)
  - Source: https://arxiv.org/abs/2509.25149
- [stable FP4 training](readings/025_stable_FP4_training_328b82.pdf)
  - Source: https://arxiv.org/abs/2607.24953
- [reliability scaling](readings/026_reliability_scaling_b6399f.pdf)
  - Source: https://arxiv.org/abs/2607.10855
- [silent failures](readings/027_silent_failures_7b4e9b.pdf)
  - Source: https://arxiv.org/abs/2607.09999
- [QuIP#](readings/028_QuIPSharp_0bdf3d.pdf)
  - Source: https://arxiv.org/abs/2402.04396
- [QuaRot](readings/029_QuaRot_50944e.pdf)
  - Source: https://arxiv.org/abs/2404.00456
- [SpinQuant](readings/030_SpinQuant_0696b0.pdf)
  - Source: https://arxiv.org/abs/2405.16406
- [block rotation MXFP4](readings/031_block_rotation_MXFP4_848748.pdf)
  - Source: https://arxiv.org/abs/2511.04214
- [SparseGPT](readings/032_SparseGPT_ee93a0.pdf)
  - Source: https://arxiv.org/abs/2301.00774
- [Wanda](readings/033_Wanda_74261c.pdf)
  - Source: https://arxiv.org/abs/2306.11695
- [LLM-Pruner](readings/034_LLM_Pruner_699e64.pdf)
  - Source: https://arxiv.org/abs/2305.11627
- [ProxSparse](readings/035_ProxSparse_89d72b.pdf)
  - Source: https://arxiv.org/abs/2502.00258
- [beyond FLOPs](readings/036_beyond_FLOPs_6b6c42.pdf)
  - Source: https://arxiv.org/abs/2606.09080

## References

- [Full course reading list](../site/readings.html)
  - Source: https://cs2680.com/readings.html#nov-11

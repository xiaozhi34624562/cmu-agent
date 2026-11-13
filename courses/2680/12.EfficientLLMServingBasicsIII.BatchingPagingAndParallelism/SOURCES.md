# 12. Efficient LLM serving basics III: Batching, paging, and parallelism

- Date: 2026-11-04

## Slides

- [Lecture slides](11_llm_serving_basics_3.pdf)
  - Source: https://cs2680.com/slides/11_llm_serving_basics_3.pdf
  - 编号说明：目录 12 是本仓库稳定编号；文件名前缀 11 是官网原始讲义编号。内容按本课日期与主题核对，保留原文件名。

## Readings

- [evaluating serving systems](readings/On_Evaluating_Performance_of_LLM_Inference_Systems.pdf)
  - Source: https://arxiv.org/abs/2507.09019
- [Orca](readings/Orca_A_Distributed_Serving_System_for_Transformer-Based_Generative_Models.html)
  - Source: https://www.usenix.org/conference/osdi22/presentation/yu
- [Sarathi-Serve](readings/Taming_Throughput-Latency_Tradeoff_in_LLM_Inference_with_Sarathi-Serve.pdf)
  - Source: https://arxiv.org/abs/2403.02310
- [DistServe](readings/DistServe_Disaggregating_Prefill_and_Decoding_for_Goodput-optimized_Large_Language_Model_Serving.pdf)
  - Source: https://arxiv.org/abs/2401.09670
- [Splitwise](readings/Splitwise_Efficient_Generative_LLM_Inference_Using_Phase_Splitting.pdf)
  - Source: https://arxiv.org/abs/2311.18677
- [learning to rank](readings/Efficient_LLM_Scheduling_by_Learning_to_Rank.pdf)
  - Source: https://arxiv.org/abs/2408.15792
- [FastServe](readings/Fast_Distributed_Inference_Serving_for_Large_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2305.05920
- [vLLM / PagedAttention](readings/Efficient_Memory_Management_for_Large_Language_Model_Serving_with_PagedAttention.pdf)
  - Source: https://arxiv.org/abs/2309.06180
- [Jenga](readings/JENGA_Effective_Memory_Management_for_Serving_LLM_with_Heterogeneity.pdf)
  - Source: https://arxiv.org/abs/2503.18292
- [SGLang / RadixAttention](readings/SGLang_Efficient_Execution_of_Structured_Language_Model_Programs.pdf)
  - Source: https://arxiv.org/abs/2312.07104
- [VTC](readings/Fairness_in_Serving_Large_Language_Models.pdf)
  - Source: https://arxiv.org/abs/2401.00588
- [DLPM](readings/Locality-aware_Fair_Scheduling_in_LLM_Serving.pdf)
  - Source: https://arxiv.org/abs/2501.14312
- [MPICH collectives](readings/Optimization_of_Collective_Communication_Operations_in_MPICH.pdf)
  - Source: https://doi.org/10.1177/1094342005051521
- [Efficiently Scaling Transformer Inference](readings/Efficiently_Scaling_Transformer_Inference.pdf)
  - Source: https://arxiv.org/abs/2211.05102
- [Megatron-LM](readings/Megatron-LM_Training_Multi-Billion_Parameter_Language_Models_Using_Model_Parallelism.pdf)
  - Source: https://arxiv.org/abs/1909.08053
- [GPipe](readings/GPipe_Easy_Scaling_with_Micro-Batch_Pipeline_Parallelism.pdf)
  - Source: https://arxiv.org/abs/1811.06965
- [LoongServe](readings/LoongServe_Efficiently_Serving_Long-Context_Large_Language_Models_with_Elastic_Sequence_Parallelism.pdf)
  - Source: https://arxiv.org/abs/2404.09526

## Retained earlier reading archive

以下原件来自此前公开阅读清单；当前课表未在本课列出，保留历史归档，不计为本次新增指定阅读。

- [NanoFlow_Towards_Optimal_Large_Language_Model_Serving_Throughput.pdf](readings/NanoFlow_Towards_Optimal_Large_Language_Model_Serving_Throughput.pdf)
- [vAttention_Dynamic_Memory_Management_for_Serving_LLMs_without_PagedAttention.pdf](readings/vAttention_Dynamic_Memory_Management_for_Serving_LLMs_without_PagedAttention.pdf)

## Local study notes

以下为本地中文学习笔记，文件名保留现有名称；教师原始讲义见上方 Slides。

- [notes.zh-CN.md](notes.zh-CN.md)

## References

- [Course reading notes](../site/readings/nov-04.html)
  - Source: https://cs2680.com/readings/nov-04.html

## Supplemental primary sources

以下为中文讲解补充的一手资料；与上方官网指定 Readings 分开登记。版本、获取状态与校验值见 [REFERENCES.json](REFERENCES.json)。

- [Orca: A Distributed Serving System for Transformer-Based Generative Models](references/Orca_A_Distributed_Serving_System_for_Transformer-Based_Generative_Models.pdf)
  - Source: https://www.usenix.org/system/files/osdi22-yu.pdf

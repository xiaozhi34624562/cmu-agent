# 10. Domains 3: Deep Research Agents

- Date: Thu, Sep 24
- Lecturer: Akari Asai

## Slides

- [Lecture 10 slides](lecture-10-deep-research-agents.pdf)
  - Source: https://www.cmu-agents.com/slides/lecture-10-deep-research-agents.pdf

## Readings

- [OpenScholar](readings/001_OpenScholar.html)
  - Source: https://www.nature.com/articles/s41586-025-10072-4

- [BrowseComp](readings/002_BrowseComp.pdf)
  - Source: https://arxiv.org/abs/2504.12516

- [DeepResearch Bench](readings/003_DeepResearch_Bench.pdf)
  - Source: https://arxiv.org/abs/2506.11763

- [Tongyi DeepResearch](readings/004_Tongyi_DeepResearch.pdf)
  - Source: https://arxiv.org/abs/2510.24701

- [DR Tulu](readings/005_DR_Tulu.pdf)
  - Source: https://arxiv.org/abs/2511.19399

- [AgentIR](readings/006_AgentIR.pdf)
  - Source: https://arxiv.org/abs/2603.04384

## References

- [Natural Questions example](references/001_Natural_Questions_example.html)
  - Source: https://ai.google.com/research/NaturalQuestions/databrowser

- [Wikipedia source document](references/002_Wikipedia_source_document.html)
  - Source: https://en.wikipedia.org/w/index.php?oldid=824425456

- [BrowseComp-Plus](references/003_BrowseComp-Plus.pdf)
  - Source: https://arxiv.org/abs/2508.06600

- [FinSearchComp](references/004_FinSearchComp.pdf)
  - Source: https://arxiv.org/abs/2509.13160

- [MedBrowseComp](references/005_MedBrowseComp.pdf)
  - Source: https://arxiv.org/abs/2505.14963

- [ScholarSearch](references/006_ScholarSearch.pdf)
  - Source: https://arxiv.org/abs/2506.13784

- [AutoResearchBench](references/007_AutoResearchBench.pdf)
  - Source: https://arxiv.org/abs/2604.25256

- [A Critical Evaluation of Evaluations for Long-form Question Answering](references/008_A_Critical_Evaluation_of_Evaluations_for_Long-form_Question_Answering.pdf)
  - Source: https://aclanthology.org/2023.acl-long.181/

- [ResearchQA](references/009_ResearchQA.pdf)
  - Source: https://arxiv.org/abs/2509.00496

- [DeepResearch Bench II](references/010_DeepResearch_Bench_II.pdf)
  - Source: https://arxiv.org/abs/2601.08536

- [CMU Archives: Herbert Simon](references/011_CMU_Archives_Herbert_Simon.html)
  - Source: https://digitalcollections.library.cmu.edu/cmu-collection/herbert-simon

- [1978 Nobel Prize in Economic Sciences](references/012_1978_Nobel_Prize_in_Economic_Sciences.html)
  - Source: https://www.nobelprize.org/prizes/economic-sciences/1978/summary/

- [WebSailor-V2](references/013_WebSailor-V2.pdf)
  - Source: https://arxiv.org/abs/2509.13305

- [WebDancer](references/014_WebDancer.pdf)
  - Source: https://arxiv.org/abs/2505.22648

- [Scaling Agents via Continual Pre-training](references/015_Scaling_Agents_via_Continual_Pre-training.pdf)
  - Source: https://arxiv.org/abs/2509.13310

- [Search-R1](references/016_Search-R1.pdf)
  - Source: https://arxiv.org/abs/2503.09516

- [DeepSeekMath](references/017_DeepSeekMath.pdf)
  - Source: https://arxiv.org/abs/2402.03300

- [Dense Passage Retrieval](references/018_Dense_Passage_Retrieval.pdf)
  - Source: https://aclanthology.org/2020.emnlp-main.550/

## Design Notes

- [Deep Research Agent 通用设计](Deep_Research_Agent_General_Design.md)
  - 结合法国教育制度研究复盘、Lecture 10 综合笔记与一手来源，整理任务规格、证据状态、动态规划、核验及落地顺序；工程建议与论文结论分别标记。
- [通用设计的一手来源核查](Deep_Research_Agent_Design_Source_Checks.md)
  - 补充 OpenScholar、AgentIR 与 Anthropic 官方研究系统文章的机制、访问状态及适用边界。

<!-- BEGIN LOCAL LEARNING -->
## 中文学习讲解

- [完整课程讲解](Deep_Research_Lecture10_Integrated_Notes.md)
- [专题补充：Deep_Research_Agent_General_Design.md](Deep_Research_Agent_General_Design.md)
- [专题补充：Deep_Research_Agent_Design_Source_Checks.md](Deep_Research_Agent_Design_Source_Checks.md)
- [专题补充：Finance_Agent_Research_2026_Three_Papers.md](Finance_Agent_Research_2026_Three_Papers.md)
- [FutureX-Pro: Extending Future Prediction to High-Value Vertical Domains](references/019_FutureX-Pro_2601.12259v1.pdf) — [原始来源](https://arxiv.org/pdf/2601.12259v1)
- [MBABench: Evaluating LLM Agents on End-to-End Spreadsheet Tasks in Finance](references/020_MBABench_2605.22664v5.pdf) — [原始来源](https://arxiv.org/pdf/2605.22664v5)
- [Can Language Models Learn to Forecast Stock Prices](references/021_AURA_2609.36914v1.pdf) — [原始来源](https://arxiv.org/pdf/2609.36914v1)
- [Futurex-Eval README](references/futurex-eval-README.md) — [原始来源](https://raw.githubusercontent.com/Futurex-ai/Futurex-Eval/2626f7a297cd87c73a45408e23af8d838f5b60e5/README.md)
- [Futurex-Eval numeric judge](references/futurex-llm_judge_level_34.py) — [原始来源](https://raw.githubusercontent.com/Futurex-ai/Futurex-Eval/2626f7a297cd87c73a45408e23af8d838f5b60e5/llm_judge_level_34.py)
- [Futurex-Eval task evaluator](references/futurex-eval.py) — [原始来源](https://raw.githubusercontent.com/Futurex-ai/Futurex-Eval/2626f7a297cd87c73a45408e23af8d838f5b60e5/eval.py)
<!-- END LOCAL LEARNING -->

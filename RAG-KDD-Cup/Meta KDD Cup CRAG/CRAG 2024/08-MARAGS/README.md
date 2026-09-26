# MARAGS

## 1. 一段结论

MARAGS 用共享 Llama 3 backbone 和多个 LoRA adapter 覆盖网页 QA、API call 与不同任务，并用 hittable 重标控制幻觉，展示模型共享、能力隔离和风险感知训练。

[论文](./papers/MARAGS.pdf) · [代码状态](./code/README.md) · [来源清单](./resources/source-manifest.md)

## 2. 论文身份与比赛背景

本文是 2024 KDD Cup CRAG Workshop 技术报告，同时发布于 arXiv。论文称 Task 1 第二、Task 2 第三，而 AIcrowd 后续 spotlight 称 Task 1 第三；本档案保留冲突。

## 3. 任务与评分目标

系统跨网页 QA 和 API 任务共享基础模型，目标是在 Incorrect=-1、Missing=0 下通过 adapter 与 hittable 标签平衡回答率和幻觉。

## 4. 问题诊断与基线弱点

普通 LoRA 会把 gold 当作总能回答，检索缺证时仍生成；每任务部署完整模型又浪费显存。检索 metric 提升也不保证最终 score 改善。

## 5. 端到端架构与数据流

BeautifulSoup 按结构切分至约 2000 字符，cross-encoder 排序；Task 2/3 用 API generation adapter，生成 adapter 按任务训练，router 切换共享 backbone 上的 LoRA。问题放在长上下文末尾缓解遗忘。

## 6. 核心机制

最终采用 `ms-marco-MiniLM-L-6-v2` cross-encoder。hittable 重标判断当前 retrieval 是否含答案，缺证样本把 target 改成拒答，避免监督模型凭空输出 gold。

## 7. 实验、消融与报告分数

500 样本 cross-encoder accuracy 0.328；基础 Llama 3 的 accuracy/hallucination/score 为 0.328/0.444/-0.116。普通 LoRA 为 0.398/0.602/-0.204；hittable 重标后为 0.242/0.056/0.186。

## 8. 评分机制下为何有效

普通 LoRA 虽提高 accuracy，却增加 Incorrect=-1；hittable 重标牺牲部分 coverage，把高风险回答转为 Missing=0，最终得到正分。这证明可靠性目标不能被裸 accuracy 替代。

## 9. 代码地图

作者未发布官方源码、adapter 或权重，无法建立文件级映射。论文只支持 HTML 切分、cross-encoder、router、API adapter、generation adapter 与 hittable relabel 的逻辑地图。

## 10. 复现条件与缺失产物

需要 Llama 3、LoRA、sentence-transformer/cross-encoder、CRAG API/数据和 GPU。代码、adapter、完整标签与 router 配置均缺失，不能声明精确复现。

## 11. 工程限制、延迟成本与故障传播

工程判断：adapter 节省显存但需要可靠 router、版本管理和加载延迟治理；hittable 标签绑定当前 retriever，换索引后可能失效。API target 人工修正也可能产生可执行但语义错误的调用。

## 12. 对金融 RAG 的迁移

工程判断：可建立 filing-QA、metric-calculation、entity-linking、abstention adapters，共享 backbone；router、adapter 与索引快照绑定。hittable 用证据 span/entailment 标注，金额评价需感知单位、币种和报告期。

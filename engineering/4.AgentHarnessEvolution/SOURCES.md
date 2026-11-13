# Agent Harness 自演化：资料入口

核查与下载日期：2026-11-13（Asia/Shanghai）。这是 engineering 专题，不是课程新增讲次。

完整讲解：[四篇论文的机制、证据与工程实践](research.zh-CN.md)。

原始 PDF 字节完整保存；版本固定，不把下载日期或封面日期当作 arXiv 提交日期。完整元数据见 [REFERENCES.json](REFERENCES.json)。

## R01 · RRSI: Regularized Recursive Self-Improvement of Agent Harnesses

- [固定版本论文页面](https://arxiv.org/abs/2609.24972v3) · [原始 PDF](https://arxiv.org/pdf/2609.24972v3) · [本地 PDF](references/RRSI_Regularized_Recursive_Self-Improvement_of_Agent_Harnesses.pdf)
- 首次提交：2026-09-21；归档版本：arXiv 2609.24972v3；修订日期：2026-10-04；PDF 27 页。
- PDF 封面日期：2026-10-06；与 arXiv 版本历史分别记录。
- 核查范围：正文 §§2–4 pp.3–10；算法/超参数/统计与案例 App D–E pp.19–27；核对 Fig3、Tables1–7。
- SHA-256：`26f8b5417f8a60c9284bb4a36d3981c41b8e071134aea0bf3402fe9584c8cd76`。

## R02 · Harness^2: Recursive Agent Harnessing for an Open World

- [固定版本论文页面](https://arxiv.org/abs/2610.14224v1) · [原始 PDF](https://arxiv.org/pdf/2610.14224v1) · [本地 PDF](references/Harness_2_Recursive_Agent_Harnessing_for_an_Open_World.pdf)
- 首次提交：2026-10-09；归档版本：arXiv 2610.14224v1；修订日期：2026-10-09；PDF 37 页。
- PDF 封面日期：2026-10-12；与 arXiv 版本历史分别记录。
- 核查范围：正文 §§2–4 pp.3–12；实现、消融、案例与限制 App D–H pp.18–37；核对 Tables1–3、Figures5–7。
- SHA-256：`440be1f694f3b0fdfb8e612e9b2288ff0d8ab38641cfd1064fd77052ba360282`。

## R03 · Evo^2: Evolving the Evolver through Weight-Harness Co-Evolution

- [固定版本论文页面](https://arxiv.org/abs/2610.13025v1) · [原始 PDF](https://arxiv.org/pdf/2610.13025v1) · [本地 PDF](references/Evo_2_Evolving_the_Evolver_through_Weight-Harness_Co-Evolution.pdf)
- 首次提交：2026-10-09；归档版本：arXiv 2610.13025v1；修订日期：2026-10-09；PDF 12 页。
- PDF 封面日期：2026-10-09；与 arXiv 版本历史分别记录。
- 核查范围：正文 §§3–4 pp.4–10；完整12页；核对全部五张结果表及奖励/训练公式。
- SHA-256：`830667d045c0b966c529ba874e2b0480eb8f3c787d31fa4c20e99e56de84e487`。

## R04 · Object-Oriented Harness: Evolving Agent Harnesses through Object-Oriented Design

- [固定版本论文页面](https://arxiv.org/abs/2610.28380v1) · [原始 PDF](https://arxiv.org/pdf/2610.28380v1) · [本地 PDF](references/Object-Oriented_Harness_Evolving_Agent_Harnesses_through_Object-Oriented_Design.pdf)
- 首次提交：2026-10-20；归档版本：arXiv 2610.28380v1；修订日期：2026-10-20；PDF 20 页。
- PDF 封面日期：2026-10-21；与 arXiv 版本历史分别记录。
- 核查范围：正文 §§3–5 pp.3–9；实现和消融 App A pp.13–18；核对 Tables1–3、Figures5–7及继承实例。
- SHA-256：`30d157984f16072ebac9bb42f39eb2630ec0163dfcf0e096fc3a986974fe6a02`。

## 获取与结论边界

- 四篇均已取得可解析 PDF，未使用摘要或验证页代替正文。
- RRSI 摘要最高 OOD +4.3 与 Fig3/Table6 的 JobBench +4.7 不一致；讲解采用具体表图并保留差异。
- Evo² 闭源实验 baseline 取 top1、该方法取 top2 较优，且为60题子集；不能当作等预算的原始base前后比较。
- OO-Harness 主文与附录的 router 模型描述不完全一致；其 Steps 不包含基础试跑和辅助路由调用。
- 模型名称和分数均为论文的实验配置与报告，不是本次对这些模型当前服务可用性的核验。
- 本次未运行模型、GPU、API 或 benchmark 实验；工程案例、建议与实验方案在正文就近标明。

## 补充比较：DSPy

访问日期2026-11-13；官方仓库提交 `2c07ebbee3a66f6e04b71e141c6c198f1b31a129`。供主文§9对照，不代表用户安装版本；未执行DSPy或模型实验。

- [DSPy Optimizers](https://github.com/stanfordnlp/dspy/blob/2c07ebbee3a66f6e04b71e141c6c198f1b31a129/docs/docs/learn/optimization/optimizers.md)。
- [GEPA Overview](https://github.com/stanfordnlp/dspy/blob/2c07ebbee3a66f6e04b71e141c6c198f1b31a129/docs/docs/api/optimizers/GEPA/overview.md)。
- [GEPA implementation：Flex code proposer与compile接口](https://github.com/stanfordnlp/dspy/blob/2c07ebbee3a66f6e04b71e141c6c198f1b31a129/dspy/teleprompt/gepa/gepa.py)。

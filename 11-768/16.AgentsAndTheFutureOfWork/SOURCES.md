# 16. Agents and the Future of Work

- 官方日期：**2026-10-27**；讲者：**Zora Wang**。
- 官方课表标题：**Agents and the Future of Work**；PDF 封面标题：**AI Agents for Human Work**。
- 官网：[CMU 11-768 AI Agents](https://www.cmu-agents.com/#/schedule)。本地编号 16 是归档次序，不等于官方 Lecture 编号。
- 资料核对与本轮取得日期：2026-10-28（Asia/Shanghai）。

## 原始讲义与学习入口

- [完整中文讲解](notes.zh-CN.md)。
- [可运行教学算例](examples/evaluation_math.py)与[实际执行记录](examples/EXECUTION.json)：只验证构造的成本、分母和条件概率计算，不代表模型实验。
- [AI Agents for Human Work · 62 页官方 PDF](2026-10-27-zora-wang.pdf)。
  - Source: https://www.cmu-agents.com/slides/2026-10-27-zora-wang.pdf
  - Original filename: `2026-10-27-zora-wang.pdf`；保留原始字节。
  - SHA-256: `e07e9da87a97680981fca5b3ba766a7c620c83e8c1515fb75a798fe5812b79b1`。
- 官方课表未为本讲单独列出 readings/references；下方原文是为核对讲义中的研究与结论补充，不能冒充教师指定阅读。

## 讲义页码与讲解主线

下表及讲解均采用实际 PDF 页序，从 1 开始。

| PDF 页序 | 问题链 | 核对与补充来源 |
|---|---|---|
| 1–14 | 基准表现、采用情况与真实工作之间的差距 | METR；RLI；讲义中的使用统计与榜单快照 |
| 15–25 | 如何定义与采样工作任务，覆盖哪些职业和交付物 | GDPval、RLI、WORKBank；工作覆盖审计 |
| 26–32 | Agent 的运行环境、工具与真实软件/数据差异 | 主讲义：Google Docs/LibreOffice、任务表与真实财务表 |
| 33–45 | 可执行评估、开放任务 rubric、人工偏好与 LLM judge | GDPval；主讲义中的评估局限与自偏好案例 |
| 46–53 | 协作、时间成本、安全与有意义的工作 | WORKBank 的 HAS；CollabSkill、TAHI；主讲义成本/安全案例 |
| 54–62 | 劳动力市场暴露、替代与新任务、观测证据与学习 | GPTs are GPTs；Canaries 版本差异；主讲义观点 |

## 补充一手原文

完整标题、版本、原文件名、获取或复用方式与 SHA-256 见 [REFERENCES.json](REFERENCES.json)。所有已保存文件均经 PDF 实际内容检查；不能以 URL 或论文摘要代替正文。

- [GDPval: Evaluating AI Model Performance on Real-World Economically Valuable Tasks](references/GDPval_Evaluating_AI_Model_Performance_on_Real-World_Economically_Valuable_Tasks.pdf)
  - Source: https://cdn.openai.com/pdf/d5eb7428-c4e9-4a33-bd86-86dd4bcf12ce/GDPval.pdf
  - Version: Official OpenAI paper, arXiv:2510.04374; 29-page publisher PDF；29 页。
  - Original filename: `GDPval.pdf`；SHA-256: `37c7604bc9da68cd8d9345ad16938164fe985182ad723fcb09e9415f84dc25d4`。
  - Status: saved；2026-10-28 取得。
- [Remote Labor Index: Measuring AI Automation of Remote Work](references/Remote_Labor_Index_Measuring_AI_Automation_of_Remote_Work.pdf)
  - Source: https://arxiv.org/pdf/2510.26787v1
  - Version: arXiv:2510.26787v1；31 页。
  - Original filename: `2510.26787v1`；SHA-256: `7bc1e50585429c83a93a8045fdaa654ba074c4fa3a35671613024de69c46d2ed`。
  - Status: saved；2026-10-28 取得。
  - 版本与解释边界：正文摘要最高 2.5%，不能写为 3.75% 或讲义后续榜单 21.25%。
- [Future of Work with AI Agents: Auditing Automation and Augmentation Potential across the U.S. Workforce](references/Future_of_Work_with_AI_Agents_Auditing_Automation_and_Augmentation_Potential_across_the_U.S._Workforce.pdf)
  - Source: https://arxiv.org/pdf/2506.06576v3
  - Version: arXiv:2506.06576v3；45 页。
  - Original filename: `2506.06576v3`；SHA-256: `8cea403d86046b14a9296991b91f659192b0aedf3d86806faeeecce3a81d962a`。
  - Status: saved；2026-10-28 取得。
- [GPTs are GPTs: An Early Look at the Labor Market Impact Potential of Large Language Models](references/GPTs_are_GPTs_An_Early_Look_at_the_Labor_Market_Impact_Potential_of_Large_Language_Models.pdf)
  - Source: https://arxiv.org/pdf/2303.10130v5
  - Version: arXiv:2303.10130v5; title page August 22, 2023；36 页。
  - Original filename: `2303.10130v5`；SHA-256: `af3edd4efc120c70f0e2e6dc7a4e314a41f1b9eb5a7e88bc25533db631f79632`。
  - Status: saved；2026-10-28 取得。
- [Canaries in the Coal Mine? Six Facts about the Recent Employment Effects of Artificial Intelligence](references/Canaries_in_the_Coal_Mine_Six_Facts_about_the_Recent_Employment_Effects_of_Artificial_Intelligence.pdf)
  - Source: https://digitaleconomy.stanford.edu/wp-content/uploads/2025/11/CanariesintheCoalMine_Nov25.pdf
  - Version: August 2026; 140 pages；140 页。
  - Original filename: `CanariesintheCoalMine_Nov25.pdf`；SHA-256: `c8d2e5c4ccc0de7ef977c191c144726d6073e164b33f30397fcb0090165d2bdf`。
  - Status: saved；2026-10-28 取得。
  - 版本与解释边界：旧 2025/11 URL 实际返回 August 2026 正文（140 页），不可当成 2025 归档；官方当前 PDF https://digitaleconomy.stanford.edu/app/uploads/2026/08/Canaries_August2026.pdf
- [Measuring AI Ability to Complete Long Software Tasks](references/Measuring_AI_Ability_to_Complete_Long_Software_Tasks.pdf)
  - Source: https://arxiv.org/pdf/2503.14499v4
  - Version: arXiv:2503.14499v4, July 10, 2026；45 页。
  - Original filename: `2503.14499.pdf`；SHA-256: `29216eb3af4daa417666757a462ab7c7b5f8c18c188ee5a56e258b04116211f7`。
  - Status: saved；2026-10-28 从[既有归档](../../2680/readings/papers/Measuring_AI_Ability_to_Complete_Long_Software_Tasks.pdf)复用并校验，不声称重新下载。
- [How Well Does Agent Development Reflect Real-World Work?](references/How_Well_Does_Agent_Development_Reflect_Real-World_Work.pdf)
  - Source: https://arxiv.org/abs/2603.01203
  - Version: 2603.01203v2；24 页。
  - Original filename: `2603.01203.pdf`；SHA-256: `3911d2d529c297fc8e00ab66a10b1f2a1084a8cade5e439849b648d56b7b6246`。
  - Status: saved；2026-10-28 取得。
- [CollabSkill: Evaluating Human-Agent Collaboration On Real-World Tasks](references/CollabSkill_Evaluating_Human-Agent_Collaboration_On_Real-World_Tasks.pdf)
  - Source: https://arxiv.org/abs/2606.09833
  - Version: 2606.09833v2；28 页。
  - Original filename: `2606.09833.pdf`；SHA-256: `ae47c83fbe88fb05e60809f061f6f7e05ed87967db3b7a079254b3f6e80703cc`。
  - Status: saved；2026-10-28 取得。
- [Efficient Test-Time Adaptation through Human-AI Interaction](references/Efficient_Test-Time_Adaptation_through_Human-AI_Interaction.pdf)
  - Source: https://arxiv.org/abs/2609.04141
  - Version: 2609.04141v1；30 页。
  - Original filename: `2609.04141.pdf`；SHA-256: `ad19a223bd6d9f92758c536e10d6c64821f4b38e8c11a9bba8d5613a4c229675`。
  - Status: saved；2026-10-28 取得。

## 数字与版本边界

- **METR**：约七个月翻倍指指定软件任务集的 50% 成功率、人类完成时长口径；不是 Agent 实际运行时间或就业替代速度。讲义含后续榜单模型，不能当作 2025 年首次论文实验。
- **GDPval**：全集 1,320 个任务，公开 gold 子集 220 个；主结果的专家偏好与自动 grader 的人类一致率是不同指标。
- **RLI**：归档的 v1 摘要最高端到端自动化率为 2.5%；讲义截图为后续榜单，不能将两版数字混用。
- **WORKBank**：46.1% 的口径是按任务平均意愿判断希望自动化的任务占比，不能改写为 46.1% 工作者希望失业或已可被替代。HAS 是所需人类参与程度，不是从低到高越优秀的评分。
- **GPTs are GPTs**：任务暴露使用等质量下节约时间的前瞻判断，不等于实际采用、净就业变化或因果替代率。
- **Canaries**：旧 `2025/11` URL 实际返回 2026 年 8 月 140 页新版。讲义第 60 页保留 2025 年图，中文讲解需区分旧图与新正文；本次没有取得与该旧图完全对应的 2025 历史 PDF。当前正文中的相关性不等于单独识别出 AI 的因果效果。

## 验证与保留限制

- 主讲义 62 页已全文提取并逐页目视核对；补充原文的实际阅读范围及最终讲解复读结果记录在课程根目录 [REVIEW.json](../REVIEW.json)。
- [原始文件检查记录](ORIGINAL_MATERIALS_VERIFICATION.json)覆盖本讲 10 份 PDF、470 页的逐页解析与哈希。3 份参考 PDF 有非致命解析告警；RLI、WORKBank 重新下载仍与原件逐字节一致，相关页和 TAHI 方法页已渲染抽查可读。保留诊断，不改写官方二进制文件，也不将解析成功称为所有原文的逐页人工精读。
- [VERIFICATION.json](../VERIFICATION.json) 检查本地链接、显式 PDF 页码、参考文件 SHA-256 与讲解审核记录；自动校验不证明研究结论或模型能力。
- 本轮没有下载视频、运行收费 API/GPU、复现论文模型实验或进行真实劳动市场因果分析；教学算例明确标为工程推导。

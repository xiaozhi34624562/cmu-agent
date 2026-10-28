# CMU 11-768 作业 3：Training Agents with Reinforcement Learning

- 官方仓库：[cmu-agents/assignment-3](https://github.com/cmu-agents/assignment-3)。
- 固定版本：[88d1b1fa2aea58938d6d251847ce5559c4ac6558](https://github.com/cmu-agents/assignment-3/tree/88d1b1fa2aea58938d6d251847ce5559c4ac6558)。提交时间：2026-10-25 21:07:03 -04:00；该提交补充训练后 checkpoint 的 vLLM 评估脚本。
- 本地取得日期：**2026-10-28（Asia/Shanghai）**。完整保留该提交的 **59 个受版本管理的原始文件**及目录结构，没有嵌入 `.git`。
- [官方课程作业入口](https://www.cmu-agents.com/#/assignments)列出的截止日期为 **Thu, Oct 29, 2026**；网页没有在该字段注明时区，不擅自换算为北京时间，也不替代 Canvas 的提交要求。
- 本目录是官方 **starter code 归档**，不是完成的作业答案。`TODO(student)` 与 `NotImplementedError` 是待实现题目，原样保留。

## 阅读与运行入口

| 材料 | 用途 |
|---|---|
| [README.md](README.md) | 官方环境、目录结构、运行与恢复说明 |
| [ASSIGNMENT.md](ASSIGNMENT.md) | Part 0–5、背景、实验对照、提交要求与评分 |
| [pyproject.toml](pyproject.toml)、[uv.lock](uv.lock) | 官方依赖；Tinker SDK 固定为 0.24.0 |
| [data/README.md](data/README.md) | 固定数据集及来源说明，不重新生成或改写 |
| [configs/required_runs.yaml](configs/required_runs.yaml) | 七个规定实验及对应配置 |
| [tests/](tests/) | 官方离线公开测试，含环境、接口和训练控制约定 |
| [skyrl_tinker_modal/README.md](skyrl_tinker_modal/README.md) | 自托管训练后端与 vLLM 评估部署说明；本次没有运行部署 |
| [归档阅读提示](ARCHIVE_NOTES.zh-CN.md) | 中文入口、易混淆口径及本次核验边界 |

作业依次要求处理轨迹和 advantage、实现同步 REINFORCE/GRPO、实现带过期轨迹处理的异步 GRPO，做 Number Search 消融，最后训练与评估 TextCraft-Synth。作业指定的学生实现范围为六个文件；本次仅归档，没有填入解答或提交到外部平台。

请从**本作业目录**按官方 README 创建独立环境。README 推荐 Python 3.12，`pyproject.toml` 接受 Python ≥3.11；不要把整个学习资料库当成这个 Python 项目。官方说明的训练时间、费用和服务版本是该快照条件下的估计，本次未验证云端价格或训练耗时。

## 原件、版本与验证

- [SNAPSHOT.json](SNAPSHOT.json)：官方仓库、固定提交、取得日期、原始文件清单、大小和 SHA-256。
- [CHECKSUMS.sha256](CHECKSUMS.sha256)：59 个官方文件的逐文件校验值，不包含本资料库另加的说明与验证记录。
- [VERIFICATION.json](VERIFICATION.json)：原件字节、Python 语法、文件链接及数据集结构的实际检查。
- [BASELINE_TESTS.json](BASELINE_TESTS.json)：未完成 starter code 的公开测试实测，明确正常通过与学生待实现失败。

在资料库根目录运行 `python3 tools/verify_assignment3_archive.py --write-report` 可重复结构检查。公开测试依赖和命令以官方 README 为准；测试通过只说明它覆盖的契约，不代表隐藏测试通过或训练效果成立。

`SOURCES.md`、`ARCHIVE_NOTES.zh-CN.md`、`SNAPSHOT.json`、`CHECKSUMS.sha256`、`VERIFICATION.json` 与 `BASELINE_TESTS.json` 是本资料库新增的归档辅助文件，不冒充官方提交。原件未发现传输损坏；未验证 GPU、Modal、Tinker 后端、真实模型 tokenizer、训练结果、模型导出或课程评分。

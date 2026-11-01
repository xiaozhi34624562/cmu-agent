# HW1：Building an Agentic Harness

本目录归档 Stanford CS329Z Fall 2026 官方作业 1 的原始 starter；不包含作业答案。

| 资料 | 本地入口 |
|---|---|
| 官方作业正文，Version 26.1.0，26 页 | [cs329z_assignment1_harness.pdf](upstream/cs329z_assignment1_harness.pdf) |
| 原始安装与使用说明 | [README.md](upstream/README.md) |
| Python 环境与依赖 | [pyproject.toml](upstream/pyproject.toml)、[uv.lock](upstream/uv.lock) |
| 学生实现的适配接口 | [adapters.py](upstream/cs329z_hw1/adapters.py) |
| 官方测试与数据契约 | [tests/](upstream/tests/)、[types.py](upstream/cs329z_hw1/types.py) |
| 压缩邮件数据及官方校验信息 | [emails.jsonl.gz](upstream/data/emails.jsonl.gz)、[source.json](upstream/data/source.json) |
| 官方许可证 | [MIT LICENSE](upstream/LICENSE) |
| 来源版本及逐文件校验值 | [SNAPSHOT.json](SNAPSHOT.json) |
| 本次真实检查结果 | [BASELINE.json](BASELINE.json) |

## 来源与版本

- 上游：https://github.com/cs329z/assignment1-harness 。
- 固定提交：`c6cab03d161e4e8db8a9e2c12caf8e353b079beb`。
- 原始归档：https://codeload.github.com/cs329z/assignment1-harness/tar.gz/c6cab03d161e4e8db8a9e2c12caf8e353b079beb 。
- 获取元数据、归档 SHA-256 和 `upstream/` 的 109 个原文件校验值见 `SNAPSHOT.json`；原始层级、许可证、测试、样例配置和压缩数据均保留。

## 作业主线与学习入口

handout PDF 第 1–7 页介绍目标、环境、模型调用接口、测试和数据；第 23–25 页说明模拟用户评测、field notes、design memo 和提交要求。

Part 1 从邮件优先级分类、日报、BM25 检索和多跳邮件问答开始。Part 2 将这些组件封装为 Cardinal 内部助手的工具，逐步构建工具注册与文本协议、Agent 循环、文档检索、终端使用、上下文压缩、跨会话记忆、人工批准与 guardrails。作业要求不用 Agent 框架，并保持官方依赖与接口约束；具体规则以 handout 与适配接口为准。

数据包含虚构公司 Cardinal Energy 的文档和 Enron 邮件切片，二者不是同一公司或同一时期的数据。官方邮件归档含 26,278 条记录，并加入少量合成 needles；不要把模拟公司的政策当作真实制度，也不要把合成记录当作原始 Enron 事实。来源范围见 handout 第 5–6 页。

学习时先阅读手册、对应 adapter 的契约和该题测试，再在独立工作副本中实现。课程资料归档中的 `upstream/` 保持固定快照，学习实现应放在另外的工作目录。

## 实际验证与运行限制

- 109 个原文件与快照记录逐一核对一致；45 个 Python 文件通过 AST 语法解析。
- `data/emails.jsonl.gz` 的大小和 SHA-256 与官方 `source.json` 一致；流式解压检查得到 26,278 行有效 JSON，未将展开后的 58 MB 数据写入归档。
- 实际运行了 `tests/test_priority.py` 的 25 个 deterministic cases，均在未实现的 `run_priority` 处抛出预期的 `NotImplementedError`。这是未经修改的 starter 基线，不能解释为已完成作业或通过功能测试。
- 测试命令为 `python3 -m pytest tests/test_priority.py -m 'not live' -q -p no:cacheprovider --tb=short`，从 `upstream/` 执行；设置 `PYTHONDONTWRITEBYTECODE=1` 与 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`，未改变原始文件集合。
- 本次未执行完整测试套件、live tests、终端沙箱任务、模拟用户评测或真实模型调用；未安装依赖、创建 `.env` 或填写密钥。当前检查环境缺少 NumPy、OpenAI client 与 python-dotenv，具体限制见 `BASELINE.json`。

官方 README 中的 `uv run python data/download.py` 会校验并展开数据，`uv run pytest` 默认运行 deterministic tests；在独立工作副本中使用这些命令。`-m live` 会调用外部模型，不能把静态检查或 scripted tests 等同于模型效果复现。

# 第 5 课代码：Frameworks & Orchestration

官方演示以日历工具 `tinycal` 为贯穿案例，分别展示 DSPy 的 signatures / modules / optimizers / agents、LangGraph 的节点与条件边，以及 Temporal 的持久工作流、Activity 重试和计时。课程讲解入口见[第 5 课](../../5.FrameworksOrchestration/SOURCES.md)。

| 资料 | 本地入口 |
|---|---|
| 官方使用说明 | [README.md](upstream/README.md) |
| 课堂演示 notebook | [lecture5.ipynb](upstream/lecture5.ipynb) |
| 依赖和锁文件 | [pyproject.toml](upstream/pyproject.toml)、[uv.lock](upstream/uv.lock) |
| 日历工具及服务 | [tinycal/](upstream/tinycal/) |
| 50 条合成邮件与生成脚本 | [emails.json](upstream/data/emails.json)、[make_emails.py](upstream/data/make_emails.py) |
| LangChain 缓存示例 | [llm_cache.py](upstream/llm_cache.py) |
| 官方许可证 | [MIT LICENSE](upstream/LICENSE) |
| 固定版本与逐文件校验 | [SNAPSHOT.json](SNAPSHOT.json) |
| 本次检查结果 | [BASELINE.json](BASELINE.json) |

## 来源与版本

- 官网代码入口：https://github.com/cs329z/lecture5-frameworks 。
- 固定提交：`4e418289b3032cb960984250395525eb91ae25c2`。
- 原始归档：https://codeload.github.com/cs329z/lecture5-frameworks/tar.gz/4e418289b3032cb960984250395525eb91ae25c2 。
- `SNAPSHOT.json` 记录实际获取元数据、归档校验值以及 `upstream/` 的 16 个原文件校验值；官方目录结构与 MIT 许可证保持原样。

## 使用方式与执行边界

官方项目要求 Python `>=3.12,<3.13`，依赖 DSPy、LangGraph、LangChain 和 Temporal 等组件；请以本快照的 `pyproject.toml` 与 `uv.lock` 为准，不与课程根目录的资料同步环境混装。

在独立工作副本中按 README 运行 `uv sync`，配置自己的示例环境变量，再逐格执行 notebook。官方 `setup.sh` 涉及依赖安装、API 密钥输入和编辑器启动；notebook 会启动日历服务，并可能下载 Temporal 开发服务二进制或调用外部模型。归档没有替用户执行这些步骤。

本次只做离线检查：16 个原文件校验一致，6 个 Python 文件通过 AST 语法解析；notebook 是 nbformat 4，共 70 格，其中 51 格为代码；合成邮件文件可解析且含 50 条记录。notebook、GEPA 优化、LangGraph Agent 和 Temporal 工作流均未运行，也未复现官方 README 中描述的费用或时长。

官方缓存示例、重试代码和已保存 notebook 输出用于阅读与教学；它们不构成本次实际成功运行或可靠性验证的证据。

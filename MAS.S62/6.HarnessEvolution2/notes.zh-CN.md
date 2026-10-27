# Week 6｜Harness evolution 2：从 Agent Loop 到可验证的多 Agent 演化

> **课程日期：**2026-10-14。**整理日期：**2026-10-26。  
> **主讲：**Paul Liang，*Multi-Agent Evolution*，40 页。**教程：**Ao Qu，*Harness Engineering*，47 页。  
> **编号说明：**官网 Week 6 的两份 PDF 都使用 Lecture 5；本文按同一次课整合，保留原始文件名。  
> **学习目标：**能够解释一个 Agent 的完整执行链，选择合适的扩展机制，并用受控实验判断多 Agent 与演化机制是否值得采用。

上一课问“什么状态可以积累，什么程序可以改变”。这一课把问题推进到实际运行：**模型给出动作后谁负责执行？错误怎样回到模型？工具、技能和子 Agent 怎样被发现与调用？多个 Agent 怎样共享信息而保持结果一致？**

本课将教程作为实现基础，将主讲义作为规划、协作和演化的主线。二者合起来说明：一个团队的系统效果同时依赖底座模型、单个 Agent 的运行机制、任务分解、协作结构和验证过程。增加角色名称或工具数量不足以回答这些问题。[T，pp.2–6、47](tutorials/harness%20engineering%20tutorial.pdf#page=2)；[L5，pp.3–8、19–31](slides/lec5%20-%20multi%20agent.pdf#page=3)

## 导读：怎样使用这篇讲解

- **第一次实现 Agent：**先读第 1–5 节，从循环、错误处理、工具和扩展机制建立运行模型。
- **已有 Coding Agent：**重点读第 6–9 节，检查上下文、缓存、计划、记忆、技能与权限的职责。
- **准备多 Agent：**读第 10–14 节，先判断任务依赖，再决定拓扑与协作协议。
- **已有实验结果：**用第 15–17 节检查预算、收益归因和失败定位。

**来源约定：**`L5` 表示主讲义，`T` 表示教程；页码统一为 PDF 实际页序。论文事实标注原文位置；“教学示例”“工程建议”“拟议实验”均为本文推导。没有运行模型或复现论文基准；唯一实际执行的本地样例只验证交接契约。

**版本约定：**教程中的模型、CLI、价格、工具行为和基准分数是课程快照。本文对 mini-swe-agent 额外核查教程指定的提交 `68d367b`；不把这些细节视为所有产品当前版本的承诺。[本课来源索引](SOURCES.md)

### 课程资料地图

| 资料位置 | 本文对应内容 | 辅助来源的分工 |
|---|---|---|
| T pp.3–15 | 单 Agent 循环、预算、异常和完成信号 | pinned mini-swe-agent 代码；ReAct 解释交互模式 |
| T pp.16–25 | 工具输入、输出、搜索、编辑和代码动作 | SWE-agent 的 ACI 实验；Toolformer/ToolLLM 区分训练和接口 |
| T pp.26–35 | Skill、MCP、Hook、Plugin、项目指令 | 以教程为版本化说明，避免混用职责 |
| T pp.36–42 | 上下文、缓存、计划文件和记忆 | 对照上一课 MEM1/CLM；不把不同机制都叫 memory |
| T pp.43–47 | 协作适用条件与运行边界 | Scaling Agent Systems、MAST 补实验与诊断 |
| L5 pp.7–18 | 计划表示、训练、校准、重规划和交互 | 按讲义论证结构解释，未取得原论文的数值不额外推广 |
| L5 pp.19–30 | 拓扑、协调者、结构与成本关系 | Scaling Agent Systems v3 的受控研究与预测局限 |
| L5 pp.31–39 | 多 Agent 演化、CORAL、共享记忆、heartbeat | CORAL §3–4；区分描述性轨迹与因果消融 |
| 课表阅读 | 工具学习、技能收益与失败模式 | Toolformer、ToolLLM、SkillsBench、Voyager、MAST |

---

## 1. Agent Loop：模型的建议怎样变成环境中的动作

### 1.1 从三次模型调用开始看

假设用户要求修复用户名验证器。一次可能的执行是：

```text
模型调用 1：提出读取验证器文件
Harness：检查并执行读取，返回内容
模型调用 2：提出修改表达式并运行测试
Harness：执行动作，返回退出码和测试输出
模型调用 3：判断测试结果，提出下一步或完成
```

模型生成的是动作意图或结构化调用；工具执行、输出采集和下一次调用由运行程序负责。ReAct 把 reasoning 与 acting 交织；教程第 5–7 页借此区分模型和 Harness 的职责。[T，pp.5–7](tutorials/harness%20engineering%20tutorial.pdf#page=5)；[ReAct，§2–3](references/ReAct_Synergizing_Reasoning_and_Acting_in_Language_Models.pdf#page=2)

**一个用户 turn 可以包含多次模型调用。** 若只按用户消息计数，就会低估工具链中的模型费用和延迟。一次模型回复可以请求多个工具，但它们怎样并发、能否写同一资源，仍由具体 Harness 的执行策略决定。

### 1.2 最小循环还缺什么

```python
while not finished:
    reply = model(context)
    action = parse(reply)
    result = execute(action)
    context = append(context, reply, result)
```

这段教学伪代码能表达信息流，但还不能支持可靠运行。需要补充预算、超时、格式错误、取消、权限、输出长度、完成判定、日志和恢复。重要的设计问题是这些条件发生时怎样转移状态，而不仅是加若干 `try/except`。

可以用以下状态理解一个执行者：

```text
Ready → ModelPending → ActionProposed → Validated → Executing
  ↑                                             ↓
  └──────────── ObservationRecorded ←───────────┘
                            ↓
                  Submitted / BudgetExceeded / Cancelled / Failed
```

状态图是本文教学模型。它帮助检查：某个异常是否会丢失日志、重复动作或错误终止。

### 1.3 完成信号只表示程序结束，不自动证明任务成功

教程中的 mini-swe-agent 使用特定输出标记触发提交。指定提交的 `has_finished()` 检查输出首行标记及返回码，再抛出 `Submitted`。这个机制结束循环，不能代替任务的隐藏测试或业务验收。[T，p.12](tutorials/harness%20engineering%20tutorial.pdf#page=12)；[源码：default.py](references/mini-swe-agent-68d367b/src/minisweagent/agents/default.py)

三件事应分开记录：模型声称完成、Harness 已提交、独立 verifier 判断成功。把 `Submitted` 直接记成 success，会让一个很稳定地提前停止的系统看起来成绩很好。

## 2. mini-swe-agent：小循环里的关键工程决定

### 2.1 为什么课堂先看一个简单实现

教程以 bash-only、线性历史和每动作一个子进程的实现展示核心链路。它不是在证明所有任务都只需要 bash，而是让我们能逐段看到模型输入、动作解析、环境执行与异常处理。[T，pp.9–14](tutorials/harness%20engineering%20tutorial.pdf#page=9)

源码被固定在 `68d367b`，而教程也注明代码是简化形式。阅读时优先理解不变量：预算在何处检查、模型输出如何解析、执行结果如何回传、哪些异常可恢复、哪些异常终止。不要把幻灯片上的函数签名直接当作跨版本 SDK 文档。

### 2.2 预算为什么要在调用前检查

指定提交的 `query()` 在每次调用前检查 `step_limit` 和 `cost_limit`，超过后进入终止异常。预算保护的是没有主动提交的长循环。[T，p.10](tutorials/harness%20engineering%20tutorial.pdf#page=10)；[default.py，query](references/mini-swe-agent-68d367b/src/minisweagent/agents/default.py)

这里有一个不能从教程简写中省掉的配置条件：源码只在 `0 < limit <= 已用量` 时终止，**0 表示关闭该限额**。归档 `AgentConfig` 的步数默认 0、费用默认 3 美元，而归档 `config/default.yaml` 将两者都设为 0。因而读取这份 YAML 运行时，并不会自动得到步数或费用上限；需要显式设置正数，并确认实际加载配置。只复制“每轮会检查预算”的伪代码，可能误以为运行已经受限。[default.py，AgentConfig/query](references/mini-swe-agent-68d367b/src/minisweagent/agents/default.py)；[default.yaml，step_limit/cost_limit](references/mini-swe-agent-68d367b/src/minisweagent/config/default.yaml)

但调用前检查通常只能依据已知费用；下一次调用本身可能使总费用越过阈值。工程上还需要最大输出、子 Agent 预算分配、工具执行费用、总墙钟时间和并发预留。父 Agent 不能把自己最后一份预算同时分配给多个孩子，否则各子任务都在局部预算内，汇总却已经超支。

### 2.3 格式错误是可修复反馈，预算耗尽是终止条件

mini-swe-agent 要求动作满足特定格式；没有或出现多个匹配动作时返回 `FormatError`。`run()` 将非终止异常写入消息历史，让模型修正；提交或超预算则结束运行。[T，pp.10、13](tutorials/harness%20engineering%20tutorial.pdf#page=10)；[default.py，run/parse_action](references/mini-swe-agent-68d367b/src/minisweagent/agents/default.py)

工程上可把错误再细分：

| 错误 | 通常处理方式 | 需要避免的后果 |
|---|---|---|
| 输出格式错误 | 反馈格式要求并有限重试 | 无限重复同一格式错误 |
| 参数不合法 | 返回字段与修正办法 | 只返回“失败”，迫使模型猜测 |
| 临时服务不可用 | 有限重试，保留幂等键 | 重复执行已成功的有副作用动作 |
| 执行超时 | 收集部分输出，检查残留进程 | 假设一定没有发生修改 |
| 预算耗尽/取消 | 终止并保存进度 | 继续让模型尝试规避限制 |
| 环境损坏 | 隔离任务并恢复环境 | 把它作为模型推理失败统计 |

这张表是通用运行设计建议；实际恢复是否安全取决于工具语义。

### 2.4 子进程隔离简化了什么，又丢掉了什么

每次 `subprocess.run()` 能较明确地得到返回码和输出，减少长期 shell 的结束判定和污染问题；代价是上一个命令中的 `cd`、`export` 不自动成为下一个子进程的 shell 状态。[T，p.11](tutorials/harness%20engineering%20tutorial.pdf#page=11)；[local.py](references/mini-swe-agent-68d367b/src/minisweagent/environments/local.py)

但文件修改会留在工作目录中。**进程状态短暂不等于文件系统状态短暂。** 超时也不意味着没有副作用；一个测试脚本可能已经写了缓存，一个服务可能已经启动子进程。可恢复执行需要额外的进程组、工作区或容器管理，不能仅依赖 Python 函数返回。

### 2.5 观测输出是一种模型接口

教程展示长输出截断为头尾并告知遗漏，保留退出码，建议更精确的查询。这样的返回帮助模型选择下一步，而不是只让执行器得到一个完整字符串。[T，p.12](tutorials/harness%20engineering%20tutorial.pdf#page=12)；[default.yaml](references/mini-swe-agent-68d367b/src/minisweagent/config/default.yaml)

截断规则也有任务偏好：编译错误可能在中部，表格可能需要全部行，头尾摘要不总够用。工程建议返回原始输出的可定位文件、总长度、截断标记、可分页读取入口与本次关键字段。模型收到“没有发现错误”和“错误区域没显示”是不同状态。

### 2.6 人类反馈怎样进入下一步

交互 Agent 可以在动作前要求用户确认。拒绝不是让模型继续假装执行，而是把“未执行”及用户理由写入下一次输入。[T，p.15](tutorials/harness%20engineering%20tutorial.pdf#page=15)；[interactive.py](references/mini-swe-agent-68d367b/src/minisweagent/agents/interactive.py)

这说明人类反馈需要执行语义：用户没有同意、命令执行失败、命令执行后结果不满意，应是不同事件。外循环学习如果把“用户拒绝安装依赖”误写为“安装命令报错”，会诱导出错误修复策略。

## 3. 工具设计：让模型能选、能用、能判断结果

### 3.1 工具描述本身参与推理

工具名、描述、参数 schema 和结果进入模型输入，影响动作选择。教程用编辑工具说明：匹配范围、空白、唯一性和失败返回都应写进契约。[T，pp.18–19](tutorials/harness%20engineering%20tutorial.pdf#page=18)

一个好的工具接口至少回答：用途与不适用情况、输入单位/格式、输出字段、分页/截断、副作用、权限、失败类型与恢复建议。把外部 API 文档完整复制成工具描述，可能增加负担而没有增加决策信息。

### 3.2 搜索结果应支持选择下一步

教程引用 SWE-agent 的 ACI 实验：模仿人类编辑器逐条“下一项”的搜索方式，会消耗多次交互；汇总定位结果能让 Agent 先决定读哪一段。结果与论文中的模型、SWE-bench Lite 和动作预算相关。[T，p.23](tutorials/harness%20engineering%20tutorial.pdf#page=23)；[SWE-agent，§5.1，pp.5–7、表3](references/SWE-agent_Agent-Computer_Interfaces_Enable_Automated_Software_Engineering.pdf#page=6)

Table 3 的实际结果是：汇总搜索解决率 18.0%，逐条搜索 12.0%，不额外提供搜索工具为 15.7%。逐条搜索甚至低于无搜索，支持的解释是这一接口诱导 Agent 把预算花在遍历匹配项。它没有证明 `grep` 或专用搜索工具哪一类永远更好；应比较它们让模型获得什么信息、为此消耗多少交互。[SWE-agent，Table 3、Figure 5，实际 PDF pp.6–7](references/SWE-agent_Agent-Computer_Interfaces_Enable_Automated_Software_Engineering.pdf#page=6)

教学工具返回：

```json
{
  "query": "ASCIIUsernameValidator",
  "matches": [{"path": "validators.py", "line": 18, "preview": "class ..."}],
  "total": 1,
  "truncated": false,
  "revision": "repo-rev-17"
}
```

`revision` 能防止后续读取或补丁发生在不同版本；`truncated` 表明“当前只看到部分”，而不是暗示不存在更多匹配。结果结构应围绕后续动作组织。

### 3.3 编辑工具的价值在于检查不变量

原始字符串替换、带上下文补丁和 shell 命令都能修改文件。它们的差异包括匹配唯一性、差异可审查性、原子性和回滚支持。某个工具返回退出码 0，只能表示程序按其定义结束；未必说明正确位置发生了预期修改。[T，pp.17、25](tutorials/harness%20engineering%20tutorial.pdf#page=17)

**工程建议：**编辑结果返回前后摘要、实际匹配数、文件版本和差异引用。若预期唯一匹配而实际匹配多个，应要求更精确上下文，而不是默默选择其中一个。模型可以提出修改，工具要保护它承诺的不变量。

### 3.4 工具少与工具多都不是目标

教程给出工具合并、工具搜索和动态发现的案例，并指出精简描述与 helpful errors 的作用。这些案例反映设计空间，不提供统一最优工具数量。[T，pp.20–24](tutorials/harness%20engineering%20tutorial.pdf#page=20)

工具很多时，发现成本和选择歧义增加；工具很少但只有一个全能 shell 时，模型需要承担更多语法、环境和安全判断。合理粒度取决于模型能力、任务可组合性、边界保证和调用成本。应比较具体接口在同任务下的无效调用、错误恢复、成功率和费用。

教程 pp.21–22 的 **工具搜索**给出第三种选择：Host 保留完整目录，模型起初只看到发现入口和少数常用工具；模型搜索能力后，Host 再展开匹配工具的完整定义。这与删除工具不同，也与 Skill 的按需读正文不同。它减少初始上下文，却新增了“先找到工具”的步骤；如果检索漏掉正确能力，后面的参数生成再好也没有用。诊断时应分别记录目录召回、工具选择、参数正确性与执行结果。[T，pp.21–22，按教程图解读](tutorials/harness%20engineering%20tutorial.pdf#page=21)

## 4. 代码行动、工具学习与 Harness 改进的边界

### 4.1 Bash 的表达能力与专用工具的保证

Bash/代码能够访问广泛能力并组合操作；专用工具可提供更窄的权限、更明确的输入输出和更强的编辑检查。教程用“广度与保证”解释为什么二者可以并存。[T，p.25](tutorials/harness%20engineering%20tutorial.pdf#page=25)

并发也应按资源语义决定。读取互不相关文件通常便于并行；两个编辑动作即使是“专用工具”，仍可能冲突；两个 bash 动作如果完全隔离，也可能安全并行。“某产品当前怎样调度”与“某类工具天生只能串行”必须分开。

### 4.2 Toolformer：模型学会何时调用，而非服务器自动变聪明

Toolformer 用少量工具示范引导模型提出调用，执行后用调用结果对后续预测的帮助进行筛选，再用插入调用的文本训练。它主要改变模型参数及工具使用行为。[TF，§2，pp.3–4](../readings/papers/Toolformer_Language_Models_Can_Teach_Themselves_to_Use_Tools.pdf#page=3)

筛选目标与下游业务目标也有差别：帮助预测后续文本，不自动等价于执行复杂事务正确、满足用户约束或在多步工具链中稳健。把它迁移到新任务，需要重新考虑训练信号是否覆盖真正的成功定义。

### 4.3 ToolLLM：工具目录、检索、路径数据和执行评价

ToolLLM 不只是把数万 API 放进 prompt。它包含工具/接口数据、API 检索、指令生成、多步解法路径，以及 ToolEval。DFSDT 允许探索和回退不同推理路径；真实 API 的可用性与评估本身也影响结果。[TL，§2–3，pp.3–7](../readings/papers/ToolLLM_Facilitating_Large_Language_Models_to_Master_16000+_Real-world_APIs.pdf#page=3)

工程启发是把链路拆开测：是否找到适合的 API、参数是否正确、服务是否可用、调用序列是否满足依赖、最终结果是否支持回答。一个全局成功率不能告诉你该换检索器、接口描述还是底座模型。

### 4.4 三类改进必须分别记录

| 干预 | 直接改变什么 | 评估时需要固定什么 |
|---|---|---|
| 修改工具描述/结果 | 模型当前看到的信息 | 模型、工具实际实现、预算 |
| 增加程序技能/控制规则 | 可复用动作与运行路径 | 模型、任务与环境版本 |
| 工具调用数据训练 | 模型参数与策略 | Harness、训练数据范围、推理预算 |

三种方法可以组合，但组合收益需要重新测量。不能把工具服务器升级后的成功率全部归给模型训练，也不能把模型升级后的收益全部归给 Harness。

## 5. Skills、MCP、Hooks、Plugins：四种扩展解决不同问题

### 5.1 Skill 是可发现、可加载的过程包

教程展示 `SKILL.md`、元数据和按需读取的脚本、参考文档、资源。渐进式披露把发现阶段的简短描述与实际使用阶段的详细说明分开。[T，pp.26–28](tutorials/harness%20engineering%20tutorial.pdf#page=26)

```text
技能描述 → 模型识别适用性 → 读取正文 → 必要时读取脚本/参考
         → 判断前置条件 → 执行 → 验证结果
```

**打包格式与加载机制是两个对象。** 文件格式正确，并不证明当前 Harness 会自动注入索引；模型看见描述，也不证明它会触发；正文被读取，也不证明脚本执行过。要衡量技能贡献，应记录发现、读取、调用和验证四个层次。

### 5.2 MCP 提供连接协议，Host 仍掌握任务循环

按教程的架构，Host 是运行 Agent 的应用；Host 为 server 建立 client，server 提供 tools/resources/prompts；双方按协议交换发现与调用消息。MCP 不替 Host 决定任务目标、工具选择或结果可信度。[T，pp.29–32](tutorials/harness%20engineering%20tutorial.pdf#page=29)

教程里的天气服务器代码是教学简化，SDK 类名和具体配置需按相应版本文档使用。理解时先跟踪四个边界：

1. server 声明了什么能力；
2. Host 将哪些能力暴露给模型；
3. 模型提出什么调用；
4. Host/client 怎样执行并回传结果。

远程服务正常返回 JSON，不意味着内容可靠。协议成功、工具成功和任务成功是不同判断。

### 5.3 Hook 把特定事件交给确定性程序

Hook 由 Harness 的生命周期事件触发，例如动作之前、之后或停止时执行程序；它不依赖模型“记得遵守一条文字规则”。但 Hook 自己需要正确的匹配范围、异常处理和阻断语义。[T，pp.33、35](tutorials/harness%20engineering%20tutorial.pdf#page=33)

“每次编辑后格式化”适合事件驱动执行；“如何审查金额解析边界”适合技能；“连接日历服务”适合外部工具连接。若只是希望文字建议一定执行，通常需要把可检查条件移到程序边界，而不只是把提示词写得更强硬。

### 5.4 Plugin 是分发与配置单位

Plugin 可以打包技能、工具连接、Hook 等。它解决共享安装和配置复用；被安装的组件仍分别承担各自的运行职责。[T，pp.34–35](tutorials/harness%20engineering%20tutorial.pdf#page=34)

跨仓库分发时应记录插件版本、组件版本和覆盖的配置。一个包更新后若同时改变技能和 Hook，行为回归需要能定位到具体组件。包数量与 Agent 能力没有直接的单调关系。

### 5.5 项目指令不等于执行器权限

教程把 `CLAUDE.md`/`AGENTS.md` 归入上下文指导。项目约定可以要求模型怎样工作，但外部程序仍需要负责权限、格式检查或资源隔离。[T，pp.26、35、45–46](tutorials/harness%20engineering%20tutorial.pdf#page=26)

工程判断时问：“如果模型忽略这段文字，系统还能在哪个边界阻止违规动作？”答案应落在工具执行、文件系统、网络、数据库或发布程序，而非只落在另一段更醒目的说明。

## 6. SkillsBench 与 Voyager：技能存在以后怎样证明有效

### 6.1 用同一任务的匹配条件比较技能贡献

SkillsBench 把技能作为独立评估对象：任务、容器、输入与 verifier 相同，比较无技能、人工整理技能，及单独报告的自生成技能条件。本文本地 PDF v4 的主聚合为 87 个任务、18 个模型/Harness 配置；任务宏平均通过率由 33.9% 到 50.5%，增益 16.6 个百分点，各配置增益为 4.1–25.7 个百分点。主聚合使用固定的每任务三次试验框架；自生成技能只在三个专用 Harness 配置中单独评价，不能当作与主聚合完全相同的 18 配置实验。具体汇总和不完整覆盖处理见 §4 与附录。[SB，§3–5、Table 2，pp.3–6](../readings/papers/SkillsBench_Benchmarking_How_Well_Agent_Skills_Work_Across_Diverse_Tasks.pdf#page=3)

这些数字应绑定版本，不能与旧版本或不同子集混用。读结果时要检查：任务宏平均、试验次数、超时/缺失处理、是否使用同一 verifier，以及“部分检查通过”与“任务通过”是否采用相同口径。

### 6.2 技能里的答案泄漏会破坏比较

如果技能直接包含本次任务的输出、特定文件名或参考解命令，增益可能来自答案传递而非可复用过程。SkillsBench 将任务构建、技能质量和泄漏审查作为重要部分。[SB，§3，pp.3–4](../readings/papers/SkillsBench_Benchmarking_How_Well_Agent_Skills_Work_Across_Diverse_Tasks.pdf#page=3)

工程上建议使用两个维度的测试：相同技能在新实例上是否有效，以及无关任务是否会被错误触发。技能的触发精度和覆盖率都需要测；只测“应该用技能”的任务，会漏掉错误调用带来的退化。

### 6.3 自生成技能没有收益时，怎样继续拆解

可能的问题包括：模型原有能力已覆盖技能内容；生成的步骤不正确；技能过长；触发描述不清；依赖缺失；当前模型不会稳定执行。应避免只用“自生成技能无效”终止分析。

可做三组诊断：人工整理内容与自生成内容在相同加载机制下比较；固定内容而改变自动/强制加载；固定加载而比较不同执行模型。它们分别检查内容、选择和使用能力，而非把所有差异归给一份技能文本。

### 6.4 Voyager 展示了积累循环，但任务分布也在变化

Voyager 中自动课程产生任务，Agent 生成和修正程序，反馈与验证帮助筛选技能，再由技能库支持新任务。Minecraft 的交互与自动课程环境构成方法的重要前提。[V，§2，pp.3–5](../readings/papers/VOYAGER_An_Open-Ended_Embodied_Agent_with_Large_Language_Models.pdf#page=3)

移植到工程任务时，需要定义哪些练习会产生有用的可复用程序，以及自动任务是否仍覆盖真实需求。探索新技能与提高指定业务任务的成功率可以是两个不同目标，应分别报告。

## 7. 上下文与缓存：管理模型实际能看到的状态

### 7.1 少量高信号信息怎样进入上下文

教程列出截断、掩蔽旧观察、摘要、外置文件和子 Agent 隔离。它们压缩或转移不同的信息，错误方式也不同。[T，pp.36–38](tutorials/harness%20engineering%20tutorial.pdf#page=36)

| 操作 | 保留/转移什么 | 典型故障 |
|---|---|---|
| 截断 | 固定窗口内片段 | 恰好删掉决定性错误 |
| 观察掩蔽 | 保留动作轨迹，减少旧工具结果 | 无法解释当前结论依据 |
| 摘要 | 提炼语义与进度 | 丢实体、版本、否定或未决项 |
| 外置文件 | 原件留在文件，输入只放指针/片段 | 指针过期、模型不再回读 |
| 子 Agent | 局部上下文隔离，只返回结果 | 关键证据和限制在汇总中丢失 |

这是机制差异表，不能据此断言某方法总最优。应看任务对原始细节的依赖以及是否允许回查。

### 7.2 Prompt caching 的工程约束

教程建议稳定静态前缀、工具顺序，并用时间戳和工具变动举例说明缓存失效。缓存机制和价格以服务版本为准；本文不使用幻灯片价格作为实时费用承诺。[T，p.37](tutorials/harness%20engineering%20tutorial.pdf#page=37)

建议分别记录逻辑输入长度、缓存命中、实际计费和调用延迟。把短小但每轮变化的字段放在很早的位置，可能影响后面的前缀复用；但是否命中还受服务端缓存粒度、有效期和实现影响。

对上一课 CLM，更要注意中间编辑与重新 prefill。一个方法在应用层 token 更少、缓存更差时，总成本可能上升；一个方法输入更长但稳定复用，也可能相对经济。应以实测计费与任务质量共同判断。

### 7.3 计划文件与记忆文件为何要分开

教程把 Plan Mode 解释为同一模型和循环中的状态切换：增加规划指令、调整可执行动作，再通过计划文件交接到执行阶段。Memory 则保存跨会话需要再次加载的约定与经验。[T，pp.39–41](tutorials/harness%20engineering%20tutorial.pdf#page=39)

计划是“接下来做什么”，记忆是“以后可能需要知道什么”。计划中的临时猜测不应自动变为长期事实；任务已完成的步骤也不应永远占用项目指令。恢复长任务时，需要当前目标、已完成证据、未决项、下一步和当前版本，而非只保留一段通用总结。

### 7.4 子 Agent 返回值是信息压缩接口

子 Agent 的完整上下文通常不会自动返回主 Agent；返回摘要会丢掉信息。因此输出契约至少应包含结论、证据位置、版本、假设、未完成部分和建议动作。[T，pp.42–44](tutorials/harness%20engineering%20tutorial.pdf#page=42)

“分析完成，没问题”无法支持独立复核。若子 Agent 读取了某版本代码，返回值必须标明版本；主 Agent 在另一版本上集成时需要重新确认。隔离上下文有助于减少噪声，不能消除信息交接责任。

## 8. 权限和执行边界：自改进不能改写自己的评分规则

教程用“读取不可信内容、访问敏感信息、向外发送”组合解释数据外泄路径，并区分应用权限规则与操作系统沙箱。[T，pp.45–46](tutorials/harness%20engineering%20tutorial.pdf#page=45)

学习时需要保留这个具体攻击路径的条件；移除其中某项能够阻断该路径，不代表系统的所有攻击都消失。对于自演化系统，还要单独规定可修改对象：候选可以改自己的技能或控制逻辑，不能顺便改隐藏测试、评测器、审计记录和资源上限。

**工程建议：**将候选工作区、评测器和发布版本分开；评测器从候选之外读取，输出原始检查结果。Hook 可以帮助执行应用规则，沙箱在更低层限制资源，两者与模型遵循文字指令承担不同职责。安全边界应当在模型提出错误动作时仍可检查和阻断。

这与研究效率直接相关：若候选能通过修改 verifier 获得高分，外循环会优化错误目标。所谓“模型发现了更好的解法”必须由未被候选改动的评价过程支持。

## 9. 规划：任务分解必须追踪真实环境反馈

### 9.1 什么情况下提前规划有用

主讲义从三个问题展开：计划何时有用、如何表示、何时生成和修改。它比较了提示式分解、规划/执行模型分工、训练规划器、校准和重规划。[L5，pp.7–18](slides/lec5%20-%20multi%20agent.pdf#page=7)

计划适合把跨阶段目标和约束显式化，但会产生错误承诺。如果关键前提尚未被观察，长计划可能建立在猜测上。一个可执行计划应标明：已知信息、待核实前提、步骤依赖、成功条件与重新规划触发条件。

### 9.2 文本分解与环境动作不是同一种对象

Least-to-Most 等提示分解可以先解决子问题，再利用结果；对于会改变环境的任务，执行一个动作后可能已不能回到原状态。讲义用这一差别引出 replanning。[L5，pp.9–10、16](slides/lec5%20-%20multi%20agent.pdf#page=9)

教学例子：搜索和阅读可以在新信息到来后重做；提交订单、数据库迁移或对外发送则不能简单当作可撤销草稿。计划里应把观察步骤、候选修改、验证和正式提交分开；“稍后重试”必须说明环境是否被恢复。

### 9.3 规划器与执行器分工为什么有时有效

主讲义展示高层计划与低层动作分工，包括视觉任务中的目标理解和坐标动作。专门的执行接口可以降低高层模型承担的细节负担；代价是规划器与执行器之间可能丢失约束。[L5，pp.11–14](slides/lec5%20-%20multi%20agent.pdf#page=11)

例如“找最低和最高价格”不能只交给执行者一句“查看第一项”。应明确排序方向、价格字段、币种、过滤条件、缺失数据和证据要求。计划质量需要以执行后的任务结果衡量，而非只看语言是否流畅。

训练一个规划器与用强模型写计划也不同。讲义涉及合成计划和监督训练；需要分别核对教师、执行者、环境和训练/测试任务划分，不能把架构分工收益全部归给模型更大。

### 9.4 校准与重规划：承认什么时候还不知道

讲义使用多次采样计划估计不确定性的例子，并强调通过实际执行获得反馈。[L5，pp.15–18](slides/lec5%20-%20multi%20agent.pdf#page=15)

工程上可以把分歧作为追加观察的线索，但“多个计划相同”不证明计划正确；同一模型可能共享系统性误解。决定是否探索时，应估计观察能否区分关键假设，以及探索动作本身的成本和副作用。

一个实用的重规划触发器是：当前状态不满足下一步前置条件；新反馈推翻关键假设；预算不足以完成剩余路径；或者独立验证发现此前步骤无效。触发器应由实际观察或明确条件支持，避免只在模型“感觉需要”时才恢复。

## 10. 多 Agent 拓扑：先画依赖图，再决定角色

### 10.1 可以并行的是任务，不是角色名字

主讲义第 19–24 页展示多种协作结构及中央协调者的作用。教程也用独立阅读和耦合修改说明协作边界。[L5，pp.19–24](slides/lec5%20-%20multi%20agent.pdf#page=19)；[T，pp.43–44](tutorials/harness%20engineering%20tutorial.pdf#page=43)

```text
适合并行读取：
  入口代码分析 ─┐
  历史问题分析 ─┼→ 一名集成者核对版本、形成补丁、统一验证
  测试边界分析 ─┘

高度依赖的执行：
  观察页面 → 执行动作 → 页面改变 → 再次观察 → 下一动作
```

第二条链如果被分给几个持有不同页面状态的执行者，局部动作可能各自合理而全局冲突。并发数量应服从状态依赖与工作区所有权。

讲义 p.22 的 MACU 架构图展示一种具体调度方式：Manager 先形成任务依赖 DAG，只启动前置条件已满足的节点；各 CUA 子 Agent 使用各自的虚拟机，完成后进入跟进循环，由 Manager 判断继续还是结束，并按反馈更新 DAG。这里“并行”来自就绪节点和隔离环境；“规划”则在执行结果回来后持续修订，不是一开始列出所有角色就让它们永远各跑各的。[L5，p.22，按讲义架构图解读](slides/lec5%20-%20multi%20agent.pdf#page=22)

### 10.2 四类协作结构如何取舍

| 结构 | 信息如何流动 | 优点 | 必须付出的代价 |
|---|---|---|---|
| Independent | 各自求解，最后聚合 | 有独立探索机会，调度简单 | 重复劳动；聚合难判断谁对 |
| Centralized | 协调者分配、收集、验证 | 有统一任务状态与汇总点 | 协调者瓶颈、信息压缩损失 |
| Decentralized | Agent 之间互相交流 | 适合并行探索与共享发现 | 交流成本、错误扩散、难以终止 |
| Hybrid | 层级协调加局部互联 | 可适配复杂任务 | 更多状态、调度和归因复杂度 |

这些结构与论文中的 canonical architectures 对应，表中的工程取舍是机制分析。[SAS，§3.1、§4.1，pp.6–7、10–12](../readings/papers/Towards_a_Science_of_Scaling_Agent_Systems.pdf#page=6)

### 10.3 Debate 的分歧如何形成价值

多 Agent debate 让不同实例提出和互相批评答案。它可能发现遗漏，也可能把一个正确的少数意见说服成多数错误。[L5，pp.20–21](slides/lec5%20-%20multi%20agent.pdf#page=20)

工程上需要明确：初始解是否独立、批评依据是什么、最终裁决是否能查询原始证据，以及额外轮数是否与单 Agent 多次采样公平比较。若所有角色只读取同一段有缺陷摘要，增加角色数量不会自动产生独立证据。

### 10.4 协调者需要哪种“强”

主讲义强调强协调者的重要性，也展示某些廉价协调者配合强执行者的有效配置。[L5，pp.24、29](slides/lec5%20-%20multi%20agent.pdf#page=24)

这不需要被化成一条“总用最贵模型当主管”或“总用便宜模型调度”的规则。协调难度取决于任务分解、冲突消解、证据整合和失败恢复；执行难度则取决于具体工具和推理。先测协调错误与执行错误各占多少，再分配能力预算。

## 11. Scaling Agent Systems：研究结论如何变成有限的选型依据

### 11.1 受控比较首先排除什么混杂

课程指定论文用多种任务、模型家族和拓扑进行受控评价，标准化工具、提示与计算配置，分析协调和任务结构的关系。本地 v3 摘要记录 260 种配置、6 类基准。[SAS，摘要、§4.1，pp.1、10–12](../readings/papers/Towards_a_Science_of_Scaling_Agent_Systems.pdf#page=1)

这类研究的重要性在于把架构效果与实现差异尽量分开。若多 Agent 系统同时获得更强模型、更多 token 和额外工具，而基线没有相应预算，很难知道收益来自哪里。

### 11.2 任务结构决定额外协作是否值得

讲义概括了可分解金融推理受益、顺序规划退化、工具复杂任务的协调开销，以及不同模型配置的成本差别。[L5，pp.25–29](slides/lec5%20-%20multi%20agent.pdf#page=25)

论文 v3 给出的相对变化范围包含可分解金融任务的 `+80.8%` 和顺序规划的 `-70.0%`；它们是具体设置相对基线的变化，不是百分点，更不是你自己的任务会取得的收益。[SAS，摘要、§4](../readings/papers/Towards_a_Science_of_Scaling_Agent_Systems.pdf#page=1)

需要问清：子任务能否独立获得正确证据？它们是否操作同一状态？输出能否无损合并？共同错误会不会在汇总中被验证？当强基线已能完成多数任务时，协作可能主要增加开销；这仍需实际测量。

### 11.3 “45% 阈值”不能变成生产规则

讲义第 29 页使用单 Agent 基线超过约 45% 时多 Agent 可能退化的概括。应把它放回原研究模型、任务、预算与拟合范围理解；不同任务的难度、指标和错误类型不能直接共用该阈值。[L5，p.29](slides/lec5%20-%20multi%20agent.pdf#page=29)；[SAS，§4.2–4.3，pp.14–19](../readings/papers/Towards_a_Science_of_Scaling_Agent_Systems.pdf#page=14)

工程上更可靠的做法是在自己的数据上画质量/成本前沿，按任务依赖分组，看哪些组能从协作中获得稳定增益。一个准确率值无法替代任务结构诊断。

### 11.4 87% 架构选择命中与性能预测精度是不同指标

讲义第 30 页提到选出最佳架构的比例。论文摘要同时报告整体交叉验证 `R²=0.373`，采用任务相关能力指标时为 `0.413`，以及在 held-out configurations 中最佳架构选择达到 87%。这些指标分别衡量连续性能拟合与架构选择，不能互相替代。[L5，p.30](slides/lec5%20-%20multi%20agent.pdf#page=30)；[SAS，摘要、§4.3](../readings/papers/Towards_a_Science_of_Scaling_Agent_Systems.pdf#page=1)

“预测最佳架构”不等于能精确预测任何新任务的成功率。把这个研究作为选型先验合理，把它直接当业务 SLA 则超出证据。

还要检查预测器输入在部署前能否取得：论文使用单 Agent 基线、协调开销、轨迹错误、消息密度与冗余等测量值，其中一些必须先运行或抽样观察才能得到。因而它更适合作为试运行后的测量式选型依据，不能只输入“模型名字、工具数量”就承诺获得同样的预测精度。[SAS，§3.2、§4.3，实际 PDF pp.8–9、15–19](../readings/papers/Towards_a_Science_of_Scaling_Agent_Systems.pdf#page=8)

### 11.5 一个简单成本与延迟模型

以下为教学估算：

$$
C_{\rm total}=C_{\rm coordinator}+\sum_i C_i+C_{\rm communication}+C_{\rm verification}+C_{\rm retry}.
$$

若子任务并行，墙钟时间近似由关键路径而非所有时间之和决定；但 API 排队、限流、合并和验证仍在关键路径上。完全互联的有向通信图中，每轮最多有 $n(n-1)$ 条点对点关系，通信量也取决于消息长度和轮数。

这不是经验缩放定律，只是提醒：Agent 数量同时改变计算、通信和状态空间。增加并发可能减少等待，也可能在相同总预算下削弱每个执行者的可用推理空间。

## 12. MAST：把失败从“模型不够聪明”拆成可定位问题

MAST 从多 Agent 轨迹归纳 14 类失败，分为系统设计、Agent 间错位和任务验证三组。六位专家先细读约 150 条轨迹并迭代分类；扩展的 MAST-Data 则有 1642 条，由带少量示例的 LLM 标注器进行规模化标注。论文报告该标注器与保留的人类标注的一致性为 κ=0.77；这不能等同于 1642 条均经同规模人工专家分析，也不保证新业务轨迹具有同样标注质量。[MAST，§3、图1、表1–2，pp.2–6](../readings/papers/Why_Do_Multi-Agent_LLM_Systems_Fail.pdf#page=2)

| 类别 | 典型表现 | 工程上优先检查 |
|---|---|---|
| 系统设计 | 不遵守任务/角色、重复步骤、历史丢失、不清楚终止 | 输入契约、状态、预算和角色冲突 |
| Agent 间错位 | 会话重置、未澄清、偏离任务、信息未传递/未采纳、推理动作不符 | 交接内容、证据版本、协调记录 |
| 任务验证 | 过早停止、验证不完整、验证错误 | 完成条件、验收器和原始结果 |

这是一种诊断语言，不是每条标签都具有独立因果解释。一次失败可以同时有多个标签：前面信息丢失导致误解，后面验证不完整又让错误被提交。仅统计最后一个可见错误，会错过更早的可修复断点。

**最小排查过程：**按时间找第一处已观察到的状态偏差，提出一个局部干预，从同一环境检查点重放。若修正交接后成功，可以说明该干预对该实例有帮助；还需要更多实例验证它是不是主导故障机制。

## 13. CORAL：让多个长期 Agent 共同探索和积累

### 13.1 演化对象不止角色 prompt

主讲义第 31 页把演化对象分为个体模型/上下文/Harness、团队角色与通信拓扑、共享记忆/工具/技能。CORAL 的路线是让长期运行的 Agent 在探索中通过共享记忆与异步协作积累发现。[L5，pp.31–33](slides/lec5%20-%20multi%20agent.pdf#page=31)；[CORAL，§3，pp.4–7](../readings/papers/CORAL_Towards_Autonomous_Multi-Agent_Evolution_for_Open-Ended_Discovery.pdf#page=4)

这比运行多份互不关联的随机搜索多了一条信息传播路径。检索历史尝试、读取别人的发现、使用共同技能，可能减少重复探索，也可能传播错误假设。因此共享库的证据、版本和评分来源都影响搜索质量。

### 13.2 从候选到反馈再到共享知识

教学记号：评估器对任务 $x$ 和候选 $y$ 返回评分与辅助反馈：

$$
E(x,y)=(s,f).
$$

Agent 可以读取历史候选及反馈，决定下一次尝试；把有用发现整理为 notes 或 skills；其他 Agent 再据此探索。论文将持续状态、异步执行和周期性干预结合，而非只用固定变异模板生成下一代。[CORAL，§3.1–3.3，pp.4–7](../readings/papers/CORAL_Towards_Autonomous_Multi-Agent_Evolution_for_Open-Ended_Discovery.pdf#page=4)

共享文件系统有三类对象：`attempts/` 保存候选和历史评价，`notes/` 保存观察、反思与失败经验，`skills/` 保存可复用流程和脚本。Agent 的本地上下文与修改工作区相互隔离，通过链接访问共享 hub；主要协作是读取和贡献这些文件，而非必有一位中央协调者逐轮分配角色。自主性体现为 Agent 可以决定检索哪个父候选、何时局部测试、何时提交评价以及留下什么知识；固定演化系统则把其中较多决定写进搜索规则。[CORAL，§3.2–3.3，PDF pp.4–6](../readings/papers/CORAL_Towards_Autonomous_Multi-Agent_Evolution_for_Open-Ended_Discovery.pdf#page=4)

工程上必须保留候选血缘、代码散列、评估环境、分数方向和失败原因。“更高分”在耗时或 cycles 指标中可能正好相反；每个任务都要声明比较函数。

### 13.3 Heartbeat 是调度触发，不是自动正确的反思

Heartbeat 给长期 Agent 周期性检查进度、重复和资源的机会。它可以促使重新探索或整理发现，但不会自动证明总结正确，也不能替代任务评估器。[L5，p.33](slides/lec5%20-%20multi%20agent.pdf#page=33)；[CORAL，§3](../readings/papers/CORAL_Towards_Autonomous_Multi-Agent_Evolution_for_Open-Ended_Discovery.pdf#page=5)

CORAL 具体分为三种：每次迭代的 **Reflect** 提醒记录观察，累计若干次评价后的 **Consolidate** 提醒整理 notes 并沉淀 skills，连续无改善后的 **Pivot** 提醒重新选择搜索方向。附录示例分别采用每个 Agent 每次评价、全局每 10 次评价、连续 5 次无改善触发；它们是归档实现的设置。触发时改变的是 Agent 上下文，模型仍须自己决定后续动作，不是确定性优化器自动完成策略切换。[CORAL，§3.3、Appendix C.1.2，PDF pp.6、17–18](../readings/papers/CORAL_Towards_Autonomous_Multi-Agent_Evolution_for_Open-Ended_Discovery.pdf#page=6)

频率过高会花费调用和打断有效工作；过低可能让 Agent 长时间重复。建议记录每次触发前后的动作变化和最终收益，而不只记录 heartbeat 次数。对运行系统来说，健康检查、资源回收和认知反思可以由不同机制承担。

### 13.4 共享候选与共享工作目录不是一回事

论文包含隔离工作空间、评估分离、资源和会话管理等保障。[CORAL，§3，pp.5–7](../readings/papers/CORAL_Towards_Autonomous_Multi-Agent_Evolution_for_Open-Ended_Discovery.pdf#page=5)

合理的共享对象可以是不可变候选、带版本的发现和经过验证的技能。让多个 Agent 任意修改同一份候选源码，会造成血缘和评分对应关系不清。应将“提出候选”“评估候选”“发布当前最好结果”分开；一次运行评分必须绑定实际执行的代码散列。

### 13.5 如何读收益与版本差异

讲义第 35 页写 8 个任务的新最好结果，第 36 页展示 **Polyominoes（多格骨牌）装填**；这些图片用不同任务指标，不能相互换算。[L5，pp.34–37](slides/lec5%20-%20multi%20agent.pdf#page=34)

本地 CORAL v3 的摘要写 10 个任务，正文 Introduction p.3 又保留“8 of 11”的表述，讲义使用 8。本文保留这个文件内部的计数差异，不把它拼成一个确定的新统计；分析具体实验应回到对应表格、任务和版本。[CORAL，pp.2–3](../readings/papers/CORAL_Towards_Autonomous_Multi-Agent_Evolution_for_Open-Ended_Discovery.pdf#page=2)

同样，第 39 页关于跨 Agent 父代使用、成功比例和探索差异的观察，不能单独证明信息共享的因果收益：被选择复用的父代可能本来就更优。受控消融应在相同预算下去掉共享或改变协作机制，再看结果。[L5，pp.38–39](slides/lec5%20-%20multi%20agent.pdf#page=38)；[CORAL，§4](../readings/papers/CORAL_Towards_Autonomous_Multi-Agent_Evolution_for_Open-Ended_Discovery.pdf#page=7)

论文还提供了比轨迹相关性更强的对照：Table 3 固定 Claude Code + Opus 4.6，在三个任务上分别关闭 notes/skills 创建，以及比较四 Agent 共演化与四个独立单 Agent 的最佳结果。Kernel Engineering 中，有知识积累的单 Agent 为 1350 cycles，关闭后为 1601；四 Agent 共演化为 1103，独立 best-of-4 为 1180，越低越好。它支持这些设置中知识与共享机制有用；正文未为每项消融单独展开完全匹配 token/GPU 成本的账目，因此不应补写成“总成本完全相同的普遍因果结论”。[CORAL，§4.4.3、Table 3，PDF pp.9–10](../readings/papers/CORAL_Towards_Autonomous_Multi-Agent_Evolution_for_Open-Ended_Discovery.pdf#page=9)

比较单 Agent 与四 Agent 时还要保留预算和环境：数学/系统套件按 §4.1 使用墙钟预算，stress tests 则运行到收敛，评价次数不相同。Kernel Engineering 的 1350→1103 是相对单 Agent 的约 18.3% cycles 降低；不是 18.3 个百分点的正确率增益。Polyominoes 主表中无网络的结果是 80.2→84.2；讲义 p.36 的 89.4 是开启网络搜索的额外实验，不能与主表条件混用。[CORAL，§4.1、§4.3、Table 2，PDF pp.7–8](../readings/papers/CORAL_Towards_Autonomous_Multi-Agent_Evolution_for_Open-Ended_Discovery.pdf#page=7)

轨迹分析还有测量边界：论文的多样性用尝试标题中的策略关键词计算 Jaccard，Kernel Engineering 为 0.43，Polyominoes 为 0.31；这是策略词汇差异的代理指标，不等于严格测出了程序行为或搜索空间覆盖率。跨 Agent 父代与更高改善率、成员贡献平衡，属于解释系统运行方式的观察，应与上述消融证据分开读。[CORAL，§4.4.2，PDF p.9](../readings/papers/CORAL_Towards_Autonomous_Multi-Agent_Evolution_for_Open-Ended_Discovery.pdf#page=9)

### 13.6 怎样避免开放探索只优化评测漏洞

评估器应验证可行性和结果质量，并将两者分开记录。优化 kernel 时，运行更快但输出错误不能进入有效候选档案；优化解题过程时，读取了隐藏答案的结果也不能当方法改进。更新者可修改的文件范围与评估器可见范围应明确。

这类约束是演化实验可解释性的组成部分。若评价规则也发生改变，应建立新的实验版本，不能把旧分数和新分数直接放在同一进步曲线上。

## 14. 贯穿案例：修复用户名验证器，怎样合理分工

本节沿用教程的 Django 用户名末尾换行案例说明完整链路，但以下分工和契约是教学设计；没有运行 Django 基准或调用真实 Agent。[T，pp.14、17、40](tutorials/harness%20engineering%20tutorial.pdf#page=14)

### 14.1 先明确成功与修改范围

需求是末尾换行不应被合法用户名验证通过，同时保留原有 ASCII/Unicode 及字符集合要求。教学任务不能只说“把 `$` 改掉”：需要定位所有相关验证器、确认正则语义、更新回归测试并检查调用范围。

Python 正则中的 `$` 可以在字符串末尾的换行之前匹配；课程案例改用更严格的字符串边界。这个例子说明要验证的是业务行为，而不是完成一次文本替换。具体仓库还需依照它支持的 Python 版本和验证框架检查语义。

### 14.2 并行读取，一名集成者修改

```text
共同任务：拒绝用户名末尾换行；工作版本 rev17
  Reader A：查验证器实现，返回定义位置和相关规则
  Reader B：查测试和历史问题，返回边界输入及现有行为
  Integrator：核对两者版本与约束，形成单个补丁
  Verifier：从实际补丁独立运行指定测试并检查遗漏
```

并行部分共享同一只读版本。修改阶段由一名集成者负责，减少互相覆盖；Verifier 可以使用新上下文，但必须验证实际补丁，不能只认可集成者的文字说明。两个 Agent 如果分别修改 ASCII 和 Unicode 验证器，也需要明确文件所有权、合并和一致性检查，而不是默认彼此兼容。

### 14.3 一个可审查的交接对象

```json
{
  "task": "tests",
  "revision": "rev17",
  "conclusion": "需要覆盖末尾换行与原有合法字符",
  "evidence": ["tests/test_validators.py:12"],
  "unresolved": ["是否已有统一的Unicode边界测试"],
  "proposed_actions": ["加入非法输入回归样例", "复用现有合法输入测试"]
}
```

父 Agent 必须处理未决项，不能把“已返回结果”当作“已解决子任务”。证据引用、版本和范围是交接契约；具体结论仍需要回查。一个结构正确的 JSON 可以装着错误判断。

### 14.4 哪些改进可以持久化

这次执行后可以形成技能：“修改字符串校验规则时同时检查首尾边界、空字符串、换行和既有合法样例”。但技能应保留适用范围和验证步骤，不应硬编码本题文件路径或参考补丁。

若未来任务是多行文本解析，这条经验可能不适用。Skill 的发现描述要帮助区分用户名验证与其他正则任务。错误泛化应进入独立回归集，而不是通过增加更长指令掩盖。

### 14.5 可运行的交接检查样例

[handoff_contract.py](examples/handoff_contract.py) 使用标准库数据类检查任务集合、版本、证据是否缺失及未决项。整理时已运行：

```bash
python3 MAS.S62/6.HarnessEvolution2/examples/handoff_contract.py
```

输出 `PASS: paired handoff, stale/evidence/unresolved/incomplete rejection`。样例验证契约规则，不检查证据真实性，不证明两个 Agent 比一个更强，也不包含真实并行 API 调用。生产系统还需要取消、资源回收、证据存储和权限处理。

## 15. 实验设计：怎样证明多 Agent 或演化有贡献

### 15.1 先固定可比较的东西

建议固定模型版本、工具能力、代码/数据版本、每任务总预算、独立评估标准与最大执行时间。把主 Agent、子 Agent、共享上下文、验证与重试费用全部计入总账。模型配置不同的实验可以有价值，但需要作为异构系统比较，不能归因成纯拓扑收益。

### 15.2 建立能区分原因的对照

| 组别 | 主要变化 | 要回答的问题 |
|---|---|---|
| A 单 Agent 强基线 | 无分工 | 简单系统可达到什么水平 |
| B 单 Agent 增加采样/预算 | 更多计算 | 收益是否仅来自额外尝试 |
| C 独立并行 + 聚合 | 多路独立结果 | 并行探索是否有价值 |
| D 中央协调 | 增加分配和交接 | 分解与整合能否提升结果 |
| E 演化但不共享 | 每个 Agent 独立更新 | 个体积累有什么贡献 |
| F 演化并共享 | 共享记忆/技能/候选 | 协作信息是否带来额外收益 |

`E` 和 `F` 要比较等预算或明确报告预算差异。若共享组既有更多模型调用又有更长执行时间，就不能独立归因给共享。

### 15.3 结果与过程同时测

**结果：**完整任务成功、约束满足、质量分布、严重错误、无法完成比例。  
**过程：**子任务分解正确性、遗漏、冲突、证据覆盖、重复工作、协调轮数、无效调用、停滞。  
**成本：**总调用、输入/缓存/输出、工具费用、评测费用、墙钟延迟、并发峰值。  
**演化：**新任务迁移、学习前后回归、共享记录使用、候选选择和失效技能。

不要把某个过程指标直接当任务指标。少花 token 但遗漏需求，是另一种失败；更多交流但没有证据使用，也不是更充分的协作。

### 15.4 验证拓扑与验证共享应分开

如果任务本身高度并行，多路独立采样可能已经取得主要收益。要证明交流有用，可在相同初始 Agent 和预算下关闭交流；要证明记忆有用，可保留多 Agent 执行而关闭共享历史；要证明更新器有用，可使用冻结的技能库。

应同时检查不该共享的内容：其他任务的答案、隐藏标签、个人凭据或被错误标注为成功的尝试。共享的“知识”需要原始证据和适用范围，尤其不能让一次评测漏洞成为团队共同策略。

### 15.5 质量/成本前沿与不确定性

对不同任务组分别画或列表比较质量与费用，区分总体平均和关键任务回归。记录每个任务的重复次数、采样设置、失败/超时规则和结果波动。对于只有少量任务的结果，保留不确定性，不把一次最好运行外推成稳定优势。

演化实验还要公开总搜索预算和候选选择流程。最终最好候选的得分，与系统平均每次更新产生的收益，是不同统计对象。

## 16. 故障诊断速查

| 现象 | 可竞争的解释 | 怎样区分 |
|---|---|---|
| 所有角色同意错误答案 | 共同错误来源、缺乏独立证据、聚合偏好多数 | 隔离初始推理，要求原始证据，独立验证 |
| 子任务都成功，整体失败 | 依赖丢失、单位/版本冲突、需求覆盖不完整 | 对照父任务约束和交接契约 |
| 并发后更慢更贵 | 排队、限流、重复工作、合并和验证成本 | 调用树与关键路径、同预算单Agent对照 |
| 技能存在但效果不变 | 未发现、未加载、内容无用、不会执行 | 强制加载对照及实际调用轨迹 |
| 计划很完整但反复返工 | 早期假设错误、无观察更新、执行前提不满足 | 在关键步骤检查真实状态并触发重规划 |
| 一直重复相同工具调用 | 结果表达含糊、状态未持久化、终止条件不清 | 观察ID、预算检查、重复动作签名 |
| 候选分数突然大涨 | 真改进、评价漏洞、隐藏答案泄漏、环境变化 | 从受保护评测器和相同环境重跑 |
| 新版本只会完成旧任务 | 过拟合、检索答案、适用范围过窄 | 新实体/新仓库/新组合任务 |
| 子Agent完成后父Agent仍失败 | 交接缺证据、摘要失真、父Agent忽略结果 | 回查原件，比较直接提供结论与完整证据 |
| heartbeat变多但没改善 | 反思空转、反馈无信息、触发过频 | 检查触发后的策略变化及净成本 |

使用这张表时，不应把观察到的标签直接当原因。先找到能区分两种解释的最小试验，再扩大评测。MAST 的分类帮助组织问题，实际修复仍依赖具体代码、状态和证据。

## 17. 自测与答案

### 问题

1. `Submitted`、工具返回码 0 和任务成功有何区别？
2. 每动作新建子进程，为什么仍需要工作区隔离？
3. Skill 格式正确且被加载，为什么不能证明技能有效？
4. MCP server 能列出工具，是否表示模型能可靠使用？
5. 哪种任务适合先试独立并行，哪种应谨慎拆分？
6. 论文的 87% 架构选择命中为什么不等于 87% 的连续性能解释能力？
7. CORAL 中跨 Agent 候选表现更好，为什么单凭观察还不能归因给交流？
8. 怎样区分多 Agent 结构收益与更多 token 的收益？
9. 更新 Harness 时为什么不能允许它改 verifier？
10. 本文的本地样例没有验证什么？

### 参考答案

1. 三者分别表示循环终止、某工具按其定义结束、独立验收满足任务；任一前者都不能自动推出后者。
2. 进程局部状态可重置，但文件修改、外部服务和数据库副作用会保留。
3. 内容可能错误或不适用；加载后可能未遵循或未调用；还需新任务和匹配对照结果。
4. 发现协议成功不意味着选择、参数、服务、结果解释和任务验证全部成功。
5. 独立证据读取或可聚合搜索适合试并行；共享可变状态和强顺序依赖需要清楚的所有权与同步。
6. 前者是离散选择指标；R² 衡量连续拟合，二者定义和错误代价不同。
7. 复用父代可能已经经过选择，观察存在混杂；需要等预算关闭交流/共享的受控比较。
8. 以强单Agent和相同额外计算的基线作比较，并计入全部子Agent、通信与验证成本。
9. 否则优化器可能通过改变评分规则获得高分，破坏结果的可比性与真实性。
10. 没有调用模型、运行Django基准、证明并行加速或验证交接结论的真实性，只验证数据契约。

## 18. 本课总结：用执行证据连接个体与团队

从本课可以形成一条完整执行链：**目标与约束 → 上下文 → 模型动作 → 工具执行 → 环境反馈 → 状态更新 → 验证 → 可复用经验**。多 Agent 把其中一些环节分给不同执行者，也增加了交接、协调和全局验证的责任。

对 Senior AI Engineer，关键选择不是团队名字或框架名称，而是任务依赖、可变状态的所有权、证据能否回查、预算怎样分配，以及独立评估能否确认新增机制的净贡献。下一课改变模型参数时，应继续固定和记录这套运行机制，才能辨别参数学习和 Harness 改进各自的作用。

## 附录 A｜来源与版本

| 简称 | 本地与原始来源 | 使用范围 |
|---|---|---|
| L5 | [Multi-Agent Evolution，40页](slides/lec5%20-%20multi%20agent.pdf)，[原站](https://mit-mi.github.io/how2ai-course/fall2026/schedule/lec5%20-%20multi%20agent.pdf) | 全部教学内容 pp.3–40；pp.1–2为封面/公告 |
| T | [Harness Engineering，47页](tutorials/harness%20engineering%20tutorial.pdf)，[原站](https://mit-mi.github.io/how2ai-course/fall2026/schedule/harness%20engineering%20tutorial.pdf) | 循环、工具、扩展、上下文、协作和边界 |
| TF | [Toolformer，17页](../readings/papers/Toolformer_Language_Models_Can_Teach_Themselves_to_Use_Tools.pdf)，[v1](https://arxiv.org/abs/2302.04761v1) | §2，调用生成/筛选与训练 |
| TL | [ToolLLM，24页](../readings/papers/ToolLLM_Facilitating_Large_Language_Models_to_Master_16000+_Real-world_APIs.pdf)，[v2](https://arxiv.org/abs/2307.16789v2) | §2–3，API数据、检索、DFSDT与评价 |
| SB | [SkillsBench，42页](../readings/papers/SkillsBench_Benchmarking_How_Well_Agent_Skills_Work_Across_Diverse_Tasks.pdf)，[v4](https://arxiv.org/abs/2602.12670v4) | §3–5、附录，匹配条件、泄漏与指标口径 |
| V | [Voyager，42页](../readings/papers/VOYAGER_An_Open-Ended_Embodied_Agent_with_Large_Language_Models.pdf)，[v2](https://arxiv.org/abs/2305.16291v2) | §2，课程、技能库、反馈与验证 |
| CORAL | [CORAL，27页](../readings/papers/CORAL_Towards_Autonomous_Multi-Agent_Evolution_for_Open-Ended_Discovery.pdf)，[v3](https://arxiv.org/abs/2604.01658v3) | §3–4，执行/共享/heartbeat与结果；摘要和正文计数差异保留 |
| SAS | [Scaling Agent Systems，44页](../readings/papers/Towards_a_Science_of_Scaling_Agent_Systems.pdf)，[v3](https://arxiv.org/abs/2512.08296v3) | §3–4，控制变量、拓扑、指标与预测边界 |
| MAST | [Why Do Multi-Agent LLM Systems Fail?，47页](../readings/papers/Why_Do_Multi-Agent_LLM_Systems_Fail.pdf)，[v3](https://arxiv.org/abs/2503.13657v3) | §3、图1、表1，失败分类与标注范围 |
| ReAct | [ReAct](references/ReAct_Synergizing_Reasoning_and_Acting_in_Language_Models.pdf)，[arXiv](https://arxiv.org/abs/2210.03629) | §2–3，推理与环境行动交织 |
| SWE-agent | [ACI论文，118页](references/SWE-agent_Agent-Computer_Interfaces_Enable_Automated_Software_Engineering.pdf)，[v3](https://arxiv.org/abs/2405.15793v3) | §5.1、实际PDF pp.5–7及p.6 表3，搜索/编辑/上下文消融；附录未逐项使用 |
| mini | [default.py](references/mini-swe-agent-68d367b/src/minisweagent/agents/default.py)、[local.py](references/mini-swe-agent-68d367b/src/minisweagent/environments/local.py)、[config](references/mini-swe-agent-68d367b/src/minisweagent/config/default.yaml)、[interactive.py](references/mini-swe-agent-68d367b/src/minisweagent/agents/interactive.py) | 教程固定提交 68d367b 的原始源码摘取；详细URL见 REFERENCES.json |

CLI/MCP/Skill/Hook 的产品细节主要按教程快照解释；没有把当前 SDK 安装运行作为本课验证项目。原始链接和附加参考均见 [SOURCES.md](SOURCES.md)、[REFERENCES.json](REFERENCES.json)。

## 附录 B｜讲义中的容易误读处

- 教程的同模型不同 Harness、工具简化和单次轨迹案例，其任务和预算不同，不能汇总为一个统一增益。
- 教程第 14 页的任务费用和隐藏测试结果属于原课程记录，不是本文运行结果。
- 教程中的 prompt 长度、技能索引 token 和缓存价格是快照示例；接口和计费需要按实际版本核对。
- L5 第 29 页的约 45% 基线阈值不能作为跨任务定理；“便宜协调者”也不是所有团队的最优配置。
- L5 第 30 页的架构选择指标不等同于连续性能预测的 R²。
- CORAL 的摘要、正文与讲义任务计数存在差异；本文不补造一个统一计数，也不将跨候选观察当成因果消融。
- “在多个任务上有结果”“跨模型能加载”“跨环境真正泛化”是不同证据层次，应分别陈述。

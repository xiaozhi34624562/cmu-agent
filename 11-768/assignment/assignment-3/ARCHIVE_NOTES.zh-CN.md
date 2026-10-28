# 作业 3 归档阅读提示

本页是对固定提交 `88d1b1f` 的中文阅读指引，不改写[官方作业说明](ASSIGNMENT.md)，不提供学生待实现函数的答案。来源与校验见 [SOURCES.md](SOURCES.md)。

## 先辨认它在训练什么

`scottyrl` 把一次 Agent 与环境的交互保存为 `Trajectory`，保留每次模型调用的 prompt tokens、completion tokens、采样 logprob 和最终奖励。训练数据管线再把这些轨迹变成 `TokenSequence`，由同步或异步 trainer 交给 Tinker 兼容后端。原始接口见 [types.py](scottyrl/types.py)、[datagen.py](scottyrl/datagen.py)、[tinker_adapter.py](scottyrl/tinker_adapter.py)。

模型采样的动作 token 参与损失，环境 observation 和提示词不参与。长度为 $n$ 的 token 序列有 $n-1$ 个 next-token 目标：第 $j$ 个 mask 对应 `tokens[j+1]`。如果 prompt 长 $L$、completion 长 $c$，动作的目标位置是 `L-1 : L-1+c`。这是官方 Part 1 明确要求的对齐方式，不应把环境返回的文本也当成模型应学习生成的动作。

## 三个容易误读的实验口径

1. **这里的 GRPO 没有除以组内奖励标准差，也没有参考策略 KL 惩罚。** 官方作业使用 $A_i=r_i-\frac{1}{G}\sum_k r_k$，组内奖励全相同时不产生相对优势。不要直接套用其他论文中同名算法的全部实现细节。REINFORCE 的退化组比例应报告 N/A，不能将日志里的 0 当作其优势。
2. **异步的版本标记应在生成组之前固定。** 同组使用捕获的 `(policy, version)`；learner 消费时再判断 staleness。混用两个策略版本生成同一组，再只记录一个版本，会使过期判断失真。重要性权重还依赖与动作 token 正确对齐的采样 logprob。官方教学流程用 token ratio 和 clipping 控制偏差与波动；这不等于证明任意异步分布偏移被完全消除。
3. **Part 4.1 不是纯粹的组大小消融。** $G=1$ 的 REINFORCE 与 $G=2,8$ 的 GRPO 同时改变 advantage 规则和损失。Part 4.3 的 `iw` 是 PPO，`noiw` 是按 advantage 加权的 cross-entropy。报告结论必须保留这些条件，不能把多个变化归因于单一因素。

前两点的实现契约在 [ASSIGNMENT.md](ASSIGNMENT.md)、[异步 trainer 的 docstring](scottyrl/train/async_grpo.py)和[公开测试](tests/test_contracts.py)中；第 3 点在官方 Part 4 中明确说明。

## 两类任务及评估边界

Number Search 有 50,000 条训练任务、1,000 条验证任务；任务区间中有 $N=\text{high}-\text{low}+1$ 个整数，猜测上限是 $\lceil\log_2(N+1)\rceil$，包括最后一次猜中。无效调用也耗费步数。

TextCraft-Synth 有 852 条训练任务、213 条 medium 验证任务及 136 条 hard 验证任务，共用含 1,452 个物品的配方库。成功要求每个目标物品的“最终库存减初始库存”达到要求数量，并在预算内调用 `finish()`；不是库存里已有目标就自动成功。净增量条件见 [环境的 `_tool_finish`](scottyrl/envs/textcraft/env.py) 及[公开环境测试](tests/test_envs.py)。`num_craft_steps` 是数据元信息，不能直接当成本次 Agent 实际调用次数；是否在步数内可解还需要按环境的批量制作语义验证。本次检查了所有记录的数量、ID、引用物品、正整数数量和 Number Search 的范围/预算，没有证明每条 TextCraft 任务可解。

官方 Part 5 要分别比较微调模型和基础模型在 medium/hard 两个验证集上的 `success_rate`、`pass@4`。测试代码中的 MockPolicy 是确定性的脚本策略，无法证明真实模型已学会使用工具。相关课程背景可回读[强化学习基础](../../9.TrainingRLBasics/SOURCES.md)、[进阶 RL](../../11.AdvancedRLAlgorithms/SOURCES.md)和[训练系统](../../12.TrainingRLSystems/SOURCES.md)。

## 本次检查与后续学习的分界

原件完整性与数据检查见 [VERIFICATION.json](VERIFICATION.json)，测试的实际环境、失败类型和范围见 [BASELINE_TESTS.json](BASELINE_TESTS.json)。官方 starter code 预留了训练方法，公开测试出现相应 `NotImplementedError` 是作业初始状态，不能通过删除测试、改写原件或填入答案来声称归档验证通过。

本次没有启动 GPU、部署训练服务、上传模型或运行七个规定实验。若继续完成作业，应先在本作业的独立环境中实现 Part 1–3，通过公开测试，再按官方短探针步骤检查日志与轨迹；完整训练结果和报告需要另行实际运行。

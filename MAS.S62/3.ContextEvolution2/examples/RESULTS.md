# 教学实验运行记录

- 运行日期：2026-10-26（Asia/Shanghai）。
- 命令：`python3 MAS.S62/3.ContextEvolution2/examples/bin_packing_lab.py`。
- 解释器：Python 3.11.10；依赖：标准库。
- 返回码：0。
- 验证范围：只比较人工写定的四个标量启发式；校验容量、物品守恒、NaN拒绝和开发/独立数据分离。没有LLM调用、动态代码执行、岛屿搜索或论文复现。移位集合的物品分布与总量不同，不能仅凭跨分布箱数均值更低就宣称泛化改善。

## 实际标准输出

```json
{
  "scope": "hand-written policies; no LLM generation; no FunSearch reproduction",
  "development": {
    "best_fit": {
      "mean_bins": 23.96875,
      "max_bins": 29,
      "instances": 64
    },
    "worst_fit": {
      "mean_bins": 25.09375,
      "max_bins": 30,
      "instances": 64
    },
    "first_fit": {
      "mean_bins": 24.15625,
      "max_bins": 29,
      "instances": 64
    },
    "reserve_half": {
      "mean_bins": 25.09375,
      "max_bins": 30,
      "instances": 64
    }
  },
  "locked_policy": "best_fit",
  "independent_uniform": {
    "mean_bins": 23.6875,
    "max_bins": 28,
    "instances": 64
  },
  "shifted_small_and_large": {
    "mean_bins": 15.921875,
    "max_bins": 21,
    "instances": 64
  },
  "lecture_example_best_fit": [
    [
      6,
      3
    ],
    [
      5,
      2,
      2
    ],
    [
      2
    ]
  ]
}
```

输出是本地确定性教学实验的记录，不是课程论文中的模型实验结果。

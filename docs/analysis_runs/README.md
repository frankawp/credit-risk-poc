# Analysis Runs

这个目录用于归档每一轮分析或实验的过程信息和结果摘要，便于后续追溯。

建议按日期或阶段建立子目录，例如：

- `2026-03-19_phase1_baseline/`
- `2026-03-21_velocity_tuning/`
- `2026-03-25_graph_features/`

每次分析目录下建议至少包含：

- `run_summary.md`
  本次目标、范围、输入、方法和结论
- `artifacts.md`
  关键输出文件索引
- `decisions.md`
  本次做出的实现和口径决策
- `open_questions.md`
  当前遗留问题和下一步方向

如果某次分析需要额外图表、表格或导出的摘要，也应放在对应 run 目录下，而不是散落在根目录。

---
name: feature-mining-selection-interpreter
description: 当用户想解释为什么某个特征被保留、被删除、被相关组代表吸收，或想理解当前筛选规则与去相关逻辑时使用。
---

# 特征筛选解释

全程使用中文。

## 什么时候用

- 用户问“为什么这个特征被删了”
- 用户问“为什么保留这个代表特征”
- 用户想理解当前评分卡、去相关结果和基础过滤结果

## 先读什么

- `../feature-mining-orchestrator/references/selection_logic.md`
- 必要时再读取：
  - `outputs/selection/feature_scorecard.csv`
  - `outputs/selection/correlation_groups.csv`
  - `outputs/selection/dropped_by_basic_filters.csv`

## 约束

- 解释必须基于现有产物，不要发明不存在的 drop reason。
- 对高相关变量，优先说明“被哪个代表特征吸收”。
- 对规则型变量，区分“覆盖率低”和“完全无用”。

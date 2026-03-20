---
name: feature-mining-results-navigator
description: 当用户想查看 outputs 里的产物、理解 viewer 展示、查询特征注册表，或解释某个组合特征的来源与公式时使用。
---

# 结果导航与解读

全程使用中文。

## 什么时候用

- 用户问“这个结果怎么看”
- 用户问“某个特征是什么意思”
- 用户要在候选池、注册表、组合说明表、筛选结果之间定位信息

## 先读什么

- `../feature-mining-orchestrator/references/outputs_map.md`
- 如需解释特征，再读 `../feature-mining-orchestrator/references/implemented_features.md`
- 对组合特征，优先读取：
  - `outputs/candidate_pool/registry/feature_registry.csv`
  - `outputs/candidate_pool/registry/composite_feature_spec.csv`

## 约束

- 先说明产物在流程中的位置，再解释内容。
- 如果看到抽样和全量口径不一致，必须提醒用户。
- 对组合特征必须说明：公式、基础变量、业务含义。

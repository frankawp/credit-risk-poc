# 输出目录地图

## candidate_pool

- `outputs/candidate_pool/auto/auto_feature_matrix.parquet`
  - 自动特征矩阵

- `outputs/candidate_pool/auto/auto_feature_defs.csv`
  - 自动特征名清单

- `outputs/candidate_pool/semantic/semantic_feature_matrix.parquet`
  - 语义特征矩阵

- `outputs/candidate_pool/semantic/semantic_feature_registry.csv`
  - 语义特征注册表

- `outputs/candidate_pool/composite/composite_feature_matrix.parquet`
  - 组合特征矩阵

- `outputs/candidate_pool/registry/composite_feature_spec.csv`
  - 组合特征说明表，优先用于解释组合特征

- `outputs/candidate_pool/registry/feature_registry.csv`
  - 候选池总注册表

- `outputs/candidate_pool/candidate_pool.parquet`
  - 合并后的候选池宽表

- `outputs/candidate_pool/candidate_pool_summary.json`
  - 候选池摘要

## selection

- `outputs/selection/feature_scorecard.csv`
  - 单变量评分卡

- `outputs/selection/correlation_groups.csv`
  - 去相关结果

- `outputs/selection/dropped_by_basic_filters.csv`
  - 基础过滤淘汰原因

- `outputs/selection/selected_features.parquet`
  - 最终入选变量宽表

- `outputs/selection/feature_selection_report.json`
  - 筛选摘要

## 口径提醒

- 当前仓库允许 `semantic_feature_matrix` 是全量，而 `auto/candidate_pool/selected` 是抽样
- 解释结果时必须显式提醒口径不一致，而不是静默对齐

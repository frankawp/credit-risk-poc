# Feature Selection Standard

## Selection Layers

1. Basic filters:
   - high missing
   - single value / near constant
   - high correlation
2. Univariate effectiveness:
   - ROC-AUC
   - PR-AUC
   - Recall@TopK
   - Top decile lift
3. Group-wise retention:
   - retain representative in correlated groups
4. Stability checks:
   - split consistency
   - drift checks

## Output Artifacts

- `selected_features.parquet`
- `feature_scorecard.csv`
- `correlation_groups.csv`
- `feature_selection_report.md`
- `feature_selection_report.json`

## Decision Principle

Apply one policy for all sources, but keep source-aware thresholds:

- auto features: stricter redundancy and weak-signal filtering.
- semantic features: allow rule-value retention.
- composite features: stricter overfit control.

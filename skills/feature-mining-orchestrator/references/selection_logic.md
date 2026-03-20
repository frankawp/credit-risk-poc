# 当前筛选逻辑

当前实现是“基础过滤 + 单变量评估”，不是完整的时间稳定性体系。

## 基础过滤

配置来自 `SelectionConfig`：

- `missing_rate_threshold = 0.95`
- `correlation_threshold = 0.95`

基础过滤会删除：

- `high_missing_rate`
  - 缺失率超过阈值

- `near_constant`
  - 唯一值数小于等于 1

- `highly_correlated_with_<feature>`
  - 与前面某个数值特征的 Spearman 相关性过高

## 单变量评估

对每个特征计算：

- `univariate_roc_auc`
- `univariate_pr_auc`
- `recall_at_topk`
- `lift_top_decile`

当前阈值：

- `min_auc = 0.52`
- `min_ap_lift = 1.02`
- `topk_ratio = 0.10`

入选规则：

- `ROC-AUC >= 0.52`
  或
- `PR-AUC >= baseline_target_rate * 1.02`

未入选时，当前统一标记为：

- `weak_univariate_signal`

## 解释时的原则

- 只能基于 `feature_scorecard.csv`、`correlation_groups.csv`、`dropped_by_basic_filters.csv`
- 不要臆造“业务上肯定没用”这类结论
- 对高相关特征，优先解释“为什么被代表特征吸收”
- 对规则型特征，要区分“覆盖率低”和“没价值”不是一回事

# 筛选逻辑说明

当前实现是"基础过滤 + 单变量评估"，不是完整的时间稳定性体系。

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

- `univariate_roc_auc` - ROC 曲线下面积
- `univariate_pr_auc` - PR 曲线下面积
- `recall_at_topk` - Top-K 召回率
- `lift_top_decile` - Top 10% Lift 值
- `iv` - Information Value 信息价值

### IV 值解释

IV (Information Value) 衡量变量的预测能力：

| IV 范围 | 预测能力 |
|---------|----------|
| IV < 0.02 | 无预测能力 |
| 0.02 ≤ IV < 0.1 | 弱预测能力 |
| 0.1 ≤ IV < 0.3 | 中等预测能力 |
| IV ≥ 0.3 | 强预测能力 |

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
- 不要臆造"业务上肯定没用"这类结论
- 对高相关特征，优先解释"为什么被代表特征吸收"
- 对规则型特征，要区分"覆盖率低"和"没价值"不是一回事

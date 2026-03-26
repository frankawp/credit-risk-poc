"""
单变量评估器。

计算每个特征的单变量预测能力指标。
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _prep_score(series: pd.Series) -> pd.Series:
    """准备评分序列，处理缺失值和非数值类型。"""
    if series.isna().all():
        return pd.Series(np.zeros(len(series)), index=series.index)
    if pd.api.types.is_numeric_dtype(series):
        return series.fillna(series.median())
    # 分类变量编码
    coded = pd.Categorical(series.astype("object").fillna("MISSING")).codes.astype(float)
    return pd.Series(coded, index=series.index)


def _recall_at_topk(y_true: np.ndarray, scores: np.ndarray, topk_ratio: float) -> float:
    """计算 Top-K 召回率。"""
    n = max(1, int(len(scores) * topk_ratio))
    order = np.argsort(-scores)[:n]
    positives = y_true.sum()
    if positives == 0:
        return 0.0
    return float(y_true[order].sum() / positives)


def _lift_top_decile(y_true: np.ndarray, scores: np.ndarray) -> float:
    """计算 Top 10% 的 Lift 值。"""
    n = max(1, int(len(scores) * 0.1))
    order = np.argsort(-scores)[:n]
    baseline = y_true.mean()
    if baseline < 1e-9:
        return 1.0
    return float(y_true[order].mean() / baseline)


def _calculate_iv(
    x: np.ndarray,
    y: np.ndarray,
    n_bins: int = 10,
) -> float:
    """计算 IV (Information Value) 值。

    IV 值解释：
    - IV < 0.02: 无预测能力
    - 0.02 ≤ IV < 0.1: 弱预测能力
    - 0.1 ≤ IV < 0.3: 中等预测能力
    - IV ≥ 0.3: 强预测能力

    参数：
        x: 特征值数组
        y: 目标变量数组（0/1）
        n_bins: 分箱数量

    返回：
        IV 值
    """
    # 移除缺失值
    valid_mask = ~(np.isnan(x) | np.isnan(y))
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]

    if len(x_valid) == 0 or len(np.unique(x_valid)) < 2:
        return 0.0

    # 分箱
    try:
        # 使用等频分箱
        bins = np.percentile(x_valid, np.linspace(0, 100, n_bins + 1))
        bins = np.unique(bins)  # 去重，处理重复边界
        if len(bins) < 2:
            return 0.0

        # 确保边界覆盖所有值
        bins[0] = -np.inf
        bins[-1] = np.inf

        bin_indices = np.digitize(x_valid, bins[1:-1])
    except Exception:
        return 0.0

    # 计算每箱的好坏客户数
    total_good = (y_valid == 0).sum()
    total_bad = (y_valid == 1).sum()

    if total_good == 0 or total_bad == 0:
        return 0.0

    iv = 0.0
    for i in range(len(bins) - 1):
        mask = bin_indices == i
        if mask.sum() == 0:
            continue

        good_count = (y_valid[mask] == 0).sum()
        bad_count = (y_valid[mask] == 1).sum()

        # 计算占比
        good_rate = good_count / total_good
        bad_rate = bad_count / total_bad

        # 避免除零
        if good_rate < 1e-10:
            good_rate = 1e-10
        if bad_rate < 1e-10:
            bad_rate = 1e-10

        # 计算 WOE 和 IV
        woe = np.log(good_rate / bad_rate)
        iv += (good_rate - bad_rate) * woe

    return float(iv)


def evaluate_univariate(
    frame: pd.DataFrame,
    id_col: str,
    target_col: str,
    topk_ratio: float = 0.1,
    n_bins: int = 10,
) -> pd.DataFrame:
    """执行单变量评估。

    参数：
        frame: 特征矩阵
        id_col: ID 列名
        target_col: 目标列名
        topk_ratio: Top-K 比例（默认 0.1）
        n_bins: IV 计算的分箱数量（默认 10）

    返回：
        包含各特征评估指标的 DataFrame
    """
    # 延迟导入，避免强依赖
    from sklearn.metrics import average_precision_score, roc_auc_score

    y = frame[target_col].to_numpy()
    rows: list[dict[str, float | str]] = []

    for col in frame.columns:
        if col in {id_col, target_col}:
            continue

        x = _prep_score(frame[col]).to_numpy()

        # 常量变量
        if len(np.unique(x)) <= 1:
            rows.append({
                "feature_name": col,
                "univariate_roc_auc": 0.5,
                "univariate_pr_auc": float(y.mean()),
                "recall_at_topk": 0.0,
                "lift_top_decile": 1.0,
                "iv": 0.0,
            })
            continue

        try:
            # 双向评估（考虑正向和负向关联）
            auc_pos = roc_auc_score(y, x)
            auc_neg = roc_auc_score(y, -x)
            ap_pos = average_precision_score(y, x)
            ap_neg = average_precision_score(y, -x)

            # 选择效果更好的方向
            if ap_pos >= ap_neg:
                auc = auc_pos
                ap = ap_pos
                scores = x
            else:
                auc = auc_neg
                ap = ap_neg
                scores = -x

            recall = _recall_at_topk(y, scores, topk_ratio)
            lift = _lift_top_decile(y, scores)

            # 计算 IV 值
            iv = _calculate_iv(x, y, n_bins)

        except ValueError:
            auc = 0.5
            ap = float(y.mean())
            recall = 0.0
            lift = 1.0
            iv = 0.0

        rows.append({
            "feature_name": col,
            "univariate_roc_auc": float(auc),
            "univariate_pr_auc": float(ap),
            "recall_at_topk": float(recall),
            "lift_top_decile": float(lift),
            "iv": float(iv),
        })

    return pd.DataFrame(rows)

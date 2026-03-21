"""
基础特征过滤器。

执行缺失率过滤、常量变量过滤、高相关变量过滤。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FilterResult:
    """过滤结果。"""

    filtered: pd.DataFrame
    drop_report: pd.DataFrame


def apply_basic_filters(
    frame: pd.DataFrame,
    id_col: str,
    target_col: str,
    missing_rate_threshold: float = 0.95,
    correlation_threshold: float = 0.95,
) -> FilterResult:
    """应用基础过滤器。

    参数：
        frame: 特征矩阵
        id_col: ID 列名
        target_col: 目标列名
        missing_rate_threshold: 缺失率阈值（默认 0.95）
        correlation_threshold: 相关系数阈值（默认 0.95）

    返回：
        FilterResult 包含过滤后的数据和删除报告
    """
    keep = {id_col, target_col}
    drop_rows: list[dict[str, str]] = []
    out = frame.copy()

    feature_cols = [c for c in out.columns if c not in keep]

    # 1. 高缺失率过滤
    high_missing = [c for c in feature_cols if out[c].isna().mean() > missing_rate_threshold]
    for col in high_missing:
        drop_rows.append({"feature_name": col, "drop_reason": "high_missing_rate"})
    out = out.drop(columns=high_missing, errors="ignore")

    feature_cols = [c for c in out.columns if c not in keep]

    # 2. 近常量变量过滤
    single_value = [c for c in feature_cols if out[c].nunique(dropna=True) <= 1]
    for col in single_value:
        drop_rows.append({"feature_name": col, "drop_reason": "near_constant"})
    out = out.drop(columns=single_value, errors="ignore")

    feature_cols = [c for c in out.columns if c not in keep]

    # 3. 高相关变量过滤
    numeric_cols = [c for c in feature_cols if pd.api.types.is_numeric_dtype(out[c])]
    if numeric_cols:
        corr = out[numeric_cols].corr(method="spearman").abs()
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
        corr_drop: list[str] = []
        for col in upper.columns:
            high = upper.index[upper[col] >= correlation_threshold].tolist()
            if high:
                parent = high[0]
                corr_drop.append(col)
                drop_rows.append({"feature_name": col, "drop_reason": f"highly_correlated_with_{parent}"})
        out = out.drop(columns=corr_drop, errors="ignore")

    drop_report = pd.DataFrame(drop_rows)
    if drop_report.empty:
        drop_report = pd.DataFrame(columns=["feature_name", "drop_reason"])

    return FilterResult(filtered=out, drop_report=drop_report)

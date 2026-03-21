"""
高频申请主题特征 - Home Credit 案例示例

业务假设：
- 短期内高频申请暗示资金紧张
- 申请时间间隔越短，风险越高
- 征信查询次数是重要的多头借贷指标

依赖数据表：
- previous_application.csv (历史申请)
- bureau.csv (征信记录)
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _decision_gap_std(series: pd.Series) -> float:
    """计算决策时间间隔的标准差。"""
    values = np.sort(series.dropna().values)
    if len(values) < 3:
        return np.nan
    gaps = np.diff(values)
    if len(gaps) == 0:
        return np.nan
    return float(np.std(np.abs(gaps)))


def build_velocity_features(previous: pd.DataFrame, bureau: pd.DataFrame) -> pd.DataFrame:
    """
    构建高频申请主题特征。

    参数:
        previous: 历史申请表 (包含 SK_ID_CURR, DAYS_DECISION)
        bureau: 征信记录表 (包含 SK_ID_CURR, DAYS_CREDIT)

    返回:
        DataFrame，索引为 SK_ID_CURR，列为高频申请特征
    """
    # 历史申请频率
    prev = previous[["SK_ID_CURR", "DAYS_DECISION"]].copy()
    prev_agg = prev.groupby("SK_ID_CURR", as_index=False).agg(
        velocity_prev_count_7d=("DAYS_DECISION", lambda s: int((s >= -7).sum())),
        velocity_prev_count_30d=("DAYS_DECISION", lambda s: int((s >= -30).sum())),
        velocity_prev_decision_gap_std=("DAYS_DECISION", _decision_gap_std),
    )

    # 征信查询频率
    buro = bureau[["SK_ID_CURR", "DAYS_CREDIT"]].copy()
    buro_agg = buro.groupby("SK_ID_CURR", as_index=False).agg(
        velocity_bureau_recent_credit_count_30d=("DAYS_CREDIT", lambda s: int((s >= -30).sum())),
    )

    result = prev_agg.merge(buro_agg, on="SK_ID_CURR", how="outer")
    return result


# 变量说明
FEATURE_DESCRIPTIONS = {
    "velocity_prev_count_7d": {
        "hypothesis": "近7天申请次数越多，资金越紧张，风险越高",
        "expected_direction": "higher_is_riskier",
    },
    "velocity_prev_count_30d": {
        "hypothesis": "近30天申请次数越多，多头借贷风险越高",
        "expected_direction": "higher_is_riskier",
    },
    "velocity_prev_decision_gap_std": {
        "hypothesis": "申请时间间隔波动越大，申请行为越不稳定",
        "expected_direction": "higher_is_riskier",
    },
    "velocity_bureau_recent_credit_count_30d": {
        "hypothesis": "近30天征信查询次数越多，多头借贷风险越高",
        "expected_direction": "higher_is_riskier",
    },
}

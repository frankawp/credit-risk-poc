"""
一致性主题特征 - Home Credit 案例示例

业务假设：
- 工作年限与年龄的比例反映职业稳定性
- 联系方式完整性反映用户真实性
- 申请金额与获批金额的差距反映审批一致性

依赖数据表：
- application_train/test.csv (主表)
- previous_application.csv (历史申请)
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_consistency_features(app: pd.DataFrame, previous: pd.DataFrame) -> pd.DataFrame:
    """
    构建一致性主题特征。

    参数:
        app: 申请主表 (包含 SK_ID_CURR, DAYS_EMPLOYED, DAYS_BIRTH 等)
        previous: 历史申请表

    返回:
        DataFrame，索引为 SK_ID_CURR，列为一致性特征
    """
    base = app[["SK_ID_CURR"]].copy()

    # 工作年限与年龄比例（职业稳定性）
    employed = app["DAYS_EMPLOYED"].abs()
    birth = app["DAYS_BIRTH"].abs().replace(0, np.nan)
    base["consistency_employed_birth_ratio"] = employed / (birth + 1.0)

    # 联系方式完整性
    phone_cols = [c for c in ["FLAG_MOBIL", "FLAG_EMP_PHONE", "FLAG_WORK_PHONE"] if c in app.columns]
    if phone_cols:
        base["consistency_contact_flag_sum"] = app[phone_cols].fillna(0).sum(axis=1)
    else:
        base["consistency_contact_flag_sum"] = np.nan

    # 历史申请的一致性
    prev = previous[["SK_ID_CURR", "AMT_APPLICATION", "AMT_CREDIT", "NAME_CONTRACT_STATUS"]].copy()
    prev["credit_gap_ratio"] = (
        (prev["AMT_CREDIT"] - prev["AMT_APPLICATION"]).abs() / (prev["AMT_APPLICATION"].abs() + 1.0)
    )
    agg = prev.groupby("SK_ID_CURR", as_index=False).agg(
        consistency_prev_credit_gap_ratio_mean=("credit_gap_ratio", "mean"),
        prev_app_count=("AMT_APPLICATION", "count"),
        prev_status_unique=("NAME_CONTRACT_STATUS", "nunique"),
    )
    agg["consistency_prev_status_change_rate"] = agg["prev_status_unique"] / agg["prev_app_count"].replace(0, np.nan)
    agg = agg.drop(columns=["prev_app_count", "prev_status_unique"])

    return base.merge(agg, on="SK_ID_CURR", how="left")


# 变量说明
FEATURE_DESCRIPTIONS = {
    "consistency_employed_birth_ratio": {
        "hypothesis": "工作年限占年龄比例越高，职业越稳定，风险越低",
        "expected_direction": "lower_is_riskier",
    },
    "consistency_contact_flag_sum": {
        "hypothesis": "联系方式越完整，用户越真实，风险越低",
        "expected_direction": "lower_is_riskier",
    },
    "consistency_prev_credit_gap_ratio_mean": {
        "hypothesis": "申请与获批金额差距越大，审批一致性越差",
        "expected_direction": "higher_is_riskier",
    },
    "consistency_prev_status_change_rate": {
        "hypothesis": "历史申请状态变化越多，用户信用越不稳定",
        "expected_direction": "higher_is_riskier",
    },
}

"""
套现倾向主题特征 - Home Credit 案例示例

业务假设：
- ATM 取现比例高可能暗示套现行为
- 首期还款违约（FPD）是重要的风险信号
- 分期还款逾期比例反映还款意愿

依赖数据表：
- previous_application.csv (历史申请)
- credit_card_balance.csv (信用卡记录)
- installments_payments.csv (分期还款记录)
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_cashout_features(
    previous: pd.DataFrame,
    credit_card: pd.DataFrame,
    installments: pd.DataFrame,
) -> pd.DataFrame:
    """
    构建套现倾向主题特征。

    参数:
        previous: 历史申请表 (包含 SK_ID_PREV, SK_ID_CURR)
        credit_card: 信用卡记录表
        installments: 分期还款记录表

    返回:
        DataFrame，索引为 SK_ID_CURR，列为套现倾向特征
    """
    prev_map = previous[["SK_ID_PREV", "SK_ID_CURR"]].drop_duplicates()

    # ATM 取现比例
    card = credit_card[["SK_ID_PREV", "AMT_DRAWINGS_ATM_CURRENT", "AMT_DRAWINGS_CURRENT"]].copy()
    card["atm_ratio"] = card["AMT_DRAWINGS_ATM_CURRENT"] / (card["AMT_DRAWINGS_CURRENT"].abs() + 1.0)
    card = card.merge(prev_map, on="SK_ID_PREV", how="inner")
    card_agg = card.groupby("SK_ID_CURR", as_index=False).agg(
        cashout_atm_ratio_mean=("atm_ratio", "mean"),
    )

    # 首期还款表现
    inst = installments[
        ["SK_ID_PREV", "NUM_INSTALMENT_NUMBER", "DAYS_INSTALMENT", "DAYS_ENTRY_PAYMENT", "AMT_INSTALMENT", "AMT_PAYMENT"]
    ].copy()
    inst = inst.merge(prev_map, on="SK_ID_PREV", how="inner")
    inst["late_days"] = inst["DAYS_ENTRY_PAYMENT"] - inst["DAYS_INSTALMENT"]
    inst["late_flag"] = (inst["late_days"] > 0).astype(int)

    # 首期还款
    first = inst[inst["NUM_INSTALMENT_NUMBER"] == 1].copy()
    first_agg = first.groupby("SK_ID_CURR", as_index=False).agg(
        cashout_first_payment_delinquency_days_max=("late_days", "max"),
    )
    first_agg["cashout_fpd_severe_flag"] = (first_agg["cashout_first_payment_delinquency_days_max"] > 30).astype(int)

    # 整体逾期比例
    late_ratio = inst.groupby("SK_ID_CURR", as_index=False).agg(
        cashout_installments_late_ratio=("late_flag", "mean")
    )

    result = card_agg.merge(first_agg, on="SK_ID_CURR", how="outer").merge(late_ratio, on="SK_ID_CURR", how="outer")
    return result


# 变量说明
FEATURE_DESCRIPTIONS = {
    "cashout_atm_ratio_mean": {
        "hypothesis": "ATM取现比例越高，套现倾向越强，风险越高",
        "expected_direction": "higher_is_riskier",
    },
    "cashout_first_payment_delinquency_days_max": {
        "hypothesis": "首期还款逾期天数越长，还款意愿越差，风险越高",
        "expected_direction": "higher_is_riskier",
    },
    "cashout_fpd_severe_flag": {
        "hypothesis": "首期逾期超过30天是强风险信号",
        "expected_direction": "higher_is_riskier",
    },
    "cashout_installments_late_ratio": {
        "hypothesis": "分期还款逾期比例越高，还款习惯越差",
        "expected_direction": "higher_is_riskier",
    },
}

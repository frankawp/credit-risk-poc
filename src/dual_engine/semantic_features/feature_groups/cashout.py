from __future__ import annotations

import numpy as np
import pandas as pd


def build_cashout_features(
    previous: pd.DataFrame,
    credit_card: pd.DataFrame,
    installments: pd.DataFrame,
) -> pd.DataFrame:
    prev_map = previous[["SK_ID_PREV", "SK_ID_CURR"]].drop_duplicates()

    card = credit_card[["SK_ID_PREV", "AMT_DRAWINGS_ATM_CURRENT", "AMT_DRAWINGS_CURRENT"]].copy()
    card["atm_ratio"] = card["AMT_DRAWINGS_ATM_CURRENT"] / (card["AMT_DRAWINGS_CURRENT"].abs() + 1.0)
    card = card.merge(prev_map, on="SK_ID_PREV", how="inner")
    card_agg = card.groupby("SK_ID_CURR", as_index=False).agg(
        cashout_atm_ratio_mean=("atm_ratio", "mean"),
    )

    inst = installments[
        ["SK_ID_PREV", "NUM_INSTALMENT_NUMBER", "DAYS_INSTALMENT", "DAYS_ENTRY_PAYMENT", "AMT_INSTALMENT", "AMT_PAYMENT"]
    ].copy()
    inst = inst.merge(prev_map, on="SK_ID_PREV", how="inner")
    inst["late_days"] = inst["DAYS_ENTRY_PAYMENT"] - inst["DAYS_INSTALMENT"]
    inst["late_flag"] = (inst["late_days"] > 0).astype(int)
    first = inst[inst["NUM_INSTALMENT_NUMBER"] == 1].copy()

    first_agg = first.groupby("SK_ID_CURR", as_index=False).agg(
        cashout_first_payment_delinquency_days_max=("late_days", "max"),
    )
    first_agg["cashout_fpd_severe_flag"] = (first_agg["cashout_first_payment_delinquency_days_max"] > 30).astype(int)

    late_ratio = inst.groupby("SK_ID_CURR", as_index=False).agg(cashout_installments_late_ratio=("late_flag", "mean"))
    result = card_agg.merge(first_agg, on="SK_ID_CURR", how="outer").merge(late_ratio, on="SK_ID_CURR", how="outer")
    return result

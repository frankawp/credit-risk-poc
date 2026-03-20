from __future__ import annotations

import numpy as np
import pandas as pd


def build_consistency_features(app: pd.DataFrame, previous: pd.DataFrame) -> pd.DataFrame:
    base = app[["SK_ID_CURR"]].copy()
    employed = app["DAYS_EMPLOYED"].abs()
    birth = app["DAYS_BIRTH"].abs().replace(0, np.nan)
    base["consistency_employed_birth_ratio"] = employed / (birth + 1.0)

    phone_cols = [c for c in ["FLAG_MOBIL", "FLAG_EMP_PHONE", "FLAG_WORK_PHONE"] if c in app.columns]
    if phone_cols:
        base["consistency_contact_flag_sum"] = app[phone_cols].fillna(0).sum(axis=1)
    else:
        base["consistency_contact_flag_sum"] = np.nan

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

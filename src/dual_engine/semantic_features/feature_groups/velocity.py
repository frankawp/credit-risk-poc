from __future__ import annotations

import numpy as np
import pandas as pd


def _decision_gap_std(series: pd.Series) -> float:
    values = np.sort(series.dropna().values)
    if len(values) < 3:
        return np.nan
    gaps = np.diff(values)
    if len(gaps) == 0:
        return np.nan
    return float(np.std(np.abs(gaps)))


def build_velocity_features(previous: pd.DataFrame, bureau: pd.DataFrame) -> pd.DataFrame:
    prev = previous[["SK_ID_CURR", "DAYS_DECISION"]].copy()
    prev_agg = prev.groupby("SK_ID_CURR", as_index=False).agg(
        velocity_prev_count_7d=("DAYS_DECISION", lambda s: int((s >= -7).sum())),
        velocity_prev_count_30d=("DAYS_DECISION", lambda s: int((s >= -30).sum())),
        velocity_prev_decision_gap_std=("DAYS_DECISION", _decision_gap_std),
    )

    buro = bureau[["SK_ID_CURR", "DAYS_CREDIT"]].copy()
    buro_agg = buro.groupby("SK_ID_CURR", as_index=False).agg(
        velocity_bureau_recent_credit_count_30d=("DAYS_CREDIT", lambda s: int((s >= -30).sum())),
    )

    result = prev_agg.merge(buro_agg, on="SK_ID_CURR", how="outer")
    return result

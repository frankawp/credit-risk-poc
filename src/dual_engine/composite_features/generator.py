from __future__ import annotations

import pandas as pd


def build_composite_features(frame: pd.DataFrame) -> pd.DataFrame:
    base = frame[["SK_ID_CURR"]].copy()

    if "velocity_prev_count_7d" in frame.columns and "cashout_atm_ratio_mean" in frame.columns:
        base["composite_velocity_x_cashout"] = frame["velocity_prev_count_7d"].fillna(0) * frame["cashout_atm_ratio_mean"].fillna(0)

    if "consistency_prev_credit_gap_ratio_mean" in frame.columns and "velocity_prev_count_30d" in frame.columns:
        base["composite_consistency_velocity_flag"] = (
            (frame["consistency_prev_credit_gap_ratio_mean"].fillna(0) > 0.20)
            & (frame["velocity_prev_count_30d"].fillna(0) >= 3)
        ).astype(int)

    if "cashout_fpd_severe_flag" in frame.columns and "velocity_prev_count_7d" in frame.columns:
        base["composite_fpd_velocity_flag"] = (
            (frame["cashout_fpd_severe_flag"].fillna(0) == 1)
            & (frame["velocity_prev_count_7d"].fillna(0) >= 2)
        ).astype(int)

    return base

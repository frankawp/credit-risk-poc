from __future__ import annotations

import numpy as np
import pandas as pd


def time_diff(current: pd.Series, previous: pd.Series) -> pd.Series:
    return current - previous


def null_count(df: pd.DataFrame, columns: list[str]) -> pd.Series:
    return df[columns].isna().sum(axis=1)


def relative_ratio(numerator: pd.Series, denominator: pd.Series, fill_value: float = np.nan) -> pd.Series:
    denominator = denominator.replace({0: np.nan})
    ratio = numerator / denominator
    return ratio.fillna(fill_value)


def change_rate(values: pd.Series) -> float:
    clean = values.dropna().reset_index(drop=True)
    if len(clean) <= 1:
        return 0.0
    changes = (clean != clean.shift(1)).sum() - 1
    return float(max(changes, 0) / (len(clean) - 1))


def window_count(values: pd.Series, windows: list[int]) -> dict[str, int]:
    clean = values.dropna()
    return {
        f"count_{window}d": int(((clean <= 0) & (clean >= -window)).sum())
        for window in windows
    }


def group_risk(df: pd.DataFrame, group_cols: list[str], target_col: str = "TARGET") -> pd.DataFrame:
    grouped = (
        df.groupby(group_cols, dropna=False)[target_col]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "group_bad_rate", "count": "group_sample_count"})
    )
    grouped["group_risk_rank"] = grouped["group_bad_rate"].rank(method="dense", pct=True)
    return grouped

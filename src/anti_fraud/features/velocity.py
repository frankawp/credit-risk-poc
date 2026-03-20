from __future__ import annotations

import numpy as np
import pandas as pd

from anti_fraud.features.metadata import metadata_frame
from anti_fraud.operators import time_diff, window_count


FEATURE_METADATA = [
    {
        "feature_name": "recent_application_gap_min",
        "source_table": "previous_application",
        "business_definition": "历史申请间隔最小值，越小越像短期集中申请。",
    },
    {
        "feature_name": "recent_application_gap_std",
        "source_table": "previous_application",
        "business_definition": "历史申请间隔标准差，用于识别时间分布异常集中。",
    },
    {
        "feature_name": "recent_application_count_7d",
        "source_table": "previous_application",
        "business_definition": "过去 7 天申请数量。",
    },
    {
        "feature_name": "recent_application_count_30d",
        "source_table": "previous_application",
        "business_definition": "过去 30 天申请数量。",
    },
    {
        "feature_name": "burst_same_day_flag",
        "source_table": "previous_application",
        "business_definition": "单日申请次数达到阈值时标记。",
    },
    {
        "feature_name": "consecutive_application_flag",
        "source_table": "previous_application",
        "business_definition": "短期内存在连续密集申请时标记。",
    },
    {
        "feature_name": "bureau_recent_credit_count_7d",
        "source_table": "bureau",
        "business_definition": "近 7 天新增征信记录数量。",
    },
    {
        "feature_name": "bureau_recent_credit_count_30d",
        "source_table": "bureau",
        "business_definition": "近 30 天新增征信记录数量。",
    },
    {
        "feature_name": "bureau_active_credit_ratio",
        "source_table": "bureau",
        "business_definition": "活跃征信账户占比。",
    },
    {
        "feature_name": "bureau_inquiry_intensity",
        "source_table": "application_train",
        "business_definition": "短期征信查询强度加权分数。",
    },
    {
        "feature_name": "bureau_inquiry_spike_flag",
        "source_table": "application_train",
        "business_definition": "短期征信查询显著激增时标记。",
    },
]


def _gap_stats(series: pd.Series) -> pd.Series:
    ordered = series.dropna().sort_values()
    diffs = time_diff(ordered.shift(-1), ordered).abs().dropna()
    if diffs.empty:
        return pd.Series({"recent_application_gap_min": np.nan, "recent_application_gap_std": np.nan})
    return pd.Series(
        {
            "recent_application_gap_min": float(diffs.min()),
            "recent_application_gap_std": float(diffs.std(ddof=0)),
        }
    )


def build_velocity_features(
    application: pd.DataFrame,
    previous: pd.DataFrame,
    bureau: pd.DataFrame,
    inquiry_day_threshold: int,
    inquiry_week_threshold: int,
    burst_same_day_threshold: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    prev_group = previous.groupby("SK_ID_CURR")
    gap_stats = prev_group["DAYS_DECISION"].apply(_gap_stats).unstack()
    counts_7 = prev_group["DAYS_DECISION"].apply(lambda s: window_count(s, [7])["count_7d"]).rename("recent_application_count_7d")
    counts_30 = prev_group["DAYS_DECISION"].apply(lambda s: window_count(s, [30])["count_30d"]).rename("recent_application_count_30d")
    same_day_max = (
        previous.groupby(["SK_ID_CURR", "DAYS_DECISION"]).size().groupby("SK_ID_CURR").max().rename("same_day_application_max")
    )

    prev_features = pd.concat([gap_stats, counts_7, counts_30, same_day_max], axis=1).reset_index()
    prev_features["burst_same_day_flag"] = (prev_features["same_day_application_max"] >= burst_same_day_threshold).astype(int)
    prev_features["consecutive_application_flag"] = (
        (prev_features["recent_application_count_7d"] >= 3) | (prev_features["recent_application_gap_min"].fillna(999) <= 1)
    ).astype(int)

    bureau_agg = bureau.groupby("SK_ID_CURR").agg(
        bureau_recent_credit_count_7d=("DAYS_CREDIT", lambda s: int(((s <= 0) & (s >= -7)).sum())),
        bureau_recent_credit_count_30d=("DAYS_CREDIT", lambda s: int(((s <= 0) & (s >= -30)).sum())),
        bureau_active_credit_ratio=("CREDIT_ACTIVE", lambda s: float((s == "Active").mean())),
    )
    bureau_agg = bureau_agg.reset_index()

    app = application[
        [
            "SK_ID_CURR",
            "AMT_REQ_CREDIT_BUREAU_HOUR",
            "AMT_REQ_CREDIT_BUREAU_DAY",
            "AMT_REQ_CREDIT_BUREAU_WEEK",
        ]
    ].copy()
    app = app.fillna(0)
    app["bureau_inquiry_intensity"] = (
        app["AMT_REQ_CREDIT_BUREAU_HOUR"] * 3
        + app["AMT_REQ_CREDIT_BUREAU_DAY"] * 2
        + app["AMT_REQ_CREDIT_BUREAU_WEEK"]
    )
    app["bureau_inquiry_spike_flag"] = (
        (app["AMT_REQ_CREDIT_BUREAU_DAY"] >= inquiry_day_threshold)
        | (app["AMT_REQ_CREDIT_BUREAU_WEEK"] >= inquiry_week_threshold)
    ).astype(int)
    app = app[["SK_ID_CURR", "bureau_inquiry_intensity", "bureau_inquiry_spike_flag"]]

    features = app.merge(prev_features, on="SK_ID_CURR", how="left").merge(bureau_agg, on="SK_ID_CURR", how="left")
    features = features.drop(columns=["same_day_application_max"])
    numeric_cols = [col for col in features.columns if col != "SK_ID_CURR"]
    features[numeric_cols] = features[numeric_cols].replace([np.inf, -np.inf], np.nan)
    return features, metadata_frame(FEATURE_METADATA)

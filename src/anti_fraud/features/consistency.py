from __future__ import annotations

import numpy as np
import pandas as pd

from anti_fraud.features.metadata import metadata_frame
from anti_fraud.operators import change_rate, relative_ratio


FEATURE_METADATA = [
    {
        "feature_name": "emp_age_ratio",
        "source_table": "application_train",
        "business_definition": "工龄绝对值相对年龄绝对值的比率。",
    },
    {
        "feature_name": "employed_birth_inconsistency_flag",
        "source_table": "application_train",
        "business_definition": "工龄与年龄比异常或工龄出现特殊异常值时标记。",
    },
    {
        "feature_name": "phone_contact_coverage",
        "source_table": "application_train",
        "business_definition": "联系方式标识总和，反映联系方式覆盖度。",
    },
    {
        "feature_name": "phone_flags_sparse_flag",
        "source_table": "application_train",
        "business_definition": "联系方式覆盖过低时标记，作为身份稳定性代理特征。",
    },
    {
        "feature_name": "phone_flags_mismatch_score",
        "source_table": "application_train",
        "business_definition": "移动电话与工作电话标识的错配程度。",
    },
    {
        "feature_name": "document_core_missing_count",
        "source_table": "application_train",
        "business_definition": "核心身份证件缺失数量。",
    },
    {
        "feature_name": "document_noncore_count",
        "source_table": "application_train",
        "business_definition": "非核心身份证件提供数量。",
    },
    {
        "feature_name": "document_noncore_only_flag",
        "source_table": "application_train",
        "business_definition": "仅提供非核心证件而未提供核心证件时标记。",
    },
    {
        "feature_name": "days_id_publish_vs_registration_gap",
        "source_table": "application_train",
        "business_definition": "证件发布时间与注册时间的绝对偏差。",
    },
    {
        "feature_name": "prev_status_change_rate",
        "source_table": "previous_application",
        "business_definition": "历史申请状态切换率，作为历史申请行为一致性代理特征。",
    },
]


def build_consistency_features(
    application: pd.DataFrame,
    previous: pd.DataFrame,
    core_documents: list[str],
    contact_flags: list[str],
    employed_birth_ratio_threshold: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    app = application.copy()
    app["emp_age_ratio"] = relative_ratio(app["DAYS_EMPLOYED"].abs(), app["DAYS_BIRTH"].abs(), fill_value=0.0)
    app["employed_birth_inconsistency_flag"] = (
        (app["emp_age_ratio"] > employed_birth_ratio_threshold) | (app["DAYS_EMPLOYED"] == 365243)
    ).astype(int)
    app["phone_contact_coverage"] = app[contact_flags].fillna(0).sum(axis=1)
    app["phone_flags_sparse_flag"] = (app["phone_contact_coverage"] <= 1).astype(int)
    app["phone_flags_mismatch_score"] = (
        (app["FLAG_MOBIL"].fillna(0) - app["FLAG_CONT_MOBILE"].fillna(0)).abs()
        + (app["FLAG_EMP_PHONE"].fillna(0) - app["FLAG_WORK_PHONE"].fillna(0)).abs()
    )
    app["document_core_missing_count"] = len(core_documents) - app[core_documents].fillna(0).sum(axis=1)
    noncore_docs = [col for col in app.columns if col.startswith("FLAG_DOCUMENT_") and col not in core_documents]
    app["document_noncore_count"] = app[noncore_docs].fillna(0).sum(axis=1)
    app["document_noncore_only_flag"] = (
        (app[core_documents].fillna(0).sum(axis=1) == 0) & (app["document_noncore_count"] > 0)
    ).astype(int)
    app["days_id_publish_vs_registration_gap"] = (app["DAYS_ID_PUBLISH"] - app["DAYS_REGISTRATION"]).abs()

    prev_sorted = previous[["SK_ID_CURR", "DAYS_DECISION", "NAME_CONTRACT_STATUS"]].copy()
    prev_sorted = prev_sorted.sort_values(["SK_ID_CURR", "DAYS_DECISION"])
    prev_change = (
        prev_sorted.groupby("SK_ID_CURR")["NAME_CONTRACT_STATUS"]
        .apply(change_rate)
        .reset_index(name="prev_status_change_rate")
    )

    features = app[
        [
            "SK_ID_CURR",
            "emp_age_ratio",
            "employed_birth_inconsistency_flag",
            "phone_contact_coverage",
            "phone_flags_sparse_flag",
            "phone_flags_mismatch_score",
            "document_core_missing_count",
            "document_noncore_count",
            "document_noncore_only_flag",
            "days_id_publish_vs_registration_gap",
        ]
    ].merge(prev_change, on="SK_ID_CURR", how="left")
    features["prev_status_change_rate"] = features["prev_status_change_rate"].fillna(0.0)
    numeric_cols = [col for col in features.columns if col != "SK_ID_CURR"]
    features[numeric_cols] = features[numeric_cols].replace([np.inf, -np.inf], np.nan)
    return features, metadata_frame(FEATURE_METADATA)

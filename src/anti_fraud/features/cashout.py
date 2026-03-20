from __future__ import annotations

import numpy as np
import pandas as pd
from collections.abc import Iterable

from anti_fraud.features.metadata import metadata_frame
from anti_fraud.operators import group_risk, relative_ratio


FEATURE_METADATA = [
    {
        "feature_name": "atm_cashout_ratio_max",
        "source_table": "credit_card_balance",
        "business_definition": "ATM 取现相对应收总额的最大比率。",
    },
    {
        "feature_name": "atm_cashout_ratio_mean",
        "source_table": "credit_card_balance",
        "business_definition": "ATM 取现占比均值。",
    },
    {
        "feature_name": "atm_heavy_usage_months",
        "source_table": "credit_card_balance",
        "business_definition": "ATM 取现占比超过高风险阈值的月份数。",
    },
    {
        "feature_name": "credit_card_max_dpd_def",
        "source_table": "credit_card_balance",
        "business_definition": "信用卡账户最大逾期天数代理值。",
    },
    {
        "feature_name": "first_payment_delinquency_days",
        "source_table": "installments_payments",
        "business_definition": "首期还款逾期天数。",
    },
    {
        "feature_name": "fpd_severe_flag",
        "source_table": "installments_payments",
        "business_definition": "首期还款严重逾期时标记。",
    },
    {
        "feature_name": "installments_late_ratio",
        "source_table": "installments_payments",
        "business_definition": "历史还款记录中的逾期占比。",
    },
    {
        "feature_name": "max_days_past_due_installments",
        "source_table": "installments_payments",
        "business_definition": "历史分期最大逾期天数。",
    },
    {
        "feature_name": "org_region_bad_rate",
        "source_table": "application_train",
        "business_definition": "组织类型和区域人口分桶组合的坏账率。",
    },
    {
        "feature_name": "org_region_risk_rank",
        "source_table": "application_train",
        "business_definition": "组织类型和区域人口分桶组合的风险排名。",
    },
]


def build_cashout_features(
    application: pd.DataFrame,
    credit_card_balance: pd.DataFrame,
    installments: pd.DataFrame,
    heavy_atm_ratio: float,
    severe_fpd_days: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    ccb = credit_card_balance[
        [
            "SK_ID_CURR",
            "AMT_DRAWINGS_ATM_CURRENT",
            "AMT_DRAWINGS_CURRENT",
            "AMT_TOTAL_RECEIVABLE",
            "SK_DPD_DEF",
        ]
    ].copy()
    ccb["atm_cashout_ratio"] = relative_ratio(ccb["AMT_DRAWINGS_ATM_CURRENT"], ccb["AMT_TOTAL_RECEIVABLE"])
    ccb["atm_drawings_share"] = relative_ratio(ccb["AMT_DRAWINGS_ATM_CURRENT"], ccb["AMT_DRAWINGS_CURRENT"])
    ccb["atm_heavy_usage_flag"] = (ccb["atm_drawings_share"].fillna(0) >= heavy_atm_ratio).astype(int)
    ccb_features = ccb.groupby("SK_ID_CURR").agg(
        atm_cashout_ratio_max=("atm_cashout_ratio", "max"),
        atm_cashout_ratio_mean=("atm_cashout_ratio", "mean"),
        atm_heavy_usage_months=("atm_heavy_usage_flag", "sum"),
        credit_card_max_dpd_def=("SK_DPD_DEF", "max"),
    ).reset_index()

    inst = installments[
        [
            "SK_ID_CURR",
            "NUM_INSTALMENT_NUMBER",
            "DAYS_INSTALMENT",
            "DAYS_ENTRY_PAYMENT",
        ]
    ].copy()
    inst["days_late"] = (inst["DAYS_ENTRY_PAYMENT"] - inst["DAYS_INSTALMENT"]).fillna(0)
    inst["late_flag"] = (inst["days_late"] > 0).astype(int)
    inst_summary = inst.groupby("SK_ID_CURR").agg(
        installments_late_ratio=("late_flag", "mean"),
        max_days_past_due_installments=("days_late", "max"),
        first_instalment_number=("NUM_INSTALMENT_NUMBER", "min"),
    )
    first_inst = inst.sort_values(["SK_ID_CURR", "NUM_INSTALMENT_NUMBER", "DAYS_INSTALMENT"]).groupby("SK_ID_CURR").first()
    inst_features = inst_summary.join(first_inst[["days_late"]]).rename(columns={"days_late": "first_payment_delinquency_days"})
    inst_features = inst_features.drop(columns=["first_instalment_number"]).reset_index()
    inst_features["fpd_severe_flag"] = (inst_features["first_payment_delinquency_days"].fillna(0) >= severe_fpd_days).astype(int)

    app = application[["SK_ID_CURR", "TARGET", "ORGANIZATION_TYPE", "REGION_POPULATION_RELATIVE"]].copy()
    app["region_population_band"] = pd.qcut(
        app["REGION_POPULATION_RELATIVE"].rank(method="first"),
        q=5,
        labels=["very_low", "low", "mid", "high", "very_high"],
    )
    risk_map = group_risk(app, ["ORGANIZATION_TYPE", "region_population_band"])
    app = app.merge(risk_map, on=["ORGANIZATION_TYPE", "region_population_band"], how="left")
    group_features = app[["SK_ID_CURR", "group_bad_rate", "group_risk_rank"]].rename(
        columns={"group_bad_rate": "org_region_bad_rate", "group_risk_rank": "org_region_risk_rank"}
    )

    features = ccb_features.merge(inst_features, on="SK_ID_CURR", how="outer").merge(group_features, on="SK_ID_CURR", how="outer")
    numeric_cols = [col for col in features.columns if col != "SK_ID_CURR"]
    features[numeric_cols] = features[numeric_cols].replace([np.inf, -np.inf], np.nan)
    return features, metadata_frame(FEATURE_METADATA)


def aggregate_credit_card_features(credit_card_chunks: Iterable[pd.DataFrame], heavy_atm_ratio: float) -> pd.DataFrame:
    aggregates: pd.DataFrame | None = None
    for chunk in credit_card_chunks:
        ccb = chunk.copy()
        ccb["atm_cashout_ratio"] = relative_ratio(ccb["AMT_DRAWINGS_ATM_CURRENT"], ccb["AMT_TOTAL_RECEIVABLE"])
        ccb["atm_drawings_share"] = relative_ratio(ccb["AMT_DRAWINGS_ATM_CURRENT"], ccb["AMT_DRAWINGS_CURRENT"])
        ccb["atm_heavy_usage_flag"] = (ccb["atm_drawings_share"].fillna(0) >= heavy_atm_ratio).astype(int)
        ccb["ratio_notnull"] = ccb["atm_cashout_ratio"].notna().astype(int)
        reduced = ccb.groupby("SK_ID_CURR").agg(
            atm_cashout_ratio_max=("atm_cashout_ratio", "max"),
            atm_cashout_ratio_sum=("atm_cashout_ratio", "sum"),
            atm_cashout_ratio_count=("ratio_notnull", "sum"),
            atm_heavy_usage_months=("atm_heavy_usage_flag", "sum"),
            credit_card_max_dpd_def=("SK_DPD_DEF", "max"),
        )
        if aggregates is None:
            aggregates = reduced
            continue
        combined = aggregates.join(reduced, how="outer", lsuffix="_left", rsuffix="_right")
        aggregates = pd.DataFrame(
            {
                "atm_cashout_ratio_max": combined[["atm_cashout_ratio_max_left", "atm_cashout_ratio_max_right"]].max(axis=1),
                "atm_cashout_ratio_sum": combined[["atm_cashout_ratio_sum_left", "atm_cashout_ratio_sum_right"]].fillna(0).sum(axis=1),
                "atm_cashout_ratio_count": combined[["atm_cashout_ratio_count_left", "atm_cashout_ratio_count_right"]].fillna(0).sum(axis=1),
                "atm_heavy_usage_months": combined[["atm_heavy_usage_months_left", "atm_heavy_usage_months_right"]].fillna(0).sum(axis=1),
                "credit_card_max_dpd_def": combined[["credit_card_max_dpd_def_left", "credit_card_max_dpd_def_right"]].max(axis=1),
            },
            index=combined.index,
        )
    if aggregates is None:
        return pd.DataFrame(columns=["SK_ID_CURR", "atm_cashout_ratio_max", "atm_cashout_ratio_mean", "atm_heavy_usage_months", "credit_card_max_dpd_def"])
    aggregates["atm_cashout_ratio_mean"] = relative_ratio(
        aggregates["atm_cashout_ratio_sum"],
        aggregates["atm_cashout_ratio_count"],
    )
    return aggregates.reset_index()[["SK_ID_CURR", "atm_cashout_ratio_max", "atm_cashout_ratio_mean", "atm_heavy_usage_months", "credit_card_max_dpd_def"]]


def aggregate_installment_features(installment_chunks: Iterable[pd.DataFrame], severe_fpd_days: int) -> pd.DataFrame:
    aggregates: pd.DataFrame | None = None
    first_rows: pd.DataFrame | None = None
    for chunk in installment_chunks:
        inst = chunk.copy()
        inst["days_late"] = (inst["DAYS_ENTRY_PAYMENT"] - inst["DAYS_INSTALMENT"]).fillna(0)
        inst["late_flag"] = (inst["days_late"] > 0).astype(int)
        reduced = inst.groupby("SK_ID_CURR").agg(
            late_sum=("late_flag", "sum"),
            payment_count=("late_flag", "count"),
            max_days_past_due_installments=("days_late", "max"),
        )
        if aggregates is None:
            aggregates = reduced
        else:
            combined = aggregates.join(reduced, how="outer", lsuffix="_left", rsuffix="_right")
            aggregates = pd.DataFrame(
                {
                    "late_sum": combined[["late_sum_left", "late_sum_right"]].fillna(0).sum(axis=1),
                    "payment_count": combined[["payment_count_left", "payment_count_right"]].fillna(0).sum(axis=1),
                    "max_days_past_due_installments": combined[
                        ["max_days_past_due_installments_left", "max_days_past_due_installments_right"]
                    ].max(axis=1),
                },
                index=combined.index,
            )
        chunk_first = (
            inst.sort_values(["SK_ID_CURR", "NUM_INSTALMENT_NUMBER", "DAYS_INSTALMENT"])
            .groupby("SK_ID_CURR")
            .first()[["NUM_INSTALMENT_NUMBER", "DAYS_INSTALMENT", "days_late"]]
            .reset_index()
        )
        if first_rows is None:
            first_rows = chunk_first
        else:
            first_rows = (
                pd.concat([first_rows, chunk_first], ignore_index=True)
                .sort_values(["SK_ID_CURR", "NUM_INSTALMENT_NUMBER", "DAYS_INSTALMENT"])
                .groupby("SK_ID_CURR")
                .first()
                .reset_index()
            )
    if aggregates is None:
        return pd.DataFrame(columns=["SK_ID_CURR", "installments_late_ratio", "max_days_past_due_installments", "first_payment_delinquency_days", "fpd_severe_flag"])
    result = aggregates.reset_index()
    result["installments_late_ratio"] = relative_ratio(result["late_sum"], result["payment_count"], fill_value=0.0)
    result = result.drop(columns=["late_sum", "payment_count"])
    result = result.merge(
        first_rows[["SK_ID_CURR", "days_late"]].rename(columns={"days_late": "first_payment_delinquency_days"}),
        on="SK_ID_CURR",
        how="left",
    )
    result["fpd_severe_flag"] = (result["first_payment_delinquency_days"].fillna(0) >= severe_fpd_days).astype(int)
    return result

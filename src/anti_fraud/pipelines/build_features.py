from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from anti_fraud.features import (
    aggregate_credit_card_features,
    aggregate_installment_features,
    build_consistency_features,
    build_velocity_features,
)
from anti_fraud.operators import group_risk
from anti_fraud.utils.io import PROCESSED_DIR, REPORT_DIR, ensure_output_dirs, iter_csv, load_yaml, read_csv, write_dataframe


def load_inputs(feature_cfg: dict) -> dict[str, pd.DataFrame]:
    application = read_csv(
        "application_train.csv",
        usecols=lambda col: col
        in {
            "SK_ID_CURR",
            "TARGET",
            "DAYS_BIRTH",
            "DAYS_EMPLOYED",
            "DAYS_REGISTRATION",
            "DAYS_ID_PUBLISH",
            "FLAG_MOBIL",
            "FLAG_EMP_PHONE",
            "FLAG_WORK_PHONE",
            "FLAG_CONT_MOBILE",
            "FLAG_PHONE",
            "FLAG_EMAIL",
            "ORGANIZATION_TYPE",
            "REGION_POPULATION_RELATIVE",
            "AMT_REQ_CREDIT_BUREAU_HOUR",
            "AMT_REQ_CREDIT_BUREAU_DAY",
            "AMT_REQ_CREDIT_BUREAU_WEEK",
        }
        or col.startswith("FLAG_DOCUMENT_"),
    )
    previous = read_csv(
        "previous_application.csv",
        usecols=["SK_ID_CURR", "DAYS_DECISION", "NAME_CONTRACT_STATUS", "NAME_CONTRACT_TYPE"],
    )
    bureau = read_csv("bureau.csv", usecols=["SK_ID_CURR", "DAYS_CREDIT", "CREDIT_ACTIVE"])
    credit_card = aggregate_credit_card_features(
        iter_csv(
            "credit_card_balance.csv",
            usecols=[
                "SK_ID_CURR",
                "AMT_DRAWINGS_ATM_CURRENT",
                "AMT_DRAWINGS_CURRENT",
                "AMT_TOTAL_RECEIVABLE",
                "SK_DPD_DEF",
            ],
        ),
        heavy_atm_ratio=feature_cfg["cashout"]["heavy_atm_ratio"],
    )
    installments = aggregate_installment_features(
        iter_csv(
            "installments_payments.csv",
            usecols=["SK_ID_CURR", "NUM_INSTALMENT_NUMBER", "DAYS_INSTALMENT", "DAYS_ENTRY_PAYMENT"],
        ),
        severe_fpd_days=feature_cfg["cashout"]["severe_fpd_days"],
    )
    return {
        "application": application,
        "previous": previous,
        "bureau": bureau,
        "credit_card": credit_card,
        "installments": installments,
    }


def build_feature_frame() -> tuple[pd.DataFrame, pd.DataFrame]:
    ensure_output_dirs()
    feature_cfg = load_yaml("features.yaml")
    inputs = load_inputs(feature_cfg)
    consistency, consistency_meta = build_consistency_features(
        inputs["application"],
        inputs["previous"],
        core_documents=feature_cfg["consistency"]["core_document_flags"],
        contact_flags=feature_cfg["consistency"]["contact_flags"],
        employed_birth_ratio_threshold=feature_cfg["consistency"]["employed_birth_ratio_threshold"],
    )
    velocity, velocity_meta = build_velocity_features(
        inputs["application"],
        inputs["previous"],
        inputs["bureau"],
        inquiry_day_threshold=feature_cfg["velocity"]["inquiry_day_threshold"],
        inquiry_week_threshold=feature_cfg["velocity"]["inquiry_week_threshold"],
        burst_same_day_threshold=feature_cfg["velocity"]["burst_same_day_threshold"],
    )
    app = inputs["application"][["SK_ID_CURR", "TARGET", "ORGANIZATION_TYPE", "REGION_POPULATION_RELATIVE"]].copy()
    app["region_population_band"] = pd.qcut(
        app["REGION_POPULATION_RELATIVE"].rank(method="first"),
        q=5,
        labels=["very_low", "low", "mid", "high", "very_high"],
    )
    risk_map = group_risk(app, ["ORGANIZATION_TYPE", "region_population_band"])
    group_features = (
        app.merge(risk_map, on=["ORGANIZATION_TYPE", "region_population_band"], how="left")[
            ["SK_ID_CURR", "group_bad_rate", "group_risk_rank"]
        ]
        .rename(columns={"group_bad_rate": "org_region_bad_rate", "group_risk_rank": "org_region_risk_rank"})
    )
    cashout = inputs["credit_card"].merge(inputs["installments"], on="SK_ID_CURR", how="outer").merge(
        group_features, on="SK_ID_CURR", how="outer"
    )
    cashout_meta = pd.concat(
        [
            pd.DataFrame(
                [
                    {"feature_name": "atm_cashout_ratio_max", "source_table": "credit_card_balance", "business_definition": "ATM 取现相对应收总额的最大比率。", "aggregation_level": "SK_ID_CURR"},
                    {"feature_name": "atm_cashout_ratio_mean", "source_table": "credit_card_balance", "business_definition": "ATM 取现占比均值。", "aggregation_level": "SK_ID_CURR"},
                    {"feature_name": "atm_heavy_usage_months", "source_table": "credit_card_balance", "business_definition": "ATM 取现占比超过高风险阈值的月份数。", "aggregation_level": "SK_ID_CURR"},
                    {"feature_name": "credit_card_max_dpd_def", "source_table": "credit_card_balance", "business_definition": "信用卡账户最大逾期天数代理值。", "aggregation_level": "SK_ID_CURR"},
                    {"feature_name": "first_payment_delinquency_days", "source_table": "installments_payments", "business_definition": "首期还款逾期天数。", "aggregation_level": "SK_ID_CURR"},
                    {"feature_name": "fpd_severe_flag", "source_table": "installments_payments", "business_definition": "首期还款严重逾期时标记。", "aggregation_level": "SK_ID_CURR"},
                    {"feature_name": "installments_late_ratio", "source_table": "installments_payments", "business_definition": "历史还款记录中的逾期占比。", "aggregation_level": "SK_ID_CURR"},
                    {"feature_name": "max_days_past_due_installments", "source_table": "installments_payments", "business_definition": "历史分期最大逾期天数。", "aggregation_level": "SK_ID_CURR"},
                    {"feature_name": "org_region_bad_rate", "source_table": "application_train", "business_definition": "组织类型和区域人口分桶组合的坏账率。", "aggregation_level": "SK_ID_CURR"},
                    {"feature_name": "org_region_risk_rank", "source_table": "application_train", "business_definition": "组织类型和区域人口分桶组合的风险排名。", "aggregation_level": "SK_ID_CURR"},
                ]
            )
        ],
        ignore_index=True,
    )

    base = inputs["application"][["SK_ID_CURR", "TARGET"]].drop_duplicates()
    feature_frame = base.merge(consistency, on="SK_ID_CURR", how="left").merge(velocity, on="SK_ID_CURR", how="left").merge(
        cashout, on="SK_ID_CURR", how="left"
    )
    metadata = pd.concat([consistency_meta, velocity_meta, cashout_meta], ignore_index=True).drop_duplicates()
    return feature_frame, metadata


def main(output_name: str = "train_features.parquet") -> None:
    feature_frame, metadata = build_feature_frame()
    write_dataframe(feature_frame, PROCESSED_DIR / output_name)
    write_dataframe(metadata, REPORT_DIR / "feature_metadata.csv")
    sample = feature_frame.sample(n=min(20, len(feature_frame)), random_state=42)
    write_dataframe(sample, REPORT_DIR / "feature_sample_customers.csv")
    completeness = feature_frame.isna().mean().sort_values(ascending=False).reset_index()
    completeness.columns = ["feature_name", "missing_rate"]
    write_dataframe(completeness, REPORT_DIR / "feature_missingness.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build anti-fraud customer-level features.")
    parser.add_argument("--output-name", default="train_features.parquet")
    args = parser.parse_args()
    main(args.output_name)

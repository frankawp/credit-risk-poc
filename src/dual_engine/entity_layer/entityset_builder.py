from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import featuretools as ft
import pandas as pd

from dual_engine.config import AutoFeatureConfig


RAW_DIR = Path("data/raw/home-credit-default-risk")


def _add_index(df: pd.DataFrame, column: str) -> pd.DataFrame:
    out = df.copy()
    out[column] = range(len(out))
    return out


def _load_sampled_frames(config: AutoFeatureConfig) -> Dict[str, pd.DataFrame]:
    app_cols = [
        "SK_ID_CURR",
        "TARGET",
        "AMT_INCOME_TOTAL",
        "AMT_CREDIT",
        "AMT_ANNUITY",
        "AMT_GOODS_PRICE",
        "REGION_POPULATION_RELATIVE",
        "DAYS_BIRTH",
        "DAYS_EMPLOYED",
        "DAYS_REGISTRATION",
        "DAYS_ID_PUBLISH",
        "EXT_SOURCE_1",
        "EXT_SOURCE_2",
        "EXT_SOURCE_3",
        "ORGANIZATION_TYPE",
        "NAME_INCOME_TYPE",
        "NAME_EDUCATION_TYPE",
        "NAME_FAMILY_STATUS",
        "HOUR_APPR_PROCESS_START",
        "AMT_REQ_CREDIT_BUREAU_HOUR",
        "AMT_REQ_CREDIT_BUREAU_DAY",
        "AMT_REQ_CREDIT_BUREAU_WEEK",
    ]
    app = pd.read_csv(RAW_DIR / "application_train.csv", usecols=app_cols)
    app = app.sample(n=min(config.sample_size, len(app)), random_state=config.random_seed).reset_index(drop=True)
    curr_ids = set(app["SK_ID_CURR"])

    previous = pd.read_csv(
        RAW_DIR / "previous_application.csv",
        usecols=[
            "SK_ID_PREV",
            "SK_ID_CURR",
            "AMT_ANNUITY",
            "AMT_APPLICATION",
            "AMT_CREDIT",
            "AMT_DOWN_PAYMENT",
            "AMT_GOODS_PRICE",
            "HOUR_APPR_PROCESS_START",
            "RATE_DOWN_PAYMENT",
            "NAME_CONTRACT_STATUS",
            "NAME_CONTRACT_TYPE",
            "DAYS_DECISION",
            "CODE_REJECT_REASON",
            "NAME_CLIENT_TYPE",
            "CHANNEL_TYPE",
            "CNT_PAYMENT",
        ],
    )
    previous = previous[previous["SK_ID_CURR"].isin(curr_ids)].reset_index(drop=True)
    prev_ids = set(previous["SK_ID_PREV"])

    bureau = pd.read_csv(
        RAW_DIR / "bureau.csv",
        usecols=[
            "SK_ID_BUREAU",
            "SK_ID_CURR",
            "CREDIT_ACTIVE",
            "DAYS_CREDIT",
            "CREDIT_DAY_OVERDUE",
            "DAYS_CREDIT_ENDDATE",
            "AMT_CREDIT_SUM",
            "AMT_CREDIT_SUM_DEBT",
            "AMT_CREDIT_SUM_OVERDUE",
            "CREDIT_TYPE",
        ],
    )
    bureau = bureau[bureau["SK_ID_CURR"].isin(curr_ids)].reset_index(drop=True)
    bureau_ids = set(bureau["SK_ID_BUREAU"])

    bureau_balance = pd.read_csv(RAW_DIR / "bureau_balance.csv", usecols=["SK_ID_BUREAU", "MONTHS_BALANCE", "STATUS"])
    bureau_balance = bureau_balance[bureau_balance["SK_ID_BUREAU"].isin(bureau_ids)].reset_index(drop=True)

    credit_card = pd.read_csv(
        RAW_DIR / "credit_card_balance.csv",
        usecols=[
            "SK_ID_PREV",
            "MONTHS_BALANCE",
            "AMT_BALANCE",
            "AMT_CREDIT_LIMIT_ACTUAL",
            "AMT_DRAWINGS_ATM_CURRENT",
            "AMT_DRAWINGS_CURRENT",
            "AMT_TOTAL_RECEIVABLE",
            "SK_DPD",
            "SK_DPD_DEF",
        ],
    )
    credit_card = credit_card[credit_card["SK_ID_PREV"].isin(prev_ids)].reset_index(drop=True)

    installments = pd.read_csv(
        RAW_DIR / "installments_payments.csv",
        usecols=["SK_ID_PREV", "NUM_INSTALMENT_NUMBER", "DAYS_INSTALMENT", "DAYS_ENTRY_PAYMENT", "AMT_INSTALMENT", "AMT_PAYMENT"],
    )
    installments = installments[installments["SK_ID_PREV"].isin(prev_ids)].reset_index(drop=True)

    pos_cash = pd.read_csv(
        RAW_DIR / "POS_CASH_balance.csv",
        usecols=["SK_ID_PREV", "MONTHS_BALANCE", "CNT_INSTALMENT", "CNT_INSTALMENT_FUTURE", "NAME_CONTRACT_STATUS", "SK_DPD", "SK_DPD_DEF"],
    )
    pos_cash = pos_cash[pos_cash["SK_ID_PREV"].isin(prev_ids)].reset_index(drop=True)

    return {
        "applications": app,
        "previous_applications": previous,
        "bureau": bureau,
        "bureau_balance": _add_index(bureau_balance, "bureau_balance_id"),
        "credit_card_balance": _add_index(credit_card, "credit_card_balance_id"),
        "installments_payments": _add_index(installments, "installment_payment_id"),
        "pos_cash_balance": _add_index(pos_cash, "pos_cash_balance_id"),
    }


def build_entityset_for_auto(config: AutoFeatureConfig) -> Tuple[ft.EntitySet, Dict[str, pd.DataFrame]]:
    frames = _load_sampled_frames(config)
    es = ft.EntitySet(id="home_credit_dual_engine")
    es = es.add_dataframe(dataframe_name="applications", dataframe=frames["applications"], index="SK_ID_CURR")
    es = es.add_dataframe(dataframe_name="previous_applications", dataframe=frames["previous_applications"], index="SK_ID_PREV")
    es = es.add_dataframe(dataframe_name="bureau", dataframe=frames["bureau"], index="SK_ID_BUREAU")
    es = es.add_dataframe(dataframe_name="bureau_balance", dataframe=frames["bureau_balance"], index="bureau_balance_id")
    es = es.add_dataframe(dataframe_name="credit_card_balance", dataframe=frames["credit_card_balance"], index="credit_card_balance_id")
    es = es.add_dataframe(dataframe_name="installments_payments", dataframe=frames["installments_payments"], index="installment_payment_id")
    es = es.add_dataframe(dataframe_name="pos_cash_balance", dataframe=frames["pos_cash_balance"], index="pos_cash_balance_id")

    relationships = [
        ("applications", "SK_ID_CURR", "previous_applications", "SK_ID_CURR"),
        ("applications", "SK_ID_CURR", "bureau", "SK_ID_CURR"),
        ("previous_applications", "SK_ID_PREV", "credit_card_balance", "SK_ID_PREV"),
        ("previous_applications", "SK_ID_PREV", "installments_payments", "SK_ID_PREV"),
        ("previous_applications", "SK_ID_PREV", "pos_cash_balance", "SK_ID_PREV"),
        ("bureau", "SK_ID_BUREAU", "bureau_balance", "SK_ID_BUREAU"),
    ]
    for parent_df, parent_col, child_df, child_col in relationships:
        es = es.add_relationship(
            parent_dataframe_name=parent_df,
            parent_column_name=parent_col,
            child_dataframe_name=child_df,
            child_column_name=child_col,
        )
    return es, frames

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from anti_fraud.utils.io import FEATURE_DIR, RAW_DIR, REPORT_DIR, ensure_output_dirs, read_columns_description, read_csv, write_dataframe, write_markdown


TABLES = [
    "application_train.csv",
    "previous_application.csv",
    "bureau.csv",
    "credit_card_balance.csv",
    "installments_payments.csv",
]


def _table_overview(name: str) -> dict:
    sample = pd.read_csv(RAW_DIR / name, nrows=1000)
    rows = sum(1 for _ in open(RAW_DIR / name, "rb")) - 1
    return {
        "table_name": name,
        "rows": rows,
        "columns": len(sample.columns),
        "sample_memory_mb": round(sample.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        "key_columns": ", ".join([col for col in sample.columns if col.startswith("SK_ID")][:3]),
    }


def generate_eda() -> None:
    ensure_output_dirs()
    overview = pd.DataFrame([_table_overview(name) for name in TABLES])
    write_dataframe(overview, REPORT_DIR / "table_overview.csv")

    columns_desc = read_columns_description()
    write_dataframe(columns_desc, REPORT_DIR / "columns_description.csv")

    app = read_csv("application_train.csv")
    target_summary = pd.DataFrame(
        {
            "metric": ["rows", "target_rate", "target_count", "non_target_count"],
            "value": [
                len(app),
                app["TARGET"].mean(),
                int(app["TARGET"].sum()),
                int((app["TARGET"] == 0).sum()),
            ],
        }
    )
    write_dataframe(target_summary, REPORT_DIR / "target_summary.csv")

    missingness = app.isna().mean().sort_values(ascending=False).head(25).reset_index()
    missingness.columns = ["column_name", "missing_rate"]
    write_dataframe(missingness, REPORT_DIR / "application_missingness_top25.csv")

    customer_density = []
    for name in ["previous_application.csv", "bureau.csv", "credit_card_balance.csv", "installments_payments.csv"]:
        df = read_csv(name, usecols=["SK_ID_CURR"])
        counts = df.groupby("SK_ID_CURR").size()
        customer_density.append(
            {
                "table_name": name,
                "customers": int(counts.index.nunique()),
                "mean_records_per_customer": float(counts.mean()),
                "p95_records_per_customer": float(counts.quantile(0.95)),
                "max_records_per_customer": int(counts.max()),
            }
        )
    density_df = pd.DataFrame(customer_density)
    write_dataframe(density_df, REPORT_DIR / "customer_density.csv")

    markdown = f"""# EDA Summary

## 数据规模

共分析 {len(TABLES)} 张核心表，主表 `application_train.csv` 含 {len(app):,} 条申请记录，坏样本率约为 {app["TARGET"].mean():.2%}。

## 业务导向结论

- 身份伪造：`application_train` 的联系方式标识位、证件标识位和 `DAYS_EMPLOYED` / `DAYS_BIRTH` 的逻辑关系最直接。
- 短期高频：`previous_application` 的 `DAYS_DECISION` 能直接识别密集申请，`application_train` 的 `AMT_REQ_CREDIT_BUREAU_*` 能补充征信查询强度。
- 套现与团伙：`credit_card_balance` 的 `AMT_DRAWINGS_ATM_CURRENT` 与 `AMT_TOTAL_RECEIVABLE` 适合刻画 ATM 取现偏好，`installments_payments` 适合定义 FPD，`ORGANIZATION_TYPE + REGION_POPULATION_RELATIVE` 适合做高危入件点群体画像。

## 风险提示

- `credit_card_balance` 与 `installments_payments` 为高行数表，后续特征工程应坚持列裁剪和客户级聚合。
- `HomeCredit_columns_description.csv` 不是 UTF-8，读取时必须显式指定编码。
"""
    write_markdown(markdown, REPORT_DIR / "eda_summary.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run EDA and produce summary artifacts.")
    parser.parse_args()
    generate_eda()

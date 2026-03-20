from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from anti_fraud.models.baseline import train_baselines, write_metrics
from anti_fraud.utils.io import MODEL_DIR, PROCESSED_DIR, REPORT_DIR, ensure_output_dirs, load_yaml, write_markdown


BASELINE_COLUMNS = [
    "emp_age_ratio",
    "phone_contact_coverage",
    "document_core_missing_count",
    "bureau_inquiry_intensity",
]


def train(feature_file: str = "train_features.parquet", feature_set: str = "all") -> dict:
    ensure_output_dirs()
    cfg = load_yaml("base.yaml")
    if feature_set == "selected":
        frame = pd.read_parquet(PROCESSED_DIR / "selected_features.parquet")
    else:
        frame = pd.read_parquet(PROCESSED_DIR / feature_file)
    feature_columns = [col for col in frame.columns if col not in {"SK_ID_CURR", "TARGET"}]
    metrics = train_baselines(
        frame=frame,
        baseline_columns=[col for col in BASELINE_COLUMNS if col in frame.columns],
        feature_columns=feature_columns,
        topk_fraction=cfg["topk_fraction"],
        random_seed=cfg["random_seed"],
        validation_size=cfg["validation_size"],
    )
    suffix = "selected" if feature_set == "selected" else "all"
    write_metrics(metrics, MODEL_DIR / f"baseline_metrics_{suffix}.json")

    report = f"""# Model Summary

## Baseline vs Anti-Fraud

- Baseline XGBoost ROC-AUC: {metrics["baseline_xgboost"]["roc_auc"]:.4f}
- Anti-Fraud XGBoost ROC-AUC: {metrics["anti_fraud_xgboost"]["roc_auc"]:.4f}
- Isolation Forest ROC-AUC: {metrics["anti_fraud_isolation_forest"]["roc_auc"]:.4f}
- Anti-Fraud XGBoost Recall@TopK: {metrics["anti_fraud_xgboost"]["recall_at_topk"]:.4f}

## FPD Slice

- FPD slice size: {metrics["fpd_slice"]["size"]}
- Baseline Recall@TopK on FPD slice: {metrics["fpd_slice"]["baseline_xgboost_recall_at_topk"]:.4f}
- Anti-Fraud Recall@TopK on FPD slice: {metrics["fpd_slice"]["anti_fraud_xgboost_recall_at_topk"]:.4f}
"""
    write_markdown(report, REPORT_DIR / f"model_summary_{suffix}.md")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train baseline anti-fraud models.")
    parser.add_argument("--feature-file", default="train_features.parquet")
    parser.add_argument("--feature-set", choices=["all", "selected"], default="all")
    args = parser.parse_args()
    train(args.feature_file, args.feature_set)

from __future__ import annotations

import argparse

from anti_fraud.pipelines.build_features import main as build_features
from anti_fraud.pipelines.run_eda import generate_eda
from anti_fraud.pipelines.select_features import run_selection
from anti_fraud.pipelines.train_models import train
from anti_fraud.utils.io import REPORT_DIR, write_markdown


def run_all(feature_output_name: str = "train_features.parquet") -> None:
    generate_eda()
    build_features(feature_output_name)
    selection_report = run_selection(feature_output_name)
    all_metrics = train(feature_output_name, feature_set="all")
    selected_metrics = train(feature_output_name, feature_set="selected")
    comparison = f"""# Unified Model Summary

## All Features

- ROC-AUC: {all_metrics["anti_fraud_xgboost"]["roc_auc"]:.4f}
- PR-AUC: {all_metrics["anti_fraud_xgboost"]["pr_auc"]:.4f}
- Recall@TopK: {all_metrics["anti_fraud_xgboost"]["recall_at_topk"]:.4f}

## Selected Features

- ROC-AUC: {selected_metrics["anti_fraud_xgboost"]["roc_auc"]:.4f}
- PR-AUC: {selected_metrics["anti_fraud_xgboost"]["pr_auc"]:.4f}
- Recall@TopK: {selected_metrics["anti_fraud_xgboost"]["recall_at_topk"]:.4f}

## Selection Summary

- Selected feature count: {selection_report["selected_feature_count"]}
- ROC-AUC delta: {selection_report["metric_deltas"]["roc_auc_delta"]:.4f}
- PR-AUC delta: {selection_report["metric_deltas"]["pr_auc_delta"]:.4f}
- Recall@TopK delta: {selection_report["metric_deltas"]["recall_at_topk_delta"]:.4f}
"""
    write_markdown(comparison, REPORT_DIR / "model_summary.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run EDA, feature engineering, and baseline model training.")
    parser.add_argument("--feature-output-name", default="train_features.parquet")
    args = parser.parse_args()
    run_all(args.feature_output_name)

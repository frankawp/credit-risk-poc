from __future__ import annotations

import argparse

import pandas as pd

from anti_fraud.models.baseline import train_baselines
from anti_fraud.models.feature_selection import (
    SelectionConfig,
    build_selection_report,
    compute_feature_scorecard,
    select_from_correlation_groups,
    selection_report_markdown,
    write_selection_json,
)
from anti_fraud.utils.io import MODEL_DIR, PROCESSED_DIR, REPORT_DIR, ensure_output_dirs, load_yaml, write_dataframe, write_markdown


def run_selection(feature_file: str = "train_features.parquet") -> dict:
    ensure_output_dirs()
    cfg = load_yaml("base.yaml")
    selection_cfg = SelectionConfig(**cfg["feature_selection"])
    frame = pd.read_parquet(PROCESSED_DIR / feature_file)
    feature_columns = [col for col in frame.columns if col not in {"SK_ID_CURR", "TARGET"}]

    full_metrics = train_baselines(
        frame=frame,
        baseline_columns=["emp_age_ratio", "phone_contact_coverage", "document_core_missing_count", "bureau_inquiry_intensity"],
        feature_columns=feature_columns,
        topk_fraction=cfg["topk_fraction"],
        random_seed=cfg["random_seed"],
        validation_size=cfg["validation_size"],
    )
    importance_map = full_metrics.get("top_feature_importance", {})
    scorecard = compute_feature_scorecard(frame, feature_columns, "TARGET", importance_map, selection_cfg)
    scorecard, corr_groups = select_from_correlation_groups(frame, scorecard, selection_cfg)

    # Keep only features that survived filtering/correlation selection.
    selected = scorecard[scorecard["selected_flag"] == 1]["feature_name"].tolist()
    selected_frame = frame[["SK_ID_CURR", "TARGET", *selected]].copy()

    selected_metrics = train_baselines(
        frame=selected_frame,
        baseline_columns=[col for col in ["emp_age_ratio", "phone_contact_coverage", "document_core_missing_count", "bureau_inquiry_intensity"] if col in selected_frame.columns],
        feature_columns=selected,
        topk_fraction=cfg["topk_fraction"],
        random_seed=cfg["random_seed"],
        validation_size=cfg["validation_size"],
    )

    report = build_selection_report(scorecard, selected)
    report["all_feature_metrics"] = full_metrics
    report["selected_feature_metrics"] = selected_metrics
    report["metric_deltas"] = {
        "roc_auc_delta": float(selected_metrics["anti_fraud_xgboost"]["roc_auc"] - full_metrics["anti_fraud_xgboost"]["roc_auc"]),
        "pr_auc_delta": float(selected_metrics["anti_fraud_xgboost"]["pr_auc"] - full_metrics["anti_fraud_xgboost"]["pr_auc"]),
        "recall_at_topk_delta": float(
            selected_metrics["anti_fraud_xgboost"]["recall_at_topk"] - full_metrics["anti_fraud_xgboost"]["recall_at_topk"]
        ),
    }

    write_dataframe(selected_frame, PROCESSED_DIR / "selected_features.parquet")
    write_dataframe(scorecard.sort_values(["selected_flag", "importance_full_model"], ascending=[False, False]), REPORT_DIR / "feature_scorecard.csv")
    write_dataframe(corr_groups, REPORT_DIR / "correlation_groups.csv")
    write_selection_json(report, MODEL_DIR / "feature_selection_report.json")
    write_markdown(
        selection_report_markdown(report, scorecard, full_metrics, selected_metrics),
        REPORT_DIR / "feature_selection_report.md",
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Select effective and low-correlation anti-fraud features.")
    parser.add_argument("--feature-file", default="train_features.parquet")
    args = parser.parse_args()
    run_selection(args.feature_file)

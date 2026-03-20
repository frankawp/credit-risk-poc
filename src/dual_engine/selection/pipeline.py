from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from dual_engine.config import SelectionConfig
from dual_engine.selection.basic_filters import apply_basic_filters
from dual_engine.selection.univariate import evaluate_univariate


def run_feature_selection(frame: pd.DataFrame, config: SelectionConfig, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    filtered = apply_basic_filters(
        frame=frame,
        id_col=config.id_col,
        target_col=config.target_col,
        missing_rate_threshold=config.missing_rate_threshold,
        correlation_threshold=config.correlation_threshold,
    )
    filtered_frame = filtered.filtered

    scorecard = evaluate_univariate(
        frame=filtered_frame,
        id_col=config.id_col,
        target_col=config.target_col,
        topk_ratio=config.topk_ratio,
    )
    baseline_ap = float(filtered_frame[config.target_col].mean())
    scorecard["selected_flag"] = (
        (scorecard["univariate_roc_auc"] >= config.min_auc)
        | (scorecard["univariate_pr_auc"] >= baseline_ap * config.min_ap_lift)
    )
    scorecard["drop_reason"] = scorecard["selected_flag"].map(lambda f: "" if f else "weak_univariate_signal")

    selected_features = scorecard.loc[scorecard["selected_flag"], "feature_name"].tolist()
    selected_frame = filtered_frame[[config.id_col, config.target_col] + selected_features].copy()

    corr_rows = filtered.drop_report[filtered.drop_report["drop_reason"].str.startswith("highly_correlated_with_")].copy()
    if not corr_rows.empty:
        corr_rows["representative_feature"] = corr_rows["drop_reason"].str.replace("highly_correlated_with_", "", regex=False)
        corr_rows = corr_rows.rename(columns={"feature_name": "dropped_feature"})
    else:
        corr_rows = pd.DataFrame(columns=["dropped_feature", "representative_feature", "drop_reason"])

    selected_frame.to_parquet(output_dir / "selected_features.parquet", index=False)
    scorecard.to_csv(output_dir / "feature_scorecard.csv", index=False)
    filtered.drop_report.to_csv(output_dir / "dropped_by_basic_filters.csv", index=False)
    corr_rows.to_csv(output_dir / "correlation_groups.csv", index=False)

    final_report = scorecard.copy()
    final_report = final_report.merge(filtered.drop_report, on="feature_name", how="left", suffixes=("", "_basic"))
    final_report["drop_reason"] = final_report["drop_reason_basic"].fillna(final_report["drop_reason"])
    final_report = final_report.drop(columns=["drop_reason_basic"])
    final_report.to_csv(output_dir / "feature_selection_report.csv", index=False)

    summary = {
        "input_feature_count": int(frame.shape[1] - 2),
        "after_basic_filter_count": int(filtered_frame.shape[1] - 2),
        "selected_feature_count": int(len(selected_features)),
        "baseline_target_rate": baseline_ap,
        "selected_features": selected_features,
    }
    (output_dir / "feature_selection_report.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    (output_dir / "feature_selection_report.md").write_text(
        "# Feature Selection Report\n\n"
        f"- input_feature_count: {summary['input_feature_count']}\n"
        f"- after_basic_filter_count: {summary['after_basic_filter_count']}\n"
        f"- selected_feature_count: {summary['selected_feature_count']}\n"
        f"- baseline_target_rate: {summary['baseline_target_rate']:.6f}\n"
    )
    return summary

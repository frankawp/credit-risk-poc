from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


@dataclass
class SelectionConfig:
    missing_rate_threshold: float = 0.85
    near_constant_threshold: float = 0.99
    min_non_null: int = 1000
    min_unique: int = 2
    weak_signal_auc_band: float = 0.02
    topk_fraction: float = 0.05
    correlation_threshold: float = 0.80
    extreme_correlation_threshold: float = 0.95
    winsorize_quantile: float = 0.99
    max_metric_drop_tolerance: float = 0.02


def recall_at_top_k(y_true: pd.Series, scores: pd.Series, fraction: float) -> float:
    if len(scores) == 0:
        return 0.0
    top_n = max(1, int(len(scores) * fraction))
    ranked = scores.sort_values(ascending=False).index[:top_n]
    positives = float(y_true.sum())
    if positives == 0:
        return 0.0
    return float(y_true.loc[ranked].sum() / positives)


def lift_top_decile(y_true: pd.Series, scores: pd.Series) -> float:
    base_rate = float(y_true.mean())
    if base_rate == 0:
        return 0.0
    top_n = max(1, int(len(scores) * 0.1))
    ranked = scores.sort_values(ascending=False).index[:top_n]
    top_rate = float(y_true.loc[ranked].mean())
    return float(top_rate / base_rate)


def _feature_type(series: pd.Series) -> str:
    non_null = series.dropna()
    if non_null.empty:
        return "empty"
    unique_count = non_null.nunique()
    if unique_count <= 2:
        return "binary"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    return "categorical"


def _winsorize(series: pd.Series, quantile: float) -> pd.Series:
    clean = series.dropna()
    if clean.empty or not pd.api.types.is_numeric_dtype(series):
        return series
    lower = clean.quantile(1 - quantile)
    upper = clean.quantile(quantile)
    return series.clip(lower=lower, upper=upper)


def compute_feature_scorecard(
    frame: pd.DataFrame,
    feature_columns: list[str],
    target_col: str,
    importance_map: dict[str, float],
    config: SelectionConfig,
) -> pd.DataFrame:
    target = frame[target_col].astype(int)
    rows: list[dict] = []
    for feature in feature_columns:
        series = frame[feature]
        non_null_mask = series.notna()
        non_null = series[non_null_mask]
        feature_type = _feature_type(series)
        row = {
            "feature_name": feature,
            "feature_type": feature_type,
            "missing_rate": float(series.isna().mean()),
            "coverage_rate": float(non_null_mask.mean()),
            "n_unique": int(non_null.nunique()),
            "importance_full_model": float(importance_map.get(feature, 0.0)),
            "selected_flag": 0,
            "drop_reason": "",
            "correlation_group_id": "",
            "stability_score": 0.0,
            "univariate_roc_auc": np.nan,
            "univariate_pr_auc": np.nan,
            "recall_at_topk": np.nan,
            "lift_top_decile": np.nan,
            "outlier_rate": np.nan,
        }

        if len(non_null) < config.min_non_null:
            row["drop_reason"] = "low_non_null_count"
            rows.append(row)
            continue

        if row["missing_rate"] > config.missing_rate_threshold:
            row["drop_reason"] = "high_missing_rate"
            rows.append(row)
            continue

        if row["n_unique"] < config.min_unique:
            row["drop_reason"] = "constant_or_single_value"
            rows.append(row)
            continue

        value_share = float(non_null.value_counts(normalize=True, dropna=False).iloc[0])
        if value_share >= config.near_constant_threshold:
            row["drop_reason"] = "near_constant"
            rows.append(row)
            continue

        scored = _winsorize(series, config.winsorize_quantile).fillna(series.median() if pd.api.types.is_numeric_dtype(series) else 0)
        try:
            roc = roc_auc_score(target, scored)
            if roc < 0.5:
                roc = 1 - roc
            pr = average_precision_score(target, scored)
            recall = recall_at_top_k(target, scored, config.topk_fraction)
            lift = lift_top_decile(target, scored)
        except Exception:
            row["drop_reason"] = "invalid_univariate_metric"
            rows.append(row)
            continue

        z = (scored - scored.mean()) / (scored.std(ddof=0) or 1)
        outlier_rate = float((z.abs() > 3).mean())
        row.update(
            {
                "univariate_roc_auc": float(roc),
                "univariate_pr_auc": float(pr),
                "recall_at_topk": float(recall),
                "lift_top_decile": float(lift),
                "outlier_rate": outlier_rate,
                "stability_score": float(max(0.0, 1 - outlier_rate - row["missing_rate"])),
            }
        )
        if abs(row["univariate_roc_auc"] - 0.5) <= config.weak_signal_auc_band and row["lift_top_decile"] <= 1.05:
            row["drop_reason"] = "weak_univariate_signal"
        rows.append(row)
    return pd.DataFrame(rows)


def _corr_graph(corr_matrix: pd.DataFrame, threshold: float) -> list[set[str]]:
    nodes = list(corr_matrix.columns)
    visited: set[str] = set()
    groups: list[set[str]] = []
    for node in nodes:
        if node in visited:
            continue
        stack = [node]
        group: set[str] = set()
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            group.add(current)
            neighbors = corr_matrix.index[(corr_matrix[current].abs() >= threshold) & (corr_matrix.index != current)].tolist()
            for neighbor in neighbors:
                if neighbor not in visited:
                    stack.append(neighbor)
        groups.append(group)
    return groups


def select_from_correlation_groups(
    frame: pd.DataFrame,
    scorecard: pd.DataFrame,
    config: SelectionConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    candidates = scorecard[scorecard["drop_reason"] == ""].copy()
    feature_names = candidates["feature_name"].tolist()
    if not feature_names:
        return scorecard, pd.DataFrame(columns=["correlation_group_id", "feature_name", "corr_to_representative", "selected_flag"])

    numeric = frame[feature_names].copy()
    for column in numeric.columns:
        if pd.api.types.is_numeric_dtype(numeric[column]):
            numeric[column] = _winsorize(numeric[column], config.winsorize_quantile)
        numeric[column] = numeric[column].fillna(numeric[column].median())

    corr = numeric.corr(method="spearman").fillna(0.0)
    groups = _corr_graph(corr, config.correlation_threshold)
    correlation_rows: list[dict] = []
    scorecard = scorecard.copy()
    for idx, group in enumerate(groups, start=1):
        group_id = f"group_{idx:03d}"
        members = scorecard[scorecard["feature_name"].isin(group)].copy()
        members["group_rank"] = (
            members["univariate_roc_auc"].fillna(0) * 4
            + members["importance_full_model"].fillna(0) * 4
            + members["stability_score"].fillna(0) * 2
            - members["missing_rate"].fillna(0) * 2
            - members["outlier_rate"].fillna(0)
        )
        members = members.sort_values(
            ["group_rank", "importance_full_model", "univariate_roc_auc", "stability_score"],
            ascending=False,
        )
        representative = members.iloc[0]["feature_name"]
        strong_set = set()
        extreme_set = set()
        for _, row in members.iterrows():
            feature = row["feature_name"]
            scorecard.loc[scorecard["feature_name"] == feature, "correlation_group_id"] = group_id
            corr_value = float(corr.loc[feature, representative]) if feature != representative else 1.0
            if abs(corr_value) >= config.correlation_threshold and feature != representative:
                strong_set.add(feature)
            if abs(corr_value) >= config.extreme_correlation_threshold and feature != representative:
                extreme_set.add(feature)
            correlation_rows.append(
                {
                    "correlation_group_id": group_id,
                    "feature_name": feature,
                    "representative_feature": representative,
                    "corr_to_representative": corr_value,
                    "selected_flag": int(feature == representative),
                }
            )

        # Preserve one continuous-strength feature and one rule flag when correlation is not extreme.
        if len(members) > 1:
            flag_candidates = members[members["feature_type"] == "binary"]["feature_name"].tolist()
            continuous_candidates = members[members["feature_type"] != "binary"]["feature_name"].tolist()
            keep_extra = None
            if representative in flag_candidates and continuous_candidates:
                candidate = continuous_candidates[0]
                if candidate not in extreme_set:
                    keep_extra = candidate
            elif representative in continuous_candidates and flag_candidates:
                candidate = flag_candidates[0]
                if candidate not in extreme_set:
                    keep_extra = candidate
            if keep_extra:
                scorecard.loc[scorecard["feature_name"] == keep_extra, "selected_flag"] = 1

        scorecard.loc[scorecard["feature_name"] == representative, "selected_flag"] = 1
        for feature in members["feature_name"]:
            if feature == representative:
                continue
            if int(scorecard.loc[scorecard["feature_name"] == feature, "selected_flag"].iloc[0]) == 1:
                continue
            scorecard.loc[scorecard["feature_name"] == feature, "drop_reason"] = f"correlated_with_{representative}"

    return scorecard, pd.DataFrame(correlation_rows)


def build_selection_report(scorecard: pd.DataFrame, selected_features: list[str]) -> dict:
    kept = scorecard[scorecard["selected_flag"] == 1]["feature_name"].tolist()
    dropped = scorecard[scorecard["selected_flag"] != 1][["feature_name", "drop_reason"]].to_dict(orient="records")
    return {
        "selected_feature_count": len(selected_features),
        "selected_features": kept,
        "dropped_features": dropped,
        "drop_reason_counts": scorecard["drop_reason"].replace("", "kept").value_counts().to_dict(),
    }


def selection_report_markdown(
    report: dict,
    scorecard: pd.DataFrame,
    full_metrics: dict,
    selected_metrics: dict,
) -> str:
    top_selected = scorecard[scorecard["selected_flag"] == 1].sort_values(
        ["importance_full_model", "univariate_roc_auc"], ascending=False
    )["feature_name"].head(15)
    lines = [
        "# Feature Selection Report",
        "",
        "## Summary",
        "",
        f"- Selected features: {report['selected_feature_count']}",
        f"- All-feature ROC-AUC: {full_metrics['anti_fraud_xgboost']['roc_auc']:.4f}",
        f"- Selected-feature ROC-AUC: {selected_metrics['anti_fraud_xgboost']['roc_auc']:.4f}",
        f"- All-feature Recall@TopK: {full_metrics['anti_fraud_xgboost']['recall_at_topk']:.4f}",
        f"- Selected-feature Recall@TopK: {selected_metrics['anti_fraud_xgboost']['recall_at_topk']:.4f}",
        "",
        "## Top Selected Features",
        "",
    ]
    lines.extend([f"- `{name}`" for name in top_selected])
    lines.extend(
        [
            "",
            "## Drop Reasons",
            "",
        ]
    )
    for reason, count in report["drop_reason_counts"].items():
        lines.append(f"- `{reason}`: {count}")
    return "\n".join(lines)


def write_selection_json(report: dict, path: Path) -> None:
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False))

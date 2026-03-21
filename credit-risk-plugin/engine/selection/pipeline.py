"""
特征筛选流水线。

整合基础过滤和单变量评估，输出完整的筛选报告。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ..config import SelectionConfig
from .basic_filters import apply_basic_filters
from .univariate import evaluate_univariate


@dataclass(frozen=True)
class SelectionResult:
    """筛选结果。"""

    selected_frame: pd.DataFrame
    scorecard: pd.DataFrame
    drop_report: pd.DataFrame
    correlation_groups: pd.DataFrame
    summary: dict


def run_feature_selection(
    frame: pd.DataFrame,
    config: SelectionConfig,
    output_dir: Path | None = None,
) -> SelectionResult:
    """执行特征筛选流程。

    参数：
        frame: 特征矩阵
        config: 筛选配置
        output_dir: 输出目录（可选）

    返回：
        SelectionResult 包含筛选结果和报告
    """
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    # 步骤 1：基础过滤
    filtered = apply_basic_filters(
        frame=frame,
        id_col=config.id_col,
        target_col=config.target_col,
        missing_rate_threshold=config.missing_rate_threshold,
        correlation_threshold=config.correlation_threshold,
    )
    filtered_frame = filtered.filtered

    # 步骤 2：单变量评估
    scorecard = evaluate_univariate(
        frame=filtered_frame,
        id_col=config.id_col,
        target_col=config.target_col,
        topk_ratio=config.topk_ratio,
    )

    # 步骤 3：筛选标记
    baseline_ap = float(filtered_frame[config.target_col].mean())
    scorecard["selected_flag"] = (
        (scorecard["univariate_roc_auc"] >= config.min_auc)
        | (scorecard["univariate_pr_auc"] >= baseline_ap * config.min_ap_lift)
    )
    scorecard["drop_reason"] = scorecard["selected_flag"].map(
        lambda f: "" if f else "weak_univariate_signal"
    )

    # 提取选中特征
    selected_features = scorecard.loc[scorecard["selected_flag"], "feature_name"].tolist()
    selected_frame = filtered_frame[[config.id_col, config.target_col] + selected_features].copy()

    # 整理相关性分组
    corr_rows = filtered.drop_report[
        filtered.drop_report["drop_reason"].str.startswith("highly_correlated_with_")
    ].copy()
    if not corr_rows.empty:
        corr_rows["representative_feature"] = corr_rows["drop_reason"].str.replace(
            "highly_correlated_with_", "", regex=False
        )
        corr_rows = corr_rows.rename(columns={"feature_name": "dropped_feature"})
    else:
        corr_rows = pd.DataFrame(columns=["dropped_feature", "representative_feature", "drop_reason"])

    # 生成汇总
    summary = {
        "input_feature_count": int(frame.shape[1] - 2),
        "after_basic_filter_count": int(filtered_frame.shape[1] - 2),
        "selected_feature_count": int(len(selected_features)),
        "baseline_target_rate": baseline_ap,
        "selected_features": selected_features,
    }

    # 保存输出
    if output_dir:
        selected_frame.to_parquet(output_dir / "selected_features.parquet", index=False)
        scorecard.to_csv(output_dir / "feature_scorecard.csv", index=False)
        filtered.drop_report.to_csv(output_dir / "dropped_by_basic_filters.csv", index=False)
        corr_rows.to_csv(output_dir / "correlation_groups.csv", index=False)

        # 合并报告
        final_report = scorecard.copy()
        final_report = final_report.merge(
            filtered.drop_report, on="feature_name", how="left", suffixes=("", "_basic")
        )
        final_report["drop_reason"] = final_report["drop_reason_basic"].fillna(final_report["drop_reason"])
        final_report = final_report.drop(columns=["drop_reason_basic"])
        final_report.to_csv(output_dir / "feature_selection_report.csv", index=False)

        # JSON 汇总
        (output_dir / "feature_selection_report.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False)
        )

        # Markdown 汇总
        (output_dir / "feature_selection_report.md").write_text(
            "# Feature Selection Report\n\n"
            f"- input_feature_count: {summary['input_feature_count']}\n"
            f"- after_basic_filter_count: {summary['after_basic_filter_count']}\n"
            f"- selected_feature_count: {summary['selected_feature_count']}\n"
            f"- baseline_target_rate: {summary['baseline_target_rate']:.6f}\n"
        )

    return SelectionResult(
        selected_frame=selected_frame,
        scorecard=scorecard,
        drop_report=filtered.drop_report,
        correlation_groups=corr_rows,
        summary=summary,
    )

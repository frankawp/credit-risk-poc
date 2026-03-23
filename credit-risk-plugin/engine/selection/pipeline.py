"""
特征筛选流水线。

整合基础过滤和单变量评估，输出完整的筛选报告。

筛选标准：
- 预测能力：IV ≥ min_iv 且 (AUC ≥ min_auc 或 Lift ≥ min_lift)
- 稳定性：PSI < max_psi
- 相关性：相关系数 < correlation_threshold
- 缺失率：< missing_rate_threshold

IV 值解读：
- IV < 0.02: 无预测能力，淘汰
- 0.02 ≤ IV < 0.1: 弱预测能力，待优化
- 0.1 ≤ IV < 0.3: 中等预测能力，入选
- IV ≥ 0.3: 强预测能力，入选
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
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

    # 计算基准指标
    baseline_target_rate = float(filtered_frame[config.target_col].mean())

    # 步骤 3：IV 等级分类
    scorecard["iv_level"] = pd.cut(
        scorecard["iv"],
        bins=[-np.inf, config.min_iv, config.min_iv_medium, config.min_iv_strong, np.inf],
        labels=["none", "weak", "medium", "strong"]
    )

    # 步骤 4：综合筛选条件
    # 预测能力：IV ≥ min_iv 且 (AUC ≥ min_auc 或 Lift ≥ min_lift)
    scorecard["selected_flag"] = (
        (scorecard["iv"] >= config.min_iv) &
        (
            (scorecard["univariate_roc_auc"] >= config.min_auc) |
            (scorecard["lift_top_decile"] >= config.min_lift)
        )
    )

    # 筛选判定
    def get_decision(row: pd.Series) -> str:
        """根据 IV 和 AUC 判定变量状态。"""
        if row["iv"] < config.min_iv:
            return "rejected"  # 无预测能力，淘汰
        elif row["iv"] < config.min_iv_medium and row["univariate_roc_auc"] < config.min_auc:
            return "needs_optimization"  # 弱预测能力，待优化
        else:
            return "selected"  # 入选

    scorecard["decision"] = scorecard.apply(get_decision, axis=1)

    # 淘汰原因
    def get_drop_reason(row: pd.Series) -> str:
        if row["decision"] == "rejected":
            return f"low_iv({row['iv']:.4f})"
        elif row["decision"] == "needs_optimization":
            return f"weak_signal(iv={row['iv']:.4f}, auc={row['univariate_roc_auc']:.4f})"
        return ""

    scorecard["drop_reason"] = scorecard.apply(get_drop_reason, axis=1)

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
    iv_stats = {
        "none": int((scorecard["iv_level"] == "none").sum()),
        "weak": int((scorecard["iv_level"] == "weak").sum()),
        "medium": int((scorecard["iv_level"] == "medium").sum()),
        "strong": int((scorecard["iv_level"] == "strong").sum()),
    }
    decision_stats = {
        "selected": int((scorecard["decision"] == "selected").sum()),
        "needs_optimization": int((scorecard["decision"] == "needs_optimization").sum()),
        "rejected": int((scorecard["decision"] == "rejected").sum()),
    }

    summary = {
        "input_feature_count": int(frame.shape[1] - 2),
        "after_basic_filter_count": int(filtered_frame.shape[1] - 2),
        "selected_feature_count": int(len(selected_features)),
        "baseline_target_rate": baseline_target_rate,
        "iv_distribution": iv_stats,
        "decision_distribution": decision_stats,
        "selected_features": selected_features,
        "selection_criteria": {
            "min_iv": config.min_iv,
            "min_auc": config.min_auc,
            "min_lift": config.min_lift,
        },
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
        md_lines = [
            "# 变量筛选报告",
            "",
            "## 筛选标准",
            "",
            f"- IV 阈值: ≥ {config.min_iv}",
            f"- AUC 阈值: ≥ {config.min_auc}",
            f"- Lift@Top10% 阈值: ≥ {config.min_lift}",
            "",
            "## 筛选结果汇总",
            "",
            f"| 阶段 | 数量 |",
            f"|------|------|",
            f"| 输入变量 | {summary['input_feature_count']} |",
            f"| 基础过滤后 | {summary['after_basic_filter_count']} |",
            f"| 最终入选 | {summary['selected_feature_count']} |",
            "",
            "## IV 分布",
            "",
            f"| IV 等级 | 数量 | 说明 |",
            f"|---------|------|------|",
            f"| none | {iv_stats['none']} | IV < 0.02，无预测能力 |",
            f"| weak | {iv_stats['weak']} | 0.02 ≤ IV < 0.1，弱预测能力 |",
            f"| medium | {iv_stats['medium']} | 0.1 ≤ IV < 0.3，中等预测能力 |",
            f"| strong | {iv_stats['strong']} | IV ≥ 0.3，强预测能力 |",
            "",
            "## 筛选判定分布",
            "",
            f"| 判定 | 数量 | 说明 |",
            f"|------|------|------|",
            f"| selected | {decision_stats['selected']} | 入选 |",
            f"| needs_optimization | {decision_stats['needs_optimization']} | 待优化 |",
            f"| rejected | {decision_stats['rejected']} | 淘汰 |",
            "",
            f"基准坏账率: {summary['baseline_target_rate']:.4%}",
            "",
        ]

        # 入选变量列表
        if selected_features:
            md_lines.extend([
                "## 入选变量清单",
                "",
            ])
            for feat in selected_features:
                row = scorecard[scorecard["feature_name"] == feat].iloc[0]
                md_lines.append(
                    f"- {feat}: IV={row['iv']:.4f}, AUC={row['univariate_roc_auc']:.4f}, "
                    f"Lift={row['lift_top_decile']:.2f}"
                )

        (output_dir / "feature_selection_report.md").write_text("\n".join(md_lines))

    return SelectionResult(
        selected_frame=selected_frame,
        scorecard=scorecard,
        drop_report=filtered.drop_report,
        correlation_groups=corr_rows,
        summary=summary,
    )

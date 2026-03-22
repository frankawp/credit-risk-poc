"""
稳定性检查模块。

提供特征稳定性评估能力：
- PSI (Population Stability Index) 计算
- 时间分片稳定性检查
- 分组一致性检查
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class StabilityResult:
    """稳定性检查结果。"""

    feature_name: str
    psi: float
    is_stable: bool
    stability_level: str
    details: dict


# PSI 稳定性阈值
PSI_THRESHOLDS = {
    "stable": 0.1,       # PSI < 0.1: 稳定
    "moderate": 0.25,    # 0.1 <= PSI < 0.25: 中等变化
    # PSI >= 0.25: 显著变化
}


def calculate_psi(
    expected: np.ndarray,
    actual: np.ndarray,
    n_bins: int = 10,
    min_pct: float = 0.01,
) -> float:
    """计算 PSI (Population Stability Index)。

    PSI 衡量两个分布的差异程度：
    - PSI < 0.1: 分布稳定
    - 0.1 <= PSI < 0.25: 中等变化，需关注
    - PSI >= 0.25: 显著变化，需处理

    参数：
        expected: 基准分布（通常是训练集）
        actual: 待评估分布（通常是测试集或新数据）
        n_bins: 分箱数量
        min_pct: 最小占比，避免除零

    返回：
        PSI 值
    """
    # 移除缺失值
    expected = np.asarray(expected)[~np.isnan(expected)]
    actual = np.asarray(actual)[~np.isnan(actual)]

    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    # 基于基准分布确定分箱边界
    bins = np.percentile(expected, np.linspace(0, 100, n_bins + 1))
    bins = np.unique(bins)  # 去重
    if len(bins) < 2:
        return 0.0

    # 确保边界覆盖所有值
    bins[0] = -np.inf
    bins[-1] = np.inf

    # 计算各箱占比
    expected_counts, _ = np.histogram(expected, bins=bins)
    actual_counts, _ = np.histogram(actual, bins=bins)

    expected_pct = expected_counts / len(expected)
    actual_pct = actual_counts / len(actual)

    # 应用最小占比
    expected_pct = np.maximum(expected_pct, min_pct)
    actual_pct = np.maximum(actual_pct, min_pct)

    # 计算 PSI
    psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))

    return float(psi)


def _get_stability_level(psi: float) -> tuple[bool, str]:
    """根据 PSI 值判断稳定性等级。"""
    if psi < PSI_THRESHOLDS["stable"]:
        return True, "stable"
    elif psi < PSI_THRESHOLDS["moderate"]:
        return True, "moderate"
    else:
        return False, "unstable"


def check_feature_stability(
    feature_name: str,
    train_values: np.ndarray,
    test_values: np.ndarray,
    n_bins: int = 10,
) -> StabilityResult:
    """检查单个特征的稳定性。

    参数：
        feature_name: 特征名
        train_values: 训练集值
        test_values: 测试集值
        n_bins: 分箱数

    返回：
        StabilityResult
    """
    psi = calculate_psi(train_values, test_values, n_bins)
    is_stable, level = _get_stability_level(psi)

    return StabilityResult(
        feature_name=feature_name,
        psi=psi,
        is_stable=is_stable,
        stability_level=level,
        details={
            "train_missing_rate": float(np.isnan(train_values).mean()),
            "test_missing_rate": float(np.isnan(test_values).mean()),
            "train_mean": float(np.nanmean(train_values)),
            "test_mean": float(np.nanmean(test_values)),
            "train_std": float(np.nanstd(train_values)),
            "test_std": float(np.nanstd(test_values)),
        },
    )


def check_time_stability(
    frame: pd.DataFrame,
    time_col: str,
    feature_cols: list[str] | None = None,
    id_col: str | None = None,
    target_col: str | None = None,
    n_splits: int = 3,
    n_bins: int = 10,
    output_dir: Path | None = None,
) -> pd.DataFrame:
    """检查时间分片稳定性。

    将数据按时间列分片，计算各特征在不同时间片的 PSI。

    参数：
        frame: 数据框
        time_col: 时间列名
        feature_cols: 待检查的特征列（None 则自动推断）
        id_col: ID 列（用于排除）
        target_col: 目标列（用于排除）
        n_splits: 时间分片数
        n_bins: PSI 分箱数
        output_dir: 输出目录

    返回：
        稳定性报告 DataFrame
    """
    # 推断特征列
    if feature_cols is None:
        exclude_cols = {time_col, id_col, target_col} - {None}
        feature_cols = [
            c for c in frame.columns
            if c not in exclude_cols and pd.api.types.is_numeric_dtype(frame[c])
        ]

    # 按时间分片
    time_values = frame[time_col].dropna()
    if len(time_values) == 0:
        raise ValueError(f"时间列 {time_col} 无有效值")

    # 计算分位点
    quantiles = np.linspace(0, 1, n_splits + 1)
    split_points = np.quantile(time_values, quantiles)

    # 分片
    splits = []
    for i in range(n_splits):
        if i == 0:
            mask = frame[time_col] <= split_points[i + 1]
        elif i == n_splits - 1:
            mask = frame[time_col] > split_points[i]
        else:
            mask = (frame[time_col] > split_points[i]) & (frame[time_col] <= split_points[i + 1])
        splits.append(frame[mask])

    # 以第一个分片为基准
    base_split = splits[0]

    # 检查每个特征
    results = []
    for col in feature_cols:
        base_values = base_split[col].to_numpy()

        for i, split in enumerate(splits[1:], start=1):
            test_values = split[col].to_numpy()
            result = check_feature_stability(col, base_values, test_values, n_bins)

            results.append({
                "feature_name": col,
                "split_index": i,
                "split_label": f"split_{i}",
                "psi": result.psi,
                "is_stable": result.is_stable,
                "stability_level": result.stability_level,
                **result.details,
            })

    # 构建报告
    report = pd.DataFrame(results)

    # 聚合结果：取最大 PSI
    agg_report = report.groupby("feature_name").agg({
        "psi": "max",
        "is_stable": "all",
        "stability_level": lambda x: "unstable" if "unstable" in x.values else ("moderate" if "moderate" in x.values else "stable"),
    }).reset_index()
    agg_report.columns = ["feature_name", "max_psi", "is_stable", "stability_level"]

    # 保存
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        report.to_csv(output_dir / "time_stability_detail.csv", index=False)
        agg_report.to_csv(output_dir / "time_stability_summary.csv", index=False)

        # Markdown 报告
        _generate_stability_report(agg_report, output_dir)

    return agg_report


def check_slice_consistency(
    frame: pd.DataFrame,
    slice_col: str,
    feature_cols: list[str] | None = None,
    id_col: str | None = None,
    target_col: str | None = None,
    min_slice_size: int = 100,
    n_bins: int = 10,
    output_dir: Path | None = None,
) -> pd.DataFrame:
    """检查分组一致性。

    检查特征在不同分组间的分布一致性。

    参数：
        frame: 数据框
        slice_col: 分组列名
        feature_cols: 待检查的特征列
        id_col: ID 列
        target_col: 目标列
        min_slice_size: 最小分组大小
        n_bins: PSI 分箱数
        output_dir: 输出目录

    返回：
        一致性报告 DataFrame
    """
    # 推断特征列
    if feature_cols is None:
        exclude_cols = {slice_col, id_col, target_col} - {None}
        feature_cols = [
            c for c in frame.columns
            if c not in exclude_cols and pd.api.types.is_numeric_dtype(frame[c])
        ]

    # 获取有效分组
    slice_counts = frame[slice_col].value_counts()
    valid_slices = slice_counts[slice_counts >= min_slice_size].index.tolist()

    if len(valid_slices) < 2:
        raise ValueError(f"有效分组数不足 2 个（需要至少 {min_slice_size} 条记录）")

    # 以最大分组为基准
    base_slice_name = slice_counts.idxmax()
    base_slice = frame[frame[slice_col] == base_slice_name]

    # 检查每个特征
    results = []
    for col in feature_cols:
        base_values = base_slice[col].to_numpy()

        for slice_name in valid_slices:
            if slice_name == base_slice_name:
                continue

            test_slice = frame[frame[slice_col] == slice_name]
            test_values = test_slice[col].to_numpy()

            result = check_feature_stability(col, base_values, test_values, n_bins)

            results.append({
                "feature_name": col,
                "slice_name": slice_name,
                "psi": result.psi,
                "is_stable": result.is_stable,
                "stability_level": result.stability_level,
                **result.details,
            })

    # 构建报告
    report = pd.DataFrame(results)

    # 聚合结果
    agg_report = report.groupby("feature_name").agg({
        "psi": "max",
        "is_stable": "all",
        "stability_level": lambda x: "unstable" if "unstable" in x.values else ("moderate" if "moderate" in x.values else "stable"),
    }).reset_index()
    agg_report.columns = ["feature_name", "max_psi", "is_stable", "stability_level"]

    # 保存
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        report.to_csv(output_dir / "slice_consistency_detail.csv", index=False)
        agg_report.to_csv(output_dir / "slice_consistency_summary.csv", index=False)

    return agg_report


def run_stability_check(
    frame: pd.DataFrame,
    config: dict,
    output_dir: Path | None = None,
) -> tuple[pd.DataFrame, dict]:
    """执行完整的稳定性检查。

    参数：
        frame: 数据框
        config: 配置字典，包含：
            - time_col: 时间列（可选）
            - slice_col: 分组列（可选）
            - id_col: ID 列
            - target_col: 目标列
            - feature_cols: 特征列列表
        output_dir: 输出目录

    返回：
        (综合报告, 汇总统计)
    """
    results = []

    # 时间稳定性检查
    if config.get("time_col"):
        time_report = check_time_stability(
            frame=frame,
            time_col=config["time_col"],
            feature_cols=config.get("feature_cols"),
            id_col=config.get("id_col"),
            target_col=config.get("target_col"),
            output_dir=output_dir / "time_stability" if output_dir else None,
        )
        time_report["check_type"] = "time_stability"
        results.append(time_report)

    # 分组一致性检查
    if config.get("slice_col"):
        slice_report = check_slice_consistency(
            frame=frame,
            slice_col=config["slice_col"],
            feature_cols=config.get("feature_cols"),
            id_col=config.get("id_col"),
            target_col=config.get("target_col"),
            output_dir=output_dir / "slice_consistency" if output_dir else None,
        )
        slice_report["check_type"] = "slice_consistency"
        results.append(slice_report)

    # 合并结果
    if results:
        combined = pd.concat(results, ignore_index=True)
    else:
        combined = pd.DataFrame(columns=["feature_name", "max_psi", "is_stable", "stability_level", "check_type"])

    # 汇总统计
    summary = {
        "total_features_checked": combined["feature_name"].nunique() if len(combined) > 0 else 0,
        "stable_count": int((combined["stability_level"] == "stable").sum()) if len(combined) > 0 else 0,
        "moderate_count": int((combined["stability_level"] == "moderate").sum()) if len(combined) > 0 else 0,
        "unstable_count": int((combined["stability_level"] == "unstable").sum()) if len(combined) > 0 else 0,
    }

    return combined, summary


def _generate_stability_report(report: pd.DataFrame, output_dir: Path) -> None:
    """生成 Markdown 稳定性报告。"""
    stable = report[report["stability_level"] == "stable"]
    moderate = report[report["stability_level"] == "moderate"]
    unstable = report[report["stability_level"] == "unstable"]

    lines = [
        "# Feature Stability Report",
        "",
        "## Summary",
        "",
        f"| Stability Level | Count |",
        f"|----------------|-------|",
        f"| Stable (PSI < 0.1) | {len(stable)} |",
        f"| Moderate (0.1 <= PSI < 0.25) | {len(moderate)} |",
        f"| Unstable (PSI >= 0.25) | {len(unstable)} |",
        "",
    ]

    if len(unstable) > 0:
        lines.extend([
            "## Unstable Features (需要处理)",
            "",
            "| Feature | Max PSI |",
            "|---------|---------|",
        ])
        for _, row in unstable.nlargest(20, "max_psi").iterrows():
            lines.append(f"| {row['feature_name']} | {row['max_psi']:.4f} |")
        lines.append("")

    if len(moderate) > 0:
        lines.extend([
            "## Moderate Features (需关注)",
            "",
            "| Feature | Max PSI |",
            "|---------|---------|",
        ])
        for _, row in moderate.nlargest(20, "max_psi").iterrows():
            lines.append(f"| {row['feature_name']} | {row['max_psi']:.4f} |")
        lines.append("")

    (output_dir / "stability_report.md").write_text("\n".join(lines))

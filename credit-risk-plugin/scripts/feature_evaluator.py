#!/usr/bin/env python3
"""
变量评估工具 - 计算变量的预测能力和分布特征。

用法:
    python feature_evaluator.py <特征矩阵> --target <目标列>
    python feature_evaluator.py <特征矩阵> --target <目标列> --output <输出文件>

示例:
    python feature_evaluator.py outputs/features.parquet --target TARGET
    python feature_evaluator.py outputs/features.csv --target bad_flag --output outputs/evaluation.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def evaluate_single_feature(
    feature: pd.Series,
    target: pd.Series,
    feature_name: str,
) -> dict[str, Any]:
    """
    评估单个变量的预测能力。

    返回 ROC-AUC、PR-AUC、缺失率、Lift 等指标。
    """
    # 对齐索引
    aligned = pd.DataFrame({"feature": feature, "target": target}).dropna()

    if len(aligned) < 10:
        return {
            "feature_name": feature_name,
            "valid_count": len(aligned),
            "warning": "有效样本数过少，无法评估",
        }

    X = aligned["feature"].values
    y = aligned["target"].values

    # 检查是否为二分类
    unique_targets = set(y)
    if len(unique_targets) != 2:
        return {
            "feature_name": feature_name,
            "valid_count": len(aligned),
            "warning": f"目标变量不是二分类，取值：{unique_targets}",
        }

    # 检查特征是否为常数
    if len(np.unique(X)) == 1:
        return {
            "feature_name": feature_name,
            "valid_count": len(aligned),
            "warning": "特征为常数，无法评估",
        }

    try:
        from sklearn.metrics import roc_auc_score, average_precision_score

        roc_auc = roc_auc_score(y, X)
        pr_auc = average_precision_score(y, X)
    except Exception as e:
        return {
            "feature_name": feature_name,
            "valid_count": len(aligned),
            "warning": f"无法计算 AUC：{e}",
        }

    # 计算 top 10% lift
    top_k = max(1, int(len(aligned) * 0.1))
    top_indices = aligned.nlargest(top_k, "feature").index
    top_bad_rate = aligned.loc[top_indices, "target"].mean()
    overall_bad_rate = aligned["target"].mean()
    lift_top_decile = top_bad_rate / overall_bad_rate if overall_bad_rate > 0 else 0

    # 计算分布特征
    return {
        "feature_name": feature_name,
        "valid_count": len(aligned),
        "missing_rate": round(1 - len(aligned) / len(feature), 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "lift_top_decile": round(lift_top_decile, 4),
        "mean": round(float(aligned["feature"].mean()), 4),
        "std": round(float(aligned["feature"].std()), 4),
        "min": round(float(aligned["feature"].min()), 4),
        "max": round(float(aligned["feature"].max()), 4),
    }


def evaluate_features(
    feature_matrix_path: Path,
    target_column: str,
    output_path: Path | None = None,
    exclude_columns: list[str] | None = None,
) -> dict[str, Any]:
    """
    评估特征矩阵中的所有变量。

    参数:
        feature_matrix_path: 特征矩阵文件路径
        target_column: 目标变量列名
        output_path: 输出报告路径
        exclude_columns: 排除评估的列名列表
    """
    # 读取数据
    if feature_matrix_path.suffix == ".parquet":
        df = pd.read_parquet(feature_matrix_path)
    elif feature_matrix_path.suffix == ".csv":
        df = pd.read_csv(feature_matrix_path)
    else:
        return {
            "status": "error",
            "message": f"不支持的文件格式：{feature_matrix_path.suffix}",
        }

    # 检查目标列
    if target_column not in df.columns:
        return {
            "status": "error",
            "message": f"目标列 '{target_column}' 不存在",
            "available_columns": list(df.columns)[:10],
        }

    target = df[target_column]
    exclude = set(exclude_columns or [])
    exclude.add(target_column)

    # 识别数值型特征列
    numeric_cols = [
        col for col in df.columns
        if col not in exclude and df[col].dtype in ["int64", "float64", "int32", "float32"]
    ]

    # 评估每个特征
    evaluations = []
    for col in numeric_cols:
        result = evaluate_single_feature(df[col], target, col)
        evaluations.append(result)

    # 排序
    evaluations.sort(key=lambda x: x.get("roc_auc", 0.5), reverse=True)

    # 统计有效特征
    effective = [
        e for e in evaluations
        if "warning" not in e and (e.get("roc_auc", 0.5) > 0.52 or e.get("lift_top_decile", 0) > 1.02)
    ]

    report = {
        "status": "success",
        "feature_matrix": str(feature_matrix_path),
        "target_column": target_column,
        "total_features": len(numeric_cols),
        "evaluated_features": len(evaluations),
        "effective_features": len(effective),
        "evaluations": evaluations,
        "top_10_features": evaluations[:10],
    }

    # 保存报告
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        report["output_file"] = str(output_path)

    return report


def print_summary(report: dict[str, Any]) -> None:
    """打印评估报告摘要。"""
    print(f"\n{'='*60}")
    print("变量评估报告")
    print(f"{'='*60}")
    print(f"特征矩阵: {report.get('feature_matrix', 'N/A')}")
    print(f"目标列: {report.get('target_column', 'N/A')}")
    print(f"总变量数: {report.get('total_features', 0)}")
    print(f"有效变量数: {report.get('effective_features', 0)}")
    print()

    print("Top 10 变量:")
    print("-" * 60)
    print(f"{'变量名':<35} {'ROC-AUC':>10} {'Lift':>10}")
    print("-" * 60)

    for e in report.get("top_10_features", []):
        if "warning" in e:
            print(f"{e['feature_name']:<35} {'--':>10} {'--':>10}")
        else:
            print(f"{e['feature_name']:<35} {e['roc_auc']:>10.4f} {e['lift_top_decile']:>10.2f}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="变量评估工具 - 计算变量的预测能力和分布特征"
    )
    parser.add_argument(
        "feature_matrix",
        type=Path,
        help="特征矩阵文件路径 (CSV 或 Parquet)",
    )
    parser.add_argument(
        "--target",
        "-t",
        type=str,
        required=True,
        help="目标变量列名",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="输出报告路径 (JSON格式)",
    )
    parser.add_argument(
        "--exclude",
        "-e",
        type=str,
        nargs="+",
        default=None,
        help="排除评估的列名",
    )

    args = parser.parse_args()

    # 确定输出路径
    output_path = args.output
    if output_path is None:
        output_path = Path("outputs/feature_evaluation.json")

    # 执行评估
    report = evaluate_features(
        feature_matrix_path=args.feature_matrix,
        target_column=args.target,
        output_path=output_path,
        exclude_columns=args.exclude,
    )

    # 打印摘要
    print_summary(report)

    # 输出保存位置
    if "output_file" in report:
        print(f"📄 完整报告已保存到: {report['output_file']}")


if __name__ == "__main__":
    main()

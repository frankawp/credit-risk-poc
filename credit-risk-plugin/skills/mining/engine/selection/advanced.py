"""
增强筛选模块。

提供高级特征筛选能力：
- 模型增益评估
- 重复特征检测
- 特征重要性排序
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ModelGainResult:
    """模型增益评估结果。"""

    feature_name: str
    gain_score: float
    relative_gain: float
    rank: int


def detect_duplicates(
    frame: pd.DataFrame,
    id_col: str,
    target_col: str,
    tolerance: float = 1e-9,
) -> pd.DataFrame:
    """检测重复特征。

    检测完全相同或高度相似的特征。

    参数：
        frame: 特征矩阵
        id_col: ID 列名
        target_col: 目标列名
        tolerance: 相似度容忍度

    返回：
        重复特征报告，包含：
        - feature_a: 特征 A
        - feature_b: 特征 B
        - correlation: 相关系数
        - is_duplicate: 是否重复
    """
    # 排除 ID 和目标列
    feature_cols = [c for c in frame.columns if c not in {id_col, target_col}]

    # 计算相关性矩阵
    numeric_cols = [c for c in feature_cols if pd.api.types.is_numeric_dtype(frame[c])]
    corr_matrix = frame[numeric_cols].corr()

    # 找出高相关对
    duplicates = []
    seen_pairs = set()

    for i, col_a in enumerate(numeric_cols):
        for j, col_b in enumerate(numeric_cols):
            if i >= j:
                continue

            pair = tuple(sorted([col_a, col_b]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            corr = abs(corr_matrix.loc[col_a, col_b])
            if corr >= 1 - tolerance:
                duplicates.append({
                    "feature_a": col_a,
                    "feature_b": col_b,
                    "correlation": corr,
                    "is_duplicate": True,
                })

    if duplicates:
        return pd.DataFrame(duplicates)
    else:
        return pd.DataFrame(columns=["feature_a", "feature_b", "correlation", "is_duplicate"])


def detect_near_duplicates(
    frame: pd.DataFrame,
    id_col: str,
    target_col: str,
    threshold: float = 0.99,
) -> pd.DataFrame:
    """检测近重复特征。

    与 detect_duplicates 类似，但使用可配置的阈值。

    参数：
        frame: 特征矩阵
        id_col: ID 列名
        target_col: 目标列名
        threshold: 相关性阈值

    返回：
        近重复特征报告
    """
    feature_cols = [c for c in frame.columns if c not in {id_col, target_col}]
    numeric_cols = [c for c in feature_cols if pd.api.types.is_numeric_dtype(frame[c])]
    corr_matrix = frame[numeric_cols].corr()

    near_duplicates = []
    seen_pairs = set()

    for i, col_a in enumerate(numeric_cols):
        for j, col_b in enumerate(numeric_cols):
            if i >= j:
                continue

            pair = tuple(sorted([col_a, col_b]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            corr = abs(corr_matrix.loc[col_a, col_b])
            if corr >= threshold:
                near_duplicates.append({
                    "feature_a": col_a,
                    "feature_b": col_b,
                    "correlation": corr,
                    "is_duplicate": corr >= 0.9999,
                })

    if near_duplicates:
        return pd.DataFrame(near_duplicates)
    else:
        return pd.DataFrame(columns=["feature_a", "feature_b", "correlation", "is_duplicate"])


def evaluate_model_gain(
    frame: pd.DataFrame,
    base_features: list[str],
    candidate_features: list[str],
    id_col: str,
    target_col: str,
    model_type: str = "lightgbm",
    cv_folds: int = 3,
    random_state: int = 42,
) -> pd.DataFrame:
    """评估特征对模型的增益。

    通过对比基线模型和添加新特征后的模型表现，评估特征增益。

    参数：
        frame: 特征矩阵
        base_features: 基线特征列表
        candidate_features: 待评估特征列表
        id_col: ID 列名
        target_col: 目标列名
        model_type: 模型类型 ("lightgbm", "xgboost", "rf")
        cv_folds: 交叉验证折数
        random_state: 随机种子

    返回：
        特征增益报告
    """
    # 延迟导入，避免强依赖
    try:
        from sklearn.model_selection import cross_val_score
        from sklearn.metrics import roc_auc_score, make_scorer
    except ImportError:
        raise ImportError("需要安装 scikit-learn: pip install scikit-learn")

    # 准备数据
    X_base = frame[base_features].copy()
    y = frame[target_col].to_numpy()

    # 处理缺失值
    for col in base_features:
        if X_base[col].isna().any():
            X_base[col] = X_base[col].fillna(X_base[col].median())

    # 获取模型
    model = _get_model(model_type, random_state)

    # 基线评分
    try:
        base_scores = cross_val_score(
            model, X_base, y,
            cv=cv_folds,
            scoring="roc_auc",
        )
        base_mean = base_scores.mean()
        base_std = base_scores.std()
    except Exception as e:
        print(f"基线模型训练失败: {e}")
        return pd.DataFrame()

    # 评估每个候选特征
    results = []
    valid_candidates = [f for f in candidate_features if f in frame.columns]

    for i, feature in enumerate(valid_candidates):
        # 添加候选特征
        X_extended = X_base.copy()
        X_extended[feature] = frame[feature].values

        # 处理缺失值
        if X_extended[feature].isna().any():
            X_extended[feature] = X_extended[feature].fillna(X_extended[feature].median())

        try:
            extended_scores = cross_val_score(
                model, X_extended, y,
                cv=cv_folds,
                scoring="roc_auc",
            )
            extended_mean = extended_scores.mean()
            extended_std = extended_scores.std()

            gain = extended_mean - base_mean
            relative_gain = gain / base_mean if base_mean > 0 else 0

            results.append(ModelGainResult(
                feature_name=feature,
                gain_score=gain,
                relative_gain=relative_gain,
                rank=0,  # 后续排序填充
            ))
        except Exception as e:
            print(f"特征 {feature} 评估失败: {e}")
            continue

    # 排序并填充排名
    results.sort(key=lambda x: x.gain_score, reverse=True)
    ranked_results = []
    for rank, r in enumerate(results, start=1):
        ranked_results.append({
            "feature_name": r.feature_name,
            "gain_score": r.gain_score,
            "relative_gain": r.relative_gain,
            "rank": rank,
        })

    return pd.DataFrame(ranked_results)


def _get_model(model_type: str, random_state: int) -> Any:
    """获取模型实例。"""
    if model_type == "lightgbm":
        try:
            from lightgbm import LGBMClassifier
            return LGBMClassifier(
                n_estimators=100,
                max_depth=4,
                random_state=random_state,
                verbose=-1,
            )
        except ImportError:
            pass

    if model_type == "xgboost":
        try:
            from xgboost import XGBClassifier
            return XGBClassifier(
                n_estimators=100,
                max_depth=4,
                random_state=random_state,
                verbosity=0,
            )
        except ImportError:
            pass

    # 默认使用 RandomForest
    from sklearn.ensemble import RandomForestClassifier
    return RandomForestClassifier(
        n_estimators=100,
        max_depth=4,
        random_state=random_state,
        n_jobs=-1,
    )


def evaluate_incremental_gain(
    frame: pd.DataFrame,
    feature_cols: list[str],
    id_col: str,
    target_col: str,
    model_type: str = "lightgbm",
    cv_folds: int = 3,
    min_gain: float = 0.0001,
    output_dir: Path | None = None,
) -> pd.DataFrame:
    """增量评估特征增益（前向选择）。

    从空集开始，逐步添加增益最大的特征。

    参数：
        frame: 特征矩阵
        feature_cols: 特征列列表
        id_col: ID 列名
        target_col: 目标列名
        model_type: 模型类型
        cv_folds: 交叉验证折数
        min_gain: 最小增益阈值
        output_dir: 输出目录

    返回：
        特征增益报告
    """
    try:
        from sklearn.model_selection import cross_val_score
    except ImportError:
        raise ImportError("需要安装 scikit-learn: pip install scikit-learn")

    y = frame[target_col].to_numpy()
    remaining = list(feature_cols)
    selected = []
    results = []

    # 初始基线（使用目标率）
    baseline_auc = 0.5  # 随机基线

    iteration = 0
    while remaining:
        iteration += 1
        best_gain = -np.inf
        best_feature = None

        for feature in remaining:
            # 构建当前特征集
            current_features = selected + [feature]
            X = frame[current_features].copy()

            # 处理缺失值
            for col in current_features:
                if X[col].isna().any():
                    X[col] = X[col].fillna(X[col].median())

            # 评估
            model = _get_model(model_type, 42)
            try:
                scores = cross_val_score(model, X, y, cv=cv_folds, scoring="roc_auc")
                mean_auc = scores.mean()
                gain = mean_auc - (baseline_auc if not selected else results[-1]["cumulative_auc"])
            except Exception:
                continue

            if gain > best_gain:
                best_gain = gain
                best_feature = feature
                best_auc = mean_auc

        if best_feature is None or best_gain < min_gain:
            break

        selected.append(best_feature)
        remaining.remove(best_feature)

        results.append({
            "iteration": iteration,
            "feature_name": best_feature,
            "gain": best_gain,
            "cumulative_auc": best_auc,
            "selected_count": len(selected),
        })

        print(f"Iteration {iteration}: {best_feature} (gain={best_gain:.6f}, AUC={best_auc:.6f})")

    report = pd.DataFrame(results)

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        report.to_csv(output_dir / "incremental_gain_report.csv", index=False)

    return report


def run_advanced_selection(
    frame: pd.DataFrame,
    id_col: str,
    target_col: str,
    feature_cols: list[str] | None = None,
    detect_duplicate: bool = True,
    evaluate_gain: bool = True,
    duplicate_threshold: float = 0.99,
    output_dir: Path | None = None,
) -> dict:
    """执行高级筛选流程。

    参数：
        frame: 特征矩阵
        id_col: ID 列名
        target_col: 目标列名
        feature_cols: 特征列列表
        detect_duplicate: 是否检测重复
        evaluate_gain: 是否评估增益
        duplicate_threshold: 重复检测阈值
        output_dir: 输出目录

    返回：
        包含各类筛选结果的字典
    """
    if feature_cols is None:
        feature_cols = [c for c in frame.columns if c not in {id_col, target_col}]

    results = {}

    # 重复检测
    if detect_duplicate:
        dup_report = detect_near_duplicates(frame, id_col, target_col, duplicate_threshold)
        results["duplicates"] = dup_report

        if output_dir:
            dup_report.to_csv(output_dir / "duplicate_features.csv", index=False)

    # 模型增益评估
    if evaluate_gain and len(feature_cols) > 0:
        # 选择基线特征（已有单变量评估中表现较好的）
        # 这里简化处理，使用前 10 个特征作为基线
        base_features = feature_cols[:min(10, len(feature_cols))]
        candidates = feature_cols[min(10, len(feature_cols)):]

        if candidates:
            gain_report = evaluate_model_gain(
                frame=frame,
                base_features=base_features,
                candidate_features=candidates,
                id_col=id_col,
                target_col=target_col,
            )
            results["model_gain"] = gain_report

            if output_dir:
                gain_report.to_csv(output_dir / "model_gain_report.csv", index=False)

    # 汇总
    summary = {
        "total_features": len(feature_cols),
        "duplicate_pairs": len(results.get("duplicates", [])),
        "features_with_positive_gain": int((results.get("model_gain", pd.DataFrame())["gain_score"] > 0).sum()) if "model_gain" in results else 0,
    }
    results["summary"] = summary

    return results

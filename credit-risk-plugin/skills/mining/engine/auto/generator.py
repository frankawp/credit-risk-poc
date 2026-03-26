"""
自动特征生成器。

使用 Featuretools 进行自动化统计挖掘，生成基于实体关系的特征。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import AutoFeatureConfig, EnginePaths

# Featuretools 是可选依赖
try:
    import featuretools as ft
    FT_AVAILABLE = True
except ImportError:
    FT_AVAILABLE = False


@dataclass(frozen=True)
class AutoFeatureResult:
    """自动特征生成结果。"""

    feature_matrix: pd.DataFrame
    feature_names: list[str]
    feature_defs: list[Any] | None = None


def _drop_target_derived_features(
    frame: pd.DataFrame,
    feature_names: list[str],
    target_col: str = "TARGET",
) -> tuple[pd.DataFrame, list[str]]:
    """移除从目标变量派生的特征，防止数据泄露。"""
    leakage_names = [name for name in feature_names if target_col in name and name != target_col]
    if not leakage_names:
        return frame, feature_names
    filtered_frame = frame.drop(columns=leakage_names, errors="ignore")
    filtered_names = [name for name in feature_names if name not in leakage_names]
    return filtered_frame, filtered_names


def generate_auto_features(
    entityset: "ft.EntitySet",
    target_entity: str,
    output_dir: Path | None = None,
    config: AutoFeatureConfig | None = None,
    agg_primitives: list[str] | None = None,
    trans_primitives: list[str] | None = None,
    target_col: str = "TARGET",
) -> AutoFeatureResult:
    """生成自动特征。

    参数：
        entityset: Featuretools EntitySet 对象
        target_entity: 目标实体名称（通常是锚点表）
        output_dir: 输出目录（可选）
        config: 自动特征配置
        agg_primitives: 聚合原语列表
        trans_primitives: 转换原语列表
        target_col: 目标变量列名

    返回：
        AutoFeatureResult 包含特征矩阵和特征名列表

    注意：
        需要安装 featuretools: pip install featuretools
    """
    if not FT_AVAILABLE:
        raise ImportError(
            "Featuretools 未安装。请运行: pip install featuretools"
        )

    config = config or AutoFeatureConfig()

    # 默认原语
    agg_primitives = agg_primitives or ["sum", "mean", "max", "min", "std", "count", "num_unique"]
    trans_primitives = trans_primitives or ["absolute"]

    # 深度特征合成
    feature_matrix, feature_defs = ft.dfs(
        entityset=entityset,
        target_dataframe_name=target_entity,
        agg_primitives=agg_primitives,
        trans_primitives=trans_primitives,
        max_depth=config.max_depth,
        features_only=False,
        verbose=True,
    )

    # 整理结果
    frame = feature_matrix.reset_index()
    names = [f.get_name() for f in feature_defs]

    # 移除目标变量派生特征
    frame, names = _drop_target_derived_features(frame, names, target_col)

    # 保存输出
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(output_dir / "auto_feature_matrix.parquet", index=False)
        pd.DataFrame({
            "feature_name": names,
            "feature_source": "auto",
        }).to_csv(output_dir / "auto_feature_defs.csv", index=False)

    return AutoFeatureResult(
        feature_matrix=frame,
        feature_names=names,
        feature_defs=feature_defs,
    )


def check_featuretools_available() -> bool:
    """检查 Featuretools 是否可用。"""
    return FT_AVAILABLE

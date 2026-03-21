"""
语义特征生成器。

协调所有主题，生成统一的语义特征矩阵。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from ..config import EnginePaths
from .base import to_registry_frame
from .registry import get_registry, ThemeRegistry


@dataclass(frozen=True)
class SemanticFeatureResult:
    """语义特征生成结果。"""

    feature_matrix: pd.DataFrame
    registry: pd.DataFrame


def generate_semantic_features(
    frames: dict[str, pd.DataFrame],
    anchor: pd.DataFrame,
    themes: Iterable[str] | None = None,
    output_dir: Path | None = None,
) -> SemanticFeatureResult:
    """生成语义特征。

    参数：
        frames: 表名到 DataFrame 的映射
        anchor: 锚点表（包含实体 ID 和目标变量）
        themes: 要生成的主题列表（None 表示全部）
        output_dir: 输出目录（可选）

    返回：
        SemanticFeatureResult 包含特征矩阵和注册表
    """
    registry = get_registry()
    requested_themes = list(themes) if themes else registry.list_themes()

    # 获取实体 ID 列
    entity_id_col = _detect_entity_id_column(anchor)

    # 构建基础 DataFrame
    result = anchor.copy()
    all_specs = []

    for theme_name in requested_themes:
        theme = registry.get(theme_name)
        if theme is None:
            continue

        # 验证数据可用性
        available, missing = theme.validate_data_availability(frames)
        if not available:
            print(f"⚠️ 主题 {theme_name} 缺少数据: {', '.join(missing)}")
            continue

        # 构建特征
        theme_features = theme.build_features(frames, anchor)

        # 合并（避免重复列）
        for col in theme_features.columns:
            if col == entity_id_col or col in result.columns:
                continue
            result[col] = theme_features[col].values

        all_specs.extend(theme.feature_specs())

    # 构建注册表
    registry_frame = to_registry_frame(all_specs)

    # 保存输出
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        result.to_parquet(output_dir / "semantic_feature_matrix.parquet", index=False)
        registry_frame.to_csv(output_dir / "semantic_feature_registry.csv", index=False)

    return SemanticFeatureResult(feature_matrix=result, registry=registry_frame)


def _detect_entity_id_column(df: pd.DataFrame) -> str:
    """检测实体 ID 列。"""
    # 常见的 ID 列名
    candidates = ["SK_ID_CURR", "entity_id", "id", "ID", "customer_id", "user_id"]
    for col in candidates:
        if col in df.columns:
            return col

    # 找第一个包含 "id" 的列
    for col in df.columns:
        if "id" in col.lower():
            return col

    return df.columns[0]


def list_available_themes() -> list[str]:
    """列出所有可用的主题。"""
    return get_registry().list_themes()


def get_theme_description(theme_name: str) -> str | None:
    """获取主题描述。"""
    theme = get_registry().get(theme_name)
    return theme.description if theme else None

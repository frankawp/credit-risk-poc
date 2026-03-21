"""
信贷变量挖掘引擎。

提供双引擎架构：
- Auto Features: 基于 Featuretools 的自动化统计挖掘
- Semantic Features: 业务语义驱动的主题特征

支持：
- Entity Layer: 通用的实体关系图构建
- Composite Features: 组合特征构建
- Selection: 特征筛选流水线
"""

from .config import (
    AutoFeatureConfig,
    EnginePaths,
    EntityConfig,
    FieldMapping,
    SelectionConfig,
)

__all__ = [
    # 配置
    "AutoFeatureConfig",
    "EnginePaths",
    "EntityConfig",
    "FieldMapping",
    "SelectionConfig",
]

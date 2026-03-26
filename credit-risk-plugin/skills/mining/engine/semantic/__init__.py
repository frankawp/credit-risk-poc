"""语义特征模块。

基于业务假设的主题特征生成。
"""

from .base import ThemeBase, FeatureSpec, to_registry_frame
from .registry import ThemeRegistry, get_registry
from .generator import (
    SemanticFeatureResult,
    generate_semantic_features,
    list_available_themes,
    get_theme_description,
)

__all__ = [
    # 基类
    "ThemeBase",
    "FeatureSpec",
    "to_registry_frame",
    # 注册表
    "ThemeRegistry",
    "get_registry",
    # 生成器
    "SemanticFeatureResult",
    "generate_semantic_features",
    "list_available_themes",
    "get_theme_description",
]

"""自动特征生成模块。

基于 Featuretools 的自动化统计挖掘。
"""

from .generator import AutoFeatureResult, generate_auto_features

__all__ = [
    "AutoFeatureResult",
    "generate_auto_features",
]

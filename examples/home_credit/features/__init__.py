"""
Home Credit 案例变量示例

此包包含 Home Credit 数据集的变量实现示例，展示如何使用 credit-risk 插件。
"""

from .consistency import build_consistency_features, FEATURE_DESCRIPTIONS as CONSISTENCY_FEATURES
from .velocity import build_velocity_features, FEATURE_DESCRIPTIONS as VELOCITY_FEATURES
from .cashout import build_cashout_features, FEATURE_DESCRIPTIONS as CASHOUT_FEATURES

__all__ = [
    "build_consistency_features",
    "build_velocity_features",
    "build_cashout_features",
    "CONSISTENCY_FEATURES",
    "VELOCITY_FEATURES",
    "CASHOUT_FEATURES",
]

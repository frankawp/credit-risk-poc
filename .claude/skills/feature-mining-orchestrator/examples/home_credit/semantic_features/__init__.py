"""语义特征生成模块。"""

from .consistency import build_consistency_features
from .velocity import build_velocity_features
from .cashout import build_cashout_features
from .generator import generate_semantic_features
from .registry import semantic_feature_specs, to_registry_frame, IMPLEMENTED_SEMANTIC_THEMES, KNOWN_SEMANTIC_THEMES

__all__ = [
    "build_consistency_features",
    "build_velocity_features",
    "build_cashout_features",
    "generate_semantic_features",
    "semantic_feature_specs",
    "to_registry_frame",
    "IMPLEMENTED_SEMANTIC_THEMES",
    "KNOWN_SEMANTIC_THEMES",
]

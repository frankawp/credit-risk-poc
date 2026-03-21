"""组合特征生成模块。"""

from .specs import composite_feature_specs, composite_specs_frame, CompositeFeatureSpec
from .generator import build_composite_features

__all__ = [
    "composite_feature_specs",
    "composite_specs_frame",
    "CompositeFeatureSpec",
    "build_composite_features",
]

"""组合特征模块。

基于业务语义的特征组合。
"""

from .builder import CompositeFeatureSpec, build_composite_features

__all__ = [
    "CompositeFeatureSpec",
    "build_composite_features",
]

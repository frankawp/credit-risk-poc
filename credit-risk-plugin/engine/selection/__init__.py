"""特征筛选模块。

提供基础过滤、单变量评估、稳定性检查和高级筛选能力。
"""

from .basic_filters import FilterResult, apply_basic_filters
from .univariate import evaluate_univariate
from .pipeline import run_feature_selection
from .stability import (
    StabilityResult,
    calculate_psi,
    check_feature_stability,
    check_time_stability,
    check_slice_consistency,
    run_stability_check,
)
from .advanced import (
    ModelGainResult,
    detect_duplicates,
    detect_near_duplicates,
    evaluate_model_gain,
    evaluate_incremental_gain,
    run_advanced_selection,
)

__all__ = [
    # 基础筛选
    "FilterResult",
    "apply_basic_filters",
    "evaluate_univariate",
    "run_feature_selection",
    # 稳定性检查
    "StabilityResult",
    "calculate_psi",
    "check_feature_stability",
    "check_time_stability",
    "check_slice_consistency",
    "run_stability_check",
    # 高级筛选
    "ModelGainResult",
    "detect_duplicates",
    "detect_near_duplicates",
    "evaluate_model_gain",
    "evaluate_incremental_gain",
    "run_advanced_selection",
]

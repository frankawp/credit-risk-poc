from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EnginePaths:
    raw_dir: Path = Path("data/raw/home-credit-default-risk")
    output_dir: Path = Path("outputs")
    candidate_dir: Path = Path("outputs/candidate_pool")
    selection_dir: Path = Path("outputs/selection")


@dataclass(frozen=True)
class AutoFeatureConfig:
    sample_size: int = 3000
    random_seed: int = 42
    max_depth: int = 2


@dataclass(frozen=True)
class SelectionConfig:
    id_col: str = "SK_ID_CURR"
    target_col: str = "TARGET"
    topk_ratio: float = 0.10
    missing_rate_threshold: float = 0.95
    correlation_threshold: float = 0.95
    min_auc: float = 0.52
    min_ap_lift: float = 1.02

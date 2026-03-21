from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import List

import featuretools as ft
import pandas as pd

from dual_engine.config import AutoFeatureConfig, EnginePaths


EXAMPLES_DIR = Path(".claude/skills/feature-mining-orchestrator/examples/home_credit")


def _load_entity_module():
    """动态加载实体层模块。"""
    spec = importlib.util.spec_from_file_location(
        "home_credit_entity",
        EXAMPLES_DIR / "entity_layer/entityset_builder.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError("无法加载实体层模块")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class AutoFeatureResult:
    feature_matrix: pd.DataFrame
    feature_names: List[str]


def _drop_target_derived_features(frame: pd.DataFrame, feature_names: list[str]) -> tuple[pd.DataFrame, list[str]]:
    leakage_names = [name for name in feature_names if "TARGET" in name and name != "TARGET"]
    if not leakage_names:
        return frame, feature_names
    filtered_frame = frame.drop(columns=leakage_names, errors="ignore")
    filtered_names = [name for name in feature_names if name not in leakage_names]
    return filtered_frame, filtered_names


def generate_auto_features(
    config: AutoFeatureConfig,
    output_dir: Path,
    agg_primitives: list[str] | None = None,
    trans_primitives: list[str] | None = None,
    paths: EnginePaths | None = None,
) -> AutoFeatureResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    agg_primitives = agg_primitives or ["sum", "mean", "max", "min", "std", "count", "num_unique"]
    trans_primitives = trans_primitives or ["absolute"]

    # 动态加载实体层模块
    entity_module = _load_entity_module()
    entityset, _ = entity_module.build_entityset_for_auto(config, paths)
    feature_matrix, feature_defs = ft.dfs(
        entityset=entityset,
        target_dataframe_name="applications",
        agg_primitives=agg_primitives,
        trans_primitives=trans_primitives,
        max_depth=config.max_depth,
        features_only=False,
        verbose=True,
    )

    frame = feature_matrix.reset_index()
    names = [f.get_name() for f in feature_defs]
    frame, names = _drop_target_derived_features(frame, names)

    frame.to_parquet(output_dir / "auto_feature_matrix.parquet", index=False)
    pd.DataFrame(
        {
            "feature_name": names,
            "feature_source": "auto",
        }
    ).to_csv(output_dir / "auto_feature_defs.csv", index=False)

    return AutoFeatureResult(feature_matrix=frame, feature_names=names)

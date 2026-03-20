from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import featuretools as ft
import pandas as pd

from dual_engine.config import AutoFeatureConfig
from dual_engine.entity_layer import build_entityset_for_auto


@dataclass(frozen=True)
class AutoFeatureResult:
    feature_matrix: pd.DataFrame
    feature_names: List[str]


def generate_auto_features(
    config: AutoFeatureConfig,
    output_dir: Path,
    agg_primitives: list[str] | None = None,
    trans_primitives: list[str] | None = None,
) -> AutoFeatureResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    agg_primitives = agg_primitives or ["sum", "mean", "max", "min", "std", "count", "num_unique"]
    trans_primitives = trans_primitives or ["absolute"]

    entityset, _ = build_entityset_for_auto(config)
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

    frame.to_parquet(output_dir / "auto_feature_matrix.parquet", index=False)
    pd.DataFrame(
        {
            "feature_name": names,
            "feature_source": "auto",
        }
    ).to_csv(output_dir / "auto_feature_defs.csv", index=False)

    return AutoFeatureResult(feature_matrix=frame, feature_names=names)

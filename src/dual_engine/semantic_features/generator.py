from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from dual_engine.config import EnginePaths
from dual_engine.semantic_features.feature_groups import (
    build_cashout_features,
    build_consistency_features,
    build_velocity_features,
)
from dual_engine.semantic_features.registry import semantic_feature_specs, to_registry_frame


@dataclass(frozen=True)
class SemanticFeatureResult:
    feature_matrix: pd.DataFrame
    registry: pd.DataFrame


def _load_frames(raw_dir: Path) -> dict[str, pd.DataFrame]:
    app = pd.read_csv(
        raw_dir / "application_train.csv",
        usecols=[
            "SK_ID_CURR",
            "TARGET",
            "DAYS_BIRTH",
            "DAYS_EMPLOYED",
            "FLAG_MOBIL",
            "FLAG_EMP_PHONE",
            "FLAG_WORK_PHONE",
        ],
    )
    previous = pd.read_csv(
        raw_dir / "previous_application.csv",
        usecols=["SK_ID_PREV", "SK_ID_CURR", "AMT_APPLICATION", "AMT_CREDIT", "DAYS_DECISION", "NAME_CONTRACT_STATUS"],
    )
    bureau = pd.read_csv(raw_dir / "bureau.csv", usecols=["SK_ID_CURR", "DAYS_CREDIT"])
    credit_card = pd.read_csv(
        raw_dir / "credit_card_balance.csv",
        usecols=["SK_ID_PREV", "AMT_DRAWINGS_ATM_CURRENT", "AMT_DRAWINGS_CURRENT"],
    )
    installments = pd.read_csv(
        raw_dir / "installments_payments.csv",
        usecols=["SK_ID_PREV", "NUM_INSTALMENT_NUMBER", "DAYS_INSTALMENT", "DAYS_ENTRY_PAYMENT", "AMT_INSTALMENT", "AMT_PAYMENT"],
    )
    return {
        "application_train": app,
        "previous_application": previous,
        "bureau": bureau,
        "credit_card_balance": credit_card,
        "installments_payments": installments,
    }


def generate_semantic_features(
    paths: EnginePaths,
    output_dir: Path,
    themes: Iterable[str] | None = None,
) -> SemanticFeatureResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    frames = _load_frames(paths.raw_dir)
    requested = None if themes is None else [theme.strip().lower() for theme in themes]

    app = frames["application_train"]
    previous = frames["previous_application"]
    bureau = frames["bureau"]
    credit_card = frames["credit_card_balance"]
    installments = frames["installments_payments"]

    anchor = app[["SK_ID_CURR", "TARGET"]].drop_duplicates().copy()
    feature_frames = {
        "consistency": build_consistency_features(app, previous),
        "velocity": build_velocity_features(previous, bureau),
        "cashout": build_cashout_features(previous, credit_card, installments),
    }
    selected_themes = list(feature_frames.keys()) if requested is None else [theme for theme in requested if theme in feature_frames]

    semantic = anchor.copy()
    for theme in selected_themes:
        semantic = semantic.merge(feature_frames[theme], on="SK_ID_CURR", how="left")

    registry = to_registry_frame(semantic_feature_specs(selected_themes))
    semantic.to_parquet(output_dir / "semantic_feature_matrix.parquet", index=False)
    registry.to_csv(output_dir / "semantic_feature_registry.csv", index=False)
    return SemanticFeatureResult(feature_matrix=semantic, registry=registry)

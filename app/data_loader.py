from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = ROOT / "outputs"


@dataclass(frozen=True)
class ArtifactFile:
    key: str
    path: Path
    kind: str
    label: str


ARTIFACTS = {
    "candidate_summary": ArtifactFile(
        key="candidate_summary",
        path=OUTPUTS_DIR / "candidate_pool" / "candidate_pool_summary.json",
        kind="json",
        label="候选池摘要",
    ),
    "candidate_pool": ArtifactFile(
        key="candidate_pool",
        path=OUTPUTS_DIR / "candidate_pool" / "candidate_pool.parquet",
        kind="parquet",
        label="候选池宽表",
    ),
    "auto_feature_matrix": ArtifactFile(
        key="auto_feature_matrix",
        path=OUTPUTS_DIR / "candidate_pool" / "auto" / "auto_feature_matrix.parquet",
        kind="parquet",
        label="自动特征矩阵",
    ),
    "semantic_feature_matrix": ArtifactFile(
        key="semantic_feature_matrix",
        path=OUTPUTS_DIR / "candidate_pool" / "semantic" / "semantic_feature_matrix.parquet",
        kind="parquet",
        label="语义特征矩阵",
    ),
    "feature_registry": ArtifactFile(
        key="feature_registry",
        path=OUTPUTS_DIR / "candidate_pool" / "registry" / "feature_registry.csv",
        kind="csv",
        label="特征注册表",
    ),
    "composite_feature_spec": ArtifactFile(
        key="composite_feature_spec",
        path=OUTPUTS_DIR / "candidate_pool" / "registry" / "composite_feature_spec.csv",
        kind="csv",
        label="组合特征说明表",
    ),
    "selection_summary": ArtifactFile(
        key="selection_summary",
        path=OUTPUTS_DIR / "selection" / "feature_selection_report.json",
        kind="json",
        label="筛选摘要",
    ),
    "feature_scorecard": ArtifactFile(
        key="feature_scorecard",
        path=OUTPUTS_DIR / "selection" / "feature_scorecard.csv",
        kind="csv",
        label="特征评分卡",
    ),
    "correlation_groups": ArtifactFile(
        key="correlation_groups",
        path=OUTPUTS_DIR / "selection" / "correlation_groups.csv",
        kind="csv",
        label="去相关结果",
    ),
    "dropped_basic_filters": ArtifactFile(
        key="dropped_basic_filters",
        path=OUTPUTS_DIR / "selection" / "dropped_by_basic_filters.csv",
        kind="csv",
        label="基础过滤淘汰结果",
    ),
    "selected_features": ArtifactFile(
        key="selected_features",
        path=OUTPUTS_DIR / "selection" / "selected_features.parquet",
        kind="parquet",
        label="最终入选特征",
    ),
}


def artifact_exists(key: str) -> bool:
    return ARTIFACTS[key].path.exists()


def load_artifact(key: str) -> Any:
    artifact = ARTIFACTS[key]
    if not artifact.path.exists():
        return None
    if artifact.kind == "json":
        return json.loads(artifact.path.read_text())
    if artifact.kind == "csv":
        return pd.read_csv(artifact.path)
    if artifact.kind == "parquet":
        return pd.read_parquet(artifact.path)
    raise ValueError(f"Unsupported artifact type: {artifact.kind}")


def load_all_artifacts() -> dict[str, Any]:
    return {key: load_artifact(key) for key in ARTIFACTS}


def summarize_matrix(frame: pd.DataFrame | None, preview_cols: int = 12) -> dict[str, Any] | None:
    if frame is None:
        return None
    return {
        "rows": int(frame.shape[0]),
        "cols": int(frame.shape[1]),
        "sample_columns": list(frame.columns[:preview_cols]),
    }


def build_lineage_warning(artifacts: dict[str, Any]) -> str | None:
    candidate_pool = artifacts.get("candidate_pool")
    auto_matrix = artifacts.get("auto_feature_matrix")
    semantic_matrix = artifacts.get("semantic_feature_matrix")
    selected = artifacts.get("selected_features")

    if candidate_pool is None or auto_matrix is None or semantic_matrix is None or selected is None:
        return None

    candidate_rows = int(candidate_pool.shape[0])
    auto_rows = int(auto_matrix.shape[0])
    semantic_rows = int(semantic_matrix.shape[0])
    selected_rows = int(selected.shape[0])

    if len({candidate_rows, auto_rows, selected_rows}) == 1 and semantic_rows == candidate_rows:
        return None

    return (
        "当前 outputs 中的数据口径不完全一致："
        f"`candidate_pool/auto/selected` 行数分别为 {candidate_rows}/{auto_rows}/{selected_rows}，"
        f"`semantic_feature_matrix` 行数为 {semantic_rows}。"
        "这表示语义特征仍是全量产物，而自动特征和筛选结果是抽样产物，页面只展示事实，不自动对齐。"
    )


def source_counts(registry: pd.DataFrame | None) -> pd.DataFrame:
    if registry is None or registry.empty:
        return pd.DataFrame(columns=["feature_source", "feature_count"])
    return (
        registry.groupby("feature_source", as_index=False)
        .size()
        .rename(columns={"size": "feature_count"})
        .sort_values("feature_count", ascending=False)
    )


def group_counts(registry: pd.DataFrame | None) -> pd.DataFrame:
    if registry is None or registry.empty:
        return pd.DataFrame(columns=["feature_group", "feature_count"])
    return (
        registry.groupby("feature_group", as_index=False)
        .size()
        .rename(columns={"size": "feature_count"})
        .sort_values("feature_count", ascending=False)
    )


def drop_reason_counts(frame: pd.DataFrame | None) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(columns=["drop_reason", "feature_count"])
    return (
        frame.groupby("drop_reason", as_index=False)
        .size()
        .rename(columns={"size": "feature_count"})
        .sort_values("feature_count", ascending=False)
    )


def scorecard_sorted(frame: pd.DataFrame | None) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    ordered = frame.copy()
    if "selected_flag" in ordered.columns:
        ordered["selected_sort"] = ordered["selected_flag"].astype(int)
    else:
        ordered["selected_sort"] = 0
    ordered = ordered.sort_values(
        by=["selected_sort", "univariate_pr_auc", "univariate_roc_auc"],
        ascending=[False, False, False],
    )
    return ordered.drop(columns=["selected_sort"])

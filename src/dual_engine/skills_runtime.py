from __future__ import annotations

import importlib.util
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

from dual_engine.auto_features import generate_auto_features
from dual_engine.config import AutoFeatureConfig, EnginePaths, SelectionConfig
from dual_engine.selection import run_feature_selection


# ============================================================================
# 样例模块动态加载
# ============================================================================

EXAMPLES_DIR = Path(".claude/skills/feature-mining-orchestrator/examples/home_credit")


def _load_semantic_module():
    """动态加载语义特征模块。"""
    spec = importlib.util.spec_from_file_location(
        "home_credit_semantic",
        EXAMPLES_DIR / "semantic_features/generator.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError("无法加载语义特征模块")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_composite_module():
    """动态加载组合特征模块。"""
    spec = importlib.util.spec_from_file_location(
        "home_credit_composite",
        EXAMPLES_DIR / "composite_features/generator.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError("无法加载组合特征模块")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_registry_module():
    """动态加载注册表模块。"""
    spec = importlib.util.spec_from_file_location(
        "home_credit_registry",
        EXAMPLES_DIR / "semantic_features/registry.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError("无法加载注册表模块")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_specs_module():
    """动态加载组合特征规格模块。"""
    spec = importlib.util.spec_from_file_location(
        "home_credit_specs",
        EXAMPLES_DIR / "composite_features/specs.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError("无法加载组合特征规格模块")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# 常量从动态加载的模块获取
def _get_implemented_themes():
    return _load_registry_module().IMPLEMENTED_SEMANTIC_THEMES


def _get_known_themes():
    return _load_registry_module().KNOWN_SEMANTIC_THEMES


# 兼容旧代码的常量引用
IMPLEMENTED_SEMANTIC_THEMES = ("consistency", "velocity", "cashout")
KNOWN_SEMANTIC_THEMES = IMPLEMENTED_SEMANTIC_THEMES


def _result(
    status: str,
    step: str,
    artifacts: dict[str, str],
    summary: dict,
    warnings: list[str] | None = None,
    next_actions: list[str] | None = None,
) -> dict:
    payload = {
        "status": status,
        "step": step,
        "artifacts": artifacts,
        "summary": summary,
    }
    if warnings:
        payload["warnings"] = warnings
    if next_actions:
        payload["next_actions"] = next_actions
    return payload


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _read_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path)


def _read_parquet(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_parquet(path)


def _check_required(paths: dict[str, Path]) -> list[str]:
    return [name for name, path in paths.items() if not path.exists()]


def _archive_artifact_map(workspace_root: Path, archive_root: Path) -> dict[str, str]:
    project_root = archive_root / "project"
    relative_project = project_root.relative_to(archive_root)
    candidates = {
        "candidate_pool_summary": (
            workspace_root / "outputs/candidate_pool/candidate_pool_summary.json",
            relative_project / "outputs/candidate_pool/candidate_pool_summary.json",
        ),
        "candidate_pool": (
            workspace_root / "outputs/candidate_pool/candidate_pool.parquet",
            relative_project / "outputs/candidate_pool/candidate_pool.parquet",
        ),
        "feature_registry": (
            workspace_root / "outputs/candidate_pool/registry/feature_registry.csv",
            relative_project / "outputs/candidate_pool/registry/feature_registry.csv",
        ),
        "composite_feature_spec": (
            workspace_root / "outputs/candidate_pool/registry/composite_feature_spec.csv",
            relative_project / "outputs/candidate_pool/registry/composite_feature_spec.csv",
        ),
        "selection_summary": (
            workspace_root / "outputs/selection/feature_selection_report.json",
            relative_project / "outputs/selection/feature_selection_report.json",
        ),
        "feature_scorecard": (
            workspace_root / "outputs/selection/feature_scorecard.csv",
            relative_project / "outputs/selection/feature_scorecard.csv",
        ),
        "selected_features": (
            workspace_root / "outputs/selection/selected_features.parquet",
            relative_project / "outputs/selection/selected_features.parquet",
        ),
    }
    artifact_map: dict[str, str] = {"project_root": str(relative_project)}
    for key, (source_path, relative_path) in candidates.items():
        if source_path.exists():
            artifact_map[key] = str(relative_path)
    return artifact_map


def _enrich_auto_registry(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "feature_name",
                "feature_source",
                "feature_group",
                "source_table",
                "business_definition",
                "risk_direction",
                "status",
            ]
        )
    registry = frame.copy()
    registry["feature_group"] = "auto_generated"
    registry["source_table"] = "entityset"
    registry["business_definition"] = "Featuretools 自动生成的统计型变量。"
    registry["risk_direction"] = "unknown"
    registry["status"] = "candidate"
    columns = [
        "feature_name",
        "feature_source",
        "feature_group",
        "source_table",
        "business_definition",
        "risk_direction",
        "status",
    ]
    return registry[columns]


def _enrich_composite_registry(frame: pd.DataFrame, specs: pd.DataFrame) -> pd.DataFrame:
    registry = frame.copy()
    registry["feature_source"] = "composite"
    registry["feature_group"] = "composite"
    registry["source_table"] = "candidate_pool"
    registry["status"] = "candidate"
    registry = registry.merge(
        specs[["feature_name", "business_definition", "risk_direction"]],
        on="feature_name",
        how="left",
    )
    registry["business_definition"] = registry["business_definition"].fillna(
        "组合特征，具体公式见 composite_feature_spec.csv。"
    )
    registry["risk_direction"] = registry["risk_direction"].fillna("higher_is_riskier")
    columns = [
        "feature_name",
        "feature_source",
        "feature_group",
        "source_table",
        "business_definition",
        "risk_direction",
        "status",
    ]
    return registry[columns]


def normalize_semantic_themes(themes: Iterable[str] | str | None) -> dict:
    if themes is None:
        requested = ["all"]
    else:
        if isinstance(themes, str):
            themes = [themes]
        requested = [str(theme).strip().lower() for theme in themes if str(theme).strip()]
        if not requested:
            requested = ["all"]

    implemented_themes = _get_implemented_themes()
    known_themes = _get_known_themes()

    if "all" in requested:
        expanded = list(implemented_themes)
        return {
            "requested": requested,
            "implemented": expanded,
            "unimplemented": [],
            "unknown": [],
        }

    implemented = [theme for theme in requested if theme in implemented_themes]
    unimplemented = [theme for theme in requested if theme in known_themes and theme not in implemented_themes]
    unknown = [theme for theme in requested if theme not in known_themes]
    return {
        "requested": requested,
        "implemented": implemented,
        "unimplemented": unimplemented,
        "unknown": unknown,
    }


def run_auto_features(sample_size: int = 3000, max_depth: int = 2) -> dict:
    paths = EnginePaths()
    output_dir = paths.candidate_dir / "auto"
    output_dir.mkdir(parents=True, exist_ok=True)
    result = generate_auto_features(
        config=AutoFeatureConfig(sample_size=sample_size, max_depth=max_depth),
        output_dir=output_dir,
        paths=paths,
    )
    summary = {
        "sample_size": sample_size,
        "max_depth": max_depth,
        "feature_count": int(len(result.feature_names)),
        "matrix_shape": list(result.feature_matrix.shape),
    }
    summary_path = output_dir / "auto_feature_summary.json"
    _write_json(summary_path, summary)
    return _result(
        status="success",
        step="generate_auto_features",
        artifacts={
            "auto_feature_matrix": str(output_dir / "auto_feature_matrix.parquet"),
            "auto_feature_defs": str(output_dir / "auto_feature_defs.csv"),
            "auto_feature_summary": str(summary_path),
        },
        summary=summary,
        next_actions=["继续生成 semantic features，或直接查看 auto 变量分布。"],
    )


def run_semantic_features(themes: Iterable[str] | None = None) -> dict:
    paths = EnginePaths()
    output_dir = paths.candidate_dir / "semantic"
    output_dir.mkdir(parents=True, exist_ok=True)
    normalized = normalize_semantic_themes(themes)
    warnings: list[str] = []

    if normalized["unimplemented"]:
        warnings.append(
            f"主题 {', '.join(normalized['unimplemented'])} 目前仅支持探索性设计，尚未实现可计算变量。"
        )
    if normalized["unknown"]:
        warnings.append(
            f"未识别的主题: {', '.join(normalized['unknown'])}。可用主题为 consistency、velocity、cashout。"
        )

    if not normalized["implemented"]:
        return _result(
            status="warning",
            step="generate_semantic_features",
            artifacts={},
            summary={
                "requested_themes": normalized["requested"],
                "generated_themes": [],
                "feature_count": 0,
            },
            warnings=warnings or ["当前没有可执行的 semantic 主题。"],
            next_actions=["改为运行 consistency、velocity 或 cashout，或先做语义变量探索。"],
        )

    # 动态加载语义特征模块
    semantic_module = _load_semantic_module()
    result = semantic_module.generate_semantic_features(paths=paths, output_dir=output_dir, themes=normalized["implemented"])
    summary = {
        "requested_themes": normalized["requested"],
        "generated_themes": normalized["implemented"],
        "feature_count": int(len(result.registry)),
        "matrix_shape": list(result.feature_matrix.shape),
    }
    summary_path = output_dir / "semantic_feature_summary.json"
    _write_json(summary_path, summary)
    return _result(
        status="warning" if warnings else "success",
        step="generate_semantic_features",
        artifacts={
            "semantic_feature_matrix": str(output_dir / "semantic_feature_matrix.parquet"),
            "semantic_feature_registry": str(output_dir / "semantic_feature_registry.csv"),
            "semantic_feature_summary": str(summary_path),
        },
        summary=summary,
        warnings=warnings,
        next_actions=["如需组合特征，继续运行 composite features；如只做解释，可直接查看 semantic 注册表。"],
    )


def run_composite_features() -> dict:
    paths = EnginePaths()
    auto_dir = paths.candidate_dir / "auto"
    semantic_dir = paths.candidate_dir / "semantic"
    composite_dir = paths.candidate_dir / "composite"
    registry_dir = paths.candidate_dir / "registry"
    composite_dir.mkdir(parents=True, exist_ok=True)
    registry_dir.mkdir(parents=True, exist_ok=True)

    required = {
        "auto_feature_matrix": auto_dir / "auto_feature_matrix.parquet",
        "semantic_feature_matrix": semantic_dir / "semantic_feature_matrix.parquet",
    }
    missing = _check_required(required)
    if missing:
        return _result(
            status="error",
            step="generate_composite_features",
            artifacts={},
            summary={"missing_artifacts": missing},
            warnings=["生成 composite features 前需要先产出 auto 和 semantic 基础特征。"],
            next_actions=["先运行 run_auto_features.py 和 run_semantic_features.py。"],
        )

    auto_frame = pd.read_parquet(required["auto_feature_matrix"])
    semantic_frame = pd.read_parquet(required["semantic_feature_matrix"])
    merged = auto_frame.merge(semantic_frame.drop(columns=["TARGET"], errors="ignore"), on="SK_ID_CURR", how="left")

    # 动态加载组合特征模块
    composite_module = _load_composite_module()
    specs_module = _load_specs_module()
    composite = composite_module.build_composite_features(merged)
    specs = specs_module.composite_specs_frame()
    registry = _enrich_composite_registry(
        pd.DataFrame({"feature_name": [col for col in composite.columns if col != "SK_ID_CURR"]}),
        specs,
    )

    matrix_path = composite_dir / "composite_feature_matrix.parquet"
    registry_path = composite_dir / "composite_feature_registry.csv"
    specs_path = registry_dir / "composite_feature_spec.csv"
    summary_path = composite_dir / "composite_feature_summary.json"
    composite.to_parquet(matrix_path, index=False)
    registry.to_csv(registry_path, index=False)
    specs.to_csv(specs_path, index=False)

    summary = {
        "composite_feature_count": int(len(registry)),
        "matrix_shape": list(composite.shape),
        "base_row_count": int(merged.shape[0]),
    }
    _write_json(summary_path, summary)
    return _result(
        status="success",
        step="generate_composite_features",
        artifacts={
            "composite_feature_matrix": str(matrix_path),
            "composite_feature_registry": str(registry_path),
            "composite_feature_spec": str(specs_path),
            "composite_feature_summary": str(summary_path),
        },
        summary=summary,
        next_actions=["继续构建 candidate pool，或优先阅读 composite_feature_spec.csv。"],
    )


def build_candidate_pool() -> dict:
    paths = EnginePaths()
    candidate_dir = paths.candidate_dir
    registry_dir = candidate_dir / "registry"
    auto_dir = candidate_dir / "auto"
    semantic_dir = candidate_dir / "semantic"
    composite_dir = candidate_dir / "composite"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    registry_dir.mkdir(parents=True, exist_ok=True)

    required = {
        "auto_feature_matrix": auto_dir / "auto_feature_matrix.parquet",
        "auto_feature_defs": auto_dir / "auto_feature_defs.csv",
        "semantic_feature_matrix": semantic_dir / "semantic_feature_matrix.parquet",
        "semantic_feature_registry": semantic_dir / "semantic_feature_registry.csv",
        "composite_feature_matrix": composite_dir / "composite_feature_matrix.parquet",
        "composite_feature_registry": composite_dir / "composite_feature_registry.csv",
        "composite_feature_spec": registry_dir / "composite_feature_spec.csv",
    }
    missing = _check_required(required)
    if missing:
        return _result(
            status="error",
            step="build_candidate_pool",
            artifacts={},
            summary={"missing_artifacts": missing},
            warnings=["构建 candidate pool 需要 auto、semantic、composite 三类上游产物同时存在。"],
            next_actions=["先分别运行 auto、semantic、composite 生成脚本。"],
        )

    auto_frame = pd.read_parquet(required["auto_feature_matrix"])
    semantic_frame = pd.read_parquet(required["semantic_feature_matrix"])
    composite_frame = pd.read_parquet(required["composite_feature_matrix"])

    merged = auto_frame.merge(semantic_frame.drop(columns=["TARGET"], errors="ignore"), on="SK_ID_CURR", how="left")
    merged = merged.merge(composite_frame, on="SK_ID_CURR", how="left")
    candidate_path = candidate_dir / "candidate_pool.parquet"
    merged.to_parquet(candidate_path, index=False)

    auto_registry = _enrich_auto_registry(pd.read_csv(required["auto_feature_defs"]))
    semantic_registry = pd.read_csv(required["semantic_feature_registry"])
    composite_registry = pd.read_csv(required["composite_feature_registry"])
    registry = pd.concat([auto_registry, semantic_registry, composite_registry], ignore_index=True).drop_duplicates(
        subset=["feature_name"],
        keep="first",
    )
    registry_path = registry_dir / "feature_registry.csv"
    registry.to_csv(registry_path, index=False)

    auto_summary = _load_json(auto_dir / "auto_feature_summary.json") or {}
    summary = {
        "sample_size": auto_summary.get("sample_size"),
        "max_depth": auto_summary.get("max_depth"),
        "auto_feature_count": int(len(auto_registry)),
        "semantic_feature_count": int(len(semantic_registry)),
        "composite_feature_count": int(len(composite_registry)),
        "candidate_pool_shape": list(merged.shape),
    }
    summary_path = candidate_dir / "candidate_pool_summary.json"
    markdown_path = candidate_dir / "candidate_pool_summary.md"
    _write_json(summary_path, summary)
    markdown_path.write_text(
        "# Candidate Pool Summary\n\n"
        f"- sample_size: {summary['sample_size']}\n"
        f"- max_depth: {summary['max_depth']}\n"
        f"- auto_feature_count: {summary['auto_feature_count']}\n"
        f"- semantic_feature_count: {summary['semantic_feature_count']}\n"
        f"- composite_feature_count: {summary['composite_feature_count']}\n"
        f"- candidate_pool_shape: {tuple(summary['candidate_pool_shape'])}\n"
    )
    return _result(
        status="success",
        step="build_candidate_pool",
        artifacts={
            "candidate_pool": str(candidate_path),
            "feature_registry": str(registry_path),
            "candidate_pool_summary": str(summary_path),
            "composite_feature_spec": str(required["composite_feature_spec"]),
        },
        summary=summary,
        next_actions=["继续运行 select_features.py，或先在 viewer 中检查候选池结构。"],
    )


def run_selection_stage(input_path: str | None = None) -> dict:
    paths = EnginePaths()
    selection_dir = paths.selection_dir
    selection_dir.mkdir(parents=True, exist_ok=True)
    pool_path = Path(input_path) if input_path else paths.candidate_dir / "candidate_pool.parquet"
    if not pool_path.exists():
        return _result(
            status="error",
            step="select_features",
            artifacts={},
            summary={"missing_artifacts": ["candidate_pool"]},
            warnings=["特征筛选依赖 candidate_pool.parquet。"],
            next_actions=["先运行 build_candidate_pool.py。"],
        )

    frame = pd.read_parquet(pool_path)
    summary = run_feature_selection(frame=frame, config=SelectionConfig(), output_dir=selection_dir)
    return _result(
        status="success",
        step="select_features",
        artifacts={
            "selected_features": str(selection_dir / "selected_features.parquet"),
            "feature_scorecard": str(selection_dir / "feature_scorecard.csv"),
            "correlation_groups": str(selection_dir / "correlation_groups.csv"),
            "feature_selection_report": str(selection_dir / "feature_selection_report.json"),
            "dropped_by_basic_filters": str(selection_dir / "dropped_by_basic_filters.csv"),
        },
        summary=summary,
        next_actions=["使用 results-navigator 解读结果，或将入选变量用于后续模型验证。"],
    )


def archive_latest_run(
    topic: str = "feature_mining",
    task_type: str = "完整变量挖掘",
    notes: str | None = None,
    base_dir: Path | None = None,
) -> dict:
    paths = EnginePaths()
    base_dir = base_dir or Path(".")
    topic_slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", topic).strip("_") or "feature_mining"
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    workspace_root = base_dir.resolve()
    archive_dir = workspace_root / "archives" / "analysis_run" / f"{date_prefix}_{topic_slug}"
    if archive_dir.exists():
        return _result(
            status="error",
            step="archive_run",
            artifacts={},
            summary={"archive_dir": str(archive_dir)},
            warnings=[f"归档目录已存在：{archive_dir}"],
            next_actions=["更换 topic，或先手动处理已有归档目录。"],
        )
    conclusion_dir = archive_dir / "conclusion"
    project_dir = archive_dir / "project"
    conclusion_dir.mkdir(parents=True, exist_ok=False)
    project_dir.mkdir(parents=True, exist_ok=False)

    candidate_summary_path = paths.candidate_dir / "candidate_pool_summary.json"
    selection_summary_path = paths.selection_dir / "feature_selection_report.json"
    registry_path = paths.candidate_dir / "registry" / "feature_registry.csv"
    composite_spec_path = paths.candidate_dir / "registry" / "composite_feature_spec.csv"

    candidate_summary = _load_json(candidate_summary_path) or {}
    selection_summary = _load_json(selection_summary_path) or {}
    registry = _read_csv(registry_path)
    composite_spec = _read_csv(composite_spec_path)
    semantic_matrix = _read_parquet(paths.candidate_dir / "semantic" / "semantic_feature_matrix.parquet")
    candidate_pool = _read_parquet(paths.candidate_dir / "candidate_pool.parquet")

    warnings: list[str] = []
    if semantic_matrix is not None and candidate_pool is not None and len(semantic_matrix) != len(candidate_pool):
        warnings.append(
            f"当前语义特征矩阵为 {len(semantic_matrix)} 行，而候选池为 {len(candidate_pool)} 行，存在口径差异。"
        )

    artifact_map = _archive_artifact_map(workspace_root, archive_dir)
    top_level_entries = [
        item for item in workspace_root.iterdir()
        if item.name not in {"data", "archives"} and not item.name.startswith(".")
    ]
    archived_entry_names = [item.name for item in top_level_entries]

    summary_path = conclusion_dir / "summary.md"
    artifacts_path = conclusion_dir / "artifacts.json"
    summary_path.write_text(
        "# 本轮挖掘摘要\n\n"
        f"- 日期：{date_prefix}\n"
        f"- 主题：{topic}\n"
        f"- 任务类型：{task_type}\n"
        f"- 候选池规模：{candidate_summary.get('candidate_pool_shape')}\n"
        f"- 自动特征数：{candidate_summary.get('auto_feature_count')}\n"
        f"- 语义特征数：{candidate_summary.get('semantic_feature_count')}\n"
        f"- 组合特征数：{candidate_summary.get('composite_feature_count')}\n"
        f"- 入选特征数：{selection_summary.get('selected_feature_count')}\n"
        f"- 归档项目目录：project/\n"
        f"- 已归档顶层条目数：{len(archived_entry_names)}\n"
        f"- 备注：{notes or '无'}\n"
    )
    if warnings:
        summary_path.write_text(
            summary_path.read_text() + "\n## 口径提醒\n\n" + "\n".join(f"- {warning}" for warning in warnings) + "\n"
        )

    artifacts_payload = {
        "topic": topic,
        "task_type": task_type,
        "archive_dir": str(archive_dir.relative_to(workspace_root)),
        "project_dir": "project",
        "conclusion_dir": "conclusion",
        "archived_entries": archived_entry_names,
        "artifacts": artifact_map,
        "warnings": warnings,
    }
    artifacts_path.write_text(json.dumps(artifacts_payload, indent=2, ensure_ascii=False))

    for item in top_level_entries:
        shutil.move(str(item), str(project_dir / item.name))

    return _result(
        status="success",
        step="archive_run",
        artifacts={
            "summary": str(summary_path.relative_to(workspace_root)),
            "artifacts": str(artifacts_path.relative_to(workspace_root)),
            "project_dir": str(project_dir.relative_to(workspace_root)),
        },
        summary={
            "archive_dir": str(archive_dir),
            "topic": topic,
            "archived_entries": archived_entry_names,
            "warnings_count": len(warnings),
        },
        warnings=warnings,
        next_actions=["当前工作区应只剩 data/ 和 archives/；下一轮挖掘请在干净工作区继续。"],
    )


# ============================================================================
# 数据探索函数
# ============================================================================


def explore_data_directory(data_dir: Path | None = None, sample_rows: int = 1000) -> dict:
    """
    探索数据目录，分析表结构和数据质量。

    返回每张表的结构、字段统计、缺失率等信息。
    """
    paths = EnginePaths()
    raw_dir = data_dir or paths.raw_dir

    if not raw_dir.exists():
        return _result(
            status="error",
            step="explore_data",
            artifacts={},
            summary={"data_dir": str(raw_dir)},
            warnings=[f"数据目录不存在：{raw_dir}"],
            next_actions=["请确认数据目录路径，或将数据放入 data/raw/ 目录。"],
        )

    csv_files = list(raw_dir.glob("*.csv"))
    parquet_files = list(raw_dir.glob("*.parquet"))
    all_files = csv_files + parquet_files

    if not all_files:
        return _result(
            status="warning",
            step="explore_data",
            artifacts={},
            summary={"data_dir": str(raw_dir), "file_count": 0},
            warnings=["数据目录中没有 CSV 或 Parquet 文件。"],
            next_actions=["请将数据文件放入数据目录。"],
        )

    tables_info = []
    for file_path in all_files[:10]:  # 最多分析 10 个文件
        try:
            if file_path.suffix == ".csv":
                df = pd.read_csv(file_path, nrows=sample_rows)
            else:
                df = pd.read_parquet(file_path)
                if len(df) > sample_rows:
                    df = df.head(sample_rows)

            # 计算字段统计
            columns_info = []
            for col in df.columns:
                col_data = df[col]
                columns_info.append({
                    "name": col,
                    "dtype": str(col_data.dtype),
                    "missing_rate": round(float(col_data.isna().mean()), 4),
                    "unique_count": int(col_data.nunique()),
                    "sample_values": col_data.dropna().head(3).tolist()[:3],
                })

            tables_info.append({
                "file_name": file_path.name,
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": columns_info[:20],  # 最多展示 20 列
                "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            })
        except Exception as e:
            tables_info.append({
                "file_name": file_path.name,
                "error": str(e),
            })

    # 保存探索结果
    output_dir = paths.candidate_dir / "exploration"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "data_exploration_report.json"
    _write_json(report_path, {
        "data_dir": str(raw_dir),
        "file_count": len(all_files),
        "sample_rows": sample_rows,
        "tables": tables_info,
    })

    return _result(
        status="success",
        step="explore_data",
        artifacts={"exploration_report": str(report_path)},
        summary={
            "data_dir": str(raw_dir),
            "file_count": len(all_files),
            "tables_analyzed": len(tables_info),
        },
        next_actions=["查看探索报告，确认数据结构，然后设计变量假设。"],
    )


# ============================================================================
# 动态特征注册机制
# ============================================================================


PROPOSED_FEATURES_DIR = Path("outputs/proposed_features")


def register_proposed_feature(
    feature_name: str,
    theme: str,
    business_hypothesis: str,
    expected_direction: str,
    calculation_logic: str | None = None,
) -> dict:
    """
    注册一个待实现的变量假设。

    参数:
        feature_name: 变量名，格式为 {theme}_{具体含义}
        theme: 主题 (consistency/velocity/cashout/collusion)
        business_hypothesis: 业务假设
        expected_direction: 预期方向 (higher_is_riskier/lower_is_riskier)
        calculation_logic: 计算逻辑描述
    """
    PROPOSED_FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    registry_path = PROPOSED_FEATURES_DIR / "registry.json"

    # 加载已有注册
    if registry_path.exists():
        registry = json.loads(registry_path.read_text())
    else:
        registry = {"features": []}

    # 检查是否已存在
    existing_names = [f["feature_name"] for f in registry["features"]]
    if feature_name in existing_names:
        return _result(
            status="warning",
            step="register_feature",
            artifacts={"registry": str(registry_path)},
            summary={"feature_name": feature_name},
            warnings=[f"变量 {feature_name} 已在注册表中。"],
            next_actions=["更改变量名或更新已有记录。"],
        )

    # 添加新记录
    from datetime import datetime
    registry["features"].append({
        "feature_name": feature_name,
        "theme": theme,
        "business_hypothesis": business_hypothesis,
        "expected_direction": expected_direction,
        "calculation_logic": calculation_logic,
        "status": "proposed",
        "created_at": datetime.now().isoformat(),
    })

    registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False))

    return _result(
        status="success",
        step="register_feature",
        artifacts={"registry": str(registry_path)},
        summary={"feature_name": feature_name, "theme": theme, "total_proposed": len(registry["features"])},
        next_actions=["继续注册其他变量，或生成实现代码。"],
    )


def list_proposed_features(theme: str | None = None) -> dict:
    """列出所有待实现的变量假设。"""
    registry_path = PROPOSED_FEATURES_DIR / "registry.json"
    if not registry_path.exists():
        return _result(
            status="success",
            step="list_proposed_features",
            artifacts={},
            summary={"features": [], "total": 0},
            next_actions=["还没有注册任何变量假设，先使用 register_proposed_feature 注册。"],
        )

    registry = json.loads(registry_path.read_text())
    features = registry.get("features", [])

    if theme:
        features = [f for f in features if f.get("theme") == theme]

    return _result(
        status="success",
        step="list_proposed_features",
        artifacts={"registry": str(registry_path)},
        summary={"features": features, "total": len(features)},
        next_actions=["查看已注册变量，选择优先实现。"],
    )


# ============================================================================
# 单变量评估函数
# ============================================================================


def evaluate_single_feature(
    feature_series: pd.Series,
    target_series: pd.Series,
    feature_name: str = "feature",
) -> dict:
    """
    评估单个变量的预测能力。

    返回 ROC-AUC、PR-AUC、缺失率等指标。
    """
    from sklearn.metrics import roc_auc_score, average_precision_score

    # 对齐索引
    aligned = pd.DataFrame({"feature": feature_series, "target": target_series}).dropna()

    if len(aligned) < 10:
        return {
            "feature_name": feature_name,
            "valid_count": len(aligned),
            "warning": "有效样本数过少，无法评估",
        }

    X = aligned["feature"].values
    y = aligned["target"].values

    # 检查是否为二分类
    unique_targets = set(y)
    if len(unique_targets) != 2:
        return {
            "feature_name": feature_name,
            "valid_count": len(aligned),
            "warning": f"目标变量不是二分类，取值：{unique_targets}",
        }

    try:
        roc_auc = roc_auc_score(y, X)
        pr_auc = average_precision_score(y, X)
    except ValueError as e:
        return {
            "feature_name": feature_name,
            "valid_count": len(aligned),
            "warning": f"无法计算 AUC：{e}",
        }

    # 计算 top 10% lift
    top_k = max(1, int(len(aligned) * 0.1))
    top_indices = aligned.nlargest(top_k, "feature").index
    top_bad_rate = aligned.loc[top_indices, "target"].mean()
    overall_bad_rate = aligned["target"].mean()
    lift_top_decile = top_bad_rate / overall_bad_rate if overall_bad_rate > 0 else 0

    return {
        "feature_name": feature_name,
        "valid_count": len(aligned),
        "missing_rate": round(1 - len(aligned) / len(feature_series), 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "lift_top_decile": round(lift_top_decile, 4),
        "mean": round(float(aligned["feature"].mean()), 4),
        "std": round(float(aligned["feature"].std()), 4),
    }


def evaluate_proposed_features(feature_matrix_path: str | None = None) -> dict:
    """
    评估所有新生成的变量。

    读取特征矩阵和目标变量，对每个变量计算评估指标。
    """
    paths = EnginePaths()

    # 读取数据
    if feature_matrix_path:
        matrix = pd.read_parquet(feature_matrix_path)
    else:
        # 尝试读取候选池
        pool_path = paths.candidate_dir / "candidate_pool.parquet"
        if not pool_path.exists():
            return _result(
                status="error",
                step="evaluate_features",
                artifacts={},
                summary={},
                warnings=["找不到特征矩阵，请先运行变量生成流程。"],
                next_actions=["运行 build_candidate_pool.py 或指定特征矩阵路径。"],
            )
        matrix = pd.read_parquet(pool_path)

    if "TARGET" not in matrix.columns:
        return _result(
            status="error",
            step="evaluate_features",
            artifacts={},
            summary={},
            warnings=["特征矩阵中没有 TARGET 列。"],
            next_actions=["确保特征矩阵包含目标变量。"],
        )

    target = matrix["TARGET"]
    feature_cols = [col for col in matrix.columns if col not in ["TARGET", "SK_ID_CURR"]]

    results = []
    for col in feature_cols:
        if matrix[col].dtype in ["int64", "float64", "int32", "float32"]:
            result = evaluate_single_feature(matrix[col], target, col)
            results.append(result)

    # 保存评估结果
    output_dir = paths.selection_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    eval_path = output_dir / "proposed_features_evaluation.json"
    _write_json(eval_path, {"evaluations": results, "total_features": len(results)})

    # 统计有效变量
    effective = [r for r in results if r.get("roc_auc", 0.5) > 0.52 or r.get("lift_top_decile", 0) > 1.02]

    return _result(
        status="success",
        step="evaluate_features",
        artifacts={"evaluation_report": str(eval_path)},
        summary={
            "total_features": len(results),
            "effective_features": len(effective),
            "top_features": sorted(results, key=lambda x: x.get("roc_auc", 0), reverse=True)[:5],
        },
        next_actions=["查看评估报告，决定保留哪些变量。"],
    )

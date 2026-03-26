from __future__ import annotations

import importlib.util
import json
import py_compile
import subprocess
import sys
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "credit-risk-plugin"
SKILL_ROOT = PLUGIN_ROOT / "skills" / "mining"
REGISTRY_SCRIPT = SKILL_ROOT / "scripts" / "feature_registry.py"
ARCHIVE_SCRIPT = SKILL_ROOT / "scripts" / "archive_run.py"


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_public_contract_docs_are_consistent() -> None:
    root_readme = (ROOT / "README.md").read_text()
    plugin_readme = (PLUGIN_ROOT / "README.md").read_text()
    maintainer_doc = (ROOT / "CLAUDE.md").read_text()
    skill_doc = (SKILL_ROOT / "SKILL.md").read_text()

    for content in (root_readme, plugin_readme, maintainer_doc):
        assert "/credit-risk:mining" in content

    assert "skills/feature-mining" not in root_readme
    assert "skills/feature-mining" not in plugin_readme
    assert "credit-risk-plugin/scripts/" not in root_readme
    assert "credit-risk-plugin/scripts/" not in plugin_readme
    assert "credit-risk-plugin/references/" not in root_readme
    assert "credit-risk-plugin/references/" not in plugin_readme
    assert skill_doc.startswith("---\nname: mining\n")


def test_feature_registry_cli_help_and_roundtrip(tmp_path: Path) -> None:
    help_result = subprocess.run(
        [sys.executable, str(REGISTRY_SCRIPT), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert help_result.returncode == 0, help_result.stderr

    registry_path = tmp_path / "registry.json"
    export_path = tmp_path / "registry.csv"

    register_result = subprocess.run(
        [
            sys.executable,
            str(REGISTRY_SCRIPT),
            "register",
            "--name",
            "velocity_apply_count_7d",
            "--theme",
            "velocity",
            "--hypothesis",
            "短期高频申请风险更高",
            "--registry",
            str(registry_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert register_result.returncode == 0, register_result.stderr

    update_result = subprocess.run(
        [
            sys.executable,
            str(REGISTRY_SCRIPT),
            "update",
            "--name",
            "velocity_apply_count_7d",
            "--status",
            "validated",
            "--registry",
            str(registry_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert update_result.returncode == 0, update_result.stderr

    export_result = subprocess.run(
        [
            sys.executable,
            str(REGISTRY_SCRIPT),
            "export",
            "--output",
            str(export_path),
            "--registry",
            str(registry_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert export_result.returncode == 0, export_result.stderr

    payload = json.loads(registry_path.read_text())
    feature = payload["features"][0]
    assert feature["name"] == "velocity_apply_count_7d"
    assert feature["status"] == "validated"
    assert export_path.exists()


def test_archive_run_only_moves_outputs_and_recreates_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    outputs = workspace / "outputs"
    (outputs / "reports").mkdir(parents=True)
    (outputs / "candidate_pool").mkdir(parents=True)
    (outputs / "selection").mkdir(parents=True)
    (outputs / "reports" / "01_data_overview.md").write_text("# report")
    (outputs / "candidate_pool" / "candidate_pool_summary.json").write_text(
        json.dumps(
            {
                "row_count": 10,
                "total_feature_count": 3,
                "auto_feature_count": 1,
                "semantic_feature_count": 2,
            }
        )
    )
    (outputs / "selection" / "feature_selection_report.json").write_text(
        json.dumps({"selected_feature_count": 2})
    )
    (workspace / "README.md").write_text("keep me")

    module = _load_module(ARCHIVE_SCRIPT, "archive_run_test")
    result = module.archive_run(
        topic="测试归档",
        notes="只归档 outputs",
        workspace_root=workspace,
    )

    assert result["status"] == "success"
    archive_dir = Path(result["archive_dir"])
    assert (workspace / "README.md").read_text() == "keep me"
    assert (archive_dir / "project" / "outputs" / "reports" / "01_data_overview.md").exists()
    assert (workspace / "outputs").exists()
    assert (workspace / "outputs" / "reports").exists()
    assert (workspace / "outputs" / "data").exists()
    assert (workspace / "outputs" / "proposed_features").exists()


def test_entity_builder_imports_without_featuretools() -> None:
    builder_path = SKILL_ROOT / "engine" / "entity" / "builder.py"
    code = textwrap.dedent(
        f"""
        import builtins
        import sys

        sys.path.insert(0, {str(PLUGIN_ROOT / "skills")!r})

        original_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "featuretools":
                raise ImportError("simulated missing featuretools")
            return original_import(name, globals, locals, fromlist, level)

        builtins.__import__ = fake_import

        import mining.engine.entity.builder as builder

        assert builder.ft is None
        try:
            builder._require_featuretools()
        except ImportError as exc:
            assert "pip install featuretools" in str(exc)
        else:
            raise AssertionError("expected ImportError when featuretools is missing")
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_example_scripts_compile() -> None:
    example_files = [
        SKILL_ROOT / "examples" / "home_credit" / "02_feature_generation" / "dual_engine.py",
        SKILL_ROOT / "examples" / "home_credit" / "03_composite_features" / "build_composite.py",
        SKILL_ROOT / "examples" / "home_credit" / "04_feature_selection" / "run_selection.py",
    ]
    for file_path in example_files:
        py_compile.compile(str(file_path), doraise=True)

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from dual_engine.auto_features.generator import _drop_target_derived_features
from dual_engine.config import EnginePaths
from dual_engine.skills_runtime import (
    archive_latest_run,
    build_candidate_pool,
    normalize_semantic_themes,
    run_composite_features,
    run_semantic_features,
)


class SkillsRuntimeTest(unittest.TestCase):
    def test_drop_target_derived_features_removes_label_leakage(self) -> None:
        frame = pd.DataFrame({"SK_ID_CURR": [1], "TARGET": [0], "ABSOLUTE(TARGET)": [0], "auto_a": [1.0]})
        filtered_frame, filtered_names = _drop_target_derived_features(
            frame=frame,
            feature_names=["ABSOLUTE(TARGET)", "auto_a"],
        )
        self.assertNotIn("ABSOLUTE(TARGET)", filtered_frame.columns)
        self.assertEqual(filtered_names, ["auto_a"])

    def test_normalize_semantic_themes_handles_known_unknown_and_unimplemented(self) -> None:
        normalized = normalize_semantic_themes(["velocity", "collusion", "foo"])
        self.assertEqual(normalized["implemented"], ["velocity"])
        self.assertEqual(normalized["unimplemented"], ["collusion"])
        self.assertEqual(normalized["unknown"], ["foo"])

    def test_run_semantic_features_returns_warning_when_only_unimplemented_theme_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paths = EnginePaths(
                raw_dir=root / "data" / "raw",
                output_dir=root / "outputs",
                candidate_dir=root / "outputs" / "candidate_pool",
                selection_dir=root / "outputs" / "selection",
            )
            with patch("dual_engine.skills_runtime.EnginePaths", return_value=paths):
                result = run_semantic_features(themes=["collusion"])
        self.assertEqual(result["status"], "warning")
        self.assertEqual(result["summary"]["generated_themes"], [])
        self.assertIn("尚未实现", result["warnings"][0])

    def test_run_composite_features_writes_matrix_and_spec(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            candidate = root / "outputs" / "candidate_pool"
            (candidate / "auto").mkdir(parents=True)
            (candidate / "semantic").mkdir(parents=True)
            paths = EnginePaths(
                raw_dir=root / "data" / "raw",
                output_dir=root / "outputs",
                candidate_dir=candidate,
                selection_dir=root / "outputs" / "selection",
            )

            pd.DataFrame(
                {
                    "SK_ID_CURR": [1, 2],
                    "TARGET": [0, 1],
                    "velocity_prev_count_7d": [3, 1],
                }
            ).to_parquet(candidate / "auto" / "auto_feature_matrix.parquet", index=False)
            pd.DataFrame(
                {
                    "SK_ID_CURR": [1, 2],
                    "TARGET": [0, 1],
                    "cashout_atm_ratio_mean": [0.5, 0.2],
                    "consistency_prev_credit_gap_ratio_mean": [0.3, 0.1],
                    "velocity_prev_count_30d": [4, 1],
                    "cashout_fpd_severe_flag": [1, 0],
                }
            ).to_parquet(candidate / "semantic" / "semantic_feature_matrix.parquet", index=False)

            with patch("dual_engine.skills_runtime.EnginePaths", return_value=paths):
                result = run_composite_features()

            self.assertEqual(result["status"], "success")
            self.assertTrue((candidate / "composite" / "composite_feature_matrix.parquet").exists())
            self.assertTrue((candidate / "registry" / "composite_feature_spec.csv").exists())

    def test_build_candidate_pool_merges_existing_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            candidate = root / "outputs" / "candidate_pool"
            (candidate / "auto").mkdir(parents=True)
            (candidate / "semantic").mkdir(parents=True)
            (candidate / "composite").mkdir(parents=True)
            (candidate / "registry").mkdir(parents=True)
            paths = EnginePaths(
                raw_dir=root / "data" / "raw",
                output_dir=root / "outputs",
                candidate_dir=candidate,
                selection_dir=root / "outputs" / "selection",
            )

            pd.DataFrame({"SK_ID_CURR": [1], "TARGET": [0], "auto_a": [1.0]}).to_parquet(
                candidate / "auto" / "auto_feature_matrix.parquet",
                index=False,
            )
            pd.DataFrame({"feature_name": ["auto_a"], "feature_source": ["auto"]}).to_csv(
                candidate / "auto" / "auto_feature_defs.csv",
                index=False,
            )
            (candidate / "auto" / "auto_feature_summary.json").write_text(json.dumps({"sample_size": 10, "max_depth": 2}))
            pd.DataFrame({"SK_ID_CURR": [1], "TARGET": [0], "semantic_a": [2.0]}).to_parquet(
                candidate / "semantic" / "semantic_feature_matrix.parquet",
                index=False,
            )
            pd.DataFrame(
                {
                    "feature_name": ["semantic_a"],
                    "feature_source": ["semantic"],
                    "feature_group": ["velocity"],
                    "source_table": ["previous_application"],
                    "business_definition": ["test semantic"],
                    "risk_direction": ["higher_is_riskier"],
                    "status": ["candidate"],
                }
            ).to_csv(candidate / "semantic" / "semantic_feature_registry.csv", index=False)
            pd.DataFrame({"SK_ID_CURR": [1], "composite_a": [1]}).to_parquet(
                candidate / "composite" / "composite_feature_matrix.parquet",
                index=False,
            )
            pd.DataFrame(
                {
                    "feature_name": ["composite_a"],
                    "feature_source": ["composite"],
                    "feature_group": ["composite"],
                    "source_table": ["candidate_pool"],
                    "business_definition": ["test composite"],
                    "risk_direction": ["higher_is_riskier"],
                    "status": ["candidate"],
                }
            ).to_csv(candidate / "composite" / "composite_feature_registry.csv", index=False)
            pd.DataFrame(
                {
                    "feature_name": ["composite_a"],
                    "formula": ["semantic_a * auto_a"],
                    "base_features": ["semantic_a, auto_a"],
                    "business_definition": ["test composite"],
                    "risk_direction": ["higher_is_riskier"],
                    "notes": ["test"],
                }
            ).to_csv(candidate / "registry" / "composite_feature_spec.csv", index=False)

            with patch("dual_engine.skills_runtime.EnginePaths", return_value=paths):
                result = build_candidate_pool()

            self.assertEqual(result["status"], "success")
            built = pd.read_parquet(candidate / "candidate_pool.parquet")
            self.assertEqual(list(built.columns), ["SK_ID_CURR", "TARGET", "auto_a", "semantic_a", "composite_a"])
            registry = pd.read_csv(candidate / "registry" / "feature_registry.csv")
            self.assertEqual(set(registry["feature_source"]), {"auto", "semantic", "composite"})

    def test_archive_latest_run_moves_project_and_keeps_clean_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "data" / "raw").mkdir(parents=True)
            outputs = root / "outputs"
            candidate = outputs / "candidate_pool"
            selection = outputs / "selection"
            (candidate / "registry").mkdir(parents=True)
            (candidate / "semantic").mkdir(parents=True)
            selection.mkdir(parents=True)
            (root / "docs").mkdir(parents=True)
            (root / "src").mkdir(parents=True)
            (root / "docs" / "note.md").write_text("doc")
            (root / "src" / "main.py").write_text("print('ok')\n")
            paths = EnginePaths(
                raw_dir=root / "data" / "raw",
                output_dir=outputs,
                candidate_dir=candidate,
                selection_dir=selection,
            )

            (candidate / "candidate_pool_summary.json").write_text(
                json.dumps(
                    {
                        "auto_feature_count": 10,
                        "semantic_feature_count": 3,
                        "composite_feature_count": 2,
                        "candidate_pool_shape": [20, 15],
                    },
                    ensure_ascii=False,
                )
            )
            (selection / "feature_selection_report.json").write_text(
                json.dumps({"selected_feature_count": 5}, ensure_ascii=False)
            )
            pd.DataFrame({"feature_name": ["a"]}).to_csv(candidate / "registry" / "feature_registry.csv", index=False)
            pd.DataFrame({"feature_name": ["b"]}).to_csv(candidate / "registry" / "composite_feature_spec.csv", index=False)
            pd.DataFrame({"SK_ID_CURR": [1, 2, 3]}).to_parquet(candidate / "semantic" / "semantic_feature_matrix.parquet", index=False)
            pd.DataFrame({"SK_ID_CURR": [1, 2]}).to_parquet(candidate / "candidate_pool.parquet", index=False)

            with patch("dual_engine.skills_runtime.EnginePaths", return_value=paths):
                result = archive_latest_run(topic="反欺诈POC", base_dir=root)

            self.assertEqual(result["status"], "success")
            archive_dir = Path(result["summary"]["archive_dir"])
            self.assertTrue((archive_dir / "conclusion" / "summary.md").exists())
            self.assertTrue((archive_dir / "conclusion" / "artifacts.json").exists())
            self.assertTrue((archive_dir / "project" / "outputs" / "candidate_pool" / "candidate_pool_summary.json").exists())
            self.assertTrue((archive_dir / "project" / "src" / "main.py").exists())
            self.assertEqual(sorted(path.name for path in root.iterdir()), ["archives", "data"])

    def test_archive_latest_run_excludes_hidden_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "data" / "raw").mkdir(parents=True)
            outputs = root / "outputs"
            candidate = outputs / "candidate_pool"
            selection = outputs / "selection"
            (candidate / "registry").mkdir(parents=True)
            (candidate / "semantic").mkdir(parents=True)
            selection.mkdir(parents=True)
            (root / "src").mkdir(parents=True)
            (root / "src" / "main.py").write_text("print('ok')\n")
            # 创建隐藏目录/文件
            (root / ".git").mkdir()
            (root / ".git" / "config").write_text("[core]")
            (root / ".claude").mkdir()
            (root / ".claude" / "settings.json").write_text("{}")
            (root / ".venv").mkdir()
            (root / ".gitignore").write_text("*.pyc\n")
            paths = EnginePaths(
                raw_dir=root / "data" / "raw",
                output_dir=outputs,
                candidate_dir=candidate,
                selection_dir=selection,
            )

            (candidate / "candidate_pool_summary.json").write_text(
                json.dumps(
                    {
                        "auto_feature_count": 1,
                        "semantic_feature_count": 0,
                        "composite_feature_count": 0,
                        "candidate_pool_shape": [2, 2],
                    },
                    ensure_ascii=False,
                )
            )
            (selection / "feature_selection_report.json").write_text(
                json.dumps({"selected_feature_count": 0}, ensure_ascii=False)
            )
            pd.DataFrame({"feature_name": ["a"]}).to_csv(candidate / "registry" / "feature_registry.csv", index=False)
            pd.DataFrame({"feature_name": ["b"]}).to_csv(candidate / "registry" / "composite_feature_spec.csv", index=False)
            pd.DataFrame({"SK_ID_CURR": [1]}).to_parquet(candidate / "semantic" / "semantic_feature_matrix.parquet", index=False)
            pd.DataFrame({"SK_ID_CURR": [1]}).to_parquet(candidate / "candidate_pool.parquet", index=False)

            with patch("dual_engine.skills_runtime.EnginePaths", return_value=paths):
                result = archive_latest_run(topic="hidden_test", base_dir=root)

            self.assertEqual(result["status"], "success")
            # 隐藏目录/文件应留在工作区，不被移走
            self.assertTrue((root / ".git" / "config").exists())
            self.assertTrue((root / ".claude" / "settings.json").exists())
            self.assertTrue((root / ".venv").exists())
            self.assertTrue((root / ".gitignore").exists())
            # 非隐藏目录应被归档
            remaining = sorted(path.name for path in root.iterdir())
            self.assertIn(".git", remaining)
            self.assertIn(".claude", remaining)
            self.assertIn(".venv", remaining)
            self.assertIn(".gitignore", remaining)
            self.assertIn("archives", remaining)
            self.assertIn("data", remaining)
            self.assertNotIn("src", remaining)
        root = Path(__file__).resolve().parents[1] / "skills"
        expected = [
            root / "feature-mining-orchestrator" / "SKILL.md",
            root / "feature-mining-orchestrator" / "agents" / "openai.yaml",
            root / "feature-mining-orchestrator" / "scripts" / "run_auto_features.py",
            root / "feature-mining-orchestrator" / "scripts" / "run_semantic_features.py",
            root / "feature-mining-orchestrator" / "scripts" / "run_composite_features.py",
            root / "feature-mining-orchestrator" / "scripts" / "build_candidate_pool.py",
            root / "feature-mining-orchestrator" / "scripts" / "select_features.py",
            root / "feature-mining-orchestrator" / "scripts" / "archive_run.py",
        ]
        for path in expected:
            self.assertTrue(path.exists(), msg=f"缺少文件: {path}")
        # 确认子 skill 已删除
        removed = [
            root / "feature-mining-semantic-ideation",
            root / "feature-mining-selection-interpreter",
            root / "feature-mining-results-navigator",
        ]
        for path in removed:
            self.assertFalse(path.exists(), msg=f"应已删除: {path}")


if __name__ == "__main__":
    unittest.main()

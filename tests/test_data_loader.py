from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from app import data_loader


class DataLoaderTest(unittest.TestCase):
    def test_build_lineage_warning_detects_row_mismatch(self) -> None:
        artifacts = {
            "candidate_pool": pd.DataFrame({"a": [1, 2]}),
            "auto_feature_matrix": pd.DataFrame({"a": [1, 2]}),
            "semantic_feature_matrix": pd.DataFrame({"a": [1, 2, 3]}),
            "selected_features": pd.DataFrame({"a": [1, 2]}),
        }
        warning = data_loader.build_lineage_warning(artifacts)
        self.assertIsNotNone(warning)
        self.assertIn("数据口径不完全一致", warning)

    def test_source_counts(self) -> None:
        registry = pd.DataFrame(
            {
                "feature_source": ["auto", "auto", "semantic"],
                "feature_group": ["g1", "g1", "g2"],
            }
        )
        counts = data_loader.source_counts(registry)
        self.assertEqual(counts.iloc[0]["feature_source"], "auto")
        self.assertEqual(int(counts.iloc[0]["feature_count"]), 2)

    def test_load_artifact_reads_json_csv_and_parquet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            json_path = tmp / "sample.json"
            csv_path = tmp / "sample.csv"
            parquet_path = tmp / "sample.parquet"
            json_path.write_text(json.dumps({"a": 1}))
            pd.DataFrame({"a": [1]}).to_csv(csv_path, index=False)
            pd.DataFrame({"a": [1]}).to_parquet(parquet_path, index=False)

            original = data_loader.ARTIFACTS.copy()
            try:
                data_loader.ARTIFACTS["json_test"] = data_loader.ArtifactFile("json_test", json_path, "json", "json")
                data_loader.ARTIFACTS["csv_test"] = data_loader.ArtifactFile("csv_test", csv_path, "csv", "csv")
                data_loader.ARTIFACTS["parquet_test"] = data_loader.ArtifactFile("parquet_test", parquet_path, "parquet", "parquet")
                self.assertEqual(data_loader.load_artifact("json_test")["a"], 1)
                self.assertEqual(int(data_loader.load_artifact("csv_test").iloc[0]["a"]), 1)
                self.assertEqual(int(data_loader.load_artifact("parquet_test").iloc[0]["a"]), 1)
            finally:
                data_loader.ARTIFACTS.clear()
                data_loader.ARTIFACTS.update(original)


if __name__ == "__main__":
    unittest.main()

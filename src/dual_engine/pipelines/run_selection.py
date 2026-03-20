from __future__ import annotations

import argparse

import pandas as pd

from dual_engine.config import EnginePaths, SelectionConfig
from dual_engine.selection import run_feature_selection


def run_selection(input_path: str | None = None) -> dict:
    paths = EnginePaths()
    pool_path = input_path or str(paths.candidate_dir / "candidate_pool.parquet")
    frame = pd.read_parquet(pool_path)
    return run_feature_selection(frame=frame, config=SelectionConfig(), output_dir=paths.selection_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run selection on dual-engine candidate pool.")
    parser.add_argument("--input-path", type=str, default=None)
    args = parser.parse_args()
    run_selection(input_path=args.input_path)

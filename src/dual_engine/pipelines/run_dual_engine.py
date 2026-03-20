from __future__ import annotations

import argparse
import json
from pathlib import Path

from dual_engine.pipelines.run_candidate_pool import run_candidate_pool
from dual_engine.pipelines.run_selection import run_selection


def run_all(sample_size: int = 3000, max_depth: int = 2) -> dict:
    candidate_summary = run_candidate_pool(sample_size=sample_size, max_depth=max_depth)
    selection_summary = run_selection()
    summary = {
        "candidate_summary": candidate_summary,
        "selection_summary": selection_summary,
    }
    output = Path("outputs/dual_engine_summary.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full dual-engine pipeline.")
    parser.add_argument("--sample-size", type=int, default=3000)
    parser.add_argument("--max-depth", type=int, default=2)
    args = parser.parse_args()
    run_all(sample_size=args.sample_size, max_depth=args.max_depth)

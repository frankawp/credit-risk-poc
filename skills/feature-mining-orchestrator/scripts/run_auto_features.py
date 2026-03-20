#!/usr/bin/env python3
from __future__ import annotations

import argparse

from common import emit_result
from dual_engine.skills_runtime import run_auto_features


def main() -> int:
    parser = argparse.ArgumentParser(description="运行自动特征生成。")
    parser.add_argument("--sample-size", type=int, default=3000)
    parser.add_argument("--max-depth", type=int, default=2)
    args = parser.parse_args()
    return emit_result(run_auto_features(sample_size=args.sample_size, max_depth=args.max_depth))


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse

from common import emit_result
from dual_engine.skills_runtime import run_selection_stage


def main() -> int:
    parser = argparse.ArgumentParser(description="运行特征筛选。")
    parser.add_argument("--input-path", type=str, default=None)
    args = parser.parse_args()
    return emit_result(run_selection_stage(input_path=args.input_path))


if __name__ == "__main__":
    raise SystemExit(main())

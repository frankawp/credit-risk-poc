#!/usr/bin/env python3
from __future__ import annotations

import argparse

from common import emit_result
from dual_engine.skills_runtime import run_semantic_features


def main() -> int:
    parser = argparse.ArgumentParser(description="运行语义特征生成。")
    parser.add_argument(
        "--themes",
        type=str,
        default="all",
        help="逗号分隔的主题列表：consistency,velocity,cashout,collusion 或 all",
    )
    args = parser.parse_args()
    themes = [theme.strip() for theme in args.themes.split(",") if theme.strip()]
    return emit_result(run_semantic_features(themes=themes))


if __name__ == "__main__":
    raise SystemExit(main())

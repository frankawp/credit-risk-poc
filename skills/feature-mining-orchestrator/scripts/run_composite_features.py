#!/usr/bin/env python3
from __future__ import annotations

from common import emit_result
from dual_engine.skills_runtime import run_composite_features


def main() -> int:
    return emit_result(run_composite_features())


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

from common import emit_result
from dual_engine.skills_runtime import build_candidate_pool


def main() -> int:
    return emit_result(build_candidate_pool())


if __name__ == "__main__":
    raise SystemExit(main())

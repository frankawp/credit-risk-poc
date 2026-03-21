#!/usr/bin/env python3
from __future__ import annotations

import argparse

from common import emit_result
from dual_engine.skills_runtime import archive_latest_run


def main() -> int:
    parser = argparse.ArgumentParser(description="归档当前变量挖掘任务。")
    parser.add_argument("--topic", type=str, default="feature_mining")
    parser.add_argument("--task-type", type=str, default="完整变量挖掘")
    parser.add_argument("--notes", type=str, default=None)
    args = parser.parse_args()
    return emit_result(archive_latest_run(topic=args.topic, task_type=args.task_type, notes=args.notes))


if __name__ == "__main__":
    raise SystemExit(main())

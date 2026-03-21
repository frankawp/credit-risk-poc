from __future__ import annotations

import json
import sys
from pathlib import Path


def _find_project_root() -> Path:
    """从当前文件向上查找包含 pyproject.toml 或 .git 的目录作为项目根。"""
    current = Path(__file__).resolve().parent
    for ancestor in [current, *current.parents]:
        if (ancestor / "pyproject.toml").exists() or (ancestor / ".git").exists():
            return ancestor
    # 兜底：回退到 scripts/ 的第 4 级父目录（.claude/skills/<name>/scripts/）
    return Path(__file__).resolve().parents[4]


ROOT = _find_project_root()
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def emit_result(result: dict) -> int:
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") != "error" else 1

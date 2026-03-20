from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"

for candidate in [str(ROOT), str(SRC)]:
    if candidate not in sys.path:
        sys.path.insert(0, candidate)


def emit_result(result: dict) -> int:
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") != "error" else 1

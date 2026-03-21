from __future__ import annotations

import json


def emit_result(result: dict) -> int:
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") != "error" else 1

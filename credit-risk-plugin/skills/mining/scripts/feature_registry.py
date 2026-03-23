#!/usr/bin/env python3
"""
变量注册管理工具 - 管理变量假设和实现状态。

用法:
    python3 feature_registry.py list [--theme <主题>]
    python3 feature_registry.py register --name <变量名> --theme <主题> --hypothesis "<假设>"
    python3 feature_registry.py update --name <变量名> --status <状态>
    python3 feature_registry.py export --output <输出文件>

示例:
    python3 feature_registry.py list
    python3 feature_registry.py register --name velocity_apply_count_7d --theme velocity --hypothesis "短期高频申请风险更高"
    python3 feature_registry.py update --name velocity_apply_count_7d --status implemented
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY_PATH = Path("outputs/proposed_features/registry.json")
VALID_STATUSES = ("proposed", "implemented", "validated", "selected", "rejected")


def validate_status(status: str) -> str:
    """校验变量状态。"""
    if status not in VALID_STATUSES:
        allowed = ", ".join(VALID_STATUSES)
        raise ValueError(f"不支持的状态: {status}。允许值: {allowed}")
    return status


def load_registry(path: Path) -> dict[str, Any]:
    """加载变量注册表。"""
    if not path.exists():
        return {"features": [], "created_at": datetime.now().isoformat()}
    return json.loads(path.read_text())


def save_registry(registry: dict[str, Any], path: Path) -> None:
    """保存变量注册表。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    registry["updated_at"] = datetime.now().isoformat()
    path.write_text(json.dumps(registry, indent=2, ensure_ascii=False))


def list_features(
    theme: str | None = None,
    status: str | None = None,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
) -> dict[str, Any]:
    """列出已注册的变量。"""
    registry = load_registry(registry_path)
    features = registry.get("features", [])

    # 过滤
    if theme:
        features = [f for f in features if f.get("theme") == theme]
    if status:
        features = [f for f in features if f.get("status") == status]

    return {
        "status": "success",
        "total": len(features),
        "features": features,
        "registry_path": str(registry_path),
    }


def register_feature(
    name: str,
    theme: str,
    hypothesis: str,
    expected_direction: str = "higher_is_riskier",
    calculation_logic: str | None = None,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
) -> dict[str, Any]:
    """注册新变量假设。"""
    registry = load_registry(registry_path)
    features = registry.get("features", [])

    # 检查是否已存在
    existing_names = [f["name"] for f in features]
    if name in existing_names:
        return {
            "status": "warning",
            "message": f"变量 '{name}' 已存在",
            "existing_feature": next(f for f in features if f["name"] == name),
        }

    # 添加新变量
    new_feature = {
        "name": name,
        "theme": theme,
        "hypothesis": hypothesis,
        "expected_direction": expected_direction,
        "calculation_logic": calculation_logic,
        "status": "proposed",
        "created_at": datetime.now().isoformat(),
    }
    features.append(new_feature)
    registry["features"] = features
    save_registry(registry, registry_path)

    return {
        "status": "success",
        "message": f"变量 '{name}' 已注册",
        "feature": new_feature,
        "total_features": len(features),
    }


def update_feature(
    name: str,
    status: str | None = None,
    hypothesis: str | None = None,
    calculation_logic: str | None = None,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
) -> dict[str, Any]:
    """更新变量状态或信息。"""
    registry = load_registry(registry_path)
    features = registry.get("features", [])

    # 查找变量
    feature = None
    for f in features:
        if f["name"] == name:
            feature = f
            break

    if feature is None:
        return {
            "status": "error",
            "message": f"变量 '{name}' 不存在",
        }

    # 更新字段
    if status:
        try:
            feature["status"] = validate_status(status)
        except ValueError as exc:
            return {
                "status": "error",
                "message": str(exc),
            }
    if hypothesis:
        feature["hypothesis"] = hypothesis
    if calculation_logic:
        feature["calculation_logic"] = calculation_logic
    feature["updated_at"] = datetime.now().isoformat()

    registry["features"] = features
    save_registry(registry, registry_path)

    return {
        "status": "success",
        "message": f"变量 '{name}' 已更新",
        "feature": feature,
    }


def export_registry(
    output_path: Path,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
) -> dict[str, Any]:
    """导出注册表到 CSV 或 JSON。"""
    registry = load_registry(registry_path)
    features = registry.get("features", [])

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix == ".csv":
        import pandas as pd
        df = pd.DataFrame(features)
        df.to_csv(output_path, index=False)
    else:
        output_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False))

    return {
        "status": "success",
        "message": f"注册表已导出到 {output_path}",
        "feature_count": len(features),
    }


def print_features(features: list[dict[str, Any]], title: str = "已注册变量") -> None:
    """打印变量列表。"""
    print(f"\n{'='*60}")
    print(title)
    print(f"{'='*60}")

    if not features:
        print("暂无注册变量")
        return

    print(f"{'变量名':<35} {'主题':<12} {'状态':<12}")
    print("-" * 60)
    for f in features:
        print(f"{f['name']:<35} {f.get('theme', 'N/A'):<12} {f.get('status', 'N/A'):<12}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="变量注册管理工具 - 管理变量假设和实现状态"
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # list 命令
    list_parser = subparsers.add_parser("list", help="列出已注册变量")
    list_parser.add_argument("--theme", "-t", type=str, help="按主题过滤")
    list_parser.add_argument("--status", "-s", type=str, help="按状态过滤")
    list_parser.add_argument("--registry", "-r", type=Path, default=DEFAULT_REGISTRY_PATH, help="注册表路径")

    # register 命令
    reg_parser = subparsers.add_parser("register", help="注册新变量")
    reg_parser.add_argument("--name", "-n", type=str, required=True, help="变量名")
    reg_parser.add_argument("--theme", "-t", type=str, required=True, help="主题")
    reg_parser.add_argument("--hypothesis", "-p", type=str, required=True, help="业务假设")
    reg_parser.add_argument("--direction", "-d", type=str, default="higher_is_riskier", help="预期方向")
    reg_parser.add_argument("--logic", "-l", type=str, default=None, help="计算逻辑")
    reg_parser.add_argument("--registry", "-r", type=Path, default=DEFAULT_REGISTRY_PATH, help="注册表路径")

    # update 命令
    upd_parser = subparsers.add_parser("update", help="更新变量信息")
    upd_parser.add_argument("--name", "-n", type=str, required=True, help="变量名")
    upd_parser.add_argument(
        "--status",
        "-s",
        type=str,
        choices=VALID_STATUSES,
        default=None,
        help=f"新状态，可选: {', '.join(VALID_STATUSES)}",
    )
    upd_parser.add_argument("--hypothesis", "-p", type=str, default=None, help="新假设")
    upd_parser.add_argument("--logic", "-l", type=str, default=None, help="新计算逻辑")
    upd_parser.add_argument("--registry", "-r", type=Path, default=DEFAULT_REGISTRY_PATH, help="注册表路径")

    # export 命令
    exp_parser = subparsers.add_parser("export", help="导出注册表")
    exp_parser.add_argument("--output", "-o", type=Path, required=True, help="输出文件路径")
    exp_parser.add_argument("--registry", "-r", type=Path, default=DEFAULT_REGISTRY_PATH, help="注册表路径")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    # 执行命令
    if args.command == "list":
        result = list_features(
            theme=args.theme,
            status=args.status,
            registry_path=args.registry,
        )
        print_features(result["features"], f"已注册变量 (共 {result['total']} 个)")

    elif args.command == "register":
        result = register_feature(
            name=args.name,
            theme=args.theme,
            hypothesis=args.hypothesis,
            expected_direction=args.direction,
            calculation_logic=args.logic,
            registry_path=args.registry,
        )
        if result["status"] == "success":
            print(f"✅ {result['message']}")
        else:
            print(f"⚠️ {result['message']}")

    elif args.command == "update":
        result = update_feature(
            name=args.name,
            status=args.status,
            hypothesis=args.hypothesis,
            calculation_logic=args.logic,
            registry_path=args.registry,
        )
        if result["status"] == "success":
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")

    elif args.command == "export":
        result = export_registry(
            output_path=args.output,
            registry_path=args.registry,
        )
        print(f"✅ {result['message']}")


if __name__ == "__main__":
    main()

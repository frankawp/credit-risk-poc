#!/usr/bin/env python3
"""
归档工具 - 归档当前分析产物并生成摘要报告。

用法:
    python archive_run.py --topic <主题> --notes "<备注>"
    python archive_run.py --topic "首期违约分析" --notes "验证套现假设"

注意: 此工具只应在用户明确要求归档时执行，禁止自动归档！
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def archive_run(
    topic: str,
    notes: str | None = None,
    workspace_root: Path | None = None,
    archive_dir_name: str = "archives",
) -> dict[str, Any]:
    """
    归档当前分析产物。

    参数:
        topic: 归档主题
        notes: 备注信息
        workspace_root: 工作区根目录
        archive_dir_name: 归档目录名
    """
    workspace_root = workspace_root or Path.cwd()

    # 生成归档目录名
    topic_slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", topic).strip("_") or "analysis"
    datetime_prefix = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    archive_dir = workspace_root / archive_dir_name / "analysis_run" / f"{datetime_prefix}_{topic_slug}"

    if archive_dir.exists():
        return {
            "status": "error",
            "message": f"归档目录已存在：{archive_dir}",
            "archive_dir": str(archive_dir),
        }

    # 创建归档目录
    conclusion_dir = archive_dir / "conclusion"
    project_dir = archive_dir / "project"
    conclusion_dir.mkdir(parents=True, exist_ok=False)
    project_dir.mkdir(parents=True, exist_ok=False)

    # 收集要归档的顶层条目（排除 data/ 和 archives/）
    top_level_entries = [
        item for item in workspace_root.iterdir()
        if item.name not in {"data", "archives", archive_dir_name} and not item.name.startswith(".")
    ]

    if not top_level_entries:
        return {
            "status": "warning",
            "message": "没有可归档的内容",
            "archive_dir": str(archive_dir),
        }

    # 移动文件到归档目录
    archived_entries = []
    for item in top_level_entries:
        try:
            shutil.move(str(item), str(project_dir / item.name))
            archived_entries.append(item.name)
        except Exception as e:
            print(f"⚠️ 无法移动 {item.name}: {e}")

    # 生成摘要报告
    summary_path = conclusion_dir / "summary.md"
    artifacts_path = conclusion_dir / "artifacts.json"

    # 尝试读取 outputs 目录中的统计信息
    outputs_dir = project_dir / "outputs"
    candidate_summary = {}
    selection_summary = {}

    candidate_summary_path = outputs_dir / "candidate_pool" / "candidate_pool_summary.json"
    if candidate_summary_path.exists():
        candidate_summary = json.loads(candidate_summary_path.read_text())

    selection_summary_path = outputs_dir / "selection" / "feature_selection_report.json"
    if selection_summary_path.exists():
        selection_summary = json.loads(selection_summary_path.read_text())

    # 写入摘要
    summary_content = f"""# 本轮挖掘摘要

- 时间：{datetime_prefix}
- 主题：{topic}
- 备注：{notes or '无'}

## 统计信息

- 候选池规模：{candidate_summary.get('candidate_pool_shape', 'N/A')}
- 自动特征数：{candidate_summary.get('auto_feature_count', 'N/A')}
- 语义特征数：{candidate_summary.get('semantic_feature_count', 'N/A')}
- 组合特征数：{candidate_summary.get('composite_feature_count', 'N/A')}
- 入选特征数：{selection_summary.get('selected_feature_count', 'N/A')}

## 归档内容

- 归档目录：project/
- 已归档条目：{len(archived_entries)} 个
"""
    summary_path.write_text(summary_content)

    # 写入产物清单
    artifacts_payload = {
        "topic": topic,
        "notes": notes,
        "archive_dir": str(archive_dir.relative_to(workspace_root)),
        "archived_at": datetime.now().isoformat(),
        "archived_entries": archived_entries,
        "statistics": {
            "candidate_pool_shape": candidate_summary.get("candidate_pool_shape"),
            "auto_feature_count": candidate_summary.get("auto_feature_count"),
            "semantic_feature_count": candidate_summary.get("semantic_feature_count"),
            "composite_feature_count": candidate_summary.get("composite_feature_count"),
            "selected_feature_count": selection_summary.get("selected_feature_count"),
        },
    }
    artifacts_path.write_text(json.dumps(artifacts_payload, indent=2, ensure_ascii=False))

    return {
        "status": "success",
        "message": f"归档完成：{len(archived_entries)} 个条目已归档",
        "archive_dir": str(archive_dir),
        "archived_entries": archived_entries,
        "summary_file": str(summary_path),
        "artifacts_file": str(artifacts_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="归档工具 - 归档当前分析产物（仅用户明确要求时执行）"
    )
    parser.add_argument(
        "--topic",
        "-t",
        type=str,
        required=True,
        help="归档主题",
    )
    parser.add_argument(
        "--notes",
        "-n",
        type=str,
        default=None,
        help="备注信息",
    )
    parser.add_argument(
        "--workspace",
        "-w",
        type=Path,
        default=None,
        help="工作区根目录（默认当前目录）",
    )

    args = parser.parse_args()

    # 确认操作
    print(f"\n{'='*60}")
    print("归档确认")
    print(f"{'='*60}")
    print(f"主题: {args.topic}")
    print(f"备注: {args.notes or '无'}")
    print(f"工作区: {args.workspace or Path.cwd()}")
    print()
    print("⚠️ 此操作将移动 outputs/ 等目录到归档位置")
    print()

    response = input("确认归档？(y/N): ")
    if response.lower() != "y":
        print("已取消归档")
        return

    # 执行归档
    result = archive_run(
        topic=args.topic,
        notes=args.notes,
        workspace_root=args.workspace,
    )

    print()
    if result["status"] == "success":
        print(f"✅ {result['message']}")
        print(f"📁 归档目录: {result['archive_dir']}")
        print(f"📄 摘要文件: {result['summary_file']}")
    else:
        print(f"❌ {result['message']}")


if __name__ == "__main__":
    main()

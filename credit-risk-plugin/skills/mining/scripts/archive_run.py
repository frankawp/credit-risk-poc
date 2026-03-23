#!/usr/bin/env python3
"""
归档工具 - 归档当前分析产物并生成摘要报告。

用法:
    python3 archive_run.py --topic <主题> --notes "<备注>"
    python3 archive_run.py --topic "首期违约分析" --notes "验证套现假设"

注意: 此工具只应在用户明确要求归档时执行，禁止自动归档！
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


OUTPUT_ROOT = "outputs"
DEFAULT_OUTPUT_SUBDIRS = ("reports", "data", "proposed_features")


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    """按需加载 JSON。"""
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _collect_archive_targets(workspace_root: Path) -> list[Path]:
    """收集允许归档的分析产物目录。"""
    outputs_dir = workspace_root / OUTPUT_ROOT
    if not outputs_dir.exists() or not outputs_dir.is_dir():
        return []
    if not any(outputs_dir.iterdir()):
        return []
    return [outputs_dir]


def _reset_output_workspace(workspace_root: Path) -> None:
    """重建空输出目录，便于下一轮分析直接开始。"""
    outputs_dir = workspace_root / OUTPUT_ROOT
    outputs_dir.mkdir(parents=True, exist_ok=True)
    for subdir in DEFAULT_OUTPUT_SUBDIRS:
        (outputs_dir / subdir).mkdir(parents=True, exist_ok=True)


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

    # 只归档分析产物，不触碰技能源码和说明文件
    top_level_entries = _collect_archive_targets(workspace_root)

    if not top_level_entries:
        _reset_output_workspace(workspace_root)
        return {
            "status": "warning",
            "message": "没有可归档的内容",
            "archive_dir": str(archive_dir),
        }

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

    # 移动文件到归档目录
    archived_entries = []
    for item in top_level_entries:
        try:
            shutil.move(str(item), str(project_dir / item.name))
            archived_entries.append(item.name)
        except Exception as e:
            print(f"⚠️ 无法移动 {item.name}: {e}")

    _reset_output_workspace(workspace_root)

    # 生成摘要报告
    summary_path = conclusion_dir / "summary.md"
    artifacts_path = conclusion_dir / "artifacts.json"

    # 尝试读取 outputs 目录中的统计信息
    outputs_dir = project_dir / "outputs"
    candidate_summary = _load_json_if_exists(outputs_dir / "candidate_pool" / "candidate_pool_summary.json")
    selection_summary = _load_json_if_exists(outputs_dir / "selection" / "feature_selection_report.json")
    report_count = len(list((outputs_dir / "reports").glob("*.md"))) if (outputs_dir / "reports").exists() else 0

    # 写入摘要
    summary_content = f"""# 本轮挖掘摘要

- 时间：{datetime_prefix}
- 主题：{topic}
- 备注：{notes or '无'}

## 统计信息

- 候选池行数：{candidate_summary.get('row_count', 'N/A')}
- 候选特征数：{candidate_summary.get('total_feature_count', candidate_summary.get('candidate_pool_shape', 'N/A'))}
- 自动特征数：{candidate_summary.get('auto_feature_count', 'N/A')}
- 语义特征数：{candidate_summary.get('semantic_feature_count', 'N/A')}
- 组合特征数：{candidate_summary.get('composite_feature_count', 'N/A')}
- 入选特征数：{selection_summary.get('selected_feature_count', 'N/A')}
- 归档报告数：{report_count}

## 归档内容

- 归档目录：project/
- 已归档条目：{len(archived_entries)} 个
- 归档对象：{', '.join(archived_entries)}
- 工作区已重建空输出目录：{OUTPUT_ROOT}/
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
            "row_count": candidate_summary.get("row_count"),
            "total_feature_count": candidate_summary.get("total_feature_count"),
            "auto_feature_count": candidate_summary.get("auto_feature_count"),
            "semantic_feature_count": candidate_summary.get("semantic_feature_count"),
            "composite_feature_count": candidate_summary.get("composite_feature_count"),
            "selected_feature_count": selection_summary.get("selected_feature_count"),
            "report_count": report_count,
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
    print("⚠️ 此操作只会移动 outputs/ 下的分析产物，并在归档后重建空 outputs/ 目录")
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

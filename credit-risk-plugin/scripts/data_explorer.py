#!/usr/bin/env python3
"""
数据探索工具 - 自动分析数据目录结构和质量。

用法:
    python data_explorer.py <数据目录> [--output <输出文件>]

示例:
    python data_explorer.py data/raw/
    python data_explorer.py data/raw/ --output outputs/exploration_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


def explore_table(file_path: Path, sample_rows: int = 1000) -> dict[str, Any]:
    """
    探索单个数据表。

    返回表结构、字段统计、缺失率等信息。
    """
    try:
        if file_path.suffix == ".csv":
            df = pd.read_csv(file_path, nrows=sample_rows)
        elif file_path.suffix == ".parquet":
            df = pd.read_parquet(file_path)
            if len(df) > sample_rows:
                df = df.head(sample_rows)
        else:
            return {"file_name": file_path.name, "error": "不支持的文件格式"}

        columns_info = []
        for col in df.columns:
            col_data = df[col]
            col_info = {
                "name": col,
                "dtype": str(col_data.dtype),
                "missing_rate": round(float(col_data.isna().mean()), 4),
                "unique_count": int(col_data.nunique()),
                "sample_values": col_data.dropna().head(3).tolist()[:3],
            }
            columns_info.append(col_info)

        # 识别可能的 ID 列
        potential_ids = [
            col for col in df.columns
            if "id" in col.lower() or df[col].nunique() == len(df)
        ]

        return {
            "file_name": file_path.name,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": columns_info[:30],  # 最多展示 30 列
            "potential_ids": potential_ids[:5],
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        }
    except Exception as e:
        return {"file_name": file_path.name, "error": str(e)}


def explore_directory(
    data_dir: Path,
    sample_rows: int = 1000,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """
    探索数据目录，分析所有表的结构和质量。
    """
    if not data_dir.exists():
        return {
            "status": "error",
            "message": f"数据目录不存在：{data_dir}",
        }

    # 查找所有数据文件
    csv_files = list(data_dir.glob("*.csv"))
    parquet_files = list(data_dir.glob("*.parquet"))
    all_files = csv_files + parquet_files

    if not all_files:
        return {
            "status": "warning",
            "data_dir": str(data_dir),
            "file_count": 0,
            "message": "数据目录中没有 CSV 或 Parquet 文件",
        }

    # 分析每个文件
    tables_info = []
    for file_path in all_files[:15]:  # 最多分析 15 个文件
        table_info = explore_table(file_path, sample_rows)
        tables_info.append(table_info)

    # 统计信息
    total_rows = sum(t.get("row_count", 0) for t in tables_info if "row_count" in t)
    total_columns = sum(t.get("column_count", 0) for t in tables_info if "column_count" in t)

    report = {
        "status": "success",
        "data_dir": str(data_dir),
        "file_count": len(all_files),
        "analyzed_count": len(tables_info),
        "total_rows": total_rows,
        "total_columns": total_columns,
        "tables": tables_info,
    }

    # 保存报告
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        report["output_file"] = str(output_path)

    return report


def print_summary(report: dict[str, Any]) -> None:
    """打印探索报告摘要。"""
    print(f"\n{'='*60}")
    print("数据探索报告")
    print(f"{'='*60}")
    print(f"数据目录: {report.get('data_dir', 'N/A')}")
    print(f"文件数量: {report.get('file_count', 0)}")
    print(f"已分析: {report.get('analyzed_count', 0)} 个文件")
    print(f"总行数: {report.get('total_rows', 0):,}")
    print(f"总列数: {report.get('total_columns', 0)}")
    print()

    for table in report.get("tables", []):
        if "error" in table:
            print(f"❌ {table['file_name']}: {table['error']}")
            continue

        print(f"📊 {table['file_name']}")
        print(f"   行数: {table['row_count']:,} | 列数: {table['column_count']} | 内存: {table['memory_mb']:.1f}MB")
        print(f"   潜在ID列: {', '.join(table.get('potential_ids', []))}")

        # 打印缺失率最高的列
        columns = table.get("columns", [])
        high_missing = [c for c in columns if c["missing_rate"] > 0.3]
        if high_missing:
            print(f"   ⚠️ 高缺失率列: {', '.join(c['name'] for c in high_missing[:3])}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="数据探索工具 - 自动分析数据目录结构和质量"
    )
    parser.add_argument(
        "data_dir",
        type=Path,
        help="数据目录路径",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="输出报告路径 (JSON格式)",
    )
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=1000,
        help="采样行数 (默认: 1000)",
    )

    args = parser.parse_args()

    # 确定输出路径
    output_path = args.output
    if output_path is None:
        output_path = Path("outputs/exploration_report.json")

    # 执行探索
    report = explore_directory(
        data_dir=args.data_dir,
        sample_rows=args.sample_rows,
        output_path=output_path,
    )

    # 打印摘要
    print_summary(report)

    # 输出保存位置
    if "output_file" in report:
        print(f"📄 完整报告已保存到: {report['output_file']}")


if __name__ == "__main__":
    main()

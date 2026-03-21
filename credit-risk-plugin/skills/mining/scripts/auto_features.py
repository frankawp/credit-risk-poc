#!/usr/bin/env python3
"""
自动特征生成工具 - 基于 Featuretools 自动生成聚合/变换特征。

此功能为可选，需要安装 featuretools:
    pip install featuretools

用法:
    python auto_features.py <数据目录> --output <输出目录>
    python auto_features.py data/raw/ --output outputs/auto_features/

注意: 此工具仅适用于结构化数据，需要定义实体关系。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# 检查 featuretools 是否可用
try:
    import featuretools as ft
    import pandas as pd
    FEATURETOOLS_AVAILABLE = True
except ImportError:
    FEATURETOOLS_AVAILABLE = False


def discover_tables(data_dir: Path) -> list[Path]:
    """发现数据目录中的所有表文件。"""
    csv_files = list(data_dir.glob("*.csv"))
    parquet_files = list(data_dir.glob("*.parquet"))
    return csv_files + parquet_files


def infer_entityset(
    data_dir: Path,
    sample_size: int = 5000,
) -> dict[str, Any]:
    """
    推断数据目录的实体关系结构。

    返回可用于构建 EntitySet 的信息。
    """
    tables = discover_tables(data_dir)

    if not tables:
        return {
            "status": "error",
            "message": "数据目录中没有找到 CSV 或 Parquet 文件",
        }

    entity_info = []
    for table_path in tables[:10]:
        try:
            if table_path.suffix == ".csv":
                df = pd.read_csv(table_path, nrows=sample_size)
            else:
                df = pd.read_parquet(table_path)
                if len(df) > sample_size:
                    df = df.head(sample_size)

            # 推断 ID 列
            potential_ids = [
                col for col in df.columns
                if "id" in col.lower() and df[col].nunique() < len(df) * 0.8
            ]

            # 推断索引列
            potential_index = [
                col for col in df.columns
                if df[col].nunique() == len(df) or "sk_id" in col.lower()
            ]

            entity_info.append({
                "table_name": table_path.stem,
                "file_path": str(table_path),
                "row_count": len(df),
                "column_count": len(df.columns),
                "potential_ids": potential_ids[:3],
                "potential_index": potential_index[:1],
            })
        except Exception as e:
            entity_info.append({
                "table_name": table_path.stem,
                "error": str(e),
            })

    return {
        "status": "success",
        "data_dir": str(data_dir),
        "sample_size": sample_size,
        "entities": entity_info,
    }


def generate_auto_features(
    data_dir: Path,
    output_dir: Path,
    sample_size: int = 5000,
    max_depth: int = 2,
    target_entity: str | None = None,
) -> dict[str, Any]:
    """
    使用 Featuretools 自动生成特征。

    此函数需要用户提供实体关系定义，这里只提供框架。
    实际使用时，用户需要根据自己的数据结构自定义 EntitySet。
    """
    if not FEATURETOOLS_AVAILABLE:
        return {
            "status": "error",
            "message": "Featuretools 未安装。请运行: pip install featuretools",
        }

    # 推断实体结构
    entity_info = infer_entityset(data_dir, sample_size)

    if entity_info["status"] == "error":
        return entity_info

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存实体信息供用户参考
    entity_info_path = output_dir / "entity_info.json"
    entity_info_path.write_text(json.dumps(entity_info, indent=2, ensure_ascii=False))

    return {
        "status": "warning",
        "message": "自动特征生成需要自定义实体关系。请参考 entity_info.json 手动配置 EntitySet。",
        "entity_info_file": str(entity_info_path),
        "entities": entity_info["entities"],
        "hint": """
Featuretools 使用示例:

    import featuretools as ft
    import pandas as pd

    # 创建 EntitySet
    es = ft.EntitySet(id="credit_data")

    # 添加实体
    es.add_dataframe(
        dataframe_name="applications",
        dataframe=applications_df,
        index="SK_ID_CURR",
    )

    # 添加关系
    es.add_relationship("applications", "SK_ID_CURR", "bureau", "SK_ID_CURR")

    # 生成特征
    features, feature_names = ft.dfs(
        entityset=es,
        target_dataframe_name="applications",
        max_depth=2,
    )
""",
    }


def main() -> None:
    if not FEATURETOOLS_AVAILABLE:
        print("❌ Featuretools 未安装")
        print("请运行: pip install featuretools")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="自动特征生成工具 - 基于 Featuretools"
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
        default=Path("outputs/auto_features"),
        help="输出目录",
    )
    parser.add_argument(
        "--sample-size",
        "-s",
        type=int,
        default=5000,
        help="采样大小",
    )
    parser.add_argument(
        "--max-depth",
        "-d",
        type=int,
        default=2,
        help="特征生成最大深度",
    )

    args = parser.parse_args()

    result = generate_auto_features(
        data_dir=args.data_dir,
        output_dir=args.output,
        sample_size=args.sample_size,
        max_depth=args.max_depth,
    )

    print(f"\n{'='*60}")
    print("自动特征生成")
    print(f"{'='*60}")

    if result["status"] == "error":
        print(f"❌ {result['message']}")
    elif result["status"] == "warning":
        print(f"⚠️ {result['message']}")
        print(f"\n📄 实体信息已保存到: {result['entity_info_file']}")
        print("\n发现的实体:")
        for e in result.get("entities", []):
            if "error" in e:
                print(f"  ❌ {e['table_name']}: {e['error']}")
            else:
                print(f"  📊 {e['table_name']}: {e['row_count']:,} 行, {e['column_count']} 列")
                print(f"     潜在ID列: {', '.join(e['potential_ids'])}")

        print("\n使用提示:")
        print(result.get("hint", ""))
    else:
        print(f"✅ {result.get('message', '完成')}")


if __name__ == "__main__":
    main()

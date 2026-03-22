"""
数据探索 - 理解数据结构和业务含义。

目标：
1. 识别主键（唯一且非空）
2. 识别外键（引用其他表的主键）
3. 理解表间关系
4. 发现数据质量问题

输出：
- 表结构报告
- 关系推断建议
- 数据质量摘要
"""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# ============================================================================
# 主键识别
# ============================================================================

def is_valid_primary_key(series: pd.Series) -> bool:
    """判断列是否是有效的主键。

    主键条件：
    1. 无缺失值
    2. 值唯一
    """
    if series.isna().any():
        return False
    if series.nunique() != len(series):
        return False
    return True


def detect_primary_key(df: pd.DataFrame) -> list[str]:
    """检测可能的主键列。

    检测策略：
    1. 列名包含 'id', 'sk_', '_id', '_ID'
    2. 值唯一且无缺失
    """
    candidates = []

    for col in df.columns:
        col_lower = col.lower()

        # 命名模式匹配
        is_id_pattern = (
            col_lower.endswith('_id') or
            col_lower.startswith('sk_') or
            col_lower == 'id' or
            '_id_' in col_lower
        )

        # 检查主键条件
        if is_id_pattern and is_valid_primary_key(df[col]):
            candidates.append(col)

    return candidates


def detect_potential_primary_key(df: pd.DataFrame) -> dict[str, Any]:
    """检测潜在主键，返回详细信息。"""
    results = []

    for col in df.columns:
        col_lower = col.lower()
        is_id_pattern = (
            col_lower.endswith('_id') or
            col_lower.startswith('sk_') or
            col_lower == 'id'
        )

        if not is_id_pattern:
            continue

        null_count = df[col].isna().sum()
        null_rate = null_count / len(df)
        unique_count = df[col].nunique()
        is_unique = unique_count == len(df)

        results.append({
            "column": col,
            "null_count": null_count,
            "null_rate": round(null_rate, 4),
            "unique_count": unique_count,
            "total_count": len(df),
            "is_unique": is_unique,
            "is_valid_pk": is_unique and null_count == 0,
        })

    return results


# ============================================================================
# 外键识别
# ============================================================================

def detect_foreign_keys(
    child_df: pd.DataFrame,
    parent_df: pd.DataFrame,
    parent_pk: str,
) -> list[str]:
    """检测子表中引用父表主键的外键列。

    外键条件：
    1. 列名与父表主键名相同
    2. 子表中的值都在父表主键范围内（引用完整性）
    """
    candidates = []
    parent_values = set(parent_df[parent_pk].dropna().unique())

    for col in child_df.columns:
        if col != parent_pk:
            continue

        child_values = set(child_df[col].dropna().unique())

        # 检查引用完整性
        orphan_values = child_values - parent_values
        orphan_rate = len(orphan_values) / len(child_values) if child_values else 0

        # 允许少量孤儿记录（数据质量问题）
        if orphan_rate < 0.01:
            candidates.append(col)

    return candidates


def analyze_table_relationships(
    tables: dict[str, pd.DataFrame],
) -> list[dict[str, Any]]:
    """分析多表之间的关系。

    参数：
        tables: 表名到 DataFrame 的映射

    返回：
        关系列表，每个关系包含父子表和外键信息
    """
    relationships = []

    # 先识别每张表的主键
    pk_map = {}
    for name, df in tables.items():
        pks = detect_primary_key(df)
        pk_map[name] = pks[0] if pks else None

    # 检测表间关系
    table_names = list(tables.keys())
    for i, parent_name in enumerate(table_names):
        parent_df = tables[parent_name]
        parent_pk = pk_map.get(parent_name)

        if not parent_pk:
            continue

        for child_name in table_names:
            if child_name == parent_name:
                continue

            child_df = tables[child_name]
            fks = detect_foreign_keys(child_df, parent_df, parent_pk)

            for fk in fks:
                # 计算关系强度
                parent_count = len(parent_df)
                child_count = len(child_df)

                # 子表中引用父表的记录数
                matched_children = child_df[child_df[fk].isin(parent_df[parent_pk])]

                relationships.append({
                    "parent_table": parent_name,
                    "parent_pk": parent_pk,
                    "child_table": child_name,
                    "foreign_key": fk,
                    "parent_count": parent_count,
                    "child_count": child_count,
                    "matched_child_count": len(matched_children),
                    "relationship_type": "one_to_many" if len(matched_children) > parent_count else "one_to_one",
                })

    return relationships


# ============================================================================
# 数据质量检查
# ============================================================================

def analyze_column_quality(df: pd.DataFrame) -> pd.DataFrame:
    """分析每列的数据质量。

    返回每列的：
    - 数据类型
    - 缺失率
    - 唯一值数
    - 示例值
    """
    results = []

    for col in df.columns:
        series = df[col]

        result = {
            "column": col,
            "dtype": str(series.dtype),
            "null_count": series.isna().sum(),
            "null_rate": round(series.isna().mean(), 4),
            "unique_count": series.nunique(),
            "unique_rate": round(series.nunique() / len(df), 4),
        }

        # 示例值
        sample_values = series.dropna().head(3).tolist()
        result["sample_values"] = sample_values

        # 数值统计
        if pd.api.types.is_numeric_dtype(series):
            result["min"] = series.min()
            result["max"] = series.max()
            result["mean"] = series.mean()

        results.append(result)

    return pd.DataFrame(results)


def analyze_table_summary(
    df: pd.DataFrame,
    table_name: str,
) -> dict[str, Any]:
    """生成表的摘要报告。"""
    pk_candidates = detect_potential_primary_key(df)
    valid_pk = [r for r in pk_candidates if r["is_valid_pk"]]

    return {
        "table_name": table_name,
        "row_count": len(df),
        "column_count": len(df.columns),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        "primary_key_candidates": pk_candidates,
        "valid_primary_keys": [r["column"] for r in valid_pk],
        "high_null_columns": [
            c for c in df.columns
            if df[c].isna().mean() > 0.5
        ],
        "constant_columns": [
            c for c in df.columns
            if df[c].nunique() <= 1
        ],
    }


# ============================================================================
# 完整探索流程
# ============================================================================

def explore_data_directory(
    data_dir: Path,
    sample_size: int = 10000,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """探索数据目录中的所有表。

    参数：
        data_dir: 数据目录路径
        sample_size: 采样行数
        output_dir: 输出目录

    返回：
        探索报告
    """
    # 发现文件
    csv_files = list(data_dir.glob("*.csv"))
    parquet_files = list(data_dir.glob("*.parquet"))
    all_files = csv_files + parquet_files

    if not all_files:
        return {"status": "error", "message": f"未找到数据文件: {data_dir}"}

    # 加载数据
    tables = {}
    for file_path in all_files[:15]:  # 最多 15 个文件
        table_name = file_path.stem
        try:
            if file_path.suffix == ".csv":
                df = pd.read_csv(file_path, nrows=sample_size)
            else:
                df = pd.read_parquet(file_path)
                if len(df) > sample_size:
                    df = df.head(sample_size)
            tables[table_name] = df
        except Exception as e:
            print(f"⚠️ 加载失败 {file_path.name}: {e}")

    # 分析每张表
    table_summaries = []
    for name, df in tables.items():
        summary = analyze_table_summary(df, name)
        summary["column_quality"] = analyze_column_quality(df)
        table_summaries.append(summary)

    # 分析表间关系
    relationships = analyze_table_relationships(tables)

    # 构建报告
    report = {
        "status": "success",
        "data_dir": str(data_dir),
        "table_count": len(tables),
        "tables": table_summaries,
        "relationships": relationships,
        "relationship_count": len(relationships),
    }

    # 保存输出
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

        import json
        (output_dir / "exploration_report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False, default=str)
        )

        # 生成关系图建议
        _generate_relationship_guide(report, output_dir)

    return report


def _generate_relationship_guide(report: dict, output_dir: Path) -> None:
    """生成关系配置建议。"""
    lines = [
        "# 数据关系配置建议",
        "",
        "## 主键识别结果",
        "",
    ]

    for table in report.get("tables", []):
        name = table["table_name"]
        pks = table.get("valid_primary_keys", [])
        lines.append(f"- **{name}**: {pks if pks else '未识别到主键'}")

    lines.extend([
        "",
        "## 推断的关系",
        "",
    ])

    for rel in report.get("relationships", []):
        lines.append(
            f"- {rel['parent_table']}.{rel['parent_pk']} "
            f"→ {rel['child_table']}.{rel['foreign_key']} "
            f"({rel['relationship_type']})"
        )

    lines.extend([
        "",
        "## EntityConfig 配置示例",
        "",
        "```python",
        "from engine import EntityConfig",
        "",
        "configs = [",
    ])

    # 找出主表（被引用最多的表）
    parent_counts = {}
    for rel in report.get("relationships", []):
        parent = rel["parent_table"]
        parent_counts[parent] = parent_counts.get(parent, 0) + 1

    main_table = max(parent_counts, key=parent_counts.get) if parent_counts else None

    for table in report.get("tables", []):
        name = table["table_name"]
        pks = table.get("valid_primary_keys", [])
        pk = pks[0] if pks else "TODO"

        if name == main_table:
            lines.append(f'    EntityConfig(')
            lines.append(f'        name="{name}",')
            lines.append(f'        file_path="{name}.csv",')
            lines.append(f'        index="{pk}",')
            lines.append(f'        parent=None,')
            lines.append(f'    ),')
        else:
            # 找到父表
            parent = None
            fk = None
            for rel in report.get("relationships", []):
                if rel["child_table"] == name:
                    parent = rel["parent_table"]
                    fk = rel["foreign_key"]
                    break

            if parent and fk:
                lines.append(f'    EntityConfig(')
                lines.append(f'        name="{name}",')
                lines.append(f'        file_path="{name}.csv",')
                lines.append(f'        index="{pk}",')
                lines.append(f'        parent="{parent}",')
                lines.append(f'        foreign_key="{fk}",')
                lines.append(f'    ),')

    lines.append("]")
    lines.append("```")

    (output_dir / "relationship_guide.md").write_text("\n".join(lines))


# ============================================================================
# 打印报告
# ============================================================================

def print_exploration_report(report: dict[str, Any]) -> None:
    """打印探索报告摘要。"""
    print("=" * 60)
    print("数据探索报告")
    print("=" * 60)
    print(f"数据目录: {report.get('data_dir', 'N/A')}")
    print(f"表数量: {report.get('table_count', 0)}")
    print(f"关系数量: {report.get('relationship_count', 0)}")
    print()

    for table in report.get("tables", []):
        print(f"📊 {table['table_name']}")
        print(f"   行数: {table['row_count']:,} | 列数: {table['column_count']} | 内存: {table['memory_mb']:.1f}MB")

        pks = table.get("valid_primary_keys", [])
        if pks:
            print(f"   主键: {', '.join(pks)}")
        else:
            print(f"   主键: 未识别")

        if table.get("high_null_columns"):
            print(f"   ⚠️ 高缺失列: {', '.join(table['high_null_columns'][:3])}")

        print()

    if report.get("relationships"):
        print("🔗 推断的关系:")
        for rel in report["relationships"][:10]:
            print(f"   {rel['parent_table']}.{rel['parent_pk']} → {rel['child_table']}.{rel['foreign_key']}")


# ============================================================================
# 运行示例
# ============================================================================

if __name__ == "__main__":
    from pathlib import Path

    # 数据目录
    data_dir = Path("data/raw")

    # 探索数据
    # report = explore_data_directory(
    #     data_dir=data_dir,
    #     sample_size=10000,
    #     output_dir=Path("outputs/exploration"),
    # )

    # 打印报告
    # print_exploration_report(report)

    print("数据探索工具")
    print("用法: explore_data_directory(data_dir, output_dir=Path('outputs/exploration'))")

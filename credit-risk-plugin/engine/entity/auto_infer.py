"""
自动推断实体关系。

扫描数据目录，自动推断表之间的关联关系。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ..config import EntityConfig


def infer_id_columns(df: pd.DataFrame, threshold: float = 0.9) -> list[str]:
    """推断可能的主键/外键列。

    规则：
    - 列名包含 "id" 或 "ID"
    - 唯一值比例 > threshold（主键特征）
    或
    - 列名符合外键命名模式（如 SK_ID_CURR）
    """
    candidates = []

    for col in df.columns:
        col_lower = col.lower()

        # 检查是否包含 id
        if "id" not in col_lower:
            continue

        unique_ratio = df[col].nunique() / len(df)

        # 主键特征：唯一值比例接近 1
        if unique_ratio > threshold:
            candidates.append((col, "primary", unique_ratio))
        # 外键特征：唯一值比例较低，但值类型与主键相似
        elif unique_ratio < threshold:
            candidates.append((col, "foreign", unique_ratio))

    return candidates


def infer_entity_configs(
    data_dir: Path,
    main_entity_hint: str | None = None,
    target_column: str | None = None,
) -> list[EntityConfig]:
    """自动推断实体配置。

    扫描数据目录，根据命名模式和列特征推断实体关系。

    参数：
        data_dir: 数据目录
        main_entity_hint: 主实体名称提示（如 "application"）
        target_column: 目标变量列名

    返回：
        推断的实体配置列表
    """
    configs = []
    id_columns_by_file: dict[str, list[tuple]] = {}

    # 扫描文件
    csv_files = list(data_dir.glob("*.csv"))
    parquet_files = list(data_dir.glob("*.parquet"))
    all_files = csv_files + parquet_files

    if not all_files:
        return configs

    # 分析每个文件
    for file_path in all_files[:20]:  # 最多分析 20 个文件
        try:
            if file_path.suffix == ".parquet":
                df = pd.read_parquet(file_path)
            else:
                df = pd.read_csv(file_path, nrows=1000)

            # 推断 ID 列
            id_cols = infer_id_columns(df)
            id_columns_by_file[file_path.stem] = id_cols

        except Exception:
            continue

    # 构建 ID 映射（哪些 ID 列出现在多个表中）
    id_occurrences: dict[str, list[str]] = {}
    for file_stem, id_cols in id_columns_by_file.items():
        for col, col_type, _ in id_cols:
            if col not in id_occurrences:
                id_occurrences[col] = []
            id_occurrences[col].append(file_stem)

    # 找主实体
    main_entity = None
    if main_entity_hint:
        for file_stem in id_columns_by_file:
            if main_entity_hint.lower() in file_stem.lower():
                main_entity = file_stem
                break

    if main_entity is None:
        # 找包含最多外键被引用的表作为主实体
        max_refs = 0
        for file_stem, id_cols in id_columns_by_file.items():
            for col, col_type, _ in id_cols:
                if col_type == "primary" and col in id_occurrences:
                    ref_count = len(id_occurrences[col])
                    if ref_count > max_refs:
                        max_refs = ref_count
                        main_entity = file_stem

    if main_entity is None:
        main_entity = list(id_columns_by_file.keys())[0] if id_columns_by_file else None

    if main_entity is None:
        return configs

    # 创建实体配置
    for file_stem, id_cols in id_columns_by_file.items():
        file_path = next(
            (f for f in all_files if f.stem == file_stem),
            None
        )
        if file_path is None:
            continue

        # 找主键
        primary_key = next((col for col, t, _ in id_cols if t == "primary"), None)
        if primary_key is None:
            primary_key = id_cols[0][0] if id_cols else None

        # 判断是否为主实体
        is_main = file_stem == main_entity

        # 找外键关系
        parent = None
        foreign_key = None
        if not is_main:
            for col, t, _ in id_cols:
                if t == "foreign" and col in id_occurrences:
                    if main_entity in id_occurrences[col]:
                        parent = main_entity
                        foreign_key = col
                        break

        config = EntityConfig(
            name=file_stem,
            file_path=file_path.name,
            index=primary_key or "id",
            parent=parent,
            foreign_key=foreign_key,
            target=target_column if is_main else None,
        )
        configs.append(config)

    return configs

"""
实体层构建器。

根据配置构建 EntitySet，支持：
1. 显式配置（通过 EntityConfig）
2. 自动推断（扫描 ID 列模式）
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from ..config import EntityConfig, EnginePaths

try:
    import featuretools as ft
except ImportError:  # pragma: no cover - optional dependency
    ft = None


def _require_featuretools() -> Any:
    """按需获取 Featuretools 模块。"""
    if ft is None:
        raise ImportError(
            "EntitySetBuilder 需要安装 featuretools。"
            " 仅使用语义特征时无需调用该构建器；若需实体层/自动特征，请运行: pip install featuretools"
        )
    return ft


class EntitySetBuilder:
    """实体集构建器。

    负责将原始数据表组织成有关系的实体集。
    """

    def __init__(
        self,
        name: str = "credit_entity_set",
        paths: EnginePaths | None = None,
    ):
        self.name = name
        self.paths = paths or EnginePaths()
        self.entities: list[EntityConfig] = []
        self._frames: dict[str, pd.DataFrame] = {}

    def add_entity(self, config: EntityConfig) -> "EntitySetBuilder":
        """添加实体配置。"""
        self.entities.append(config)
        return self

    def add_entities(self, configs: list[EntityConfig]) -> "EntitySetBuilder":
        """批量添加实体配置。"""
        self.entities.extend(configs)
        return self

    def _load_frame(self, config: EntityConfig, sample_ids: set | None = None) -> pd.DataFrame:
        """加载数据表。"""
        file_path = self.paths.data_dir / config.file_path

        if file_path.suffix == ".parquet":
            df = pd.read_parquet(file_path)
        else:
            df = pd.read_csv(file_path)

        # 选择列
        if config.columns:
            available = [c for c in config.columns if c in df.columns]
            df = df[available]

        # 过滤样本
        if sample_ids and config.foreign_key:
            df = df[df[config.foreign_key].isin(sample_ids)]

        return df

    def build(self, sample_size: int | None = None) -> tuple[Any, dict[str, pd.DataFrame]]:
        """构建 EntitySet。

        返回：
            - EntitySet 对象
            - 表名到 DataFrame 的映射
        """
        ft_module = _require_featuretools()
        es = ft_module.EntitySet(id=self.name)
        config_by_name = {config.name: config for config in self.entities}

        # 找到主实体
        main_entity = next((e for e in self.entities if e.parent is None), None)
        if main_entity is None:
            raise ValueError("需要指定一个主实体（parent=None）")

        # 加载主实体
        main_frame = self._load_frame(main_entity)

        # 采样
        if sample_size and len(main_frame) > sample_size:
            main_frame = main_frame.sample(n=sample_size, random_state=42).reset_index(drop=True)

        self._frames[main_entity.name] = main_frame

        # 添加主实体到 EntitySet
        es = es.add_dataframe(
            dataframe_name=main_entity.name,
            dataframe=main_frame,
            index=main_entity.index,
        )

        # 逐层加载子实体，确保孙表按父表主键采样
        remaining = [config for config in self.entities if config.name != main_entity.name]
        while remaining:
            progressed = False

            for config in remaining[:]:
                if config.parent not in self._frames:
                    continue

                parent_config = config_by_name.get(config.parent)
                if parent_config is None:
                    raise ValueError(f"未找到父实体配置: {config.parent}")

                parent_frame = self._frames[config.parent]
                parent_ids = set(parent_frame[parent_config.index].dropna().unique())
                frame = self._load_frame(config, parent_ids)

                if config.index not in frame.columns:
                    frame = frame.copy()
                    frame[config.index] = range(len(frame))

                self._frames[config.name] = frame
                es = es.add_dataframe(
                    dataframe_name=config.name,
                    dataframe=frame,
                    index=config.index,
                )

                if config.foreign_key:
                    es = es.add_relationship(
                        parent_dataframe_name=config.parent,
                        parent_column_name=parent_config.index,
                        child_dataframe_name=config.name,
                        child_column_name=config.foreign_key,
                    )

                remaining.remove(config)
                progressed = True

            if not progressed:
                unresolved = ", ".join(
                    f"{config.name}(parent={config.parent})" for config in remaining
                )
                raise ValueError(f"存在未解析的实体依赖，请检查 parent 配置: {unresolved}")

        return es, self._frames

    def get_frame(self, name: str) -> pd.DataFrame | None:
        """获取已加载的数据表。"""
        return self._frames.get(name)


def build_entityset_from_config(
    entity_configs: list[EntityConfig],
    paths: EnginePaths | None = None,
    sample_size: int | None = None,
) -> tuple[Any, dict[str, pd.DataFrame]]:
    """从配置构建 EntitySet。

    快捷函数，用于从配置列表构建。
    """
    builder = EntitySetBuilder(paths=paths)
    builder.add_entities(entity_configs)
    return builder.build(sample_size=sample_size)

"""
语义特征主题基类。

定义主题的接口规范，所有主题实现都需要继承此类。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class FeatureSpec:
    """特征规格定义。"""

    name: str                               # 特征名称
    theme: str                              # 所属主题
    hypothesis: str                         # 业务假设
    expected_direction: str                 # 预期方向：higher_is_riskier / lower_is_riskier
    calculation_logic: str | None = None    # 计算逻辑描述
    source_tables: list[str] | None = None  # 依赖的数据表
    status: str = "proposed"                # 状态：proposed / implemented / validated


class ThemeBase(ABC):
    """主题基类。

    所有语义特征主题都需要继承此类并实现：
    - name: 主题名称
    - description: 主题描述
    - feature_specs: 特征规格列表
    - build_features: 构建特征的实现
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """主题名称。"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """主题描述。"""
        pass

    @abstractmethod
    def feature_specs(self) -> list[FeatureSpec]:
        """返回主题下所有特征的规格定义。"""
        pass

    @abstractmethod
    def build_features(
        self,
        frames: dict[str, pd.DataFrame],
        anchor: pd.DataFrame,
    ) -> pd.DataFrame:
        """构建特征。

        参数：
            frames: 表名到 DataFrame 的映射
            anchor: 锚点表（包含实体 ID 和目标变量）

        返回：
            特征矩阵，索引为实体 ID
        """
        pass

    def validate_data_availability(
        self,
        frames: dict[str, pd.DataFrame],
    ) -> tuple[bool, list[str]]:
        """验证数据是否满足主题需求。

        返回：
            - 是否满足
            - 缺失的表/字段列表
        """
        missing = []

        specs = self.feature_specs()
        required_tables = set()
        for spec in specs:
            if spec.source_tables:
                required_tables.update(spec.source_tables)

        for table in required_tables:
            if table not in frames:
                missing.append(f"表: {table}")

        return len(missing) == 0, missing


def to_registry_frame(specs: list[FeatureSpec]) -> pd.DataFrame:
    """将特征规格列表转换为注册表 DataFrame。"""
    return pd.DataFrame([
        {
            "feature_name": spec.name,
            "theme": spec.theme,
            "hypothesis": spec.hypothesis,
            "expected_direction": spec.expected_direction,
            "calculation_logic": spec.calculation_logic,
            "status": spec.status,
        }
        for spec in specs
    ])

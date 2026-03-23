"""
通用配置模块。

定义引擎的核心配置类，支持 Python 代码配置。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EntityConfig:
    """实体配置。

    定义一个数据表的元信息。
    """

    name: str                           # 实体名称（如 applications）
    file_path: Path | str               # 文件路径（相对于数据目录）
    index: str                          # 主键列名
    parent: str | None = None           # 父实体名称
    foreign_key: str | None = None      # 外键列名
    columns: list[str] | None = None    # 需要加载的列（None 表示全部）
    target: str | None = None           # 目标变量列名（仅主实体需要）

    def __post_init__(self):
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)


@dataclass
class AutoFeatureConfig:
    """自动特征配置。"""

    sample_size: int = 3000
    random_seed: int = 42
    max_depth: int = 2
    agg_primitives: list[str] = field(
        default_factory=lambda: ["sum", "mean", "max", "min", "std", "count", "num_unique"]
    )
    trans_primitives: list[str] = field(
        default_factory=lambda: ["absolute"]
    )


@dataclass
class SelectionConfig:
    """筛选配置。

    风控变量筛选标准：
    - 预测能力：IV ≥ min_iv 且 (AUC ≥ min_auc 或 Lift ≥ min_lift)
    - 稳定性：PSI < max_psi
    - 相关性：相关系数 < correlation_threshold
    - 缺失率：< missing_rate_threshold
    """

    id_col: str = "entity_id"
    target_col: str = "target"
    topk_ratio: float = 0.10
    # 基础过滤阈值
    missing_rate_threshold: float = 0.95
    correlation_threshold: float = 0.95
    # 预测能力阈值
    min_auc: float = 0.55           # AUC 阈值
    min_lift: float = 1.5           # Lift@Top10% 阈值
    min_iv: float = 0.02            # IV 最小阈值（无预测能力边界）
    min_iv_medium: float = 0.1      # IV 中等预测能力阈值
    min_iv_strong: float = 0.3      # IV 强预测能力阈值
    # 稳定性阈值
    max_psi: float = 0.25           # PSI 最大阈值


@dataclass
class EnginePaths:
    """引擎路径配置。"""

    data_dir: Path = Path("data/raw")
    output_dir: Path = Path("outputs")
    candidate_dir: Path = Path("outputs/candidate_pool")
    selection_dir: Path = Path("outputs/selection")

    def __post_init__(self):
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir)
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        if isinstance(self.candidate_dir, str):
            self.candidate_dir = Path(self.candidate_dir)
        if isinstance(self.selection_dir, str):
            self.selection_dir = Path(self.selection_dir)

    @property
    def raw_dir(self) -> Path:
        return self.data_dir

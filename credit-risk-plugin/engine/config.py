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
class FieldMapping:
    """字段映射。

    将通用字段名映射到实际字段名，实现业务解耦。
    """

    # 实体标识
    entity_id: str = "entity_id"
    target: str = "target"

    # 时间字段（相对天数，负数表示距今天数）
    decision_date: str | None = None        # 申请决策日期
    credit_date: str | None = None          # 征信查询日期
    payment_date: str | None = None         # 还款日期
    due_date: str | None = None             # 应还日期

    # 金额字段
    application_amount: str | None = None   # 申请金额
    credit_amount: str | None = None        # 批准金额
    payment_amount: str | None = None       # 还款金额
    due_amount: str | None = None           # 应还金额

    # 行为字段
    atm_drawings: str | None = None         # ATM取现金额
    total_drawings: str | None = None       # 总取现金额

    # 状态字段
    contract_status: str | None = None      # 合同状态

    def to_dict(self) -> dict[str, Any]:
        return {
            k: v for k, v in {
                "entity_id": self.entity_id,
                "target": self.target,
                "decision_date": self.decision_date,
                "credit_date": self.credit_date,
                "payment_date": self.payment_date,
                "due_date": self.due_date,
                "application_amount": self.application_amount,
                "credit_amount": self.credit_amount,
                "payment_amount": self.payment_amount,
                "due_amount": self.due_amount,
                "atm_drawings": self.atm_drawings,
                "total_drawings": self.total_drawings,
                "contract_status": self.contract_status,
            }.items() if v is not None
        }


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
    """筛选配置。"""

    id_col: str = "entity_id"
    target_col: str = "target"
    topk_ratio: float = 0.10
    missing_rate_threshold: float = 0.95
    correlation_threshold: float = 0.95
    min_auc: float = 0.52
    min_ap_lift: float = 1.02


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

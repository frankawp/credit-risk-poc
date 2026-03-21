"""
组合特征构建器。

基于业务语义，将有预测力的基础特征组合成更有业务解释性的新特征。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CompositeFeatureSpec:
    """组合特征规格。"""

    feature_name: str
    formula: str
    base_features: str
    business_definition: str
    risk_direction: str
    notes: str = ""

    def to_frame(self) -> pd.DataFrame:
        """转换为单行 DataFrame。"""
        return pd.DataFrame([asdict(self)])


def build_composite_features(
    frame: pd.DataFrame,
    specs: list[CompositeFeatureSpec],
    output_dir: Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """构建组合特征。

    参数：
        frame: 基础特征矩阵
        specs: 组合特征规格列表
        output_dir: 输出目录（可选）

    返回：
        (增强的特征矩阵, 组合特征规格表)
    """
    result = frame.copy()
    valid_specs = []

    for spec in specs:
        try:
            # 解析并执行公式
            new_col = _evaluate_formula(result, spec.formula, spec.feature_name)
            if new_col is not None:
                result[spec.feature_name] = new_col
                valid_specs.append(spec)
        except Exception as e:
            print(f"⚠️ 组合特征 {spec.feature_name} 构建失败: {e}")

    specs_frame = pd.DataFrame([asdict(s) for s in valid_specs])

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        result.to_parquet(output_dir / "composite_feature_matrix.parquet", index=False)
        specs_frame.to_csv(output_dir / "composite_feature_specs.csv", index=False)

    return result, specs_frame


def _evaluate_formula(
    frame: pd.DataFrame,
    formula: str,
    feature_name: str,
) -> pd.Series | None:
    """评估特征公式。

    支持简单的数学表达式和条件判断。
    """
    # 提取公式中引用的列
    import re
    referenced_cols = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", formula))

    # 检查引用列是否存在
    missing = referenced_cols - set(frame.columns) - {"fillna", "if", "else"}
    if missing:
        # 尝试忽略缺失列（可能是内置函数）
        pass

    # 创建安全的评估环境
    safe_dict = {
        "fillna": lambda s, v: pd.Series(s).fillna(v) if isinstance(s, (pd.Series, np.ndarray)) else s,
        "np": np,
    }

    # 添加列数据
    for col in frame.columns:
        safe_dict[col] = frame[col]

    try:
        result = eval(formula, {"__builtins__": {}}, safe_dict)
        if isinstance(result, (pd.Series, np.ndarray)):
            return pd.Series(result, index=frame.index)
        else:
            # 标量值，广播到整列
            return pd.Series([result] * len(frame), index=frame.index)
    except Exception:
        return None


# ============== 预定义的组合特征模板 ==============

def create_cross_feature(
    name: str,
    col1: str,
    col2: str,
    operator: str,
    business_definition: str,
    risk_direction: str = "higher_is_riskier",
) -> CompositeFeatureSpec:
    """创建交叉特征规格。

    参数：
        name: 特征名
        col1: 第一列
        col2: 第二列
        operator: 操作符 (+, -, *, /)
        business_definition: 业务定义
        risk_direction: 风险方向
    """
    op_map = {
        "+": "+",
        "-": "-",
        "*": "*",
        "/": "/",
    }
    formula = f"fillna({col1}, 0) {op_map.get(operator, '*')} fillna({col2}, 0)"
    return CompositeFeatureSpec(
        feature_name=name,
        formula=formula,
        base_features=f"{col1}, {col2}",
        business_definition=business_definition,
        risk_direction=risk_direction,
    )


def create_flag_feature(
    name: str,
    condition: str,
    base_features: str,
    business_definition: str,
    risk_direction: str = "higher_is_riskier",
) -> CompositeFeatureSpec:
    """创建标记特征规格。

    参数：
        name: 特征名
        condition: 条件表达式
        base_features: 基础特征列表
        business_definition: 业务定义
        risk_direction: 风险方向
    """
    formula = f"1 if {condition} else 0"
    return CompositeFeatureSpec(
        feature_name=name,
        formula=formula,
        base_features=base_features,
        business_definition=business_definition,
        risk_direction=risk_direction,
    )

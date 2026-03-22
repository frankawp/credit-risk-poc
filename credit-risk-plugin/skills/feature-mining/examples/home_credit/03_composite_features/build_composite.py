"""
组合特征构建。

展示如何从基础特征构建有业务含义的组合特征。

类型：
1. Ratios - 比率类（额度使用率、负债比）
2. Interactions - 交互类（风险叠加）
3. Rule Crosses - 规则交叉类（多条件组合）
"""

from pathlib import Path
from dataclasses import dataclass

import pandas as pd
import numpy as np

from engine.composite import (
    CompositeFeatureSpec,
    build_composite_features,
    create_cross_feature,
    create_flag_feature,
)


# ============================================================================
# 定义组合特征规格
# ============================================================================

def get_composite_specs() -> list[CompositeFeatureSpec]:
    """定义组合特征规格。

    每个规格包含：
    - feature_name: 特征名
    - formula: 计算公式
    - base_features: 基础特征列表
    - business_definition: 业务定义
    - risk_direction: 风险方向
    - notes: 备注
    """
    return [
        # ===== 比率类 =====
        CompositeFeatureSpec(
            feature_name="composite_credit_usage_ratio",
            formula="AMT_BALANCE / AMT_CREDIT_LIMIT_ACTUAL",
            base_features="AMT_BALANCE, AMT_CREDIT_LIMIT_ACTUAL",
            business_definition="信用卡额度使用率",
            risk_direction="higher_is_riskier",
            notes="超过 0.8 表示高使用率",
        ),
        CompositeFeatureSpec(
            feature_name="composite_income_to_annuity_ratio",
            formula="AMT_INCOME_TOTAL / AMT_ANNUITY",
            base_features="AMT_INCOME_TOTAL, AMT_ANNUITY",
            business_definition="收入覆盖年还款的能力",
            risk_direction="lower_is_riskier",
            notes="低于 2 表示还款压力较大",
        ),

        # ===== 交互类 =====
        CompositeFeatureSpec(
            feature_name="composite_velocity_x_external",
            formula="prev_app_count_30d * (1 - EXT_SOURCE_2)",
            base_features="prev_app_count_30d, EXT_SOURCE_2",
            business_definition="短期申请密度 × 外部评分风险",
            risk_direction="higher_is_riskier",
            notes="同时具备高申请频率和低外部评分",
        ),

        # ===== 规则交叉类 =====
        CompositeFeatureSpec(
            feature_name="composite_high_risk_flag",
            formula="1 if prev_reject_count > 0 and EXT_SOURCE_1 < 0.3 else 0",
            base_features="prev_reject_count, EXT_SOURCE_1",
            business_definition="被拒历史 + 低外部评分组合标记",
            risk_direction="higher_is_riskier",
            notes="二元标记，用于规则筛选",
        ),
    ]


# ============================================================================
# 构建组合特征
# ============================================================================

def build_from_specs(
    feature_matrix: pd.DataFrame,
    specs: list[CompositeFeatureSpec],
    output_dir: Path,
) -> pd.DataFrame:
    """根据规格构建组合特征。

    参数：
        feature_matrix: 基础特征矩阵
        specs: 组合特征规格列表
        output_dir: 输出目录

    返回：
        添加了组合特征的特征矩阵
    """
    result = build_composite_features(
        frame=feature_matrix,
        specs=specs,
    )

    # 保存规格文档
    spec_df = pd.DataFrame([{
        "feature_name": s.feature_name,
        "formula": s.formula,
        "base_features": s.base_features,
        "business_definition": s.business_definition,
        "risk_direction": s.risk_direction,
    } for s in specs])
    spec_df.to_csv(output_dir / "composite_feature_specs.csv", index=False)

    return result


# ============================================================================
# 快捷函数：创建特定类型
# ============================================================================

def create_ratio_feature(
    frame: pd.DataFrame,
    numerator: str,
    denominator: str,
    new_name: str,
) -> pd.Series:
    """创建比率特征。

    自动处理：
    - 除零保护
    - 缺失值填充
    """
    ratio = frame[numerator] / frame[denominator].replace(0, np.nan)
    return ratio.fillna(0)


def create_interaction_feature(
    frame: pd.DataFrame,
    col_a: str,
    col_b: str,
    operation: str = "multiply",
) -> pd.Series:
    """创建交互特征。

    支持操作：
    - multiply: 乘法
    - add: 加法
    - subtract: 减法
    """
    if operation == "multiply":
        return frame[col_a] * frame[col_b]
    elif operation == "add":
        return frame[col_a] + frame[col_b]
    elif operation == "subtract":
        return frame[col_a] - frame[col_b]
    else:
        raise ValueError(f"不支持的操作: {operation}")


# ============================================================================
# 业务主题组合特征示例
# ============================================================================

def build_velocity_risk_composite(frame: pd.DataFrame) -> pd.DataFrame:
    """构建速度风险组合特征。

    业务假设：
    - 短期内多次申请 + 低外部评分 = 高风险
    - 申请被拒历史 + 再次申请 = 风险叠加
    """
    result = frame.copy()

    # 申请密度风险
    if "prev_app_count_7d" in frame.columns and "EXT_SOURCE_2" in frame.columns:
        result["composite_velocity_risk_score"] = create_interaction_feature(
            frame, "prev_app_count_7d", "EXT_SOURCE_2", "multiply"
        )

    # 被拒后重新申请标记
    if "prev_reject_count" in frame.columns:
        result["composite_rejected_reapplicant"] = create_flag_feature(
            frame,
            condition="prev_reject_count > 0",
            flag_value=1,
        )

    return result


def build_stability_risk_composite(frame: pd.DataFrame) -> pd.DataFrame:
    """构建稳定性风险组合特征。

    业务假设：
    - 工作时间短 + 高负债 = 稳定性差
    - 居住变更频繁 + 收入不稳定 = 流动风险
    """
    result = frame.copy()

    # 工作稳定性风险
    if "DAYS_EMPLOYED" in frame.columns and "AMT_CREDIT" in frame.columns:
        # 工作天数越少（负数绝对值小），风险越高
        employment_years = -frame["DAYS_EMPLOYED"] / 365
        credit_to_income = frame.get("AMT_CREDIT", 1) / frame.get("AMT_INCOME_TOTAL", 1)
        result["composite_stability_risk"] = (
            (1 - employment_years.clip(0, 1)) * credit_to_income
        )

    return result


# ============================================================================
# 运行示例
# ============================================================================

if __name__ == "__main__":
    # 假设已有特征矩阵
    # from examples.home_credit.02_feature_generation import run_pipeline
    # feature_matrix = run_pipeline(...)

    output_dir = Path("outputs/run_001/composite")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 方法一：根据规格构建
    # specs = get_composite_specs()
    # result = build_from_specs(feature_matrix, specs, output_dir)

    # 方法二：按主题构建
    # result = build_velocity_risk_composite(feature_matrix)
    # result = build_stability_risk_composite(result)

    print("组合特征构建完成")

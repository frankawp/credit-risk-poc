"""
高频申请主题（Velocity）。

识别短时间高频申请、多头借贷激增、脚本化申请行为的风险客户。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..base import ThemeBase, FeatureSpec


def _decision_gap_std(series: pd.Series) -> float:
    """计算决策时间间隔的标准差。"""
    values = np.sort(series.dropna().values)
    if len(values) < 3:
        return np.nan
    gaps = np.diff(values)
    if len(gaps) == 0:
        return np.nan
    return float(np.std(np.abs(gaps)))


class VelocityTheme(ThemeBase):
    """高频申请主题。

    适合挖掘：
    - 近 7 天 / 30 天 / 90 天申请次数
    - 申请间隔波动
    - 征信近期活跃度
    """

    @property
    def name(self) -> str:
        return "velocity"

    @property
    def description(self) -> str:
        return "识别短时间高频申请、多头借贷激增"

    def feature_specs(self) -> list[FeatureSpec]:
        return [
            FeatureSpec(
                name="velocity_prev_count_7d",
                theme="velocity",
                hypothesis="7天内多次申请资金可能紧张",
                expected_direction="higher_is_riskier",
                calculation_logic="previous_application 中 DAYS_DECISION >= -7 的笔数",
                source_tables=["previous_application"],
            ),
            FeatureSpec(
                name="velocity_prev_count_30d",
                theme="velocity",
                hypothesis="30天内申请密度高风险",
                expected_direction="higher_is_riskier",
                calculation_logic="previous_application 中 DAYS_DECISION >= -30 的笔数",
                source_tables=["previous_application"],
            ),
            FeatureSpec(
                name="velocity_prev_decision_gap_std",
                theme="velocity",
                hypothesis="申请间隔稳定可能是脚本化申请",
                expected_direction="higher_is_riskier",
                calculation_logic="历史申请决策时间间隔的标准差",
                source_tables=["previous_application"],
            ),
            FeatureSpec(
                name="velocity_bureau_recent_credit_count_30d",
                theme="velocity",
                hypothesis="近期征信查询多可能多头",
                expected_direction="higher_is_riskier",
                calculation_logic="bureau 中 DAYS_CREDIT >= -30 的笔数",
                source_tables=["bureau"],
            ),
        ]

    def build_features(
        self,
        frames: dict[str, pd.DataFrame],
        anchor: pd.DataFrame,
    ) -> pd.DataFrame:
        """构建高频申请特征。"""
        entity_id_col = "SK_ID_CURR"
        result = anchor[[entity_id_col]].copy()

        previous = frames.get("previous_application")
        bureau = frames.get("bureau")

        if previous is not None and "DAYS_DECISION" in previous.columns:
            prev = previous[["SK_ID_CURR", "DAYS_DECISION"]].copy()
            prev_agg = prev.groupby("SK_ID_CURR", as_index=False).agg(
                velocity_prev_count_7d=("DAYS_DECISION", lambda s: int((s >= -7).sum())),
                velocity_prev_count_30d=("DAYS_DECISION", lambda s: int((s >= -30).sum())),
                velocity_prev_decision_gap_std=("DAYS_DECISION", _decision_gap_std),
            )
            result = result.merge(prev_agg, on="SK_ID_CURR", how="left")

        if bureau is not None and "DAYS_CREDIT" in bureau.columns:
            buro = bureau[["SK_ID_CURR", "DAYS_CREDIT"]].copy()
            buro_agg = buro.groupby("SK_ID_CURR", as_index=False).agg(
                velocity_bureau_recent_credit_count_30d=("DAYS_CREDIT", lambda s: int((s >= -30).sum())),
            )
            result = result.merge(buro_agg, on="SK_ID_CURR", how="left")

        return result

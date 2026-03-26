"""
一致性主题（Consistency）。

识别身份伪造、资料不稳定、申请行为异常一致的风险客户。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..base import ThemeBase, FeatureSpec


class ConsistencyTheme(ThemeBase):
    """一致性主题。

    适合挖掘：
    - 工龄年龄比例异常
    - 联系方式稳定性
    - 申请金额与批核金额偏差
    - 历史状态切换频率
    """

    @property
    def name(self) -> str:
        return "consistency"

    @property
    def description(self) -> str:
        return "识别资料前后不一致、身份伪造、稳定性异常"

    def feature_specs(self) -> list[FeatureSpec]:
        return [
            FeatureSpec(
                name="consistency_employed_birth_ratio",
                theme="consistency",
                hypothesis="工龄占年龄比例异常偏高可能是不合理的工作经历",
                expected_direction="higher_is_riskier",
                calculation_logic="abs(DAYS_EMPLOYED) / (abs(DAYS_BIRTH) + 1)",
                source_tables=["application"],
            ),
            FeatureSpec(
                name="consistency_contact_flag_sum",
                theme="consistency",
                hypothesis="联系方式可用数量越少越可疑",
                expected_direction="lower_is_riskier",
                calculation_logic="FLAG_MOBIL + FLAG_EMP_PHONE + FLAG_WORK_PHONE",
                source_tables=["application"],
            ),
            FeatureSpec(
                name="consistency_prev_credit_gap_ratio_mean",
                theme="consistency",
                hypothesis="申请金额与批核金额长期偏差异常",
                expected_direction="higher_is_riskier",
                calculation_logic="历史申请中 abs(AMT_CREDIT - AMT_APPLICATION) / (abs(AMT_APPLICATION) + 1) 的均值",
                source_tables=["previous_application"],
            ),
            FeatureSpec(
                name="consistency_prev_status_change_rate",
                theme="consistency",
                hypothesis="历史状态切换异常频繁",
                expected_direction="higher_is_riskier",
                calculation_logic="历史合同状态去重数 / 历史申请数",
                source_tables=["previous_application"],
            ),
        ]

    def build_features(
        self,
        frames: dict[str, pd.DataFrame],
        anchor: pd.DataFrame,
    ) -> pd.DataFrame:
        """构建一致性特征。"""
        # 从 anchor 获取实体 ID
        entity_id_col = "SK_ID_CURR"  # 默认值，实际应从配置获取
        result = anchor[[entity_id_col]].copy()

        # 获取需要的表
        app = frames.get("application") or frames.get("application_train")
        previous = frames.get("previous_application")

        if app is not None:
            # 工龄年龄比例
            if "DAYS_EMPLOYED" in app.columns and "DAYS_BIRTH" in app.columns:
                employed = app["DAYS_EMPLOYED"].abs()
                birth = app["DAYS_BIRTH"].abs().replace(0, np.nan)
                result["consistency_employed_birth_ratio"] = employed / (birth + 1.0)

            # 联系方式完整性
            phone_cols = [c for c in ["FLAG_MOBIL", "FLAG_EMP_PHONE", "FLAG_WORK_PHONE"] if c in app.columns]
            if phone_cols:
                result["consistency_contact_flag_sum"] = app[phone_cols].fillna(0).sum(axis=1)

        if previous is not None:
            # 申请批核金额偏差
            if all(c in previous.columns for c in ["AMT_APPLICATION", "AMT_CREDIT"]):
                prev = previous[["SK_ID_CURR", "AMT_APPLICATION", "AMT_CREDIT", "NAME_CONTRACT_STATUS"]].copy()
                prev["credit_gap_ratio"] = (
                    (prev["AMT_CREDIT"] - prev["AMT_APPLICATION"]).abs()
                    / (prev["AMT_APPLICATION"].abs() + 1.0)
                )
                agg = prev.groupby("SK_ID_CURR", as_index=False).agg(
                    consistency_prev_credit_gap_ratio_mean=("credit_gap_ratio", "mean"),
                    prev_app_count=("AMT_APPLICATION", "count"),
                    prev_status_unique=("NAME_CONTRACT_STATUS", "nunique"),
                )
                agg["consistency_prev_status_change_rate"] = (
                    agg["prev_status_unique"] / agg["prev_app_count"].replace(0, np.nan)
                )
                agg = agg.drop(columns=["prev_app_count", "prev_status_unique"])
                result = result.merge(agg, on="SK_ID_CURR", how="left")

        return result

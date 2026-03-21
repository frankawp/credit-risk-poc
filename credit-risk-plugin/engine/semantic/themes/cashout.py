"""
套现风险主题（Cashout）。

识别套现倾向、首期违约、异常还款行为的风险客户。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..base import ThemeBase, FeatureSpec


class CashoutTheme(ThemeBase):
    """套现风险主题。

    适合挖掘：
    - ATM 取现偏好
    - 首期逾期天数
    - 严重 FPD 标记
    - 分期整体逾期率
    """

    @property
    def name(self) -> str:
        return "cashout"

    @property
    def description(self) -> str:
        return "识别套现倾向、首期违约、异常还款行为"

    def feature_specs(self) -> list[FeatureSpec]:
        return [
            FeatureSpec(
                name="cashout_atm_ratio_mean",
                theme="cashout",
                hypothesis="ATM 取现比例高可能是套现",
                expected_direction="higher_is_riskier",
                calculation_logic="AMT_DRAWINGS_ATM_CURRENT / (AMT_DRAWINGS_CURRENT + 1) 的客户级均值",
                source_tables=["credit_card_balance", "previous_application"],
            ),
            FeatureSpec(
                name="cashout_first_payment_delinquency_days_max",
                theme="cashout",
                hypothesis="首期逾期天数多高风险",
                expected_direction="higher_is_riskier",
                calculation_logic="首期还款 DAYS_ENTRY_PAYMENT - DAYS_INSTALMENT 的最大值",
                source_tables=["installments_payments", "previous_application"],
            ),
            FeatureSpec(
                name="cashout_fpd_severe_flag",
                theme="cashout",
                hypothesis="首期严重逾期极高风险",
                expected_direction="higher_is_riskier",
                calculation_logic="首期逾期是否 > 30 天",
                source_tables=["installments_payments", "previous_application"],
            ),
            FeatureSpec(
                name="cashout_installments_late_ratio",
                theme="cashout",
                hypothesis="分期还款逾期比例高信用差",
                expected_direction="higher_is_riskier",
                calculation_logic="分期还款记录中逾期笔数占比",
                source_tables=["installments_payments", "previous_application"],
            ),
        ]

    def build_features(
        self,
        frames: dict[str, pd.DataFrame],
        anchor: pd.DataFrame,
    ) -> pd.DataFrame:
        """构建套现风险特征。"""
        entity_id_col = "SK_ID_CURR"
        result = anchor[[entity_id_col]].copy()

        previous = frames.get("previous_application")
        credit_card = frames.get("credit_card_balance")
        installments = frames.get("installments_payments")

        if previous is None:
            return result

        # 建立 SK_ID_PREV -> SK_ID_CURR 映射
        prev_map = previous[["SK_ID_PREV", "SK_ID_CURR"]].drop_duplicates()

        # ATM 取现比例
        if credit_card is not None and all(
            c in credit_card.columns
            for c in ["SK_ID_PREV", "AMT_DRAWINGS_ATM_CURRENT", "AMT_DRAWINGS_CURRENT"]
        ):
            card = credit_card[["SK_ID_PREV", "AMT_DRAWINGS_ATM_CURRENT", "AMT_DRAWINGS_CURRENT"]].copy()
            card["atm_ratio"] = card["AMT_DRAWINGS_ATM_CURRENT"] / (card["AMT_DRAWINGS_CURRENT"].abs() + 1.0)
            card = card.merge(prev_map, on="SK_ID_PREV", how="inner")
            card_agg = card.groupby("SK_ID_CURR", as_index=False).agg(
                cashout_atm_ratio_mean=("atm_ratio", "mean"),
            )
            result = result.merge(card_agg, on="SK_ID_CURR", how="left")

        # 首期还款行为
        if installments is not None and all(
            c in installments.columns
            for c in ["SK_ID_PREV", "NUM_INSTALMENT_NUMBER", "DAYS_INSTALMENT", "DAYS_ENTRY_PAYMENT"]
        ):
            inst = installments[
                ["SK_ID_PREV", "NUM_INSTALMENT_NUMBER", "DAYS_INSTALMENT", "DAYS_ENTRY_PAYMENT"]
            ].copy()
            inst = inst.merge(prev_map, on="SK_ID_PREV", how="inner")
            inst["late_days"] = inst["DAYS_ENTRY_PAYMENT"] - inst["DAYS_INSTALMENT"]
            inst["late_flag"] = (inst["late_days"] > 0).astype(int)

            # 首期还款
            first = inst[inst["NUM_INSTALMENT_NUMBER"] == 1].copy()
            first_agg = first.groupby("SK_ID_CURR", as_index=False).agg(
                cashout_first_payment_delinquency_days_max=("late_days", "max"),
            )
            first_agg["cashout_fpd_severe_flag"] = (
                first_agg["cashout_first_payment_delinquency_days_max"] > 30
            ).astype(int)

            # 整体逾期比例
            late_ratio = inst.groupby("SK_ID_CURR", as_index=False).agg(
                cashout_installments_late_ratio=("late_flag", "mean")
            )

            result = result.merge(first_agg, on="SK_ID_CURR", how="left")
            result = result.merge(late_ratio, on="SK_ID_CURR", how="left")

        return result

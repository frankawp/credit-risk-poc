from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class FeatureSpec:
    feature_name: str
    feature_source: str
    feature_group: str
    source_table: str
    business_definition: str
    risk_direction: str
    status: str = "candidate"


def semantic_feature_specs() -> list[FeatureSpec]:
    return [
        FeatureSpec(
            feature_name="consistency_employed_birth_ratio",
            feature_source="semantic",
            feature_group="consistency",
            source_table="application_train",
            business_definition="Absolute employment days divided by absolute birth days.",
            risk_direction="higher_is_riskier",
        ),
        FeatureSpec(
            feature_name="consistency_contact_flag_sum",
            feature_source="semantic",
            feature_group="consistency",
            source_table="application_train",
            business_definition="Availability count of mobile, employer, and work phone flags.",
            risk_direction="lower_is_riskier",
        ),
        FeatureSpec(
            feature_name="consistency_prev_credit_gap_ratio_mean",
            feature_source="semantic",
            feature_group="consistency",
            source_table="previous_application",
            business_definition="Mean absolute gap ratio between requested and approved credit.",
            risk_direction="higher_is_riskier",
        ),
        FeatureSpec(
            feature_name="consistency_prev_status_change_rate",
            feature_source="semantic",
            feature_group="consistency",
            source_table="previous_application",
            business_definition="Unique contract status count divided by previous application count.",
            risk_direction="higher_is_riskier",
        ),
        FeatureSpec(
            feature_name="velocity_prev_count_7d",
            feature_source="semantic",
            feature_group="velocity",
            source_table="previous_application",
            business_definition="Count of previous applications in recent 7 days window.",
            risk_direction="higher_is_riskier",
        ),
        FeatureSpec(
            feature_name="velocity_prev_count_30d",
            feature_source="semantic",
            feature_group="velocity",
            source_table="previous_application",
            business_definition="Count of previous applications in recent 30 days window.",
            risk_direction="higher_is_riskier",
        ),
        FeatureSpec(
            feature_name="velocity_prev_decision_gap_std",
            feature_source="semantic",
            feature_group="velocity",
            source_table="previous_application",
            business_definition="Standard deviation of day gaps between previous decisions.",
            risk_direction="lower_is_riskier",
        ),
        FeatureSpec(
            feature_name="velocity_bureau_recent_credit_count_30d",
            feature_source="semantic",
            feature_group="velocity",
            source_table="bureau",
            business_definition="Count of bureau credits opened in recent 30 days window.",
            risk_direction="higher_is_riskier",
        ),
        FeatureSpec(
            feature_name="cashout_atm_ratio_mean",
            feature_source="semantic",
            feature_group="cashout",
            source_table="credit_card_balance",
            business_definition="Mean ratio of ATM drawings to total drawings.",
            risk_direction="higher_is_riskier",
        ),
        FeatureSpec(
            feature_name="cashout_first_payment_delinquency_days_max",
            feature_source="semantic",
            feature_group="cashout",
            source_table="installments_payments",
            business_definition="Maximum first-payment delinquency days.",
            risk_direction="higher_is_riskier",
        ),
        FeatureSpec(
            feature_name="cashout_fpd_severe_flag",
            feature_source="semantic",
            feature_group="cashout",
            source_table="installments_payments",
            business_definition="Flag for severe first payment delinquency over 30 days.",
            risk_direction="higher_is_riskier",
        ),
        FeatureSpec(
            feature_name="cashout_installments_late_ratio",
            feature_source="semantic",
            feature_group="cashout",
            source_table="installments_payments",
            business_definition="Late-payment ratio in installment records.",
            risk_direction="higher_is_riskier",
        ),
    ]


def to_registry_frame(specs: Iterable[FeatureSpec]) -> pd.DataFrame:
    return pd.DataFrame([asdict(spec) for spec in specs])

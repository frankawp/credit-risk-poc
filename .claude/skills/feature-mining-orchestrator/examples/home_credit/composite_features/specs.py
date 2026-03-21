from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd


@dataclass(frozen=True)
class CompositeFeatureSpec:
    feature_name: str
    formula: str
    base_features: str
    business_definition: str
    risk_direction: str
    notes: str


def composite_feature_specs() -> list[CompositeFeatureSpec]:
    return [
        CompositeFeatureSpec(
            feature_name="composite_velocity_x_cashout",
            formula="fillna(velocity_prev_count_7d, 0) * fillna(cashout_atm_ratio_mean, 0)",
            base_features="velocity_prev_count_7d, cashout_atm_ratio_mean",
            business_definition="Short-window application velocity multiplied by ATM cash-out preference.",
            risk_direction="higher_is_riskier",
            notes="Captures resonance between recent application density and ATM-heavy cash-out behavior.",
        ),
        CompositeFeatureSpec(
            feature_name="composite_consistency_velocity_flag",
            formula="1 if fillna(consistency_prev_credit_gap_ratio_mean, 0) > 0.20 and fillna(velocity_prev_count_30d, 0) >= 3 else 0",
            base_features="consistency_prev_credit_gap_ratio_mean, velocity_prev_count_30d",
            business_definition="Flag for abnormal requested-vs-approved credit gap together with elevated recent application density.",
            risk_direction="higher_is_riskier",
            notes="Used as a rule-cross feature rather than a continuous score.",
        ),
        CompositeFeatureSpec(
            feature_name="composite_fpd_velocity_flag",
            formula="1 if fillna(cashout_fpd_severe_flag, 0) == 1 and fillna(velocity_prev_count_7d, 0) >= 2 else 0",
            base_features="cashout_fpd_severe_flag, velocity_prev_count_7d",
            business_definition="Flag for severe first-payment delinquency combined with recent application burst.",
            risk_direction="higher_is_riskier",
            notes="Represents joint early-default and short-window velocity risk.",
        ),
    ]


def composite_specs_frame() -> pd.DataFrame:
    return pd.DataFrame([asdict(spec) for spec in composite_feature_specs()])

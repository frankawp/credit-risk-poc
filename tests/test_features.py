import pandas as pd

from anti_fraud.features import build_cashout_features, build_consistency_features, build_velocity_features


def _application():
    return pd.DataFrame(
        {
            "SK_ID_CURR": [1, 2],
            "TARGET": [1, 0],
            "DAYS_BIRTH": [-10000, -12000],
            "DAYS_EMPLOYED": [-5000, 365243],
            "DAYS_REGISTRATION": [-2000, -3000],
            "DAYS_ID_PUBLISH": [-1000, -100],
            "FLAG_MOBIL": [1, 1],
            "FLAG_EMP_PHONE": [0, 1],
            "FLAG_WORK_PHONE": [0, 0],
            "FLAG_CONT_MOBILE": [1, 1],
            "FLAG_PHONE": [0, 1],
            "FLAG_EMAIL": [0, 0],
            "FLAG_DOCUMENT_2": [0, 1],
            "FLAG_DOCUMENT_3": [1, 0],
            "FLAG_DOCUMENT_4": [0, 0],
            "FLAG_DOCUMENT_5": [0, 0],
            "FLAG_DOCUMENT_6": [0, 0],
            "FLAG_DOCUMENT_7": [1, 0],
            "ORGANIZATION_TYPE": ["Business", "School"],
            "REGION_POPULATION_RELATIVE": [0.01, 0.05],
            "AMT_REQ_CREDIT_BUREAU_HOUR": [1, 0],
            "AMT_REQ_CREDIT_BUREAU_DAY": [2, 0],
            "AMT_REQ_CREDIT_BUREAU_WEEK": [4, 1],
        }
    )


def test_consistency_features():
    previous = pd.DataFrame(
        {
            "SK_ID_CURR": [1, 1, 2],
            "DAYS_DECISION": [-10, -1, -2],
            "NAME_CONTRACT_STATUS": ["Approved", "Refused", "Approved"],
            "NAME_CONTRACT_TYPE": ["Cash loans", "Cash loans", "Consumer loans"],
        }
    )
    features, metadata = build_consistency_features(
        _application(),
        previous,
        core_documents=["FLAG_DOCUMENT_2", "FLAG_DOCUMENT_3", "FLAG_DOCUMENT_4", "FLAG_DOCUMENT_5", "FLAG_DOCUMENT_6"],
        contact_flags=["FLAG_MOBIL", "FLAG_EMP_PHONE", "FLAG_WORK_PHONE", "FLAG_CONT_MOBILE", "FLAG_PHONE", "FLAG_EMAIL"],
        employed_birth_ratio_threshold=0.8,
    )
    assert "document_noncore_only_flag" in features.columns
    assert int(features.loc[features["SK_ID_CURR"] == 2, "employed_birth_inconsistency_flag"].iloc[0]) == 1
    assert not metadata.empty


def test_velocity_features():
    previous = pd.DataFrame(
        {
            "SK_ID_CURR": [1, 1, 1, 1, 2],
            "DAYS_DECISION": [-5, -5, -5, -1, -40],
            "NAME_CONTRACT_STATUS": ["Approved", "Approved", "Refused", "Approved", "Approved"],
            "NAME_CONTRACT_TYPE": ["Cash", "Cash", "Cash", "Cash", "Consumer"],
        }
    )
    bureau = pd.DataFrame(
        {
            "SK_ID_CURR": [1, 1, 2],
            "DAYS_CREDIT": [-3, -20, -1],
            "CREDIT_ACTIVE": ["Active", "Closed", "Active"],
        }
    )
    features, _ = build_velocity_features(_application(), previous, bureau, 2, 4, 3)
    assert int(features.loc[features["SK_ID_CURR"] == 1, "burst_same_day_flag"].iloc[0]) == 1
    assert int(features.loc[features["SK_ID_CURR"] == 1, "bureau_inquiry_spike_flag"].iloc[0]) == 1


def test_cashout_features():
    credit_card = pd.DataFrame(
        {
            "SK_ID_CURR": [1, 1, 2],
            "AMT_DRAWINGS_ATM_CURRENT": [100, 50, 0],
            "AMT_DRAWINGS_CURRENT": [100, 100, 1],
            "AMT_TOTAL_RECEIVABLE": [200, 100, 50],
            "SK_DPD_DEF": [0, 5, 0],
        }
    )
    installments = pd.DataFrame(
        {
            "SK_ID_CURR": [1, 1, 2],
            "NUM_INSTALMENT_NUMBER": [1, 2, 1],
            "DAYS_INSTALMENT": [-30, -10, -40],
            "DAYS_ENTRY_PAYMENT": [-10, -8, -45],
        }
    )
    features, _ = build_cashout_features(_application(), credit_card, installments, 0.8, 30)
    assert "fpd_severe_flag" in features.columns
    assert int(features.loc[features["SK_ID_CURR"] == 1, "atm_heavy_usage_months"].iloc[0]) == 1

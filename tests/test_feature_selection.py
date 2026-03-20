import pandas as pd

from anti_fraud.models.feature_selection import SelectionConfig, compute_feature_scorecard, select_from_correlation_groups


def test_scorecard_drops_constant_and_high_missing():
    frame = pd.DataFrame(
        {
            "TARGET": [0, 1, 0, 1, 0, 1],
            "const_feature": [1, 1, 1, 1, 1, 1],
            "missing_feature": [None, None, None, None, 1.0, None],
            "good_feature": [0.1, 0.9, 0.2, 0.8, 0.3, 0.7],
        }
    )
    cfg = SelectionConfig(min_non_null=1, missing_rate_threshold=0.8, min_unique=2)
    scorecard = compute_feature_scorecard(frame, ["const_feature", "missing_feature", "good_feature"], "TARGET", {}, cfg)
    reasons = scorecard.set_index("feature_name")["drop_reason"].to_dict()
    assert reasons["const_feature"] == "constant_or_single_value"
    assert reasons["missing_feature"] == "high_missing_rate"
    assert reasons["good_feature"] == ""


def test_correlation_selection_keeps_one_representative():
    frame = pd.DataFrame(
        {
            "TARGET": [0, 1, 0, 1, 0, 1],
            "a": [1, 2, 3, 4, 5, 6],
            "b": [2, 4, 6, 8, 10, 12],
            "rule_flag": [0, 1, 0, 1, 0, 1],
        }
    )
    cfg = SelectionConfig(min_non_null=1, correlation_threshold=0.8, extreme_correlation_threshold=0.95)
    scorecard = compute_feature_scorecard(frame, ["a", "b", "rule_flag"], "TARGET", {"a": 0.2, "b": 0.1, "rule_flag": 0.15}, cfg)
    scorecard, groups = select_from_correlation_groups(frame, scorecard, cfg)
    selected = scorecard[scorecard["selected_flag"] == 1]["feature_name"].tolist()
    assert "a" in selected
    assert "b" not in selected
    assert not groups.empty

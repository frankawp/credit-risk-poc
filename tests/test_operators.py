import pandas as pd

from anti_fraud.operators import change_rate, null_count, relative_ratio, time_diff, window_count


def test_time_diff():
    current = pd.Series([3, 10])
    previous = pd.Series([1, 4])
    result = time_diff(current, previous)
    assert result.tolist() == [2, 6]


def test_null_count():
    frame = pd.DataFrame({"a": [1, None], "b": [None, None], "c": [1, 2]})
    assert null_count(frame, ["a", "b", "c"]).tolist() == [1, 2]


def test_relative_ratio_handles_zero():
    ratio = relative_ratio(pd.Series([10, 5]), pd.Series([2, 0]), fill_value=0.0)
    assert ratio.tolist() == [5.0, 0.0]


def test_change_rate():
    values = pd.Series(["Approved", "Approved", "Refused", "Approved"])
    assert change_rate(values) == 2 / 3


def test_window_count():
    result = window_count(pd.Series([-1, -3, -10, 2]), [7, 30])
    assert result == {"count_7d": 2, "count_30d": 3}

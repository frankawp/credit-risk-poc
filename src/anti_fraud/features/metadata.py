from __future__ import annotations

import pandas as pd


def metadata_frame(records: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(records)
    frame["aggregation_level"] = "SK_ID_CURR"
    return frame[["feature_name", "source_table", "business_definition", "aggregation_level"]]

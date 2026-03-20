from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


def _prep_score(series: pd.Series) -> pd.Series:
    if series.isna().all():
        return pd.Series(np.zeros(len(series)), index=series.index)
    if pd.api.types.is_numeric_dtype(series):
        return series.fillna(series.median())
    coded = pd.Categorical(series.astype("object").fillna("MISSING")).codes.astype(float)
    return pd.Series(coded, index=series.index)


def _recall_at_topk(y_true: np.ndarray, scores: np.ndarray, topk_ratio: float) -> float:
    n = max(1, int(len(scores) * topk_ratio))
    order = np.argsort(-scores)[:n]
    positives = y_true.sum()
    if positives == 0:
        return 0.0
    return float(y_true[order].sum() / positives)


def evaluate_univariate(frame: pd.DataFrame, id_col: str, target_col: str, topk_ratio: float) -> pd.DataFrame:
    y = frame[target_col].to_numpy()
    rows: list[dict[str, float | str]] = []

    for col in frame.columns:
        if col in {id_col, target_col}:
            continue
        x = _prep_score(frame[col]).to_numpy()
        if len(np.unique(x)) <= 1:
            rows.append(
                {
                    "feature_name": col,
                    "univariate_roc_auc": 0.5,
                    "univariate_pr_auc": float(y.mean()),
                    "recall_at_topk": 0.0,
                    "lift_top_decile": 1.0,
                }
            )
            continue
        try:
            auc_pos = roc_auc_score(y, x)
            auc_neg = roc_auc_score(y, -x)
            ap_pos = average_precision_score(y, x)
            ap_neg = average_precision_score(y, -x)
            if ap_pos >= ap_neg:
                auc = auc_pos
                ap = ap_pos
                scores = x
            else:
                auc = auc_neg
                ap = ap_neg
                scores = -x
            recall = _recall_at_topk(y, scores, topk_ratio)
            lift = (y[np.argsort(-scores)[: max(1, int(len(scores) * 0.1))]].mean() / max(1e-9, y.mean()))
        except ValueError:
            auc = 0.5
            ap = float(y.mean())
            recall = 0.0
            lift = 1.0

        rows.append(
            {
                "feature_name": col,
                "univariate_roc_auc": float(auc),
                "univariate_pr_auc": float(ap),
                "recall_at_topk": float(recall),
                "lift_top_decile": float(lift),
            }
        )

    return pd.DataFrame(rows)

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier


def recall_at_top_k(y_true: pd.Series, scores: np.ndarray, fraction: float) -> float:
    top_n = max(1, int(len(scores) * fraction))
    ranked = np.argsort(scores)[::-1][:top_n]
    positives = float(y_true.sum())
    if positives == 0:
        return 0.0
    return float(y_true.iloc[ranked].sum() / positives)


def evaluate_scores(y_true: pd.Series, scores: np.ndarray, topk_fraction: float) -> dict[str, float]:
    return {
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "pr_auc": float(average_precision_score(y_true, scores)),
        "recall_at_topk": float(recall_at_top_k(y_true, scores, topk_fraction)),
    }


def train_baselines(
    frame: pd.DataFrame,
    baseline_columns: list[str],
    feature_columns: list[str],
    topk_fraction: float,
    random_seed: int,
    validation_size: float,
) -> dict:
    y = frame["TARGET"].astype(int)
    X_baseline = frame[baseline_columns].fillna(-999)
    X_features = frame[feature_columns].fillna(-999)
    (
        Xb_train,
        Xb_valid,
        Xf_train,
        Xf_valid,
        y_train,
        y_valid,
        train_index,
        valid_index,
    ) = train_test_split(
        X_baseline,
        X_features,
        y,
        frame.index,
        test_size=validation_size,
        stratify=y,
        random_state=random_seed,
    )

    xgb_base = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=random_seed,
        n_jobs=4,
    )
    xgb_feat = XGBClassifier(
        n_estimators=250,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=random_seed,
        n_jobs=4,
    )
    iso = IsolationForest(
        n_estimators=200,
        contamination=max(y_train.mean(), 0.01),
        random_state=random_seed,
        n_jobs=4,
    )

    xgb_base.fit(Xb_train, y_train)
    xgb_feat.fit(Xf_train, y_train)
    iso.fit(Xf_train)

    base_scores = xgb_base.predict_proba(Xb_valid)[:, 1]
    feat_scores = xgb_feat.predict_proba(Xf_valid)[:, 1]
    iso_scores = -iso.decision_function(Xf_valid)

    valid_y = y_valid.reset_index(drop=True)
    valid_rows = frame.loc[valid_index].reset_index(drop=True)
    if "fpd_severe_flag" in valid_rows.columns:
        fpd_slice = valid_rows["fpd_severe_flag"].fillna(0).astype(int) == 1
    else:
        fpd_slice = pd.Series(False, index=valid_rows.index)

    feature_importance = (
        pd.Series(xgb_feat.feature_importances_, index=X_features.columns)
        .sort_values(ascending=False)
        .head(20)
        .to_dict()
    )

    metrics = {
        "baseline_xgboost": evaluate_scores(valid_y, base_scores, topk_fraction),
        "anti_fraud_xgboost": evaluate_scores(valid_y, feat_scores, topk_fraction),
        "anti_fraud_isolation_forest": evaluate_scores(valid_y, iso_scores, topk_fraction),
        "fpd_slice": {
            "size": int(fpd_slice.sum()),
            "baseline_xgboost_recall_at_topk": float(recall_at_top_k(valid_y[fpd_slice], base_scores[fpd_slice], topk_fraction)) if fpd_slice.sum() else 0.0,
            "anti_fraud_xgboost_recall_at_topk": float(recall_at_top_k(valid_y[fpd_slice], feat_scores[fpd_slice], topk_fraction)) if fpd_slice.sum() else 0.0,
        },
        "top_feature_importance": feature_importance,
    }
    return metrics


def write_metrics(metrics: dict, path: Path) -> None:
    path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))

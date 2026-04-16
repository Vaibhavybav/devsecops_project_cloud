from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score


def evaluate_predictions(frame: pd.DataFrame) -> dict[str, Any]:
    if "rule_anomaly" not in frame.columns or "ml_anomaly" not in frame.columns:
        raise ValueError("Both rule_anomaly and ml_anomaly columns are required for evaluation.")

    y_true = frame["rule_anomaly"]
    y_pred = frame["ml_anomaly"]

    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1_score": f1_score(y_true, y_pred, zero_division=0),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }


def format_metrics(metrics: dict[str, Any]) -> str:
    lines = [
        f"Accuracy: {metrics['accuracy']:.4f}",
        f"Precision: {metrics['precision']:.4f}",
        f"Recall: {metrics['recall']:.4f}",
        f"F1 Score: {metrics['f1_score']:.4f}",
        f"Confusion Matrix: {metrics['confusion_matrix']}",
    ]
    return "\n".join(lines)

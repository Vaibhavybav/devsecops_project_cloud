from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


FEATURE_COLUMNS = ["vcpu_usage", "ram_usage", "cost"]


@dataclass
class ModelArtifacts:
    pipeline: Pipeline
    train_frame: pd.DataFrame
    test_frame: pd.DataFrame
    train_size: int
    test_size: int


class ModelArtifactError(Exception):
    """Raised when model artifacts cannot be saved or loaded."""


def build_pipeline(random_state: int = 42, contamination: float = 0.1) -> Pipeline:
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "isolation_forest",
                IsolationForest(
                    contamination=contamination,
                    random_state=random_state,
                    n_estimators=150,
                ),
            ),
        ]
    )


def train_and_predict(
    frame: pd.DataFrame,
    test_size: float = 0.3,
    random_state: int = 42,
    contamination: float = 0.1,
) -> ModelArtifacts:
    if frame.empty:
        raise ValueError("Cannot train model on an empty dataset.")
    if "rule_anomaly" not in frame.columns:
        raise ValueError("rule_anomaly column is required for train-test splitting and evaluation.")

    X = frame[FEATURE_COLUMNS]
    y = frame["rule_anomaly"]

    X_train, X_test, y_train, y_test, train_index, test_index = train_test_split(
        X,
        y,
        frame.index,
        test_size=test_size,
        random_state=random_state,
        shuffle=True,
        stratify=y,
    )

    pipeline = build_pipeline(random_state=random_state, contamination=contamination)
    # The scaler is inside the pipeline, so fitting the pipeline on X_train keeps
    # both scaling and model training isolated to the training split.
    pipeline.fit(X_train)

    train_frame = frame.loc[train_index].copy()
    test_frame = frame.loc[test_index].copy()

    test_predictions = pipeline.predict(X_test)
    scored_test = test_frame.copy()
    scored_test["ml_anomaly"] = (test_predictions == -1).astype(int)

    return ModelArtifacts(
        pipeline=pipeline,
        train_frame=train_frame,
        test_frame=scored_test,
        train_size=len(X_train),
        test_size=len(X_test),
    )


def save_model_artifacts(
    pipeline: Pipeline,
    model_path: str | Path = "model.pkl",
    scaler_path: str | Path = "scaler.pkl",
) -> None:
    try:
        joblib.dump(pipeline.named_steps["isolation_forest"], model_path)
        joblib.dump(pipeline.named_steps["scaler"], scaler_path)
    except Exception as exc:  # pragma: no cover - defensive path
        raise ModelArtifactError(f"Failed to save model artifacts: {exc}") from exc


def load_model_artifacts(
    model_path: str | Path = "model.pkl",
    scaler_path: str | Path = "scaler.pkl",
) -> tuple[Any, StandardScaler]:
    model_file = Path(model_path)
    scaler_file = Path(scaler_path)

    if not model_file.exists() or not scaler_file.exists():
        raise ModelArtifactError(
            f"Missing model artifacts. Expected {model_file} and {scaler_file}."
        )

    try:
        model = joblib.load(model_file)
        scaler = joblib.load(scaler_file)
    except Exception as exc:  # pragma: no cover - defensive path
        raise ModelArtifactError(f"Failed to load model artifacts: {exc}") from exc

    return model, scaler


def predict_with_artifacts(
    frame: pd.DataFrame,
    model: Any,
    scaler: StandardScaler,
) -> pd.DataFrame:
    scored = frame.copy()
    transformed = scaler.transform(scored[FEATURE_COLUMNS])
    predictions = model.predict(transformed)
    scored["ml_anomaly"] = (predictions == -1).astype(int)
    return scored

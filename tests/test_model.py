"""Unit tests for model.py — train_and_predict, save/load artifacts, predict_with_artifacts."""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from model import (
    ModelArtifactError,
    ModelArtifacts,
    build_pipeline,
    load_model_artifacts,
    predict_with_artifacts,
    save_model_artifacts,
    train_and_predict,
    FEATURE_COLUMNS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_frame() -> pd.DataFrame:
    """Minimal but realistic DataFrame for model tests."""
    rng = np.random.default_rng(0)
    n = 100
    return pd.DataFrame(
        {
            "vcpu_usage": rng.uniform(1, 100, n),
            "ram_usage": rng.uniform(10, 90, n),
            "cost": rng.uniform(5, 200, n),
            "rule_anomaly": rng.integers(0, 2, n),
        }
    )


@pytest.fixture
def trained_artifacts(sample_frame: pd.DataFrame) -> ModelArtifacts:
    return train_and_predict(sample_frame, test_size=0.3, random_state=42, contamination=0.1)


# ---------------------------------------------------------------------------
# build_pipeline
# ---------------------------------------------------------------------------

class TestBuildPipeline:
    def test_returns_pipeline_with_correct_steps(self):
        pipeline = build_pipeline()
        assert "scaler" in pipeline.named_steps
        assert "isolation_forest" in pipeline.named_steps

    def test_contamination_is_set(self):
        pipeline = build_pipeline(contamination=0.05)
        assert pipeline.named_steps["isolation_forest"].contamination == pytest.approx(0.05)

    def test_random_state_is_set(self):
        pipeline = build_pipeline(random_state=7)
        assert pipeline.named_steps["isolation_forest"].random_state == 7


# ---------------------------------------------------------------------------
# train_and_predict
# ---------------------------------------------------------------------------

class TestTrainAndPredict:
    def test_returns_model_artifacts(self, trained_artifacts: ModelArtifacts):
        assert isinstance(trained_artifacts, ModelArtifacts)

    def test_split_sizes_are_correct(self, sample_frame: pd.DataFrame, trained_artifacts: ModelArtifacts):
        expected_test = int(len(sample_frame) * 0.3)
        # Allow ±1 due to stratified rounding
        assert abs(trained_artifacts.test_size - expected_test) <= 1

    def test_ml_anomaly_column_exists(self, trained_artifacts: ModelArtifacts):
        assert "ml_anomaly" in trained_artifacts.test_frame.columns

    def test_ml_anomaly_values_are_binary(self, trained_artifacts: ModelArtifacts):
        values = trained_artifacts.test_frame["ml_anomaly"].unique()
        assert set(values).issubset({0, 1})

    def test_train_test_frames_do_not_overlap(self, trained_artifacts: ModelArtifacts):
        train_idx = set(trained_artifacts.train_frame.index)
        test_idx = set(trained_artifacts.test_frame.index)
        assert train_idx.isdisjoint(test_idx)

    def test_raises_on_empty_dataframe(self):
        with pytest.raises(ValueError, match="empty"):
            train_and_predict(pd.DataFrame())

    def test_raises_when_rule_anomaly_missing(self):
        df = pd.DataFrame({"vcpu_usage": [1, 2], "ram_usage": [10, 20], "cost": [5, 6]})
        with pytest.raises(ValueError, match="rule_anomaly"):
            train_and_predict(df)

    def test_train_frame_has_no_ml_anomaly(self, trained_artifacts: ModelArtifacts):
        # Train frame should NOT have ml_anomaly — only test frame does
        assert "ml_anomaly" not in trained_artifacts.train_frame.columns

    def test_all_feature_columns_present_in_test_frame(self, trained_artifacts: ModelArtifacts):
        for col in FEATURE_COLUMNS:
            assert col in trained_artifacts.test_frame.columns


# ---------------------------------------------------------------------------
# save_model_artifacts / load_model_artifacts
# ---------------------------------------------------------------------------

class TestSaveLoadArtifacts:
    def test_save_and_load_round_trip(self, trained_artifacts: ModelArtifacts):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model.pkl"
            scaler_path = Path(tmpdir) / "scaler.pkl"

            save_model_artifacts(
                trained_artifacts.pipeline,
                model_path=model_path,
                scaler_path=scaler_path,
            )

            assert model_path.exists()
            assert scaler_path.exists()

            model, scaler = load_model_artifacts(
                model_path=model_path, scaler_path=scaler_path
            )
            assert model is not None
            assert scaler is not None

    def test_load_raises_when_files_missing(self):
        with pytest.raises(ModelArtifactError, match="Missing"):
            load_model_artifacts(
                model_path="/nonexistent/model.pkl",
                scaler_path="/nonexistent/scaler.pkl",
            )


# ---------------------------------------------------------------------------
# predict_with_artifacts
# ---------------------------------------------------------------------------

class TestPredictWithArtifacts:
    def test_predict_returns_ml_anomaly_column(self, trained_artifacts: ModelArtifacts):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model.pkl"
            scaler_path = Path(tmpdir) / "scaler.pkl"
            save_model_artifacts(
                trained_artifacts.pipeline,
                model_path=model_path,
                scaler_path=scaler_path,
            )
            model, scaler = load_model_artifacts(model_path=model_path, scaler_path=scaler_path)

            test_df = trained_artifacts.test_frame[FEATURE_COLUMNS].copy()
            result = predict_with_artifacts(test_df, model, scaler)

            assert "ml_anomaly" in result.columns
            assert set(result["ml_anomaly"].unique()).issubset({0, 1})

    def test_predict_does_not_mutate_input(self, trained_artifacts: ModelArtifacts):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model.pkl"
            scaler_path = Path(tmpdir) / "scaler.pkl"
            save_model_artifacts(
                trained_artifacts.pipeline,
                model_path=model_path,
                scaler_path=scaler_path,
            )
            model, scaler = load_model_artifacts(model_path=model_path, scaler_path=scaler_path)

            test_df = trained_artifacts.test_frame[FEATURE_COLUMNS].copy()
            original_cols = list(test_df.columns)
            predict_with_artifacts(test_df, model, scaler)

            assert list(test_df.columns) == original_cols

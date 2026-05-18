"""Centralised configuration for the Green FinOps pipeline.

All tuneable constants live here so operators can override them via
environment variables without touching source code.  Import this module
instead of scattering ``os.getenv`` calls across the codebase.

Usage
-----
    from config import settings

    print(settings.contamination)          # 0.1 (or whatever $CONTAMINATION is set to)
    print(settings.low_carbon_threshold)   # 300.0
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_float(name: str, default: float) -> float:
    """Read *name* from environment, coerce to float, fall back to *default*."""
    raw = os.getenv(name, "")
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "")
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_str(name: str, default: str) -> str:
    return os.getenv(name, default)


# ---------------------------------------------------------------------------
# Pipeline settings
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PipelineSettings:
    """Immutable settings loaded once at import time.

    Every field can be overridden by the corresponding environment variable.
    """

    # --- Data ingestion ---
    data_dir: str = field(
        default_factory=lambda: _env_str("DATA_DIR", "data")
    )
    output_file: str = field(
        default_factory=lambda: _env_str("OUTPUT_FILE", "outputs/final_output.csv")
    )
    nrows: int | None = field(
        default_factory=lambda: (
            _env_int("NROWS", 0) or None  # 0 → None (no limit)
        )
    )

    # --- Merge tolerance ---
    merge_tolerance: int = field(
        default_factory=lambda: _env_int("MERGE_TOLERANCE", 5)
    )

    # --- Model hyperparameters ---
    random_state: int = field(
        default_factory=lambda: _env_int("RANDOM_STATE", 42)
    )
    contamination: float = field(
        default_factory=lambda: _env_float("CONTAMINATION", 0.1)
    )
    test_size: float = field(
        default_factory=lambda: _env_float("TEST_SIZE", 0.3)
    )

    # --- Artifact paths ---
    model_file: str = field(
        default_factory=lambda: _env_str("MODEL_FILE", "model.pkl")
    )
    scaler_file: str = field(
        default_factory=lambda: _env_str("SCALER_FILE", "scaler.pkl")
    )

    # --- Carbon / region thresholds (mirrors feature_engineering constants) ---
    low_carbon_threshold: float = field(
        default_factory=lambda: _env_float("LOW_CARBON_THRESHOLD", 300.0)
    )
    min_carbon_reduction_for_move: float = field(
        default_factory=lambda: _env_float("MIN_CARBON_REDUCTION_FOR_MOVE", 150.0)
    )
    significant_score_improvement: float = field(
        default_factory=lambda: _env_float("SIGNIFICANT_SCORE_IMPROVEMENT", 120.0)
    )
    max_target_region_ratio: float = field(
        default_factory=lambda: _env_float("MAX_TARGET_REGION_RATIO", 0.5)
    )

    # --- Anomaly rebalancing ---
    anomaly_min_ratio: float = field(
        default_factory=lambda: _env_float("ANOMALY_MIN_RATIO", 0.10)
    )
    anomaly_max_ratio: float = field(
        default_factory=lambda: _env_float("ANOMALY_MAX_RATIO", 0.15)
    )

    # --- External APIs ---
    electricity_maps_api_key: str = field(
        default_factory=lambda: _env_str("ELECTRICITY_MAPS_API_KEY", "")
    )

    def __post_init__(self) -> None:
        if not (0.0 < self.contamination < 0.5):
            raise ValueError(
                f"contamination must be in (0, 0.5), got {self.contamination}"
            )
        if not (0.0 < self.test_size < 1.0):
            raise ValueError(
                f"test_size must be in (0, 1), got {self.test_size}"
            )
        if not (0.0 < self.max_target_region_ratio <= 1.0):
            raise ValueError(
                f"max_target_region_ratio must be in (0, 1], got {self.max_target_region_ratio}"
            )


# Singleton — import this everywhere instead of constructing a new instance.
settings = PipelineSettings()

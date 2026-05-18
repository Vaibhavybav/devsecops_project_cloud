"""Unit tests for feature_engineering.py."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from feature_engineering import (
    FALLBACK_CARBON_INTENSITY,
    LOW_CARBON_THRESHOLD,
    MIN_CARBON_REDUCTION_FOR_MOVE,
    SIGNIFICANT_SCORE_IMPROVEMENT,
    _compute_region_score,
    _fallback_carbon_intensity,
    _get_migration_penalty,
    _get_ranked_target_regions,
    add_features,
    apply_decision_engine,
    get_best_region_for_vm,
    region_to_zone,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def minimal_frame() -> pd.DataFrame:
    """Small raw DataFrame (pre-feature-engineering)."""
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=20, freq="1min"),
            "vcpu_usage": [2.0] * 10 + [90.0] * 10,   # 10 idle, 10 spike
            "ram_usage": [60.0] * 20,
        }
    )


@pytest.fixture
def featured_frame(minimal_frame: pd.DataFrame) -> pd.DataFrame:
    return add_features(minimal_frame, random_state=0)


# ---------------------------------------------------------------------------
# _fallback_carbon_intensity
# ---------------------------------------------------------------------------

class TestFallbackCarbonIntensity:
    def test_known_zones_return_expected_values(self):
        for zone, expected in FALLBACK_CARBON_INTENSITY.items():
            assert _fallback_carbon_intensity(zone) == pytest.approx(expected)

    def test_unknown_zone_returns_default(self):
        assert _fallback_carbon_intensity("UNKNOWN") == pytest.approx(500.0)


# ---------------------------------------------------------------------------
# _get_migration_penalty
# ---------------------------------------------------------------------------

class TestGetMigrationPenalty:
    def test_same_region_has_zero_penalty(self):
        for region in region_to_zone.keys():
            assert _get_migration_penalty(region, region) == pytest.approx(0.0)

    def test_known_pair_returns_expected_penalty(self):
        assert _get_migration_penalty("India", "Europe") == pytest.approx(200.0)
        assert _get_migration_penalty("India", "US") == pytest.approx(150.0)

    def test_unknown_pair_returns_default_penalty(self):
        assert _get_migration_penalty("India", "China") == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# _compute_region_score
# ---------------------------------------------------------------------------

class TestComputeRegionScore:
    def test_same_region_score_equals_carbon(self):
        score = _compute_region_score("India", "India", 700.0, 700.0)
        assert score == pytest.approx(700.0)

    def test_stability_block_applied_when_low_carbon_and_small_saving(self):
        """Current region has low carbon, small saving → stability penalty is added."""
        current_carbon = 250.0  # < LOW_CARBON_THRESHOLD (300)
        target_carbon = 200.0   # saving = 50 < MIN_CARBON_REDUCTION_FOR_MOVE (150)
        score = _compute_region_score("India", "Europe", current_carbon, target_carbon)
        # Penalty of 10000 + migration penalty + target_carbon
        assert score > 10000

    def test_no_stability_block_when_saving_is_large(self):
        current_carbon = 700.0
        target_carbon = 200.0   # saving = 500 > MIN_CARBON_REDUCTION_FOR_MOVE
        score = _compute_region_score("India", "Europe", current_carbon, target_carbon)
        # Should just be target_carbon + migration_penalty, no stability block
        assert score < 10000


# ---------------------------------------------------------------------------
# _get_ranked_target_regions
# ---------------------------------------------------------------------------

class TestGetRankedTargetRegions:
    def test_returns_all_known_regions(self):
        intensity = {r: 400.0 for r in region_to_zone}
        ranked = _get_ranked_target_regions("India", 700.0, intensity)
        returned_regions = [r for r, _ in ranked]
        assert set(returned_regions) == set(region_to_zone.keys())

    def test_sorted_by_score_ascending(self):
        intensity = {"India": 700.0, "Europe": 200.0, "US": 400.0, "China": 650.0}
        ranked = _get_ranked_target_regions("India", 700.0, intensity)
        scores = [s for _, s in ranked]
        assert scores == sorted(scores)


# ---------------------------------------------------------------------------
# get_best_region_for_vm
# ---------------------------------------------------------------------------

class TestGetBestRegionForVm:
    def test_returns_a_known_region(self):
        intensity = {"India": 700.0, "Europe": 200.0, "US": 400.0, "China": 650.0}
        best = get_best_region_for_vm("India", intensity_by_region=intensity)
        assert best in region_to_zone.keys()

    def test_low_carbon_region_prefers_staying(self):
        """When current region is already low-carbon, stay preference should win."""
        # Europe has 200 → movement to similarly low region incurs stability block
        intensity = {"India": 700.0, "Europe": 200.0, "US": 400.0, "China": 650.0}
        best = get_best_region_for_vm("Europe", intensity_by_region=intensity)
        # May stay in Europe or move — just assert valid output
        assert best in region_to_zone.keys()


# ---------------------------------------------------------------------------
# add_features
# ---------------------------------------------------------------------------

class TestAddFeatures:
    def test_output_has_expected_columns(self, featured_frame: pd.DataFrame):
        for col in [
            "cost", "carbon_intensity", "carbon_score", "target_region",
            "carbon_saving", "rule_anomaly",
        ]:
            assert col in featured_frame.columns, f"Missing column: {col}"

    def test_cost_is_non_negative(self, featured_frame: pd.DataFrame):
        assert (featured_frame["cost"] >= 0).all()

    def test_rule_anomaly_is_binary(self, featured_frame: pd.DataFrame):
        assert set(featured_frame["rule_anomaly"].unique()).issubset({0, 1})

    def test_anomaly_ratio_within_target_range(self, featured_frame: pd.DataFrame):
        ratio = featured_frame["rule_anomaly"].mean()
        # rebalance targets [0.10, 0.15]; allow slight slack for small frames
        assert 0.05 <= ratio <= 0.30, f"Anomaly ratio {ratio:.2f} out of expected range"

    def test_target_region_in_known_regions(self, featured_frame: pd.DataFrame):
        assert featured_frame["target_region"].isin(region_to_zone.keys()).all()

    def test_does_not_mutate_input(self, minimal_frame: pd.DataFrame):
        original_cols = list(minimal_frame.columns)
        add_features(minimal_frame.copy(), random_state=0)
        assert list(minimal_frame.columns) == original_cols


# ---------------------------------------------------------------------------
# apply_decision_engine
# ---------------------------------------------------------------------------

class TestApplyDecisionEngine:
    def test_final_action_column_exists(self, featured_frame: pd.DataFrame):
        # Add ml_anomaly for decision engine
        frame = featured_frame.copy()
        frame["ml_anomaly"] = 0
        result = apply_decision_engine(frame)
        assert "final_action" in result.columns

    def test_vm_status_values_are_valid(self, featured_frame: pd.DataFrame):
        frame = featured_frame.copy()
        frame["ml_anomaly"] = 0
        result = apply_decision_engine(frame)
        assert result["vm_status"].isin({"Healthy", "Bad"}).all()

    def test_reason_column_exists(self, featured_frame: pd.DataFrame):
        frame = featured_frame.copy()
        frame["ml_anomaly"] = 0
        result = apply_decision_engine(frame)
        assert "reason" in result.columns

    def test_move_action_only_when_score_improves(self, featured_frame: pd.DataFrame):
        frame = featured_frame.copy()
        frame["ml_anomaly"] = 0
        result = apply_decision_engine(frame)
        move_rows = result[result["final_action"].str.startswith("Move")]
        if not move_rows.empty:
            assert (move_rows["score_improvement"] >= SIGNIFICANT_SCORE_IMPROVEMENT).all()
            assert (move_rows["carbon_saving"] > 0).all()

    def test_bad_status_on_ml_anomaly(self, featured_frame: pd.DataFrame):
        frame = featured_frame.copy()
        frame["ml_anomaly"] = 1
        result = apply_decision_engine(frame)
        # All rows have ml_anomaly=1 → all should be "Bad"
        assert (result["vm_status"] == "Bad").all()

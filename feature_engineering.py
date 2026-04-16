from __future__ import annotations

import numpy as np
import pandas as pd
import requests


API_KEY = "b6efnGdwZWPrHKmH8HNe"

region_to_zone = {
    "India": "IN",
    "Europe": "FR",
    "US": "US-CAL",
    "China": "CN",
}

zone_to_region = {
    "IN": "India",
    "FR": "Europe",
    "US-CAL": "US",
    "CN": "China",
}

MIGRATION_PENALTY = {
    ("India", "Europe"): 200.0,
    ("India", "US"): 150.0,
    ("China", "Europe"): 250.0,
    ("China", "US"): 120.0,
    ("US", "Europe"): 100.0,
    ("Europe", "US"): 80.0,
}

DEFAULT_MIGRATION_PENALTY = 50.0
LOW_CARBON_THRESHOLD = 300.0
MIN_CARBON_REDUCTION_FOR_MOVE = 150.0
STABILITY_BLOCK_PENALTY = 10000.0
SIGNIFICANT_SCORE_IMPROVEMENT = 120.0
MAX_TARGET_REGION_RATIO = 0.5

FALLBACK_CARBON_INTENSITY = {
    "IN": 700.0,
    "FR": 200.0,
    "US-CAL": 400.0,
    "CN": 650.0,
}


def _fallback_carbon_intensity(zone: str) -> float:
    return float(FALLBACK_CARBON_INTENSITY.get(zone, 500.0))


def get_carbon_intensity(zone: str) -> float:
    url = f"https://api-access.electricitymaps.com/free-tier/carbon-intensity/latest?zone={zone}"
    headers = {"auth-token": API_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        payload = response.json()
        return float(payload.get("carbonIntensity", _fallback_carbon_intensity(zone)))
    except Exception:
        return _fallback_carbon_intensity(zone)


def get_best_zone() -> str:
    zones = list(zone_to_region.keys())
    values = {zone: get_carbon_intensity(zone) for zone in zones}
    return min(values, key=values.get)


def _get_migration_penalty(current_region: str, target_region: str) -> float:
    if current_region == target_region:
        return 0.0
    return float(MIGRATION_PENALTY.get((current_region, target_region), DEFAULT_MIGRATION_PENALTY))


def _compute_region_score(
    current_region: str,
    target_region: str,
    current_carbon: float,
    target_carbon: float,
) -> float:
    migration_penalty = _get_migration_penalty(current_region, target_region)

    stability_penalty = 0.0
    carbon_reduction = current_carbon - target_carbon
    if (
        current_region != target_region
        and current_carbon < LOW_CARBON_THRESHOLD
        and carbon_reduction <= MIN_CARBON_REDUCTION_FOR_MOVE
    ):
        stability_penalty = STABILITY_BLOCK_PENALTY

    return float(target_carbon + migration_penalty + stability_penalty)


def _get_ranked_target_regions(
    current_region: str,
    current_carbon: float,
    intensity_by_region: dict[str, float],
) -> list[tuple[str, float]]:
    scored_targets: list[tuple[str, float]] = []
    for region in region_to_zone.keys():
        target_carbon = float(intensity_by_region.get(region, current_carbon))
        score = _compute_region_score(
            current_region=current_region,
            target_region=region,
            current_carbon=current_carbon,
            target_carbon=target_carbon,
        )
        scored_targets.append((region, score))

    scored_targets.sort(key=lambda item: item[1])
    return scored_targets


def _assign_target_regions_with_diversity(
    frame: pd.DataFrame,
    intensity_by_region: dict[str, float],
    max_target_region_ratio: float = MAX_TARGET_REGION_RATIO,
) -> pd.Series:
    if frame.empty:
        return pd.Series(dtype="object")

    assigned_counts = {region: 0 for region in region_to_zone.keys()}
    max_per_region = max(1, int(np.floor(len(frame) * max_target_region_ratio)))

    ranked_indices = frame.sort_values("carbon_intensity", ascending=False).index
    assigned_targets: dict[int, str] = {}

    for idx in ranked_indices:
        current_region = str(frame.at[idx, "region"])
        current_carbon = float(frame.at[idx, "carbon_intensity"])

        candidates = _get_ranked_target_regions(
            current_region=current_region,
            current_carbon=current_carbon,
            intensity_by_region=intensity_by_region,
        )

        selected_region = current_region
        for candidate_region, _ in candidates:
            if assigned_counts[candidate_region] < max_per_region:
                selected_region = candidate_region
                break

        # If all regions hit the cap (edge case), choose the least-loaded target.
        if assigned_counts[selected_region] >= max_per_region:
            selected_region = min(assigned_counts, key=assigned_counts.get)

        assigned_targets[idx] = selected_region
        assigned_counts[selected_region] = assigned_counts.get(selected_region, 0) + 1

    return pd.Series(assigned_targets).reindex(frame.index)


def get_best_region_for_vm(
    current_region: str,
    intensity_by_region: dict[str, float] | None = None,
) -> str:
    if intensity_by_region is None:
        intensity_by_region = {
            region: get_carbon_intensity(zone)
            for region, zone in region_to_zone.items()
        }

    current_carbon = float(intensity_by_region.get(current_region, 500.0))
    ranked_targets = _get_ranked_target_regions(
        current_region=current_region,
        current_carbon=current_carbon,
        intensity_by_region=intensity_by_region,
    )

    if not ranked_targets:
        return current_region

    return ranked_targets[0][0]


def _attach_live_carbon_context(frame: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    enriched = frame.copy()
    regions = list(region_to_zone.keys())

    if "server_id" not in enriched.columns:
        enriched["server_id"] = [f"vm-{index + 1}" for index in range(len(enriched))]

    enriched["region"] = rng.choice(regions, size=len(enriched), replace=True)

    live_intensity_by_region = {
        region: get_carbon_intensity(zone)
        for region, zone in region_to_zone.items()
    }

    enriched["carbon_intensity"] = enriched["region"].map(live_intensity_by_region).astype(float)
    enriched["carbon_score"] = enriched["carbon_intensity"] / 1000.0

    enriched["target_region"] = _assign_target_regions_with_diversity(
        enriched,
        intensity_by_region=live_intensity_by_region,
    )
    enriched["target_zone"] = enriched["target_region"].map(region_to_zone)
    enriched["target_carbon_intensity"] = (
        enriched["target_region"].map(live_intensity_by_region).fillna(enriched["carbon_intensity"])
    )
    enriched["carbon_saving"] = enriched["carbon_intensity"] - enriched["target_carbon_intensity"]
    enriched["current_region_score"] = enriched.apply(
        lambda row: _compute_region_score(
            current_region=row["region"],
            target_region=row["region"],
            current_carbon=float(row["carbon_intensity"]),
            target_carbon=float(row["carbon_intensity"]),
        ),
        axis=1,
    )
    enriched["target_region_score"] = enriched.apply(
        lambda row: _compute_region_score(
            current_region=row["region"],
            target_region=row["target_region"],
            current_carbon=float(row["carbon_intensity"]),
            target_carbon=float(row["target_carbon_intensity"]),
        ),
        axis=1,
    )
    enriched["score_improvement"] = enriched["current_region_score"] - enriched["target_region_score"]

    return enriched


def _rebalance_rule_anomalies(
    frame: pd.DataFrame,
    rng: np.random.Generator,
    target_min_ratio: float = 0.10,
    target_max_ratio: float = 0.15,
) -> pd.DataFrame:
    balanced = frame.copy()
    current_ratio = balanced["rule_anomaly"].mean()

    if current_ratio < target_min_ratio:
        target_count = int(np.ceil(len(balanced) * target_min_ratio))
        shortfall = max(0, target_count - int(balanced["rule_anomaly"].sum()))

        if shortfall > 0:
            candidate_mask = balanced["rule_anomaly"] == 0
            candidate_scores = (
                balanced["ram_usage"].rank(pct=True)
                + balanced["cost"].rank(pct=True)
                - balanced["vcpu_usage"].rank(pct=True)
            )
            candidates = balanced.loc[candidate_mask].assign(_score=candidate_scores[candidate_mask])
            selected_index = candidates.nlargest(shortfall, "_score").index

            split_point = shortfall // 2
            idle_heavy_index = selected_index[:split_point]
            cpu_spike_index = selected_index[split_point:]

            ram_baseline = float(balanced["ram_usage"].quantile(0.90))

            if len(idle_heavy_index) > 0:
                balanced.loc[idle_heavy_index, "vcpu_usage"] = rng.uniform(0.5, 4.8, len(idle_heavy_index))
                balanced.loc[idle_heavy_index, "ram_usage"] = np.maximum(
                    balanced.loc[idle_heavy_index, "ram_usage"].to_numpy(),
                    ram_baseline + np.abs(rng.normal(6, 3, len(idle_heavy_index))),
                )

            if len(cpu_spike_index) > 0:
                balanced.loc[cpu_spike_index, "vcpu_usage"] = np.maximum(
                    balanced.loc[cpu_spike_index, "vcpu_usage"].to_numpy(),
                    85 + np.abs(rng.normal(8, 4, len(cpu_spike_index))),
                )

            balanced.loc[selected_index, "cost"] = (
                balanced.loc[selected_index, "vcpu_usage"] * 0.6
                + balanced.loc[selected_index, "ram_usage"] * 0.4
                + rng.normal(0, 2, len(selected_index))
            ).clip(lower=0)

            balanced["rule_anomaly"] = (
                ((balanced["vcpu_usage"] < 5) & (balanced["ram_usage"] > balanced["ram_usage"].mean()))
                | (balanced["vcpu_usage"] > 80)
            ).astype(int)

    elif current_ratio > target_max_ratio:
        target_count = int(np.floor(len(balanced) * target_max_ratio))
        excess = max(0, int(balanced["rule_anomaly"].sum()) - target_count)

        if excess > 0:
            anomaly_scores = (
                balanced["vcpu_usage"].rank(pct=True)
                + balanced["ram_usage"].rank(pct=True)
                + balanced["cost"].rank(pct=True)
            )
            anomalies = balanced.loc[balanced["rule_anomaly"] == 1].assign(
                _score=anomaly_scores[balanced["rule_anomaly"] == 1]
            )
            selected_index = anomalies.nsmallest(excess, "_score").index
            balanced.loc[selected_index, "rule_anomaly"] = 0

    balanced["rule_anomaly"] = balanced["rule_anomaly"].astype(int)
    return balanced


def add_features(frame: pd.DataFrame, random_state: int = 42) -> pd.DataFrame:
    enriched = frame.copy()
    rng = np.random.default_rng(random_state)

    enriched["cost"] = (
        enriched["vcpu_usage"] * 0.6
        + enriched["ram_usage"] * 0.4
        + rng.normal(0, 2, len(enriched))
    )
    enriched["cost"] = enriched["cost"].clip(lower=0)
    enriched = _attach_live_carbon_context(enriched, rng)

    enriched["rule_anomaly"] = (
        ((enriched["vcpu_usage"] < 5) & (enriched["ram_usage"] > enriched["ram_usage"].mean()))
        | (enriched["vcpu_usage"] > 80)
    ).astype(int)

    return _rebalance_rule_anomalies(enriched, rng=rng)


def add_inference_features(frame: pd.DataFrame, random_state: int = 42) -> pd.DataFrame:
    enriched = frame.copy()
    rng = np.random.default_rng(random_state)

    enriched["cost"] = (
        enriched["vcpu_usage"] * 0.6
        + enriched["ram_usage"] * 0.4
        + rng.normal(0, 2, len(enriched))
    )
    enriched["cost"] = enriched["cost"].clip(lower=0)
    enriched = _attach_live_carbon_context(enriched, rng)

    return enriched


def apply_decision_engine(frame: pd.DataFrame) -> pd.DataFrame:
    decided = frame.copy()

    if "target_region" not in decided.columns:
        decided["target_region"] = decided["region"].apply(get_best_region_for_vm)
    if "target_carbon_intensity" not in decided.columns:
        decided["target_carbon_intensity"] = decided["target_region"].map(
            {region: get_carbon_intensity(zone) for region, zone in region_to_zone.items()}
        )
    if "carbon_saving" not in decided.columns:
        decided["carbon_saving"] = decided["carbon_intensity"] - decided["target_carbon_intensity"]
    if "current_region_score" not in decided.columns:
        decided["current_region_score"] = decided.apply(
            lambda row: _compute_region_score(
                current_region=row["region"],
                target_region=row["region"],
                current_carbon=float(row["carbon_intensity"]),
                target_carbon=float(row["carbon_intensity"]),
            ),
            axis=1,
        )
    if "target_region_score" not in decided.columns:
        decided["target_region_score"] = decided.apply(
            lambda row: _compute_region_score(
                current_region=row["region"],
                target_region=row["target_region"],
                current_carbon=float(row["carbon_intensity"]),
                target_carbon=float(row["target_carbon_intensity"]),
            ),
            axis=1,
        )
    decided["score_improvement"] = decided["current_region_score"] - decided["target_region_score"]

    decided["final_action"] = decided.apply(
        lambda row: f"Move from {row['region']} -> {row['target_region']}"
        if row["region"] != row["target_region"]
        and row["score_improvement"] >= SIGNIFICANT_SCORE_IMPROVEMENT
        and row["carbon_saving"] > 0
        and not (
            row["carbon_intensity"] < LOW_CARBON_THRESHOLD
            and row["carbon_saving"] <= MIN_CARBON_REDUCTION_FOR_MOVE
        )
        else "Stay in current region",
        axis=1,
    )

    def get_reason(row: pd.Series) -> str:
        if row["ml_anomaly"] == 1 and row["vcpu_usage"] > 80:
            return "CPU spike anomaly"
        if row["ml_anomaly"] == 1 and row["ram_usage"] > 50:
            return "High memory usage anomaly"
        if row["carbon_intensity"] > 600:
            return "High carbon intensity region"
        return "Healthy"

    decided["reason"] = decided.apply(get_reason, axis=1)
    decided["vm_status"] = decided.apply(
        lambda row: "Bad"
        if row["ml_anomaly"] == 1 or row["carbon_intensity"] > 600
        else "Healthy",
        axis=1,
    )

    return decided

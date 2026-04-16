from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd


class DataLoadError(Exception):
    """Raised when source data cannot be loaded or merged."""


def _clean_columns(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    cleaned.columns = (
        cleaned.columns.str.strip().str.lower().str.replace(" ", "_", regex=False)
    )
    return cleaned


def _load_csv(path: Path, usecols: list[str], nrows: Optional[int] = None) -> pd.DataFrame:
    if not path.exists():
        raise DataLoadError(f"Missing input file: {path}")

    try:
        frame = pd.read_csv(
            path,
            usecols=usecols,
            nrows=nrows,
            low_memory=False,
        )
    except Exception as exc:  # pragma: no cover - defensive path
        raise DataLoadError(f"Failed to read {path}: {exc}") from exc

    frame = _clean_columns(frame)
    if "timestamp" in frame.columns:
        frame["timestamp"] = pd.to_numeric(frame["timestamp"], errors="coerce")

    return frame


def _fill_missing_values(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = frame.copy()

    numeric_columns = prepared.select_dtypes(include=["number"]).columns
    categorical_columns = prepared.select_dtypes(exclude=["number"]).columns

    for column in numeric_columns:
        prepared[column] = prepared[column].fillna(prepared[column].median())

    for column in categorical_columns:
        prepared[column] = prepared[column].fillna("unknown")

    return prepared


def merge_datasets(
    metadata: pd.DataFrame,
    usage: pd.DataFrame,
    tolerance_seconds: int = 5,
) -> pd.DataFrame:
    merge_keys = ["server_id", "timestamp"]

    exact_merge = metadata.merge(
        usage,
        on=merge_keys,
        how="inner",
        suffixes=("_meta", "_usage"),
    )
    if not exact_merge.empty:
        return _fill_missing_values(exact_merge)

    # Some telemetry feeds arrive a few seconds apart, so we fall back to
    # nearest-timestamp matching within each server_id when exact joins fail.
    meta_sorted = metadata.sort_values(["timestamp", "server_id"]).reset_index(drop=True)
    usage_sorted = usage.sort_values(["timestamp", "server_id"]).reset_index(drop=True)

    merged = pd.merge_asof(
        meta_sorted,
        usage_sorted,
        on="timestamp",
        by="server_id",
        direction="nearest",
        tolerance=tolerance_seconds,
        suffixes=("_meta", "_usage"),
    )
    merged = merged.dropna(subset=["vcpu_usage", "ram_usage"])

    if merged.empty:
        raise DataLoadError(
            "No rows matched between metadata and usage data. "
            "Check timestamp alignment or increase the merge tolerance."
        )

    return _fill_missing_values(merged)


def load_and_merge_data(
    data_dir: str | Path = "data",
    metadata_file: str = "servers_specs.csv",
    usage_file: str = "servers_usage.csv",
    nrows: Optional[int] = None,
    tolerance_seconds: int = 5,
) -> pd.DataFrame:
    base_path = Path(data_dir)
    metadata = _load_csv(
        base_path / metadata_file,
        usecols=["id", "timestamp", "server_id", "flavor_id"],
        nrows=nrows,
    )
    usage = _load_csv(
        base_path / usage_file,
        usecols=["id", "timestamp", "server_id", "vcpu_usage", "ram_usage", "host_id"],
        nrows=nrows,
    )

    return merge_datasets(metadata, usage, tolerance_seconds=tolerance_seconds)

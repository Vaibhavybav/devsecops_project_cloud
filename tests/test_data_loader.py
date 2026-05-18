import csv
import pandas as pd
import pytest
from pathlib import Path

from data_loader import load_and_merge_data, DataLoadError

@pytest.fixture
def synthetic_data(tmp_path: Path):
    # Create metadata CSV
    meta_path = tmp_path / "servers_specs.csv"
    meta_rows = [
        {"id": 1, "timestamp": 1000, "server_id": "srv1", "flavor_id": "flv1"},
        {"id": 2, "timestamp": 1005, "server_id": "srv2", "flavor_id": "flv2"},
    ]
    pd.DataFrame(meta_rows).to_csv(meta_path, index=False)

    # Create usage CSV
    usage_path = tmp_path / "servers_usage.csv"
    usage_rows = [
        {"id": 10, "timestamp": 1000, "server_id": "srv1", "vcpu_usage": 55.0, "ram_usage": 70.0, "host_id": "h1"},
        {"id": 11, "timestamp": 1005, "server_id": "srv2", "vcpu_usage": 60.0, "ram_usage": 65.0, "host_id": "h2"},
    ]
    pd.DataFrame(usage_rows).to_csv(usage_path, index=False)
    return tmp_path

def test_load_and_merge_success(synthetic_data: Path):
    merged = load_and_merge_data(
        data_dir=synthetic_data,
        metadata_file="servers_specs.csv",
        usage_file="servers_usage.csv",
        tolerance_seconds=5,
    )
    # Expect a merge on server_id and timestamp resulting in 2 rows
    assert isinstance(merged, pd.DataFrame)
    assert len(merged) == 2
    # Columns from both datasets should be present
    expected_cols = {"id_meta", "timestamp", "server_id", "flavor_id", "id_usage", "vcpu_usage", "ram_usage", "host_id"}
    assert expected_cols.issubset(set(merged.columns))

def test_load_and_merge_no_match_raises(synthetic_data: Path):
    # Use a tolerance that is too low to force failure
    with pytest.raises(DataLoadError):
        load_and_merge_data(
            data_dir=synthetic_data,
            metadata_file="servers_specs.csv",
            usage_file="servers_usage.csv",
            tolerance_seconds=0,
        )

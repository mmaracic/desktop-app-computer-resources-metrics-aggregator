"""Tests for FileUpdater, ensuring successive updates are appended to the same file."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from src.metric.model.component_type import ComponentType
from src.metric.model.metric import Metric
from src.metric.model.metric_type import MetricType
from src.updaters.file_updater import FileUpdater


def _build_metric(name: str, value: float) -> Metric:
    """Build a Metric instance with the given name and value for test purposes."""
    return Metric(
        name=name,
        metric_type=MetricType.FLOAT,
        value=value,
        alias=name,
        description=name,
        component_type=ComponentType.CPU,
    )


def test_update_appends_multiple_updates_to_same_file(tmp_path: Path):
    file_name = str(tmp_path / "metrics")
    updater = FileUpdater(file_name)
    fixed_now = datetime(2026, 9, 16, 12, 0, 0)

    with patch("src.updaters.file_updater.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        updater.update([_build_metric("cpu_usage_percent", 10.0)])
        updater.update([_build_metric("cpu_usage_percent", 20.0)])

    output_file = tmp_path / "metrics_20260916.json"
    assert output_file.exists()

    lines = output_file.read_text().splitlines()
    assert len(lines) == 2

    first_entry = json.loads(lines[0])
    second_entry = json.loads(lines[1])
    assert first_entry["metrics"][0] == {"name": "cpu_usage_percent", "value": 10.0}
    assert second_entry["metrics"][0] == {"name": "cpu_usage_percent", "value": 20.0}

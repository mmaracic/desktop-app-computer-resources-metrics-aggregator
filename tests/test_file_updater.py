"""Tests for FileUpdater, ensuring successive updates are appended to the same file."""

import json
from datetime import UTC, datetime
from pathlib import Path

from src.metric.model.component_type import ComponentType
from src.metric.model.metric import Metric
from src.metric.model.metric_metadata import MetricMetadata
from src.metric.model.metric_type import MetricType
from src.storage.disk_text_file_storage import DiskTextFileStorage
from src.updaters.file_updater import FileUpdater, MetricsInTime


def _build_metric(name: str, value: float) -> Metric:
    """Build a Metric instance with the given name and value for test purposes."""
    return Metric(
        name=name,
        value=value,
        metadata=MetricMetadata(
            metric_type=MetricType.FLOAT,
            alias=name,
            description=name,
            component_type=ComponentType.CPU,
        ),
    )


def test_update_appends_multiple_updates_to_same_file(tmp_path: Path) -> None:
    file_name = str(tmp_path / "metrics")
    disk_storage = DiskTextFileStorage(str(tmp_path))
    updater = FileUpdater(file_name, disk_storage)
    fixed_now = datetime(2026, 9, 16, 12, 0, 0, tzinfo=UTC)

    updater.update(
        MetricsInTime(
            metrics=[_build_metric("cpu_usage_percent", 10.0)],
            stored_at=fixed_now,
        ),
    )
    updater.update(
        MetricsInTime(
            metrics=[_build_metric("cpu_usage_percent", 20.0)],
            stored_at=fixed_now,
        ),
    )

    output_file = tmp_path / f"metrics_{fixed_now.strftime('%Y%m%d')}.json"
    assert output_file.exists()

    lines = output_file.read_text().splitlines()
    assert len(lines) == 2

    first_entry = json.loads(lines[0])
    second_entry = json.loads(lines[1])
    expected_stored_at = fixed_now.isoformat()
    assert first_entry == {
        "stored_at": expected_stored_at,
        "metrics": [{"name": "cpu_usage_percent", "value": 10.0}],
    }
    assert second_entry == {
        "stored_at": expected_stored_at,
        "metrics": [{"name": "cpu_usage_percent", "value": 20.0}],
    }


def test_update_uses_separate_file_per_day(tmp_path: Path) -> None:
    file_name = str(tmp_path / "metrics")
    disk_storage = DiskTextFileStorage(str(tmp_path))
    updater = FileUpdater(file_name, disk_storage)
    fixed_now = datetime(2026, 9, 16, 12, 0, 0, tzinfo=UTC)

    updater.update(
        MetricsInTime(
            metrics=[_build_metric("cpu_usage_percent", 10.0)],
            stored_at=fixed_now,
        ),
    )

    fixed_now = datetime(2026, 9, 17, 0, 0, 0, tzinfo=UTC)
    updater.update(
        MetricsInTime(
            metrics=[_build_metric("cpu_usage_percent", 20.0)],
            stored_at=fixed_now,
        ),
    )

    day_one_file = (
        tmp_path
        / f"metrics_{datetime(2026, 9, 16, tzinfo=UTC).strftime('%Y%m%d')}.json"
    )
    day_two_file = (
        tmp_path
        / f"metrics_{datetime(2026, 9, 17, tzinfo=UTC).strftime('%Y%m%d')}.json"
    )
    assert day_one_file.exists()
    assert day_two_file.exists()
    assert len(day_one_file.read_text().splitlines()) == 1
    assert len(day_two_file.read_text().splitlines()) == 1

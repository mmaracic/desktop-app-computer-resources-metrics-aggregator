"""Unit tests for MetricsService with mocked storage."""

from datetime import datetime
from unittest.mock import MagicMock

from src.metric.model.component_type import ComponentType
from src.metric.model.metric_metadata import MetricMetadata
from src.metric.model.metric_type import MetricType
from src.service.metrics_service import MetricsService


def test_retrieve_metrics_with_mocked_disk_storage_and_no_azure_storage(
    tmp_path,
    monkeypatch,
):
    """Test retrieving metrics with disk storage mocked and Azure storage set to None, verifying filtering."""
    mock_disk_storage = MagicMock()
    mock_disk_storage.list_files.return_value = [
        "daily_metrics_20260918.json",
        "daily_metrics_20260919.json",
        "daily_metrics_20260920.json",
        "daily_metrics_20260921.json",
    ]
    mock_disk_storage.base_path = str(tmp_path)

    # Only the 2026-09-19 file has metrics; others are empty
    def read_file_side_effect(file_name):
        if "20260919" in file_name:
            return (
                '{"stored_at": "2026-09-19T12:00:00", '
                '"metrics": [{"name": "cpu_usage", "value": 50.5}]}\n'
                '{"stored_at": "2026-09-19T23:59:59", '
                '"metrics": [{"name": "cpu_usage", "value": 10.0}]}\n'
                '{"stored_at": "2026-09-20T02:40:59", '
                '"metrics": [{"name": "cpu_usage", "value": 15.0}]}\n'
                '{"stored_at": "2026-09-20T05:59:59", '
                '"metrics": [{"name": "cpu_usage", "value": 20.0}]}\n'
            )
        return ""  # Empty files for other dates

    mock_disk_storage.read_file.side_effect = read_file_side_effect

    # Create mock metric metadata
    mock_metric_metadata = {
        "cpu_usage": MetricMetadata(
            metric_type=MetricType.FLOAT,
            alias="CPU Usage",
            description="CPU usage percentage",
            component_type=ComponentType.CPU,
            warning_threshold=0.0,
            critical_threshold=100.0,
        )
    }

    # Filename-based date parsing is timezone-aware; keep it naive here so it can be
    # compared against the naive stored_at datetimes used for the actual metric filtering.
    monkeypatch.setattr(
        "src.service.metrics_service.UtilsService.parse_datetime_from_filename",
        lambda file_name, base_file_name: datetime(2026, 9, 19, 1, 30, 0),
    )

    service = MetricsService(None, mock_disk_storage, "daily_metrics")

    start_datetime = datetime(2026, 9, 19, 3, 0, 0)
    end_datetime = datetime(2026, 9, 20, 3, 0, 0)

    result = service.retrieve_metrics_by_datetime_range(
        mock_metric_metadata, start_datetime, end_datetime
    )

    mock_disk_storage.list_files.assert_called_once()
    # read_file is called for each file in list_files(), so we just verify it was called
    assert mock_disk_storage.read_file.call_count == 4

    # Only the two metrics within the range should be returned, the one after end_datetime is excluded
    assert len(result) == 3
    assert result[0].metrics[0].value == 50.5
    assert result[1].metrics[0].value == 10.0
    assert result[2].metrics[0].value == 15.0

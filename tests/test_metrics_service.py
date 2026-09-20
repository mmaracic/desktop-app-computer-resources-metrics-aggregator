"""Unit tests for MetricsService with mocked storage."""

from datetime import datetime
from unittest.mock import MagicMock

from src.service.metrics_service import MetricsService


def test_retrieve_metrics_with_mocked_disk_storage_and_no_azure_storage(
    tmp_path, monkeypatch,
):
    """Test retrieving metrics with disk storage mocked and Azure storage set to None, verifying filtering."""
    # File content has two metrics inside the range and one outside it
    metadata = (
        '{"metric_type": 2, "alias": "CPU Usage", '
        '"description": "CPU usage percentage", "component_type": "cpu"}'
    )
    file_content = (
        f'{{"stored_at": "2026-09-19T12:00:00", '
        f'"metrics": [{{"name": "cpu_usage", "value": 50.5, "metadata": {metadata}}}]}}\n'
        f'{{"stored_at": "2026-09-19T23:59:59", '
        f'"metrics": [{{"name": "cpu_usage", "value": 10.0, "metadata": {metadata}}}]}}\n'
        f'{{"stored_at": "2026-09-20T00:00:01", '
        f'"metrics": [{{"name": "cpu_usage", "value": 99.9, "metadata": {metadata}}}]}}\n'
    )

    mock_disk_storage = MagicMock()
    mock_disk_storage.list_files.return_value = ["daily_metrics_20260919.json"]
    mock_disk_storage.base_path = str(tmp_path)
    mock_disk_storage.read_file.return_value = file_content

    # Filename-based date parsing is timezone-aware; keep it naive here so it can be
    # compared against the naive stored_at datetimes used for the actual metric filtering.
    monkeypatch.setattr(
        "src.service.metrics_service.UtilsService.parse_datetime_from_filename",
        lambda file_name, base_file_name: datetime(2026, 9, 19),
    )

    service = MetricsService(None, mock_disk_storage, "daily_metrics")

    start_datetime = datetime(2026, 9, 19, 0, 0, 0)
    end_datetime = datetime(2026, 9, 19, 23, 59, 59)

    result = service.retrieve_metrics_by_datetime_range(start_datetime, end_datetime)

    mock_disk_storage.list_files.assert_called_once()
    mock_disk_storage.read_file.assert_called_once()

    # Only the two metrics within the range should be returned, the one after end_datetime is excluded
    assert len(result) == 2
    assert result[0].metrics[0].value == 50.5
    assert result[1].metrics[0].value == 10.0

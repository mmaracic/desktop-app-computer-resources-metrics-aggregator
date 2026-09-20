"""Unit tests for the /metrics/range API endpoint with mocked storage."""

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.api import router
from src.service.metrics_service import MetricsService


def test_get_metrics_by_datetime_range_with_mocked_disk_storage_and_no_azure_storage(
    tmp_path,
):
    """Test the /metrics/range endpoint with disk storage mocked and Azure storage set to None, verifying filtering."""
    # File content has two metrics inside the range and one outside it
    metadata = (
        '{"metric_type": 2, "alias": "CPU Usage", '
        '"description": "CPU usage percentage", "component_type": "cpu"}'
    )
    file_content = (
        f'{{"stored_at": "2026-09-19T12:00:00+00:00", '
        f'"metrics": [{{"name": "cpu_usage", "value": 50.5, "metadata": {metadata}}}]}}\n'
        f'{{"stored_at": "2026-09-19T23:59:59+00:00", '
        f'"metrics": [{{"name": "cpu_usage", "value": 10.0, "metadata": {metadata}}}]}}\n'
        f'{{"stored_at": "2026-09-20T00:00:01+00:00", '
        f'"metrics": [{{"name": "cpu_usage", "value": 99.9, "metadata": {metadata}}}]}}\n'
    )

    mock_disk_storage = MagicMock()
    mock_disk_storage.list_files.return_value = ["daily_metrics_20260919.json"]
    mock_disk_storage.base_path = str(tmp_path)
    mock_disk_storage.read_file.return_value = file_content

    metrics_service = MetricsService(None, mock_disk_storage, "daily_metrics")

    app = FastAPI()
    app.include_router(router)
    app.state.metrics_service = metrics_service
    client = TestClient(app)

    response = client.get(
        "/metrics/range",
        params={
            "start_datetime": "2026-09-19T00:00:00.000000+00:00",
            "end_datetime": "2026-09-19T23:59:59.000000+00:00",
            "container_name": None,
        },
    )

    assert response.status_code == 200
    result = response.json()

    mock_disk_storage.list_files.assert_called_once()
    mock_disk_storage.read_file.assert_called_once()

    # Only the two metrics within the range should be returned, the one after end_datetime is excluded
    assert len(result) == 2
    assert result[0]["metrics"][0]["value"] == 50.5
    assert result[1]["metrics"][0]["value"] == 10.0

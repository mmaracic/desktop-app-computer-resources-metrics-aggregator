"""Unit tests for the /metrics/range API endpoint with mocked storage."""

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.api import router
from src.config.metric_config import MetricConfig
from src.metric.model.component_type import ComponentType
from src.metric.model.metric_metadata import MetricMetadata
from src.metric.model.metric_type import MetricType
from src.service.metrics_service import MetricsService


def test_get_metrics_by_datetime_range_with_mocked_disk_storage_and_no_azure_storage(
    tmp_path,
):
    """Test the /metrics/range endpoint with disk storage mocked and Azure storage set to None, verifying filtering."""
    # File content has two metrics inside the range and one outside it
    file_content = (
        '{"stored_at": "2026-09-19T12:00:00+00:00", '
        '"metrics": [{"name": "cpu_usage", "value": 50.5}]}\n'
        '{"stored_at": "2026-09-19T23:59:59+00:00", '
        '"metrics": [{"name": "cpu_usage", "value": 10.0}]}\n'
        '{"stored_at": "2026-09-20T00:00:01+00:00", '
        '"metrics": [{"name": "cpu_usage", "value": 99.9}]}\n'
    )

    mock_disk_storage = MagicMock()
    mock_disk_storage.list_files.return_value = ["daily_metrics_20260919.json"]
    mock_disk_storage.base_path = str(tmp_path)
    mock_disk_storage.read_file.return_value = file_content

    metrics_service = MetricsService(None, mock_disk_storage, "daily_metrics")

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

    app = FastAPI()
    app.include_router(router)
    app.state.metrics_service = metrics_service
    app.state.metric_metadata = mock_metric_metadata
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


def test_get_metric_configs_success_with_configs() -> None:
    """Test GET /metrics/config returns configs when reader/writer has data."""
    # Create a mock config reader/writer
    mock_reader_writer = MagicMock()

    # Mock configs to return (as dicts for JSON serialization)
    mock_configs = [
        {"name": "gpu_utilization", "enabled": True, "order": 1, "color": "#00ff00"},
        {"name": "cpu_temperature", "enabled": False, "order": 2, "color": "#ff0000"},
    ]
    mock_reader_writer.read_configs.return_value = mock_configs

    app = FastAPI()
    app.include_router(router)
    app.state.config_reader_writer = mock_reader_writer
    client = TestClient(app)

    response = client.get("/metrics/config")

    assert response.status_code == 200
    result = response.json()

    # Verify the reader/writer was called
    mock_reader_writer.read_configs.assert_called_once()

    # Verify the response contains the configs
    assert len(result) == 2
    assert result[0]["name"] == "gpu_utilization"
    assert result[1]["name"] == "cpu_temperature"


def test_get_metric_configs_success_with_empty_list() -> None:
    """Test GET /metrics/config returns empty list when reader/writer has no data."""
    # Create a mock config reader/writer that returns empty list
    mock_reader_writer = MagicMock()
    mock_reader_writer.read_configs.return_value = []

    app = FastAPI()
    app.include_router(router)
    app.state.config_reader_writer = mock_reader_writer
    client = TestClient(app)

    response = client.get("/metrics/config")

    assert response.status_code == 200
    result = response.json()

    # Verify empty list is returned
    assert len(result) == 0

    # Verify the reader/writer was called
    mock_reader_writer.read_configs.assert_called_once()


def test_store_metric_configs_success() -> None:
    """Test POST /metrics/config successfully stores configs."""
    # Create a mock config reader/writer
    mock_reader_writer = MagicMock()

    # Configs to store (as dicts for JSON serialization - API will convert to MetricConfig)
    configs_to_store = [
        {"name": "gpu_utilization", "enabled": True, "order": 1, "color": "#00ff00"},
        {"name": "cpu_temperature", "enabled": False, "order": 2, "color": "#ff0000"},
    ]

    app = FastAPI()
    app.include_router(router)
    app.state.config_reader_writer = mock_reader_writer
    client = TestClient(app)

    response = client.post(
        "/metrics/config",
        json=configs_to_store,
    )

    assert response.status_code == 200

    # Verify the reader/writer was called with MetricConfig objects (API converts dicts to objects)
    expected_configs = [
        MetricConfig(name="gpu_utilization", enabled=True, order=1, color="#00ff00"),
        MetricConfig(name="cpu_temperature", enabled=False, order=2, color="#ff0000"),
    ]
    mock_reader_writer.write_configs.assert_called_once_with(expected_configs)


def test_store_metric_configs_empty_body() -> None:
    """Test POST /metrics/config returns 400 when body is empty."""
    # Create a mock config reader/writer (won't be called due to validation)
    mock_reader_writer = MagicMock()

    app = FastAPI()
    app.include_router(router)
    app.state.config_reader_writer = mock_reader_writer
    client = TestClient(app)

    response = client.post(
        "/metrics/config",
        json=[],  # Empty list
    )

    assert response.status_code == 400

    # Verify the reader/writer was NOT called (validation failed first)
    mock_reader_writer.write_configs.assert_not_called()


def test_get_metric_metadata_success() -> None:
    """Test GET /metrics/metadata returns all registered metric metadata."""
    # Create mock metric metadata
    mock_metric_metadata = {
        "cpu_usage": MetricMetadata(
            metric_type=MetricType.FLOAT,
            alias="CPU Usage",
            description="CPU usage percentage",
            component_type=ComponentType.CPU,
            warning_threshold=0.8,
            critical_threshold=0.95,
        ),
        "gpu_temperature": MetricMetadata(
            metric_type=MetricType.FLOAT,
            alias="GPU Temperature",
            description="GPU temperature in Celsius",
            component_type=ComponentType.GPU,
            warning_threshold=75.0,
            critical_threshold=85.0,
        ),
    }

    app = FastAPI()
    app.include_router(router)
    app.state.metric_metadata = mock_metric_metadata
    client = TestClient(app)

    response = client.get("/metrics/metadata")

    assert response.status_code == 200
    result = response.json()

    # Verify the response is a list of dictionaries (Pydantic models are serialized)
    assert isinstance(result, list)
    assert len(result) == 2

    # Verify CPU usage metadata - use alias since MetricMetadata doesn't have a name field
    cpu_metadata = None
    for item in result:
        if isinstance(item, dict):
            if item.get("alias") == "CPU Usage":
                cpu_metadata = item
                break
        else:
            # If it's an object, check its attributes
            if hasattr(item, "alias") and item.alias == "CPU Usage":
                cpu_metadata = (
                    item.model_dump() if hasattr(item, "model_dump") else dict(item)
                )
                break

    assert cpu_metadata is not None, "CPU usage metadata not found in response"
    assert cpu_metadata["metric_type"] == "FLOAT"
    assert cpu_metadata["alias"] == "CPU Usage"
    assert cpu_metadata["description"] == "CPU usage percentage"
    assert cpu_metadata["component_type"] == "CPU"
    assert cpu_metadata["warning_threshold"] == 0.8
    assert cpu_metadata["critical_threshold"] == 0.95

    # Verify GPU temperature metadata - use alias since MetricMetadata doesn't have a name field
    gpu_metadata = None
    for item in result:
        if isinstance(item, dict):
            if item.get("alias") == "GPU Temperature":
                gpu_metadata = item
                break
        else:
            if hasattr(item, "alias") and item.alias == "GPU Temperature":
                gpu_metadata = (
                    item.model_dump() if hasattr(item, "model_dump") else dict(item)
                )
                break

    assert gpu_metadata is not None, "GPU temperature metadata not found in response"
    assert gpu_metadata["metric_type"] == "FLOAT"
    assert gpu_metadata["alias"] == "GPU Temperature"
    assert gpu_metadata["description"] == "GPU temperature in Celsius"
    assert gpu_metadata["component_type"] == "GPU"
    assert gpu_metadata["warning_threshold"] == 75.0
    assert gpu_metadata["critical_threshold"] == 85.0


def test_get_metric_metadata_empty() -> None:
    """Test GET /metrics/metadata returns empty list when no metadata registered."""
    app = FastAPI()
    app.include_router(router)
    app.state.metric_metadata = {}
    client = TestClient(app)

    response = client.get("/metrics/metadata")

    assert response.status_code == 200
    result = response.json()

    # Verify empty list is returned
    assert isinstance(result, list)
    assert len(result) == 0


def test_get_metric_metadata_consistency_with_metrics_data() -> None:
    """Test that metadata endpoint returns consistent data structure for metrics."""
    # Create mock metric metadata matching the MetricMetadata model
    mock_metric_metadata = {
        "cpu_usage": MetricMetadata(
            metric_type=MetricType.FLOAT,
            alias="CPU Usage",
            description="CPU usage percentage",
            component_type=ComponentType.CPU,
            warning_threshold=0.8,
            critical_threshold=0.95,
        ),
    }

    app = FastAPI()
    app.include_router(router)
    app.state.metric_metadata = mock_metric_metadata
    client = TestClient(app)

    response = client.get("/metrics/metadata")

    assert response.status_code == 200
    result = response.json()

    # Verify the response structure matches what frontend expects (MetricMetadata fields)
    assert len(result) == 1
    assert "metric_type" in result[0]
    assert "alias" in result[0]
    assert "description" in result[0]
    assert "component_type" in result[0]
    assert "warning_threshold" in result[0]
    assert "critical_threshold" in result[0]

    # Verify all required fields are present and have correct types
    metadata = result[0]
    assert isinstance(metadata["metric_type"], str)
    assert isinstance(metadata["alias"], str)
    assert isinstance(metadata["description"], str)
    assert isinstance(metadata["component_type"], str)
    assert isinstance(metadata["warning_threshold"], (int, float))
    assert isinstance(metadata["critical_threshold"], (int, float))

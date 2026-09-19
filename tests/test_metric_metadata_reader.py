"""Unit tests for MetricMetadataReader."""

import json
from pathlib import Path

from src.config.metadata_reader import MetadataReader
from src.metric.model.component_type import ComponentType
from src.metric.model.metric_metadata import MetricMetadata
from src.metric.model.metric_type import MetricType


def _write_metadata_file(path: Path, content: dict) -> Path:
    file_path = path / "metric_metadata.json"
    file_path.write_text(json.dumps(content))
    return file_path


def test_read_returns_dict_keyed_by_metric_name(tmp_path: Path) -> None:
    file_path = _write_metadata_file(
        tmp_path,
        {
            "cpu_usage_percent": {
                "metric_type": "FLOAT",
                "alias": "Overall CPU utilization percentage",
                "description": "Shows how much CPU capacity is currently being used",
                "component_type": "CPU",
                "warning_threshold": 80.0,
                "critical_threshold": 90.0,
            },
        },
    )

    result = MetadataReader(file_path).read()

    assert list(result.keys()) == ["cpu_usage_percent"]
    metadata = result["cpu_usage_percent"]
    assert isinstance(metadata, MetricMetadata)
    assert metadata.metric_type == MetricType.FLOAT
    assert metadata.warning_threshold == 80.0
    assert metadata.critical_threshold == 90.0
    assert metadata.alias == "Overall CPU utilization percentage"
    assert metadata.component_type == ComponentType.CPU


def test_read_handles_missing_warning_critical_values(tmp_path: Path) -> None:
    file_path = _write_metadata_file(
        tmp_path,
        {
            "temperature_acpitz": {
                "metric_type": "FLOAT",
                "alias": "System temperature",
                "description": "Temperature reading from acpitz sensor",
                "component_type": "MOTHERBOARD",
                "warning_threshold": None,
                "critical_threshold": None,
            }
        },
    )

    result = MetadataReader(file_path).read()

    metadata = result["temperature_acpitz"]
    assert metadata.warning_threshold is None
    assert metadata.critical_threshold is None


def test_read_returns_entry_per_metric(tmp_path: Path) -> None:
    file_path = _write_metadata_file(
        tmp_path,
        {
            "gpu_busy_percent": {
                "metric_type": "FLOAT",
                "alias": "GPU utilization percentage",
                "description": "Shows how much the GPU is actively processing",
                "component_type": "GPU",
                "warning_threshold": 80.0,
                "critical_threshold": 90.0,
            },
            "network_bytes_sent": {
                "metric_type": "INTEGER",
                "alias": "Total network bytes transmitted",
                "description": "Cumulative count of data sent",
                "component_type": "NETWORK",
                "warning_threshold": None,
                "critical_threshold": None,
            },
        },
    )

    result = MetadataReader(file_path).read()

    assert len(result) == 2
    assert result["gpu_busy_percent"].component_type == ComponentType.GPU
    assert result["network_bytes_sent"].metric_type == MetricType.INTEGER


def test_read_real_metric_metadata_file() -> None:
    real_file = Path(__file__).resolve().parent.parent / "metadata" / "metric_metadata.json"

    result = MetadataReader(real_file).read()

    assert len(result) > 0
    assert all(isinstance(metadata, MetricMetadata) for metadata in result.values())

import json

import pytest

from src.config.metadata_reader import MetadataReader
from src.metric.model.metric_metadata import MetricMetadata
from src.providers.ati_gpu_provider import AtiGpuProvider
from src.providers.resource_utilization_provider import ResourceUtilizationProvider
from src.providers.temperature_provider import TemperatureProvider


def test_all_metrics_output() -> None:
    # Metadata
    metadata_map: dict[str, MetricMetadata] = {}
    metadata_map.update(
        MetadataReader(file_path="metadata/temperature_metadata.json").read(),
    )
    metadata_map.update(MetadataReader(file_path="metadata/fan_metadata.json").read())
    metadata_map.update(
        MetadataReader(file_path="metadata/metric_metadata.json").read(),
    )

    # Initialize providers
    temp_provider = TemperatureProvider()
    resource_provider = ResourceUtilizationProvider()
    ati_gpu_provider = AtiGpuProvider()

    # Collect all metrics with aliases as keys
    all_metrics = {}

    # Update dictionary with metrics from each provider using aliases
    for metric in temp_provider.get_metrics(metadata_map):
        all_metrics[metric.get_alias()] = metric.value

    for metric in resource_provider.get_metrics(metadata_map):
        all_metrics[metric.get_alias()] = metric.value

    for metric in ati_gpu_provider.get_metrics(metadata_map):
        all_metrics[metric.get_alias()] = metric.value

    # Sort metrics alphabetically by key
    sorted_metrics = dict(sorted(all_metrics.items()))

    # Convert to JSON string
    json_output = json.dumps(sorted_metrics, indent=4)
    print(json_output)

    # Assert that the output is a valid JSON string and contains expected aliases
    assert json_output.startswith("{")
    assert json_output.endswith("}")

    # Check for basic resource metrics using aliases (short format, max 80 chars)
    assert "Overall CPU utilization percentage" in sorted_metrics
    assert "System RAM utilization percentage" in sorted_metrics
    assert "Root filesystem disk usage percentage" in sorted_metrics

    # Check for detailed resource metrics that should be present (short format)
    assert "Current CPU operating frequency in MHz" in sorted_metrics
    assert "Available system memory in MB" in sorted_metrics
    assert "Total network bytes transmitted" in sorted_metrics
    assert "Total network bytes received" in sorted_metrics

    # Check for temperature metrics using aliases
    temp_aliases = [
        alias for alias in sorted_metrics if "temperature" in alias.lower()
    ]
    assert len(temp_aliases) > 0, "Expected at least one temperature metric"

    # Check for fan speed metrics using aliases
    fan_aliases = [
        alias for alias in sorted_metrics if "fan speed" in alias.lower()
    ]
    assert len(fan_aliases) > 0, "Expected at least one fan speed metric"

import pytest

from src.config.metadata_reader import MetadataReader
from src.metric.model.metric import Metric
from src.metric.model.metric_metadata import MetricMetadata
from src.providers.ati_gpu_provider import AtiGpuProvider
from src.providers.resource_utilization_provider import ResourceUtilizationProvider
from src.providers.temperature_provider import TemperatureProvider


def test_temperature_provider_metrics() -> None:
    provider = TemperatureProvider()
    metrics = provider.get_metrics(get_metadata_map())
    assert isinstance(metrics, list)
    assert len(metrics) > 0
    assert all(isinstance(m, Metric) for m in metrics)


def test_resource_utilization_provider_metrics() -> None:
    provider = ResourceUtilizationProvider()
    metrics = provider.get_metrics(get_metadata_map())
    assert isinstance(metrics, list)
    assert len(metrics) > 0

    # Check that metrics have aliases using get_alias() method
    aliases = [m.get_alias() for m in metrics]

    # Verify basic resource metrics exist with proper aliases (short format, max 80 chars)
    assert any("Overall CPU utilization percentage" in alias for alias in aliases)
    assert any("System RAM utilization percentage" in alias for alias in aliases)
    assert any("Root filesystem disk usage percentage" in alias for alias in aliases)

    # Verify detailed metrics are present (short format)
    assert any("Current CPU operating frequency" in alias for alias in aliases)
    assert any("Available system memory" in alias for alias in aliases)
    assert any("Total network bytes transmitted" in alias for alias in aliases)
    assert any("Total disk read operations" in alias for alias in aliases)


def test_ati_gpu_provider_metrics() -> None:
    provider = AtiGpuProvider()
    metrics = provider.get_metrics(get_metadata_map())
    assert isinstance(metrics, list)
    assert len(metrics) > 0
    assert all(isinstance(m, Metric) for m in metrics)

    # Verify GPU metrics have proper aliases
    aliases = [m.get_alias() for m in metrics]
    gpu_aliases = [alias for alias in aliases if "GPU" in alias]
    assert len(gpu_aliases) > 0, "Expected at least one GPU metric with alias"


def get_metadata_map() -> dict[str, MetricMetadata]:
    # Metadata
    metadata_map: dict[str, MetricMetadata] = {}
    metadata_map.update(
        MetadataReader(file_path="metadata/temperature_metadata.json").read(),
    )
    metadata_map.update(MetadataReader(file_path="metadata/fan_metadata.json").read())
    metadata_map.update(
        MetadataReader(file_path="metadata/metric_metadata.json").read(),
    )
    return metadata_map

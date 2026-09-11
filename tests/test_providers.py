import pytest
from src.providers.temperature_provider import TemperatureProvider
from src.providers.resource_utilization_provider import ResourceUtilizationProvider
from src.providers.ati_gpu_provider import AtiGpuProvider
from src.metric.model.metric import Metric

def test_temperature_provider_metrics():
    provider = TemperatureProvider()
    metrics = provider.get_metrics()
    assert isinstance(metrics, list)
    assert len(metrics) > 0
    assert all(isinstance(m, Metric) for m in metrics)

def test_resource_utilization_provider_metrics():
    provider = ResourceUtilizationProvider()
    metrics = provider.get_metrics()
    assert isinstance(metrics, list)
    assert len(metrics) > 0
    assert any(m._name == "cpu_usage_percent" for m in metrics)
    assert any(m._name == "memory_usage_percent" for m in metrics)
    assert any(m._name == "disk_usage_percent" for m in metrics)

def test_ati_gpu_provider_metrics():
    provider = AtiGpuProvider()
    metrics = provider.get_metrics()
    assert isinstance(metrics, list)
    assert len(metrics) > 0
    assert all(isinstance(m, Metric) for m in metrics)


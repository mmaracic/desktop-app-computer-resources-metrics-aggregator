import json

import pytest

from src.providers.ati_gpu_provider import AtiGpuProvider
from src.providers.resource_utilization_provider import ResourceUtilizationProvider
from src.providers.temperature_provider import TemperatureProvider


def test_all_metrics_output():
    # Initialize providers
    temp_provider = TemperatureProvider()
    resource_provider = ResourceUtilizationProvider()
    ati_gpu_provider = AtiGpuProvider()

    # Collect all metrics
    all_metrics = {}
    
    # Update dictionary with metrics from each provider
    for metric in temp_provider.get_metrics():
        all_metrics[metric._name] = metric._value
        
    for metric in resource_provider.get_metrics():
        all_metrics[metric._name] = metric._value
        
    for metric in ati_gpu_provider.get_metrics():
        all_metrics[metric._name] = metric._value

    # Sort metrics alphabetically by key
    sorted_metrics = dict(sorted(all_metrics.items()))

    # Convert to JSON string
    json_output = json.dumps(sorted_metrics, indent=4)
    print(json_output)
    
    # Assert that the output is a valid JSON string and contains expected keys
    assert json_output.startswith('{')
    assert json_output.endswith('}')
    assert "cpu_usage_percent" in sorted_metrics
    assert "memory_usage_percent" in sorted_metrics
    assert "disk_usage_percent" in sorted_metrics


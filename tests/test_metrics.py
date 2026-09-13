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

    # Collect all metrics with aliases as keys
    all_metrics = {}
    
    # Update dictionary with metrics from each provider using aliases
    for metric in temp_provider.get_metrics():
        all_metrics[metric.get_alias()] = metric._value
        
    for metric in resource_provider.get_metrics():
        all_metrics[metric.get_alias()] = metric._value
        
    for metric in ati_gpu_provider.get_metrics():
        all_metrics[metric.get_alias()] = metric._value

    # Sort metrics alphabetically by key
    sorted_metrics = dict(sorted(all_metrics.items()))

    # Convert to JSON string
    json_output = json.dumps(sorted_metrics, indent=4)
    print(json_output)
    
    # Assert that the output is a valid JSON string and contains expected aliases
    assert json_output.startswith('{')
    assert json_output.endswith('}')
    
    # Check for basic resource metrics using aliases
    assert "Overall CPU utilization percentage across all processors - shows how much CPU capacity is currently being used" in sorted_metrics
    assert "System RAM utilization percentage - indicates how much of the available memory is currently in use" in sorted_metrics
    assert "Root filesystem disk usage percentage - shows how much of the system drive is occupied with data and applications" in sorted_metrics
    
    # Check for detailed resource metrics that should be present
    assert "Current CPU operating frequency in megahertz - indicates the actual speed at which the processor is running" in sorted_metrics
    assert "Available system memory in megabytes - shows how much RAM is currently free for new applications and processes" in sorted_metrics
    assert "Total network bytes transmitted - cumulative count of data sent out through all network interfaces" in sorted_metrics
    assert "Total network bytes received - cumulative count of data received through all network interfaces" in sorted_metrics
    
    # Check for temperature metrics using aliases
    temp_aliases = [alias for alias in sorted_metrics.keys() if "temperature" in alias.lower()]
    assert len(temp_aliases) > 0, "Expected at least one temperature metric"
    
    # Check for fan speed metrics using aliases
    fan_aliases = [alias for alias in sorted_metrics.keys() if "fan speed" in alias.lower()]
    assert len(fan_aliases) > 0, "Expected at least one fan speed metric"


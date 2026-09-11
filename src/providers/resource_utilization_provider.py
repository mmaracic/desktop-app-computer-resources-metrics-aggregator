import psutil

from src.metric.metric_provider import MetricProvider
from src.metric.model.metric import Metric
from src.metric.model.metric_type import MetricType


class ResourceUtilizationProvider(MetricProvider):
    """
    Provider for system resource utilization using psutil.
    """

    def get_metrics(self) -> list[Metric]:
        metrics = []
        
        # CPU Usage
        cpu_usage = psutil.cpu_percent(interval=1)
        metrics.append(Metric(
            name="cpu_usage_percent",
            type=MetricType.FLOAT,
            value=cpu_usage
        ))
        
        # Memory Usage
        mem = psutil.virtual_memory()
        metrics.append(Metric(
            name="memory_usage_percent",
            type=MetricType.FLOAT,
            value=mem.percent
        ))
        
        # Disk Usage
        disk = psutil.disk_usage('/')
        metrics.append(Metric(
            name="disk_usage_percent",
            type=MetricType.FLOAT,
            value=disk.percent
        ))
        
        return metrics

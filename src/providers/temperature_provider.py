import psutil

from src.metric.metric_provider import MetricProvider
from src.metric.model.metric import Metric
from src.metric.model.metric_type import MetricType


class TemperatureProvider(MetricProvider):
    """
    Provider for system temperatures and fan speeds using psutil.
    """

    def get_metrics(self) -> list[Metric]:
        metrics = []
        
        # Temperatures
        sensors = psutil.sensors_temperatures()
        for name, temps in sensors.items():
            for temp in temps:
                metrics.append(Metric(
                    name=f"temperature_{name}",
                    type=MetricType.FLOAT,
                    value=temp.current
                ))
        
        # Fan Speeds
        fans = psutil.sensors_fans()
        for name, fans_list in fans.items():
            for fan in fans_list:
                metrics.append(Metric(
                    name=f"fan_speed_{name}",
                    type=MetricType.INTEGER,
                    value=fan.current
                ))
                
        return metrics

import psutil

from src.metric.metric_provider import MetricProvider
from src.metric.model.metric import Metric
from src.metric.model.metric_metadata import MetricMetadata


class TemperatureProvider(MetricProvider):
    """Provider for system temperatures and fan speeds using psutil."""

    def get_metrics(self, metadata: dict[str, MetricMetadata]) -> list[Metric]:
        metrics = []

        # Temperatures
        sensors = psutil.sensors_temperatures()
        for name, temps in sensors.items():
            for temp in temps:
                metrics.extend(
                    [
                        self.createMetric(
                            name=f"temperature_{name}",
                            value=temp.current,
                            metadata=metadata,
                        ),
                    ]
                )

        # Fan Speeds
        fans = psutil.sensors_fans()
        for name, fans_list in fans.items():
            for fan in fans_list:
                metrics.extend(
                    [
                        self.createMetric(
                            name=f"fan_speed_{name}",
                            value=fan.current,
                            metadata=metadata,
                        )
                    ]
                )

        return metrics

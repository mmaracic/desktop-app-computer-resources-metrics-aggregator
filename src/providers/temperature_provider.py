import re

import psutil

from src.metric.metric_provider import MetricProvider
from src.metric.model.metric import Metric
from src.metric.model.metric_metadata import MetricMetadata

# amdgpu readings are reported per card by AtiGpuProvider
_SKIPPED_CHIPS = {"amdgpu"}


class TemperatureProvider(MetricProvider):
    """Provider for system temperatures and fan speeds using psutil."""

    def get_metrics(self, metadata: dict[str, MetricMetadata]) -> list[Metric]:
        metrics: list[Metric] = []

        for chip, temps in psutil.sensors_temperatures().items():
            if chip in _SKIPPED_CHIPS:
                continue
            for index, temp in enumerate(temps, 1):
                metrics.append(
                    self.createMetric(
                        name=self._sensor_name(
                            "temperature", chip, temp.label, index, len(temps)
                        ),
                        value=temp.current,
                        metadata=metadata,
                    ),
                )

        for chip, fans in psutil.sensors_fans().items():
            if chip in _SKIPPED_CHIPS:
                continue
            for index, fan in enumerate(fans, 1):
                metrics.append(
                    self.createMetric(
                        name=self._sensor_name(
                            "fan_speed", chip, fan.label, index, len(fans)
                        ),
                        value=fan.current,
                        metadata=metadata,
                    ),
                )

        return metrics

    @staticmethod
    def _sensor_name(prefix: str, chip: str, label: str, index: int, count: int) -> str:
        # Chips with several sensors need a per-sensor suffix to avoid name collisions
        if count == 1:
            return f"{prefix}_{chip}"
        suffix = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") or str(index)
        return f"{prefix}_{chip}_{suffix}"

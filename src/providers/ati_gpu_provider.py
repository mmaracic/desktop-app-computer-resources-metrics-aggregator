#!/usr/bin/env python3
from pathlib import Path

from src.metric.metric_provider import MetricProvider
from src.metric.model.metric import Metric
from src.metric.model.metric_metadata import MetricMetadata


class AtiGpuProvider(MetricProvider):
    """Provider for ATI/AMD Radeon GPU metrics using sysfs.

    Supports both standalone and integrated GPUs.
    """

    def __init__(self) -> None:
        self.cards = ["card0", "card1"]

    def get_metrics(self, metadata: dict[str, MetricMetadata]) -> list[Metric]:
        metrics = []
        for card in self.cards:
            path = f"/sys/class/drm/{card}/device"
            if not Path(path).exists():
                continue

            # GPU Busy Percentage - already covered, skip
            metrics.append(
                self.createMetric(
                    name=f"{card}_gpu_busy_percent",
                    value=float(self._read_sysfs(path, "gpu_busy_percent")),
                    metadata=metadata,
                )
            )

            # VRAM metrics - already covered by TemperatureProvider's broader sensor approach, skip to avoid duplication

            # GTT (Graphics Translation Table) memory - unique to GPU, not duplicated elsewhere
            gtt_total = self._read_sysfs(path, "mem_info_gtt_total")
            gtt_used = self._read_sysfs(path, "mem_info_gtt_used")
            if gtt_total > 0:
                metrics.append(
                    self.createMetric(
                        name=f"{card}_gtt_utilization_percent",
                        value=float(gtt_used) / float(gtt_total) * 100.0,
                        metadata=metadata,
                    )
                )

            # GPU Clock Frequency - unique metric not covered by other providers
            try:
                freq_path = f"{path}/hwmon/hwmon5/freq1_input"
                if Path(freq_path).exists():
                    with open(freq_path, "r", encoding="utf-8") as f:
                        freq_mhz = int(f.read().strip())
                    metrics.append(
                        self.createMetric(
                            name=f"{card}_gpu_clock_mhz",
                            value=freq_mhz,
                            metadata=metadata,
                        )
                    )
            except (ValueError, OSError):
                pass

            # GPU Power Consumption - unique metric not covered by other providers
            try:
                power_path = f"{path}/hwmon/hwmon5/power1_input"
                if Path(power_path).exists():
                    with open(power_path, "r", encoding="utf-8") as f:
                        power_milliwatts = int(f.read().strip())
                    metrics.append(
                        self.createMetric(
                            name=f"{card}_gpu_power_milliwatts",
                            value=power_milliwatts,
                            metadata=metadata,
                        )
                    )
            except (ValueError, OSError):
                pass

            # GPU Memory Clock Frequency - unique metric for memory subsystem
            try:
                mem_freq_path = f"{path}/hwmon/hwmon5/freq2_input"
                if Path(mem_freq_path).exists():
                    with open(mem_freq_path, "r", encoding="utf-8") as f:
                        mem_freq_mhz = int(f.read().strip())
                    metrics.append(
                        self.createMetric(
                            name=f"{card}_gpu_memory_clock_mhz",
                            value=mem_freq_mhz,
                            metadata=metadata,
                        )
                    )
            except (ValueError, OSError):
                pass

        return metrics

    def _read_sysfs(self, path: str, filename: str) -> int:
        full_path = Path(path) / filename
        if full_path.exists():
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    return int(f.read().strip())
            except (ValueError, OSError):
                return 0
        return 0

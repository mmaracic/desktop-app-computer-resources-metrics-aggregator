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
                ),
            )

            vram_total = self._read_sysfs(path, "mem_info_vram_total")
            vram_used = self._read_sysfs(path, "mem_info_vram_used")
            if vram_total > 0:
                metrics.append(
                    self.createMetric(
                        name=f"{card}_vram_utilization_percent",
                        value=float(vram_used) / float(vram_total) * 100.0,
                        metadata=metadata,
                    ),
                )

            hwmon = self._find_hwmon(path)
            temp = self._read_hwmon(hwmon, ["temp2_input", "temp1_input"])
            if temp is not None:
                metrics.append(
                    self.createMetric(
                        name=f"{card}_gpu_temperature_celsius",
                        value=temp / 1000.0,
                        metadata=metadata,
                    ),
                )

            # GTT (Graphics Translation Table) memory - unique to GPU, not duplicated elsewhere
            gtt_total = self._read_sysfs(path, "mem_info_gtt_total")
            gtt_used = self._read_sysfs(path, "mem_info_gtt_used")
            if gtt_total > 0:
                metrics.append(
                    self.createMetric(
                        name=f"{card}_gtt_utilization_percent",
                        value=float(gtt_used) / float(gtt_total) * 100.0,
                        metadata=metadata,
                    ),
                )

            # GPU Clock Frequency - unique metric not covered by other providers
            freq_hz = self._read_hwmon(hwmon, ["freq1_input"])
            if freq_hz is not None:
                metrics.append(
                    self.createMetric(
                        name=f"{card}_gpu_clock_mhz",
                        value=freq_hz // 1_000_000,
                        metadata=metadata,
                    ),
                )

            # GPU Power Consumption - unique metric not covered by other providers
            # hwmon reports microwatts; discrete cards expose power1_average instead of power1_input
            power_uw = self._read_hwmon(hwmon, ["power1_input", "power1_average"])
            if power_uw is not None:
                metrics.append(
                    self.createMetric(
                        name=f"{card}_gpu_power_milliwatts",
                        value=power_uw // 1000,
                        metadata=metadata,
                    ),
                )

            # GPU Memory Clock Frequency - unique metric for memory subsystem
            mem_freq_hz = self._read_hwmon(hwmon, ["freq2_input"])
            if mem_freq_hz is not None:
                metrics.append(
                    self.createMetric(
                        name=f"{card}_gpu_memory_clock_mhz",
                        value=mem_freq_hz // 1_000_000,
                        metadata=metadata,
                    ),
                )

        return metrics

    def _find_hwmon(self, device_path: str) -> Path | None:
        # hwmon index differs per card and boot, so discover it
        hwmons = sorted(Path(device_path, "hwmon").glob("hwmon*"))
        return hwmons[0] if hwmons else None

    def _read_hwmon(self, hwmon: Path | None, filenames: list[str]) -> int | None:
        if hwmon is None:
            return None
        for filename in filenames:
            try:
                return int((hwmon / filename).read_text(encoding="utf-8").strip())
            except (ValueError, OSError):
                continue
        return None

    def _read_sysfs(self, path: str, filename: str) -> int:
        full_path = Path(path) / filename
        if full_path.exists():
            try:
                with open(full_path, encoding="utf-8") as f:
                    return int(f.read().strip())
            except (ValueError, OSError):
                return 0
        return 0

import os

from src.metric.metric_provider import MetricProvider
from src.metric.model.metric import Metric
from src.metric.model.metric_type import MetricType


class AtiGpuProvider(MetricProvider):
    """
    Provider for ATI/AMD Radeon GPU metrics using sysfs.
    Supports both standalone and integrated GPUs.
    """
    def __init__(self):
        self.cards = ["card0", "card1"]

    def get_metrics(self) -> list[Metric]:
        metrics = []
        for card in self.cards:
            path = f"/sys/class/drm/{card}/device"
            if not os.path.exists(path):
                continue
            
            metrics.append(Metric(
                name=f"{card}_gpu_busy_percent",
                type=MetricType.FLOAT,
                value=float(self._read_sysfs(path, "gpu_busy_percent"))
            ))
            metrics.append(Metric(
                name=f"{card}_vram_total",
                type=MetricType.INTEGER,
                value=int(self._read_sysfs(path, "mem_info_vram_total"))
            ))
            metrics.append(Metric(
                name=f"{card}_vram_used",
                type=MetricType.INTEGER,
                value=int(self._read_sysfs(path, "mem_info_vram_used"))
            ))
            
            # GTT metrics might be relevant for integrated GPUs
            metrics.append(Metric(
                name=f"{card}_gtt_total",
                type=MetricType.INTEGER,
                value=int(self._read_sysfs(path, "mem_info_gtt_total"))
            ))
            metrics.append(Metric(
                name=f"{card}_gtt_used",
                type=MetricType.INTEGER,
                value=int(self._read_sysfs(path, "mem_info_gtt_used"))
            ))
            metrics.append(Metric(
                name=f"{card}_vram_used",
                type=MetricType.INTEGER,
                value=int(self._read_sysfs(path, "mem_info_vram_used"))
            ))
            
            # GTT metrics might be relevant for integrated GPUs
            metrics.append(Metric(
                name=f"{card}_gtt_total",
                type=MetricType.INTEGER,
                value=int(self._read_sysfs(path, "mem_info_gtt_total"))
            ))
            metrics.append(Metric(
                name=f"{card}_gtt_used",
                type=MetricType.INTEGER,
                value=int(self._read_sysfs(path, "mem_info_gtt_used"))
            ))
            
        return metrics

    def _read_sysfs(self, path: str, filename: str) -> int:
        full_path = os.path.join(path, filename)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r') as f:
                    return int(f.read().strip())
            except (ValueError, IOError):
                return 0
        return 0

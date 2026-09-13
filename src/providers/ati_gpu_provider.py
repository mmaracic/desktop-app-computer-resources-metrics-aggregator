#!/usr/bin/env python3
import os

from src.metric.model.component_type import ComponentType
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
            
            # GPU Busy Percentage - already covered, skip
            metrics.append(Metric(
                name=f"{card}_gpu_busy_percent",
                metric_type=MetricType.FLOAT,
                value=float(self._read_sysfs(path, "gpu_busy_percent")),
                alias=f"GPU {card} utilization percentage",
                description=f"Shows how much the GPU is actively processing graphics workloads on card {card}",
                component_type=ComponentType.GPU
            ))
            
            # VRAM metrics - already covered by TemperatureProvider's broader sensor approach, skip to avoid duplication
            
            # GTT (Graphics Translation Table) memory - unique to GPU, not duplicated elsewhere
            gtt_total = self._read_sysfs(path, "mem_info_gtt_total")
            gtt_used = self._read_sysfs(path, "mem_info_gtt_used")
            if gtt_total > 0:
                metrics.append(Metric(
                    name=f"{card}_gtt_utilization_percent",
                    metric_type=MetricType.FLOAT,
                    value=float(gtt_used) / float(gtt_total) * 100.0,
                    alias=f"GPU {card} shared graphics memory usage percentage",
                    description=f"Tracks usage of system RAM allocated for GPU operations on card {card}",
                    component_type=ComponentType.GPU
                ))
            
            # GPU Clock Frequency - unique metric not covered by other providers
            try:
                freq_path = f"{path}/hwmon/hwmon5/freq1_input"
                if os.path.exists(freq_path):
                    with open(freq_path, 'r', encoding='utf-8') as f:
                        freq_mhz = int(f.read().strip())
                    metrics.append(Metric(
                        name=f"{card}_gpu_clock_mhz",
                        metric_type=MetricType.INTEGER,
                        value=freq_mhz,
                        alias=f"GPU {card} current clock frequency in MHz",
                        description=f"Indicates the GPU's operating speed for graphics processing on card {card}",
                        component_type=ComponentType.GPU
                    ))
            except (ValueError, OSError):
                pass
            
            # GPU Power Consumption - unique metric not covered by other providers
            try:
                power_path = f"{path}/hwmon/hwmon5/power1_input"
                if os.path.exists(power_path):
                    with open(power_path, 'r', encoding='utf-8') as f:
                        power_milliwatts = int(f.read().strip())
                    metrics.append(Metric(
                        name=f"{card}_gpu_power_milliwatts",
                        metric_type=MetricType.INTEGER,
                        value=power_milliwatts,
                        alias=f"GPU {card} current power consumption in mW",
                        description=f"Shows how much electrical power the GPU is currently using on card {card}",
                        component_type=ComponentType.GPU
                    ))
            except (ValueError, OSError):
                pass
            
            # GPU Memory Clock Frequency - unique metric for memory subsystem
            try:
                mem_freq_path = f"{path}/hwmon/hwmon5/freq2_input"
                if os.path.exists(mem_freq_path):
                    with open(mem_freq_path, 'r', encoding='utf-8') as f:
                        mem_freq_mhz = int(f.read().strip())
                    metrics.append(Metric(
                        name=f"{card}_gpu_memory_clock_mhz",
                        metric_type=MetricType.INTEGER,
                        value=mem_freq_mhz,
                        alias=f"GPU {card} memory clock frequency in MHz",
                        description=f"Indicates the speed of GPU video memory operations on card {card}",
                        component_type=ComponentType.GPU
                    ))
            except (ValueError, OSError):
                pass
            
        return metrics

    def _read_sysfs(self, path: str, filename: str) -> int:
        full_path = os.path.join(path, filename)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    return int(f.read().strip())
            except (ValueError, OSError):
                return 0
        return 0

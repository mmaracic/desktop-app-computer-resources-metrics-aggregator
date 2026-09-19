#!/usr/bin/env python3
import logging

import psutil

from src.metric.metric_provider import MetricProvider
from src.metric.model.metric import Metric
from src.metric.model.metric_metadata import MetricMetadata

logger = logging.getLogger(__name__)


class ResourceUtilizationProvider(MetricProvider):
    """Provider for system resource utilization using psutil."""

    def get_metrics(self, metadata: dict[str, MetricMetadata]) -> list[Metric]:
        metrics = []

        # CPU Usage - aggregate percentage (basic metric)
        cpu_usage = psutil.cpu_percent(interval=1)
        metrics.append(
            self.createMetric(
                name="cpu_usage_percent",
                value=cpu_usage,
                metadata=metadata,
            )
        )

        # CPU Count - number of logical processors (basic metric)
        cpu_count = psutil.cpu_count(logical=True)
        metrics.append(
            self.createMetric(
                name="cpu_count_logical",
                value=cpu_count,
                metadata=metadata,
            )
        )

        # Memory Usage - basic percentage (basic metric)
        mem = psutil.virtual_memory()
        metrics.append(
            self.createMetric(
                name="memory_usage_percent",
                value=mem.percent,
                metadata=metadata,
            )
        )

        # Memory Total - total available memory in bytes
        metrics.append(
            self.createMetric(
                name="memory_total_bytes",
                value=int(mem.total),
                metadata=metadata,
            )
        )

        # Memory Used - used memory in bytes
        metrics.append(
            self.createMetric(
                name="memory_used_bytes",
                value=int(mem.used),
                metadata=metadata,
            )
        )

        # Memory Free - free memory in bytes
        metrics.append(
            self.createMetric(
                name="memory_free_bytes",
                value=int(mem.free),
                metadata=metadata,
            )
        )

        # Memory Active - actively used memory in bytes
        metrics.append(
            self.createMetric(
                name="memory_active_bytes",
                value=int(mem.active),
                metadata=metadata,
            )
        )

        # Memory Inactive - inactive memory in bytes
        metrics.append(
            self.createMetric(
                name="memory_inactive_bytes",
                value=int(mem.inactive),
                metadata=metadata,
            )
        )

        # Memory Buffers - buffer memory in bytes
        metrics.append(
            self.createMetric(
                name="memory_buffers_bytes",
                value=int(mem.buffers),
                metadata=metadata,
            )
        )

        # Memory Cached - cached memory in bytes
        metrics.append(
            self.createMetric(
                name="memory_cached_bytes",
                value=int(mem.cached),
                metadata=metadata,
            )
        )

        # Memory Shared - shared memory in bytes
        metrics.append(
            self.createMetric(
                name="memory_shared_bytes",
                value=int(mem.shared),
                metadata=metadata,
            )
        )

        # Memory Slab - kernel slab memory in bytes
        metrics.append(
            self.createMetric(
                name="memory_slab_bytes",
                value=int(mem.slab),
                metadata=metadata,
            )
        )

        # Disk Usage - root partition only (basic metric)
        disk = psutil.disk_usage("/")
        metrics.append(
            self.createMetric(
                name="disk_usage_percent",
                metadata=metadata,
                value=disk.percent,
            )
        )

        # CPU Frequency - additional detailed metric not covered by basic usage
        try:
            freq = psutil.cpu_freq()
            if freq and freq.current:
                metrics.append(
                    self.createMetric(
                        name="cpu_frequency_mhz",
                        metadata=metadata,
                        value=freq.current,
                    )
                )
        except (OSError, AttributeError) as exc:
            logger.debug("Failed to get CPU frequency: %s", exc)

        # CPU Stats - context switches and interrupts (detailed metric)
        try:
            cpu_stats = psutil.cpu_stats()
            if cpu_stats.ctx_switches:
                metrics.append(
                    self.createMetric(
                        name="cpu_context_switches_voluntary",
                        metadata=metadata,
                        value=cpu_stats.ctx_switches,
                    )
                )
            if cpu_stats.interrupts:
                metrics.append(
                    self.createMetric(
                        name="cpu_interrupts",
                        metadata=metadata,
                        value=cpu_stats.interrupts,
                    )
                )
        except (OSError, AttributeError) as exc:
            logger.debug("Failed to get CPU stats: %s", exc)

        # Memory Available - additional detail beyond percentage
        metrics.append(
            self.createMetric(
                name="memory_available_mb",
                metadata=metadata,
                value=int(mem.available),
            )
        )

        # Disk Usage - root partition only (basic metric)
        try:
            swap = psutil.swap_memory()
            if swap.total > 0:
                metrics.append(
                    self.createMetric(
                        name="swap_usage_percent",
                        metadata=metadata,
                        value=swap.percent,
                    )
                )
                metrics.append(
                    self.createMetric(
                        name="swap_used_mb",
                        metadata=metadata,
                        value=int(swap.used),
                    )
                )
        except (OSError, AttributeError) as exc:
            logger.debug("Failed to get swap memory: %s", exc)

        # Network I/O - network activity metrics not covered by basic resource monitoring
        try:
            net_io = psutil.net_io_counters()
            metrics.append(
                self.createMetric(
                    name="network_bytes_sent",
                    metadata=metadata,
                    value=net_io.bytes_sent,
                )
            )
            metrics.append(
                self.createMetric(
                    name="network_bytes_received",
                    metadata=metadata,
                    value=net_io.bytes_recv,
                )
            )
        except (OSError, AttributeError) as exc:
            logger.debug("Failed to get network I/O stats: %s", exc)

        # Disk I/O - disk performance metrics beyond simple usage percentage
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics.append(
                    self.createMetric(
                        name="disk_read_count",
                        metadata=metadata,
                        value=disk_io.read_count,
                    )
                )
                metrics.append(
                    self.createMetric(
                        name="disk_write_count",
                        metadata=metadata,
                        value=disk_io.write_count,
                    )
                )
                metrics.append(
                    self.createMetric(
                        name="disk_read_bytes",
                        metadata=metadata,
                        value=disk_io.read_bytes,
                    )
                )
                metrics.append(
                    self.createMetric(
                        name="disk_write_bytes",
                        metadata=metadata,
                        value=disk_io.write_bytes,
                    )
                )
                metrics.append(
                    self.createMetric(
                        name="disk_read_time_ms",
                        metadata=metadata,
                        value=disk_io.read_time,
                    )
                )
                metrics.append(
                    self.createMetric(
                        name="disk_write_time_ms",
                        metadata=metadata,
                        value=disk_io.write_time,
                    )
                )
        except (OSError, AttributeError) as exc:
            logger.debug("Failed to get disk I/O stats: %s", exc)

        return metrics

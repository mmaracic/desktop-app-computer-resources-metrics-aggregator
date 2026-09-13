#!/usr/bin/env python3
import logging

import psutil

from src.metric.metric_provider import MetricProvider
from src.metric.model.component_type import ComponentType
from src.metric.model.metric import Metric
from src.metric.model.metric_type import MetricType

logger = logging.getLogger(__name__)


class ResourceUtilizationProvider(MetricProvider):
    """
    Provider for system resource utilization using psutil.
    """

    def get_metrics(self) -> list[Metric]:
        metrics = []
        
        # CPU Usage - aggregate percentage (basic metric)
        cpu_usage = psutil.cpu_percent(interval=1)
        metrics.append(Metric(
            name="cpu_usage_percent",
            metric_type=MetricType.FLOAT,
            value=cpu_usage,
            alias="Overall CPU utilization percentage",
            description="Shows how much CPU capacity is currently being used across all processors",
            component_type=ComponentType.CPU
        ))
        
        # Memory Usage - basic percentage (basic metric)
        mem = psutil.virtual_memory()
        metrics.append(Metric(
            name="memory_usage_percent",
            metric_type=MetricType.FLOAT,
            value=mem.percent,
            alias="System RAM utilization percentage",
            description="Indicates how much of the available memory is currently in use",
            component_type=ComponentType.RAM
        ))
        
        # Disk Usage - root partition only (basic metric)
        disk = psutil.disk_usage('/')
        metrics.append(Metric(
            name="disk_usage_percent",
            metric_type=MetricType.FLOAT,
            value=disk.percent,
            alias="Root filesystem disk usage percentage",
            description="Shows how much of the system drive is occupied with data and applications",
            component_type=ComponentType.DISK
        ))
        
        # CPU Frequency - additional detailed metric not covered by basic usage
        try:
            freq = psutil.cpu_freq()
            if freq and freq.current:
                metrics.append(Metric(
                    name="cpu_frequency_mhz",
                    metric_type=MetricType.INTEGER,
                    value=freq.current,
                    alias="Current CPU operating frequency in MHz",
                    description="Indicates the actual speed at which the processor is running",
                    component_type=ComponentType.CPU
                ))
        except (OSError, AttributeError) as exc:
            logger.debug("Failed to get CPU frequency: %s", exc)
        
        # CPU Stats - context switches and interrupts (detailed metric)
        try:
            cpu_stats = psutil.cpu_stats()
            if cpu_stats.context_switches_voluntary:
                metrics.append(Metric(
                    name="cpu_context_switches_voluntary",
                    metric_type=MetricType.INTEGER,
                    value=cpu_stats.context_switches_voluntary,
                    alias="Total voluntary context switches",
                    description="Counts CPU task switches when processes voluntarily yield control",
                    component_type=ComponentType.CPU
                ))
            if cpu_stats.context_switches_involuntary:
                metrics.append(Metric(
                    name="cpu_context_switches_involuntary",
                    metric_type=MetricType.INTEGER,
                    value=cpu_stats.context_switches_involuntary,
                    alias="Total involuntary context switches",
                    description="Counts CPU task switches forced by the system due to resource constraints",
                    component_type=ComponentType.CPU
                ))
        except (OSError, AttributeError) as exc:
            logger.debug("Failed to get CPU stats: %s", exc)
        
        # Memory Available - additional detail beyond percentage
        metrics.append(Metric(
            name="memory_available_mb",
            metric_type=MetricType.INTEGER,
            value=int(mem.available),
            alias="Available system memory in MB",
            description="Shows how much RAM is currently free for new applications and processes",
            component_type=ComponentType.RAM
        ))
        
        # Swap Usage - additional memory detail not covered by virtual memory metrics
        try:
            swap = psutil.swap_memory()
            if swap.total > 0:
                metrics.append(Metric(
                    name="swap_usage_percent",
                    metric_type=MetricType.FLOAT,
                    value=swap.percent,
                    alias="Swap space utilization percentage",
                    description="Indicates how much of the virtual memory (page file/swap) is currently in use",
                    component_type=ComponentType.RAM
                ))
                metrics.append(Metric(
                    name="swap_used_mb",
                    metric_type=MetricType.INTEGER,
                    value=int(swap.used),
                    alias="Used swap space in MB",
                    description="Shows the amount of virtual memory currently being used on disk",
                    component_type=ComponentType.RAM
                ))
        except (OSError, AttributeError) as exc:
            logger.debug("Failed to get swap memory: %s", exc)
        
        # Network I/O - network activity metrics not covered by basic resource monitoring
        try:
            net_io = psutil.net_io_counters()
            metrics.append(Metric(
                name="network_bytes_sent",
                metric_type=MetricType.INTEGER,
                value=net_io.bytes_sent,
                alias="Total network bytes transmitted",
                description="Cumulative count of data sent out through all network interfaces",
                component_type=ComponentType.NETWORK
            ))
            metrics.append(Metric(
                name="network_bytes_received",
                metric_type=MetricType.INTEGER,
                value=net_io.bytes_recv,
                alias="Total network bytes received",
                description="Cumulative count of data received through all network interfaces",
                component_type=ComponentType.NETWORK
            ))
        except (OSError, AttributeError) as exc:
            logger.debug("Failed to get network I/O stats: %s", exc)
        
        # Disk I/O - disk performance metrics beyond simple usage percentage
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics.append(Metric(
                    name="disk_reads_total",
                    metric_type=MetricType.INTEGER,
                    value=disk_io.reads if hasattr(disk_io, 'reads') else 0,
                    alias="Total disk read operations",
                    description="Counts the number of times data has been read from the storage device",
                    component_type=ComponentType.DISK
                ))
                metrics.append(Metric(
                    name="disk_writes_total",
                    metric_type=MetricType.INTEGER,
                    value=disk_io.writes if hasattr(disk_io, 'writes') else 0,
                    alias="Total disk write operations",
                    description="Counts the number of times data has been written to the storage device",
                    component_type=ComponentType.DISK
                ))
        except (OSError, AttributeError) as exc:
            logger.debug("Failed to get disk I/O stats: %s", exc)
        
        return metrics

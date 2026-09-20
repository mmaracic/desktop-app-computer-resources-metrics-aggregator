import logging

import psutil

from src.metric.metric_provider import MetricProvider
from src.metric.model.metric import Metric
from src.metric.model.metric_metadata import MetricMetadata

logger = logging.getLogger(__name__)


class TopProcessesProvider(MetricProvider):
    """Provider for top CPU and RAM consuming processes.

    Returns the top 5 processes by CPU usage and the top 5 processes by memory usage.
    """

    def __init__(self, top_n: int = 5) -> None:
        """Initialize the provider with the number of top processes to return.

        Args:
            top_n: Number of top processes to return for each metric type (default: 5).

        """
        self.top_n = top_n

    def get_metrics(self, metadata: dict[str, MetricMetadata]) -> list[Metric]:
        """Retrieve the top CPU and RAM consuming processes.

        Args:
            metadata: A dictionary mapping metric names to MetricMetadata objects.

        Returns:
            list[Metric]: A list of Metric objects for top processes.

        """
        metrics = []

        # Get top N processes
        cpu_metrics = self._get_top_processes(metadata)
        metrics.extend(cpu_metrics)

        return metrics

    def _get_top_processes(self, metadata: dict[str, MetricMetadata]) -> list[Metric]:
        """Get the top N processes by CPU and memory usage.

        Args:
            metadata: A dictionary mapping metric names to MetricMetadata objects.

        Returns:
            list[Metric]: List of metrics for top CPU and memory-consuming processes.

        """
        # Get all running processes, sorted by CPU percentage (descending)
        processes = []
        for proc in psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_percent"],
        ):
            try:
                info = proc.info
                processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Normalise CPU to 0..1 and memort yo 0..1 and multiply
        # Sort by maximum combined CPU and memory usage
        sorted_processes = sorted(
            processes,
            key=lambda x: (
                ((x["cpu_percent"] or 0) / 100) * ((x["memory_percent"] or 0) / 100)
            ),
            reverse=True,
        )[: self.top_n]

        metrics = []
        for i, proc in enumerate(sorted_processes, 1):
            pid = proc["pid"]
            name = proc["name"]
            cpu_percent = proc["cpu_percent"]

            # Create metric name: top_process_1, top_cpu_process_2, etc.
            metric_name = f"top_process_{i}"

            metrics.append(
                self.createMetric(
                    name=metric_name,
                    value={
                        "pid": pid,
                        "name": name,
                        "cpu_percent": cpu_percent,
                        "memory_percent": proc["memory_percent"],
                    },
                    metadata=metadata,
                ),
            )

        return metrics

from abc import ABC, abstractmethod
from typing import Any

from src.metric.model.metric import Metric
from src.metric.model.metric_metadata import MetricMetadata


class MetricProvider(ABC):
    """Abstract base class for providing metrics.

    Subclasses of MetricProvider should implement the `get_metrics` method
    to return a list of Metric objects.
    """

    @abstractmethod
    def get_metrics(self, metadata: dict[str, MetricMetadata]) -> list[Metric]:
        """Retrieve the current metrics.

        Args:
            metadata: A dictionary mapping metric names to MetricMetadata objects.

        Returns:
            list[Metric]: A list of Metric objects.

        """

    def createMetric(
        self,
        name: str,
        value: Any,
        metadata: dict[str, MetricMetadata],
    ) -> Metric:
        """Create a Metric object.

        Args:
            name: The name of the metric.
            value: The value of the metric.
            metadata: The dictionary mapping metric names to MetricMetadata objects.

        Returns:
            Metric: The created Metric object.

        """
        metadata_value = metadata.get(name)
        if not metadata_value:
            raise ValueError(f"Metadata for {name} not found")
        return Metric(
            name=name,
            value=value,
            metadata=metadata_value,
        )

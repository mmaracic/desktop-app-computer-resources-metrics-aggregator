from abc import ABC, abstractmethod

from src.metric.model.metrics_in_time import MetricsInTime


class MetricUpdater(ABC):
    """Responsible to receive metrics from the observer and update the relevant components that process the metrics."""

    @abstractmethod
    def update(self, metrics_in_time: MetricsInTime) -> None:
        """Update the relevant components with metrics stored at a specific point in time.

        Args:
            metrics_in_time: A MetricsInTime object containing the metrics to update.
        s

        """

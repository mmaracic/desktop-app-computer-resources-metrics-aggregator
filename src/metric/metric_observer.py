from abc import ABC, abstractmethod

from src.metric.model.metrics_in_time import MetricsInTime


class MetricObserver(ABC):
    """Abstract base class for observing metrics.

    Subclasses of MetricObserver should implement the `update` method
    to handle received metrics.
    """

    @abstractmethod
    def update(self, metrics_in_time: MetricsInTime) -> None:
        """Update the observer with metrics stored at a specific point in time.

        Args:
            metrics_in_time: A MetricsInTime object to process.

        """
        pass

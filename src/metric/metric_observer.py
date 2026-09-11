from abc import ABC, abstractmethod

from src.metric.model.metric import Metric


class MetricObserver(ABC):
    """
    Abstract base class for observing metrics.

    Subclasses of MetricObserver should implement the `update` method
    to handle received metrics.
    """
    @abstractmethod
    def update(self, metrics: list[Metric]):
        """
        Update the observer with a list of metrics.

        Args:
            metrics: A list of Metric objects to process.
        """
        pass
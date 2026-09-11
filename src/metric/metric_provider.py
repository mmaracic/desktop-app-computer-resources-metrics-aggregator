from abc import ABC, abstractmethod

from src.metric.model.metric import Metric


class MetricProvider(ABC):
    """
    Abstract base class for providing metrics.

    Subclasses of MetricProvider should implement the `get_metrics` method
    to return a list of Metric objects.
    """

    @abstractmethod
    def get_metrics(self) -> list[Metric]:
        """
        Retrieve the current metrics.

        Returns:
            list[Metric]: A list of Metric objects.
        """
        pass
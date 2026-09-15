from abc import ABC, abstractmethod

from src.metric.model.metric import Metric


class MetricUpdater(ABC):
    """Responsible to receive metrics from the observer and update the relevant components that process the metrics."""

    @abstractmethod
    def update(self, metrics: list[Metric]):
        """Update the relevant components with new metrics."""
        pass
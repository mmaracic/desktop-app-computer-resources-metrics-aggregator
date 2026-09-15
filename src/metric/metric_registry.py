import logging

from src.metric.metric_observer import MetricObserver
from src.metric.metric_provider import MetricProvider
from src.metric.model.metric import Metric

logger = logging.getLogger(__name__)
class MetricRegistry:
    """
    A registry for managing metric providers and observers.

    This class handles the registration of various metric providers and
    observers, and provides methods to collect metrics from all providers
    and notify all registered observers.
    """
    def __init__(self):
        self._metrics: list[MetricProvider] = []
        self._observers: list[MetricObserver] = []

    def register_metric_provider(self, provider: MetricProvider):
        """
        Register a new metric provider.

        Args:
            provider: A MetricProvider instance to register.
        """
        self._metrics.append(provider)

    def register_metric_observer(self, observer: MetricObserver):
        """
        Register a new metric observer.

        Args:
            observer: A MetricObserver instance to register.
        """
        self._observers.append(observer)

    def unregister_all_providers_observers(self):
        """
        Unregister all metric providers and observers.
        """
        self._metrics.clear()
        self._observers.clear()

    def extract_metrics(self):
        """
        Collect metrics from all providers and notify all registered observers.
        """
        all_metrics: list[Metric] = []
        for provider in self._metrics:
            all_metrics.extend(provider.get_metrics())
        if len(all_metrics) != 0:
            logger.info("Extracted %d metrics, sending to %d observers", len(all_metrics), len(self._observers))
            for observer in self._observers:
                observer.update(all_metrics)
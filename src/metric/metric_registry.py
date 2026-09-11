from src.metric.metric_observer import MetricObserver
from src.metric.metric_provider import MetricProvider
from src.metric.model.metric import Metric


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

    def get_metrics(self) -> list[Metric]:
        """
        Collect metrics from all registered providers.

        Returns:
            list[Metric]: A list of all metrics collected from all providers.
        """
        all_metrics: list[Metric] = []
        for provider in self._metrics:
            all_metrics.extend(provider.get_metrics())
        return all_metrics

    def notify_observers(self, metrics: list[Metric] | None = None):
        """
        Notify all registered observers with the provided metrics.

        Args:
            metrics: A list of Metric objects to pass to observers. 
                     If None, no observers are notified.
        """
        if metrics is not None:
            for observer in self._observers:
                observer.update(metrics)
import logging
from typing import Any

from src.metric.metric_observer import MetricObserver
from src.metric.metric_updater import MetricUpdater
from src.metric.model.metrics_in_time import MetricsInTime

logger = logging.getLogger(__name__)


class AggregationObserver(MetricObserver):
    """Observer that keeps track of metrics and emits forward only updates that have changed."""

    def __init__(self, metric_updaters: list[MetricUpdater]) -> None:
        super().__init__()
        self._last_metrics: dict[str, Any] = {}
        self._metric_updaters = metric_updaters

    def update(self, metrics_in_time: MetricsInTime) -> None:
        """Update the observer with new metrics, emitting only changes."""
        changed_metrics = [
            metric
            for metric in metrics_in_time.metrics
            if self._last_metrics.get(metric.name) != metric.value
        ]
        if changed_metrics:
            logger.info("Detected changed metrics: %d", len(changed_metrics))
            self._last_metrics.update(
                {metric.name: metric.value for metric in changed_metrics}
            )
            for updater in self._metric_updaters:
                updater.update(
                    MetricsInTime(
                        stored_at=metrics_in_time.stored_at, metrics=changed_metrics
                    )
                )
        else:
            logger.info("No changed metrics detected")

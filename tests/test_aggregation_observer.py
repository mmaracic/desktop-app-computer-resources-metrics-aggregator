"""Tests for the AggregationObserver, ensuring it forwards only changed metrics as a list."""

from src.metric.metric_updater import MetricUpdater
from src.metric.model.component_type import ComponentType
from src.metric.model.metric import Metric
from src.metric.model.metric_type import MetricType
from src.observers.aggregation_observer import AggregationObserver


class RecordingUpdater(MetricUpdater):
    """Test double that records every batch of metrics it receives."""

    def __init__(self):
        """Initialize the updater with an empty list of received updates."""
        self.received_updates: list[list[Metric]] = []

    def update(self, metrics: list[Metric]):
        """Record the received metrics and enforce the expected list[Metric] contract."""
        assert isinstance(metrics, list)
        assert all(isinstance(metric, Metric) for metric in metrics)
        self.received_updates.append(metrics)


def _build_metric(name: str, value: float) -> Metric:
    """Build a Metric instance with the given name and value for test purposes."""
    return Metric(
        name=name,
        metric_type=MetricType.FLOAT,
        value=value,
        alias=name,
        description=name,
        component_type=ComponentType.CPU,
    )


def test_update_forwards_all_metrics_on_first_call():
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    metrics = [
        _build_metric("cpu_usage_percent", 10.0),
        _build_metric("memory_usage_percent", 20.0),
    ]
    observer.update(metrics)

    assert len(updater.received_updates) == 1
    forwarded = updater.received_updates[0]
    assert isinstance(forwarded, list)
    assert {metric.name for metric in forwarded} == {
        "cpu_usage_percent",
        "memory_usage_percent",
    }


def test_update_forwards_only_changed_metrics():
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    observer.update(
        [
            _build_metric("cpu_usage_percent", 10.0),
            _build_metric("memory_usage_percent", 20.0),
        ]
    )
    observer.update(
        [
            _build_metric("cpu_usage_percent", 10.0),
            _build_metric("memory_usage_percent", 25.0),
        ]
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 1
    assert second_update[0].name == "memory_usage_percent"
    assert second_update[0].value == 25.0


def test_update_skips_updaters_when_nothing_changed():
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    metrics = [_build_metric("cpu_usage_percent", 10.0)]
    observer.update(metrics)
    observer.update(metrics)

    assert len(updater.received_updates) == 1


def test_update_notifies_all_registered_updaters():
    first_updater = RecordingUpdater()
    second_updater = RecordingUpdater()
    observer = AggregationObserver([first_updater, second_updater])

    metrics = [_build_metric("cpu_usage_percent", 10.0)]
    observer.update(metrics)

    assert len(first_updater.received_updates) == 1
    assert len(second_updater.received_updates) == 1

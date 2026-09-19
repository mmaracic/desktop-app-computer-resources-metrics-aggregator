"""Tests for the AggregationObserver, ensuring it forwards only changed metrics as a list."""

from datetime import UTC, datetime

from src.metric.metric_updater import MetricUpdater
from src.metric.model.component_type import ComponentType
from src.metric.model.metric import Metric
from src.metric.model.metric_metadata import MetricMetadata
from src.metric.model.metric_type import MetricType
from src.metric.model.metrics_in_time import MetricsInTime
from src.observers.aggregation_observer import AggregationObserver


class RecordingUpdater(MetricUpdater):
    """Test double that records every batch of metrics it receives."""

    def __init__(self):
        """Initialize the updater with an empty list of received updates."""
        self.received_updates: list[list[Metric]] = []

    def update(self, metrics_in_time: MetricsInTime) -> None:
        """Record the received metrics and enforce the expected list[Metric] contract."""
        assert isinstance(metrics_in_time, MetricsInTime)
        assert all(isinstance(metric, Metric) for metric in metrics_in_time.metrics)
        self.received_updates.append(metrics_in_time.metrics)


def _build_metric(name: str, value: float) -> Metric:
    """Build a Metric instance with the given name and value for test purposes."""
    return Metric(
        name=name,
        value=value,
        metadata=MetricMetadata(
            metric_type=MetricType.FLOAT,
            alias=name,
            description=name,
            component_type=ComponentType.CPU,
        ),
    )


def test_update_forwards_all_metrics_on_first_call() -> None:
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    metrics = [
        _build_metric("cpu_usage_percent", 10.0),
        _build_metric("memory_usage_percent", 20.0),
    ]
    observer.update(
        MetricsInTime(metrics=metrics, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 1
    forwarded = updater.received_updates[0]
    assert isinstance(forwarded, list)
    assert {metric.name for metric in forwarded} == {
        "cpu_usage_percent",
        "memory_usage_percent",
    }


def test_update_forwards_only_changed_metrics() -> None:
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    observer.update(
        MetricsInTime(
            metrics=[
                _build_metric("cpu_usage_percent", 10.0),
                _build_metric("memory_usage_percent", 20.0),
            ],
            stored_at=datetime.now(UTC),
        )
    )
    observer.update(
        MetricsInTime(
            metrics=[
                _build_metric("cpu_usage_percent", 10.0),
                _build_metric("memory_usage_percent", 25.0),
            ],
            stored_at=datetime.now(UTC),
        )
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 1
    assert second_update[0].name == "memory_usage_percent"
    assert second_update[0].value == 25.0


def test_update_skips_updaters_when_nothing_changed() -> None:
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    metrics = [_build_metric("cpu_usage_percent", 10.0)]
    observer.update(
        MetricsInTime(metrics=metrics, stored_at=datetime.now(UTC)),
    )
    observer.update(
        MetricsInTime(metrics=metrics, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 1


def test_update_notifies_all_registered_updaters() -> None:
    first_updater = RecordingUpdater()
    second_updater = RecordingUpdater()
    observer = AggregationObserver([first_updater, second_updater])

    metrics = [_build_metric("cpu_usage_percent", 10.0)]
    observer.update(
        MetricsInTime(metrics=metrics, stored_at=datetime.now(UTC)),
    )

    assert len(first_updater.received_updates) == 1
    assert len(second_updater.received_updates) == 1

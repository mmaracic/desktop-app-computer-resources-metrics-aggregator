"""Tests for the AggregationObserver, ensuring it forwards only changed metrics as a list."""

from datetime import UTC, datetime
from typing import Any

from src.metric.metric_updater import MetricUpdater
from src.metric.model.component_type import ComponentType
from src.metric.model.metric import Metric
from src.metric.model.metric_metadata import MetricMetadata
from src.metric.model.metric_type import MetricType
from src.metric.model.metric_unit import MetricUnit
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
            metric_unit=MetricUnit.PERCENT,
            minimal_delta=0.5,
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
        ),
    )
    observer.update(
        MetricsInTime(
            metrics=[
                _build_metric("cpu_usage_percent", 10.0),
                _build_metric("memory_usage_percent", 25.0),
            ],
            stored_at=datetime.now(UTC),
        ),
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


def test_update_filters_out_none_values() -> None:
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    metrics_with_none = [
        _build_metric("cpu_usage_percent", 10.0),
        Metric(
            name="memory_usage_percent",
            value=None,
            metadata=MetricMetadata(
                metric_type=MetricType.FLOAT,
                metric_unit=MetricUnit.PERCENT,
                minimal_delta=0.5,
                alias="memory_usage_percent",
                description="memory usage percent",
                component_type=ComponentType.CPU,
            ),
        ),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_with_none, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 1
    assert len(updater.received_updates[0]) == 1
    assert updater.received_updates[0][0].name == "cpu_usage_percent"


def test_update_respects_minimal_delta_threshold() -> None:
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with value 10.0
    metrics_first = [_build_metric("cpu_usage_percent", 10.0)]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    # Second update with value 10.2 (below minimal_delta of 0.5)
    metrics_second = [_build_metric("cpu_usage_percent", 10.2)]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 1
    # The second update should not have triggered a notification
    assert updater.received_updates[0][0].value == 10.0


def test_update_respects_minimal_delta_threshold_exact_boundary() -> None:
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with value 10.0
    metrics_first = [_build_metric("cpu_usage_percent", 10.0)]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    # Second update with value 10.5 (exactly at minimal_delta boundary)
    metrics_second = [_build_metric("cpu_usage_percent", 10.5)]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 2
    assert updater.received_updates[1][0].value == 10.5


def test_update_handles_empty_metrics_list() -> None:
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # Update with empty metrics list
    observer.update(
        MetricsInTime(metrics=[], stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 0


def test_update_handles_all_metrics_unchanged() -> None:
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    metrics = [_build_metric("cpu_usage_percent", 10.0)]
    observer.update(
        MetricsInTime(metrics=metrics, stored_at=datetime.now(UTC)),
    )

    # Second update with identical metrics
    observer.update(
        MetricsInTime(metrics=metrics, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 1


def test_update_handles_negative_values() -> None:
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    metrics_first = [_build_metric("cpu_usage_percent", -5.0)]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    metrics_second = [_build_metric("cpu_usage_percent", -3.0)]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 2
    assert updater.received_updates[1][0].value == -3.0


def test_update_handles_zero_delta() -> None:
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    metrics_first = [_build_metric("cpu_usage_percent", 10.0)]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    # Second update with same value (zero delta)
    metrics_second = [_build_metric("cpu_usage_percent", 10.0)]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 1


def test_update_handles_mixed_changed_and_unchanged_metrics() -> None:
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    metrics_first = [
        _build_metric("cpu_usage_percent", 10.0),
        _build_metric("memory_usage_percent", 20.0),
        _build_metric("disk_usage_percent", 30.0),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    # Second update with only cpu and disk changed
    metrics_second = [
        _build_metric("cpu_usage_percent", 15.0),
        _build_metric("memory_usage_percent", 20.0),  # unchanged
        _build_metric("disk_usage_percent", 35.0),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 2
    names = {metric.name for metric in second_update}
    assert names == {"cpu_usage_percent", "disk_usage_percent"}


def test_update_handles_multiple_component_types() -> None:
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    metrics_first = [
        _build_metric("cpu_usage_percent", 10.0),
        Metric(
            name="gpu_temperature_celsius",
            value=65.0,
            metadata=MetricMetadata(
                metric_type=MetricType.FLOAT,
                metric_unit=MetricUnit.PERCENT,
                minimal_delta=1.0,
                alias="GPU Temperature",
                description="GPU temperature in Celsius",
                component_type=ComponentType.GPU,
            ),
        ),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    # Second update with only GPU changed
    metrics_second = [
        _build_metric("cpu_usage_percent", 10.0),
        Metric(
            name="gpu_temperature_celsius",
            value=67.0,
            metadata=MetricMetadata(
                metric_type=MetricType.FLOAT,
                metric_unit=MetricUnit.PERCENT,
                minimal_delta=1.0,
                alias="GPU Temperature",
                description="GPU temperature in Celsius",
                component_type=ComponentType.GPU,
            ),
        ),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 1
    assert second_update[0].name == "gpu_temperature_celsius"


# =============================================================================
# Dict Metric Tests
# =============================================================================

def _build_dict_metric(name: str, value: dict[str, Any]) -> Metric:
    """Build a Metric instance with DICT type and the given value for test purposes."""
    return Metric(
        name=name,
        value=value,
        metadata=MetricMetadata(
            metric_type=MetricType.DICT,
            metric_unit=MetricUnit.PERCENT,
            minimal_delta=0.5,
            alias=name,
            description=name,
            component_type=ComponentType.CPU,
        ),
    )


def test_update_forwards_dict_metrics_on_first_call() -> None:
    """Test that dict metrics are forwarded correctly on the first update."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    metrics = [
        _build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2000}),
        _build_dict_metric("memory_details", {"used": 8.5, "available": 1.5}),
    ]
    observer.update(
        MetricsInTime(metrics=metrics, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 1
    forwarded = updater.received_updates[0]
    assert isinstance(forwarded, list)
    names = {metric.name for metric in forwarded}
    assert names == {"gpu_load", "memory_details"}


def test_update_forwards_only_changed_dict_metrics() -> None:
    """Test that only changed dict metrics are forwarded on subsequent updates."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with initial dict values
    observer.update(
        MetricsInTime(
            metrics=[
                _build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2000}),
                _build_dict_metric("memory_details", {"used": 8.5, "available": 1.5}),
            ],
            stored_at=datetime.now(UTC),
        ),
    )

    # Second update with only gpu_load changed (temperature increased)
    observer.update(
        MetricsInTime(
            metrics=[
                _build_dict_metric("gpu_load", {"temperature": 70.0, "fan_speed": 2000}),
                _build_dict_metric("memory_details", {"used": 8.5, "available": 1.5}),
            ],
            stored_at=datetime.now(UTC),
        ),
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 1
    assert second_update[0].name == "gpu_load"
    assert second_update[0].value == {"temperature": 70.0, "fan_speed": 2000}


def test_update_forwards_all_dict_metrics_when_any_changed() -> None:
    """Test that when any dict metric changes, all changed dict metrics are forwarded."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with initial dict values
    observer.update(
        MetricsInTime(
            metrics=[
                _build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2000}),
                _build_dict_metric("memory_details", {"used": 8.5, "available": 1.5}),
            ],
            stored_at=datetime.now(UTC),
        ),
    )

    # Second update with both dict metrics changed
    observer.update(
        MetricsInTime(
            metrics=[
                _build_dict_metric("gpu_load", {"temperature": 70.0, "fan_speed": 2500}),
                _build_dict_metric("memory_details", {"used": 9.0, "available": 1.0}),
            ],
            stored_at=datetime.now(UTC),
        ),
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 2
    names = {metric.name for metric in second_update}
    assert names == {"gpu_load", "memory_details"}


def test_update_skips_dict_metrics_when_unchanged() -> None:
    """Test that unchanged dict metrics are not forwarded."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    metrics = [_build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2000})]
    observer.update(
        MetricsInTime(metrics=metrics, stored_at=datetime.now(UTC)),
    )
    # Second update with identical dict value
    observer.update(
        MetricsInTime(metrics=metrics, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 1


def test_update_filters_out_none_values_in_dict_metrics() -> None:
    """Test that dict metrics with None values are filtered out."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    metrics_with_none = [
        _build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2000}),
        Metric(
            name="memory_details",
            value=None,
            metadata=MetricMetadata(
                metric_type=MetricType.DICT,
                metric_unit=MetricUnit.PERCENT,
                minimal_delta=0.5,
                alias="memory_details",
                description="memory details",
                component_type=ComponentType.CPU,
            ),
        ),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_with_none, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 1
    assert len(updater.received_updates[0]) == 1
    assert updater.received_updates[0][0].name == "gpu_load"


def test_update_handles_empty_dict_values() -> None:
    """Test that dict metrics with empty dicts are handled correctly."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with empty dict
    metrics_first = [_build_dict_metric("gpu_load", {})]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    # Second update with non-empty dict (should trigger update)
    metrics_second = [_build_dict_metric("gpu_load", {"temperature": 65.0})]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 2
    assert updater.received_updates[1][0].value == {"temperature": 65.0}


def test_update_handles_dict_with_nested_changes() -> None:
    """Test that dict metrics detect changes within nested structures."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with initial dict value
    observer.update(
        MetricsInTime(
            metrics=[
                _build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2000}),
            ],
            stored_at=datetime.now(UTC),
        ),
    )

    # Second update with only fan_speed changed (same temperature)
    observer.update(
        MetricsInTime(
            metrics=[
                _build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2500}),
            ],
            stored_at=datetime.now(UTC),
        ),
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 1
    assert second_update[0].name == "gpu_load"
    assert second_update[0].value == {"temperature": 65.0, "fan_speed": 2500}


def test_update_handles_dict_with_added_keys() -> None:
    """Test that dict metrics detect when new keys are added."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with initial dict value (no power_usage)
    observer.update(
        MetricsInTime(
            metrics=[
                _build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2000}),
            ],
            stored_at=datetime.now(UTC),
        ),
    )

    # Second update with new key added (power_usage)
    observer.update(
        MetricsInTime(
            metrics=[
                _build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2000, "power_usage": 150}),
            ],
            stored_at=datetime.now(UTC),
        ),
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 1
    assert second_update[0].name == "gpu_load"


def test_update_handles_dict_with_removed_keys() -> None:
    """Test that dict metrics detect when keys are removed."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with dict containing power_usage
    observer.update(
        MetricsInTime(
            metrics=[
                _build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2000, "power_usage": 150}),
            ],
            stored_at=datetime.now(UTC),
        ),
    )

    # Second update with power_usage removed
    observer.update(
        MetricsInTime(
            metrics=[
                _build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2000}),
            ],
            stored_at=datetime.now(UTC),
        ),
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 1
    assert second_update[0].name == "gpu_load"


def test_update_handles_mixed_value_and_dict_metrics() -> None:
    """Test that mixed value and dict metrics are handled correctly together."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with both value and dict metrics
    metrics_first = [
        _build_metric("cpu_usage_percent", 10.0),
        _build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2000}),
        _build_metric("memory_usage_percent", 20.0),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    # Second update with only dict metric changed
    metrics_second = [
        _build_metric("cpu_usage_percent", 10.0),
        _build_dict_metric("gpu_load", {"temperature": 70.0, "fan_speed": 2500}),
        _build_metric("memory_usage_percent", 20.0),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 1
    assert second_update[0].name == "gpu_load"
    assert isinstance(second_update[0].value, dict)


def test_update_dict_metrics_respects_minimal_delta() -> None:
    """Test that dict metrics respect minimal_delta threshold."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with value 10.0
    metrics_first = [_build_metric("cpu_usage_percent", 10.0)]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    # Second update with dict metric (should be forwarded regardless of minimal_delta)
    metrics_second = [_build_dict_metric("gpu_load", {"temperature": 65.0})]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 2
    # The second update should have forwarded the dict metric
    assert updater.received_updates[1][0].name == "gpu_load"


def test_update_dict_metrics_with_same_value_not_forwarded() -> None:
    """Test that dict metrics with identical values are not forwarded."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with dict value
    metrics_first = [_build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2000})]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    # Second update with identical dict value
    metrics_second = [_build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2000})]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 1


def test_update_dict_metrics_with_different_keys_forwarded() -> None:
    """Test that dict metrics with different keys are forwarded even if values match."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with dict value (no power_usage)
    metrics_first = [_build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2000})]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    # Second update with dict value that has same values but different keys
    metrics_second = [_build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2000, "power_usage": 150})]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 1
    assert second_update[0].name == "gpu_load"


# =============================================================================
# Metric Type Differentiation Tests
# =============================================================================

def test_update_differentiates_between_value_and_dict_metrics() -> None:
    """Test that the observer correctly differentiates between value and dict metrics."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with both types
    metrics_first = [
        _build_metric("cpu_usage_percent", 10.0),
        _build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2000}),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    # Second update: value metric unchanged, dict metric changed
    metrics_second = [
        _build_metric("cpu_usage_percent", 10.0),  # unchanged
        _build_dict_metric("gpu_load", {"temperature": 70.0, "fan_speed": 2500}),  # changed
    ]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 1
    assert second_update[0].name == "gpu_load"


def test_update_value_metric_with_minimal_delta_vs_dict_metric() -> None:
    """Test that value metrics use minimal_delta while dict metrics don't."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with value metric at 10.0 and dict metric
    metrics_first = [
        _build_metric("cpu_usage_percent", 10.0),
        _build_dict_metric("gpu_load", {"temperature": 65.0}),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    # Second update: value metric below minimal_delta (should not forward)
    # but dict metric changed (should forward)
    metrics_second = [
        _build_metric("cpu_usage_percent", 10.2),  # below minimal_delta of 0.5
        _build_dict_metric("gpu_load", {"temperature": 70.0}),  # changed
    ]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 1
    # Only the dict metric should be forwarded (value metric below threshold)
    assert second_update[0].name == "gpu_load"


def test_update_all_metrics_same_type_consistency() -> None:
    """Test that all metrics of the same type are handled consistently."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with only value metrics
    metrics_first = [
        _build_metric("cpu_usage_percent", 10.0),
        _build_metric("memory_usage_percent", 20.0),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    # Second update with only value metrics changed
    metrics_second = [
        _build_metric("cpu_usage_percent", 15.0),
        _build_metric("memory_usage_percent", 25.0),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 2
    names = {metric.name for metric in second_update}
    assert names == {"cpu_usage_percent", "memory_usage_percent"}


def test_update_all_metrics_same_type_dict_consistency() -> None:
    """Test that all dict metrics are handled consistently."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with only dict metrics
    metrics_first = [
        _build_dict_metric("gpu_load", {"temperature": 65.0, "fan_speed": 2000}),
        _build_dict_metric("memory_details", {"used": 8.5, "available": 1.5}),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    # Second update with only dict metrics changed
    metrics_second = [
        _build_dict_metric("gpu_load", {"temperature": 70.0, "fan_speed": 2500}),
        _build_dict_metric("memory_details", {"used": 9.0, "available": 1.0}),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 2
    names = {metric.name for metric in second_update}
    assert names == {"gpu_load", "memory_details"}


def test_update_mixed_metric_types_partial_change() -> None:
    """Test that partial changes in mixed metric types are handled correctly."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with mixed metrics
    metrics_first = [
        _build_metric("cpu_usage_percent", 10.0),
        _build_dict_metric("gpu_load", {"temperature": 65.0}),
        _build_metric("memory_usage_percent", 20.0),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    # Second update: only value metric changed (cpu)
    metrics_second = [
        _build_metric("cpu_usage_percent", 15.0),  # changed
        _build_dict_metric("gpu_load", {"temperature": 65.0}),  # unchanged
        _build_metric("memory_usage_percent", 20.0),  # unchanged
    ]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 1
    assert second_update[0].name == "cpu_usage_percent"


def test_update_mixed_metric_types_dict_only_change() -> None:
    """Test that only dict metric change is forwarded when value metrics unchanged."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with mixed metrics
    metrics_first = [
        _build_metric("cpu_usage_percent", 10.0),
        _build_dict_metric("gpu_load", {"temperature": 65.0}),
        _build_metric("memory_usage_percent", 20.0),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    # Second update: only dict metric changed
    metrics_second = [
        _build_metric("cpu_usage_percent", 10.0),  # unchanged
        _build_dict_metric("gpu_load", {"temperature": 70.0}),  # changed
        _build_metric("memory_usage_percent", 20.0),  # unchanged
    ]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 1
    assert second_update[0].name == "gpu_load"
    assert isinstance(second_update[0].value, dict)


def test_update_metric_type_preserved_in_forwarded_metrics() -> None:
    """Test that metric types are preserved in forwarded metrics."""
    updater = RecordingUpdater()
    observer = AggregationObserver([updater])

    # First update with mixed types
    metrics_first = [
        _build_metric("cpu_usage_percent", 10.0),
        _build_dict_metric("gpu_load", {"temperature": 65.0}),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_first, stored_at=datetime.now(UTC)),
    )

    # Second update with changes
    metrics_second = [
        _build_metric("cpu_usage_percent", 15.0),
        _build_dict_metric("gpu_load", {"temperature": 70.0}),
    ]
    observer.update(
        MetricsInTime(metrics=metrics_second, stored_at=datetime.now(UTC)),
    )

    assert len(updater.received_updates) == 2
    second_update = updater.received_updates[1]
    assert len(second_update) == 2
    
    # Verify metric types are preserved
    cpu_metric = next(m for m in second_update if m.name == "cpu_usage_percent")
    gpu_metric = next(m for m in second_update if m.name == "gpu_load")
    
    assert cpu_metric.metadata.metric_type == MetricType.FLOAT
    assert gpu_metric.metadata.metric_type == MetricType.DICT

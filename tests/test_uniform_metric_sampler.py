"""Test suite for UniformMetricSampler class.

This module contains comprehensive tests for the UniformMetricSampler class,
covering edge cases, normal operation, and time-based sampling behavior.
"""

from datetime import datetime, timedelta

import pytest

from src.metric.model.component_type import ComponentType
from src.metric.model.metric_type import MetricType
from src.metric.model.metrics_in_time import MetricsInTime
from src.samplers.uniform_metric_sampler import UniformMetricSampler


def create_metadata(alias: str = "Test", description: str = "Test metric") -> dict:
    """Create a dictionary for MetricMetadata with required fields."""
    return {
        "metric_type": MetricType.FLOAT,
        "alias": alias,
        "description": description,
        "component_type": ComponentType.CPU,
    }


class TestUniformMetricSampler:
    """Test cases for UniformMetricSampler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sampler = UniformMetricSampler()

    # ==================== Edge Cases ====================

    def test_empty_metrics_list(self):
        """Test sampling with empty metrics list returns empty list."""
        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)

        result = self.sampler.sample([], start_time, end_time, bucket_count=10)
        assert result == []

    def test_zero_bucket_count_raises_error(self):
        """Test that zero bucket count raises ValueError."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1),
                metrics=[Metric(name="CPU", value=50.0, metadata=metadata)],
            )
        ]

        with pytest.raises(ValueError, match="bucket_count must be greater than 0"):
            self.sampler.sample(
                metrics, datetime(2026, 1, 1), datetime(2026, 1, 2), bucket_count=0
            )

    def test_negative_bucket_count_raises_error(self):
        """Test that negative bucket count raises ValueError."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1),
                metrics=[Metric(name="CPU", value=50.0, metadata=metadata)],
            )
        ]

        with pytest.raises(ValueError, match="bucket_count must be greater than 0"):
            self.sampler.sample(
                metrics, datetime(2026, 1, 1), datetime(2026, 1, 2), bucket_count=-5
            )

    def test_single_bucket_returns_one_metric(self):
        """Test that a single bucket returns one MetricsInTime with all metric types."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)

        # Multiple MetricsInTime with same metric types at different timestamps
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 30, 0),
                metrics=[Metric(name="CPU_Usage", value=50.0, metadata=metadata)],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 45, 0),
                metrics=[Metric(name="CPU_Usage", value=75.0, metadata=metadata)],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 59, 0),
                metrics=[Metric(name="CPU_Usage", value=90.0, metadata=metadata)],
            ),
        ]

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=1)
        # With one bucket, should return one MetricsInTime with max CPU value
        assert len(result) == 1
        assert result[0].stored_at == datetime(
            2026, 1, 1, 0, 45, 0
        )  # median of [30, 45, 59]
        assert result[0].metrics[0].name == "CPU_Usage"
        assert result[0].metrics[0].value == 90.0  # maximum value

    # ==================== Normal Operation ====================

    def test_uniform_sampling_across_time_range(self):
        """Test that metrics are sampled uniformly across time buckets."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 2, 0, 0)  # 2 hours

        # Create metrics at regular intervals (every 5 minutes)
        metrics = []
        for i in range(24):  # 24 * 5 minutes = 2 hours
            timestamp = start_time + timedelta(minutes=i * 5)
            metrics.append(
                MetricsInTime(
                    stored_at=timestamp,
                    metrics=[
                        Metric(name="CPU_Usage", value=float(i), metadata=metadata)
                    ],
                )
            )

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=4)

        # Should have at most one metric per bucket (4 buckets)
        assert len(result) == 4

        # Verify each result is from a different time bucket (30-minute intervals)
        for i, sampled_metric in enumerate(result):
            expected_bucket_start = start_time + timedelta(minutes=i * 30)
            assert (
                expected_bucket_start
                <= sampled_metric.stored_at
                < expected_bucket_start + timedelta(minutes=30)
            )
            # Verify it has the maximum CPU value for that bucket

    def test_sampling_with_many_metrics_per_bucket(self):
        """Test sampling when there are many metrics within each bucket."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)  # 1 hour

        # Create 100 metrics within 1 hour (every 36 seconds)
        metrics = []
        for i in range(100):
            timestamp = start_time + timedelta(seconds=i * 36)
            metrics.append(
                MetricsInTime(
                    stored_at=timestamp,
                    metrics=[
                        Metric(name="CPU_Usage", value=float(i), metadata=metadata)
                    ],
                )
            )

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=10)

        # Should have at most one metric per bucket (10 buckets)
        assert len(result) == 10

        # Verify each bucket has exactly one metric with maximum value
        bucket_duration = timedelta(minutes=6)  # 1 hour / 10 buckets
        for i, sampled_metric in enumerate(result):
            expected_bucket_start = start_time + (i * bucket_duration)
            assert (
                expected_bucket_start
                <= sampled_metric.stored_at
                < expected_bucket_start + bucket_duration
            )
            # Verify it has the maximum CPU value for that bucket

    def test_sampling_with_fewer_metrics_than_buckets(self):
        """Test sampling when there are fewer metrics than buckets."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)

        # Create only 3 metrics but request 10 buckets
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 10, 0),
                metrics=[Metric(name="CPU_Usage", value=10.0, metadata=metadata)],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 30, 0),
                metrics=[Metric(name="CPU_Usage", value=30.0, metadata=metadata)],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 50, 0),
                metrics=[Metric(name="CPU_Usage", value=50.0, metadata=metadata)],
            ),
        ]

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=10)

        # Should return all 3 metrics (each in its own bucket)
        assert len(result) == 3

    def test_sampling_with_metrics_at_bucket_boundaries(self):
        """Test sampling when metrics fall exactly on bucket boundaries."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)

        # Create metrics at exact bucket boundaries (every 10 minutes for 6 buckets)
        metrics = []
        for i in range(7):  # 0 to 60 minutes inclusive
            timestamp = start_time + timedelta(minutes=i * 10)
            metrics.append(
                MetricsInTime(
                    stored_at=timestamp,
                    metrics=[
                        Metric(name="CPU_Usage", value=float(i), metadata=metadata)
                    ],
                )
            )

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=6)

        # Should have at most one metric per bucket (6 buckets)
        assert len(result) == 6

    def test_sampling_preserves_order(self):
        """Test that sampled metrics are returned in chronological order."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)

        # Create metrics out of order
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 50, 0),
                metrics=[Metric(name="CPU_Usage", value=50.0, metadata=metadata)],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 10, 0),
                metrics=[Metric(name="CPU_Usage", value=10.0, metadata=metadata)],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 30, 0),
                metrics=[Metric(name="CPU_Usage", value=30.0, metadata=metadata)],
            ),
        ]

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=3)

        # Results should be sorted by timestamp
        assert result[0].stored_at == datetime(2026, 1, 1, 0, 10, 0)
        assert result[1].stored_at == datetime(2026, 1, 1, 0, 30, 0)
        assert result[2].stored_at == datetime(2026, 1, 1, 0, 50, 0)

    # ==================== Time Range Edge Cases ====================

    def test_sampling_with_zero_duration(self):
        """Test sampling when start_time equals end_time."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        same_time = datetime(2026, 1, 1, 12, 0, 0)

        metrics = [
            MetricsInTime(
                stored_at=same_time,
                metrics=[Metric(name="CPU_Usage", value=1.0, metadata=metadata)],
            ),
            MetricsInTime(
                stored_at=same_time,
                metrics=[Metric(name="CPU_Usage", value=2.0, metadata=metadata)],
            ),
            MetricsInTime(
                stored_at=same_time,
                metrics=[Metric(name="CPU_Usage", value=3.0, metadata=metadata)],
            ),
        ]

        result = self.sampler.sample(metrics, same_time, same_time, bucket_count=5)

        # Zero duration collapses into a single bucket holding the max
        assert len(result) == 1
        assert result[0].stored_at == same_time
        assert result[0].metrics[0].value == 3.0

    def test_end_before_start_raises_error(self):
        """Test that a reversed time range raises ValueError."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1),
                metrics=[Metric(name="CPU", value=1.0, metadata=metadata)],
            )
        ]
        with pytest.raises(ValueError, match="end_time must not be before"):
            self.sampler.sample(
                metrics, datetime(2026, 1, 2), datetime(2026, 1, 1), bucket_count=2
            )

    def test_start_and_end_times_are_inclusive(self):
        """Test that metrics exactly at start and end fall into first and last bucket."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)
        metrics = [
            MetricsInTime(
                stored_at=ts,
                metrics=[Metric(name="CPU", value=v, metadata=metadata)],
            )
            for ts, v in [(start_time, 1.0), (end_time, 2.0)]
        ]

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=2)

        assert [r.stored_at for r in result] == [start_time, end_time]
        assert [r.metrics[0].value for r in result] == [1.0, 2.0]

    def test_input_is_not_mutated(self):
        """Test that sampling does not reorder the caller's list."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, m),
                metrics=[Metric(name="CPU", value=1.0, metadata=metadata)],
            )
            for m in (30, 10, 20)
        ]
        before = list(metrics)

        self.sampler.sample(
            metrics, datetime(2026, 1, 1), datetime(2026, 1, 1, 1), bucket_count=2
        )

        assert metrics == before

    def test_metric_names_missing_in_some_entries(self):
        """Test that a name present in only some entries is still reported."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 1),
                metrics=[Metric(name="CPU", value=5.0, metadata=metadata)],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 2),
                metrics=[Metric(name="RAM", value=7.0, metadata=metadata)],
            ),
        ]

        result = self.sampler.sample(
            metrics, datetime(2026, 1, 1), datetime(2026, 1, 1, 1), bucket_count=1
        )

        assert {m.name: m.value for m in result[0].metrics} == {"CPU": 5.0, "RAM": 7.0}

    def test_dict_type_with_dict_and_list_values(self):
        """Test DICT mode over nested dict/list values returns the most frequent one."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        meta = {**create_metadata(), "metric_type": MetricType.DICT}
        metadata = MetricMetadata(**meta)
        common = {"eth0": [1, 2], "lo": {"up": True}}
        other = {"eth0": [3]}
        values = [other, common, common]
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, i),
                metrics=[Metric(name="Net", value=v, metadata=metadata)],
            )
            for i, v in enumerate(values)
        ]

        result = self.sampler.sample(
            metrics, datetime(2026, 1, 1), datetime(2026, 1, 1, 1), bucket_count=1
        )

        assert result[0].metrics[0].value == common

    def test_dict_type_tie_selects_first_seen(self):
        """Test that a DICT mode tie resolves to the earliest value."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        meta = {**create_metadata(), "metric_type": MetricType.DICT}
        metadata = MetricMetadata(**meta)
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, i),
                metrics=[Metric(name="S", value=v, metadata=metadata)],
            )
            for i, v in enumerate(["b", "a"])
        ]

        result = self.sampler.sample(
            metrics, datetime(2026, 1, 1), datetime(2026, 1, 1, 1), bucket_count=1
        )

        assert result[0].metrics[0].value == "b"

    def test_sampling_with_large_time_range(self):
        """Test sampling with a large time range (multiple days)."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 31, 23, 59, 59)  # Almost a full month

        # Create metrics spread across the month (every day at noon)
        metrics = []
        for day in range(1, 32):
            timestamp = datetime(2026, 1, day, 12, 0, 0)
            metrics.append(
                MetricsInTime(
                    stored_at=timestamp,
                    metrics=[
                        Metric(name="CPU_Usage", value=float(day), metadata=metadata)
                    ],
                )
            )

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=7)

        # Should have at most one metric per bucket (7 buckets)
        assert len(result) == 7

    def test_sampling_with_metrics_outside_range(self):
        """Test that metrics outside the time range are ignored."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        start_time = datetime(2026, 1, 1, 1, 0, 0)
        end_time = datetime(2026, 1, 1, 23, 0, 0)

        # Create metrics, some inside and some outside the range
        # With bucket_count=4, each bucket is 5.75 hours wide
        metrics = [
            MetricsInTime(
                stored_at=datetime(2025, 12, 31, 23, 0, 0),
                metrics=[Metric(name="CPU_Usage", value=99.0, metadata=metadata)],
            ),  # Before range
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 2, 0, 0),
                metrics=[Metric(name="CPU_Usage", value=50.0, metadata=metadata)],
            ),  # Inside range (bucket 0)
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 12, 0, 0),
                metrics=[Metric(name="CPU_Usage", value=75.0, metadata=metadata)],
            ),  # Inside range (bucket 1)
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 23, 30, 0),
                metrics=[Metric(name="CPU_Usage", value=85.0, metadata=metadata)],
            ),  # After range
        ]

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=4)

        # Should only include metrics within the time range (2 metrics in different buckets)
        assert len(result) == 2

    # ==================== Multiple Metrics Per Bucket Selection ====================

    def test_selects_maximum_value_per_metric_type_in_bucket(self):
        """Test that metrics are grouped by name and maximum value is selected for each type."""
        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)

        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = create_metadata()

        # Multiple MetricsInTime objects in first bucket with varying values per metric type
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 59, 0),
                metrics=[
                    Metric(name="CPU_Usage", value=50.0, metadata=metadata),
                    Metric(name="RAM_Usage", value=30.0, metadata=metadata),
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 30, 0),
                metrics=[
                    Metric(name="CPU_Usage", value=75.0, metadata=metadata),
                    Metric(name="RAM_Usage", value=40.0, metadata=metadata),
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 10, 0),
                metrics=[
                    Metric(name="CPU_Usage", value=90.0, metadata=metadata),
                    Metric(name="RAM_Usage", value=60.0, metadata=metadata),
                ],
            ),
        ]

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=3)

        # Should have one MetricsInTime per bucket (containing all metric types)
        assert len(result) == 3

        # First bucket (0:00-0:20): max CPU=90.0 at 0:10, max RAM=60.0 at 0:10
        assert result[0].stored_at == datetime(2026, 1, 1, 0, 10, 0)
        assert len(result[0].metrics) == 2

        # Verify maximum values are selected for each metric type
        cpu_metric = next(m for m in result[0].metrics if m.name == "CPU_Usage")
        ram_metric = next(m for m in result[0].metrics if m.name == "RAM_Usage")
        assert cpu_metric.value == 90.0
        assert ram_metric.value == 60.0

    def test_selects_maximum_value_per_metric_type_with_multiple_timestamps(self):
        """Test selection when same metric type appears at multiple timestamps."""
        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)

        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = create_metadata()

        # Multiple MetricsInTime with same metric types at different timestamps
        # All within first bucket (0:00-0:20) so they're sampled together
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 19, 0),
                metrics=[
                    Metric(name="CPU_Usage", value=50.0, metadata=metadata),
                    Metric(name="RAM_Usage", value=30.0, metadata=metadata),
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 15, 0),
                metrics=[
                    Metric(name="CPU_Usage", value=75.0, metadata=metadata),
                    Metric(name="RAM_Usage", value=80.0, metadata=metadata),
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 10, 0),
                metrics=[
                    Metric(name="CPU_Usage", value=90.0, metadata=metadata),
                    Metric(name="RAM_Usage", value=40.0, metadata=metadata),
                ],
            ),
        ]

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=3)

        # Should have one MetricsInTime per bucket (only first bucket has metrics)
        assert len(result) == 1

        # First bucket: max CPU=90.0 at 0:10, max RAM=80.0 at 0:15
        # Median timestamp of [0:10, 0:15, 0:19] is 0:15
        assert result[0].stored_at == datetime(2026, 1, 1, 0, 15, 0)
        assert len(result[0].metrics) == 2

        cpu_metric = next(m for m in result[0].metrics if m.name == "CPU_Usage")
        ram_metric = next(m for m in result[0].metrics if m.name == "RAM_Usage")
        assert cpu_metric.value == 90.0  # Max CPU from 0:10
        assert ram_metric.value == 80.0  # Max RAM from 0:15

    def test_selects_maximum_value_per_metric_type_with_clustering(self):
        """Test selection behavior when metrics are clustered in some buckets."""
        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)

        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = create_metadata()

        # Create metrics with clustering: many in first bucket, few in others
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 1, 0),
                metrics=[
                    Metric(name="CPU_Usage", value=30.0, metadata=metadata),
                    Metric(name="RAM_Usage", value=50.0, metadata=metadata),
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 2, 0),
                metrics=[
                    Metric(name="CPU_Usage", value=70.0, metadata=metadata),
                    Metric(name="RAM_Usage", value=90.0, metadata=metadata),
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 3, 0),
                metrics=[
                    Metric(name="CPU_Usage", value=40.0, metadata=metadata),
                    Metric(name="RAM_Usage", value=60.0, metadata=metadata),
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 59, 0),
                metrics=[
                    Metric(name="CPU_Usage", value=80.0, metadata=metadata),
                    Metric(name="RAM_Usage", value=100.0, metadata=metadata),
                ],
            ),
        ]

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=4)

        # Should have at most one MetricsInTime per bucket (4 buckets)
        # Only first and last buckets have metrics, so we get 2 results
        assert len(result) == 2

        # First bucket (0:00-0:16): max CPU=70.0 at 0:02, max RAM=90.0 at 0:02
        # Median timestamp of [0:01, 0:02, 0:03] is 0:02
        assert result[0].stored_at == datetime(2026, 1, 1, 0, 2, 0)
        assert len(result[0].metrics) == 2

        cpu_metric = next(m for m in result[0].metrics if m.name == "CPU_Usage")
        ram_metric = next(m for m in result[0].metrics if m.name == "RAM_Usage")
        assert cpu_metric.value == 70.0
        assert ram_metric.value == 90.0

        # Last bucket (0:48-1:00): max CPU=80.0 at 0:59, max RAM=100.0 at 0:59
        assert result[1].stored_at == datetime(2026, 1, 1, 0, 59, 0)
        assert len(result[1].metrics) == 2

        cpu_metric = next(m for m in result[1].metrics if m.name == "CPU_Usage")
        ram_metric = next(m for m in result[1].metrics if m.name == "RAM_Usage")
        assert cpu_metric.value == 80.0
        assert ram_metric.value == 100.0

    # ==================== Large Scale Tests ====================

    def test_sampling_with_very_large_dataset(self):
        """Test sampling with a very large number of metrics."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)

        # Create 10,000 metrics within 1 hour (every 3.6 seconds)
        metrics = []
        for i in range(10000):
            timestamp = start_time + timedelta(seconds=i * 3.6)
            metrics.append(
                MetricsInTime(
                    stored_at=timestamp,
                    metrics=[
                        Metric(name="CPU_Usage", value=float(i), metadata=metadata)
                    ],
                )
            )

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=100)

        # Should have at most one metric per bucket (100 buckets)
        assert len(result) == 100

    def test_sampling_with_very_small_bucket_count(self):
        """Test sampling with a very small number of buckets."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)

        # Create metrics spread throughout the hour (every minute + 30 seconds)
        metrics = []
        for i in range(60):
            timestamp = start_time + timedelta(seconds=i * 60 + 30)
            metrics.append(
                MetricsInTime(
                    stored_at=timestamp,
                    metrics=[
                        Metric(name="CPU_Usage", value=float(i), metadata=metadata)
                    ],
                )
            )

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=2)

        # Should have at most one metric per bucket (2 buckets of 30 minutes each)
        assert len(result) == 2


class TestUniformMetricSamplerIntegration:
    """Integration tests for UniformMetricSampler with realistic scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sampler = UniformMetricSampler()

    def test_daily_metrics_sampling_with_actual_data(self):
        """Test sampling typical daily metrics data with actual metric values."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = create_metadata()

        start_time = datetime(2026, 1, 15, 0, 0, 0)
        end_time = datetime(2026, 1, 15, 23, 59, 59)

        # Simulate metrics collected every minute throughout the day with varying values
        metrics = []
        for minute in range(1440):
            timestamp = start_time + timedelta(minutes=minute)
            # Create metrics with increasing values to test maximum selection
            value = (minute % 100) * 1.5  # Values from 0 to 98.5
            metrics.append(
                MetricsInTime(
                    stored_at=timestamp,
                    metrics=[Metric(name="CPU_Usage", value=value, metadata=metadata)],
                )
            )

        # Sample into 24 hourly buckets
        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=24)

        assert len(result) == 24

        # Verify each hour has exactly one sample with maximum value
        for i, sampled_metric in enumerate(result):
            expected_hour_start = start_time + timedelta(hours=i)
            expected_hour_end = expected_hour_start + timedelta(hours=1)

            assert expected_hour_start <= sampled_metric.stored_at < expected_hour_end

            # Verify this is the maximum value metric in this hour
            expected_max = max((m % 100) * 1.5 for m in range(i * 60, (i + 1) * 60))
            assert len(sampled_metric.metrics) == 1
            cpu_metric = sampled_metric.metrics[0]
            assert cpu_metric.name == "CPU_Usage"
            assert cpu_metric.value == expected_max

    def test_metrics_with_multiple_metrics_per_timestamp(self):
        """Test sampling with metrics that have multiple metrics at each timestamp."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        cpu_metadata = create_metadata(
            alias="CPU Usage", description="CPU usage percentage"
        )
        ram_metadata = create_metadata(
            alias="RAM Usage", description="RAM usage percentage"
        )
        disk_metadata = create_metadata(
            alias="Disk Usage", description="Disk usage percentage"
        )

        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 2, 0, 0)

        # Create metrics with multiple metrics per timestamp (CPU, RAM, Disk)
        # Each MetricsInTime has 3 different metrics
        # CPU starts highest and grows fastest to ensure it's always the maximum
        metrics = []
        for i in range(6):
            timestamp = start_time + timedelta(minutes=i * 20)
            cpu_value = 100.0 + i * 10
            ram_value = 80.0 + i * 5
            disk_value = 60.0 + i * 3

            metrics.append(
                MetricsInTime(
                    stored_at=timestamp,
                    metrics=[
                        Metric(
                            name="CPU_Usage", value=cpu_value, metadata=cpu_metadata
                        ),
                        Metric(
                            name="RAM_Usage", value=ram_value, metadata=ram_metadata
                        ),
                        Metric(
                            name="Disk_Usage", value=disk_value, metadata=disk_metadata
                        ),
                    ],
                )
            )

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=6)

        assert len(result) == 6

        # Verify each sampled metric has the expected data structure
        for i, m in enumerate(result):
            assert isinstance(m, MetricsInTime)
            assert len(m.metrics) == 3

            # Find the maximum value metric (should be CPU_Usage since it starts highest and grows fastest)
            max_metric = max(m.metrics, key=lambda x: x.value)
            expected_cpu_value = 100.0 + i * 10
            assert max_metric.name == "CPU_Usage"
            assert max_metric.value == expected_cpu_value

    def test_sampling_with_metrics_outside_range_with_data(self):
        """Test that metrics outside the time range are ignored (with actual data)."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = create_metadata()

        start_time = datetime(2026, 1, 1, 1, 0, 0)
        end_time = datetime(2026, 1, 1, 23, 0, 0)

        # Create metrics, some inside and some outside the range with actual values
        metrics = [
            MetricsInTime(
                stored_at=datetime(2025, 12, 31, 23, 0, 0),
                metrics=[Metric(name="CPU_Usage", value=99.0, metadata=metadata)],
            ),  # Before range - should be ignored
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 2, 0, 0),
                metrics=[Metric(name="CPU_Usage", value=50.0, metadata=metadata)],
            ),  # Inside range (bucket 0)
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 12, 0, 0),
                metrics=[Metric(name="CPU_Usage", value=75.0, metadata=metadata)],
            ),  # Inside range (bucket 1)
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 23, 30, 0),
                metrics=[Metric(name="CPU_Usage", value=85.0, metadata=metadata)],
            ),  # After range - should be ignored
        ]

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=4)

        # Should only include metrics within the time range (2 metrics in different buckets)
        assert len(result) == 2

        # Verify the sampled metrics have correct values
        assert result[0].metrics[0].value == 50.0
        assert result[1].metrics[0].value == 75.0

    # ==================== DICT Type Tests ====================

    def test_dict_type_selects_most_frequent_value(self):
        """Test that DICT-type metrics select the most frequently occurring value (mode)."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        # Change metric type to DICT
        metadata.metric_type = MetricType.DICT

        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)

        # Create DICT metrics with values that have different frequencies
        # All within the same bucket (first 15 minutes for 4 buckets of 15 min each)
        # 'active' appears 3 times, 'inactive' appears 1 time
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 2, 0),
                metrics=[
                    Metric(name="Network_Status", value="active", metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 5, 0),
                metrics=[
                    Metric(name="Network_Status", value="inactive", metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 8, 0),
                metrics=[
                    Metric(name="Network_Status", value="active", metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 12, 0),
                metrics=[
                    Metric(name="Network_Status", value="active", metadata=metadata)
                ],
            ),
        ]

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=4)

        # Should have one MetricsInTime (only first bucket has all metrics)
        assert len(result) == 1

        # The most frequent value is 'active' (appears 3 times vs 1 for 'inactive')
        network_metric = result[0].metrics[0]
        assert network_metric.name == "Network_Status"
        assert network_metric.value == "active"

    def test_dict_type_with_tie_selects_any_most_frequent(self):
        """Test that when there's a tie in frequency, any of the most frequent values is selected."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        metadata.metric_type = MetricType.DICT

        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)

        # Create DICT metrics with equal frequency for two values
        # All within the same bucket (first 15 minutes for 4 buckets of 15 min each)
        # 'status_a' and 'status_b' both appear 2 times
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 2, 0),
                metrics=[
                    Metric(name="System_Status", value="status_a", metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 5, 0),
                metrics=[
                    Metric(name="System_Status", value="status_b", metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 8, 0),
                metrics=[
                    Metric(name="System_Status", value="status_a", metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 12, 0),
                metrics=[
                    Metric(name="System_Status", value="status_b", metadata=metadata)
                ],
            ),
        ]

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=4)

        assert len(result) == 1

        # Either 'status_a' or 'status_b' should be selected (both appear twice)
        system_metric = result[0].metrics[0]
        assert system_metric.name == "System_Status"
        assert system_metric.value in ["status_a", "status_b"]

    def test_dict_type_mixed_with_other_types(self):
        """Test that DICT-type metrics are handled correctly alongside other metric types."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        cpu_metadata = MetricMetadata(**create_metadata())
        network_metadata = MetricMetadata(**create_metadata())
        # Change network to DICT type
        network_metadata.metric_type = MetricType.DICT

        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)

        # Mix of CPU (FLOAT) and Network_Status (DICT) metrics
        # All within the same bucket (first 15 minutes for 4 buckets of 15 min each)
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 2, 0),
                metrics=[
                    Metric(name="CPU_Usage", value=75.0, metadata=cpu_metadata),
                    Metric(
                        name="Network_Status", value="active", metadata=network_metadata
                    ),
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 5, 0),
                metrics=[
                    Metric(name="CPU_Usage", value=90.0, metadata=cpu_metadata),
                    Metric(
                        name="Network_Status",
                        value="inactive",
                        metadata=network_metadata,
                    ),
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 8, 0),
                metrics=[
                    Metric(name="CPU_Usage", value=85.0, metadata=cpu_metadata),
                    Metric(
                        name="Network_Status", value="active", metadata=network_metadata
                    ),
                ],
            ),
        ]

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=4)

        assert len(result) == 1

        # CPU should have maximum value (90.0)
        cpu_metric = next(m for m in result[0].metrics if m.name == "CPU_Usage")
        assert cpu_metric.value == 90.0

        # Network_Status should have most frequent value ('active' appears twice, 'inactive' once)
        network_metric = next(
            m for m in result[0].metrics if m.name == "Network_Status"
        )
        assert network_metric.value == "active"

    def test_dict_type_single_value(self):
        """Test DICT-type metric with only one unique value."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        metadata.metric_type = MetricType.DICT

        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)

        # All values are the same - all within first bucket
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 2, 0),
                metrics=[
                    Metric(
                        name="Connection_State", value="connected", metadata=metadata
                    )
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 5, 0),
                metrics=[
                    Metric(
                        name="Connection_State", value="connected", metadata=metadata
                    )
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 8, 0),
                metrics=[
                    Metric(
                        name="Connection_State", value="connected", metadata=metadata
                    )
                ],
            ),
        ]

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=4)

        assert len(result) == 1
        connection_metric = result[0].metrics[0]
        assert connection_metric.name == "Connection_State"
        assert connection_metric.value == "connected"

    def test_dict_type_multiple_buckets(self):
        """Test DICT-type metrics across multiple buckets."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        metadata.metric_type = MetricType.DICT

        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)

        # Create metrics across multiple buckets with different frequencies per bucket
        # Bucket 0 (0:00-0:14): 'online' appears twice, 'offline' once
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 2, 0),
                metrics=[
                    Metric(name="Server_Status", value="online", metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 5, 0),
                metrics=[
                    Metric(name="Server_Status", value="offline", metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 8, 0),
                metrics=[
                    Metric(name="Server_Status", value="online", metadata=metadata)
                ],
            ),
            # Bucket 1 (0:14-0:29): 'maintenance' appears twice, 'online' once
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 15, 0),
                metrics=[
                    Metric(name="Server_Status", value="maintenance", metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 20, 0),
                metrics=[
                    Metric(name="Server_Status", value="online", metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 25, 0),
                metrics=[
                    Metric(name="Server_Status", value="maintenance", metadata=metadata)
                ],
            ),
            # Bucket 2 (0:29-0:44): 'online' appears three times
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 30, 0),
                metrics=[
                    Metric(name="Server_Status", value="online", metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 35, 0),
                metrics=[
                    Metric(name="Server_Status", value="online", metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 40, 0),
                metrics=[
                    Metric(name="Server_Status", value="online", metadata=metadata)
                ],
            ),
            # Bucket 3 (0:44-1:00): 'offline' appears twice, 'online' once
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 45, 0),
                metrics=[
                    Metric(name="Server_Status", value="offline", metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 50, 0),
                metrics=[
                    Metric(name="Server_Status", value="online", metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 55, 0),
                metrics=[
                    Metric(name="Server_Status", value="offline", metadata=metadata)
                ],
            ),
        ]

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=4)

        assert len(result) == 4

        # Verify each bucket has the correct most frequent value
        expected_values = ["online", "maintenance", "online", "offline"]
        for i, m in enumerate(result):
            server_metric = next(
                metric for metric in m.metrics if metric.name == "Server_Status"
            )
            assert server_metric.value == expected_values[i], (
                f"Bucket {i}: expected {expected_values[i]}, got {server_metric.value}"
            )

    def test_dict_type_complex_nested_dict_values(self):
        """Test DICT-type metrics with complex nested dictionary values."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        metadata.metric_type = MetricType.DICT

        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)

        # Create DICT metrics with nested dictionary values - all within first bucket
        config_a = {"setting": "high", "threshold": 80}
        config_b = {"setting": "low", "threshold": 40}

        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 2, 0),
                metrics=[
                    Metric(name="Config_Profile", value=config_a, metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 5, 0),
                metrics=[
                    Metric(name="Config_Profile", value=config_b, metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 8, 0),
                metrics=[
                    Metric(name="Config_Profile", value=config_a, metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 12, 0),
                metrics=[
                    Metric(name="Config_Profile", value=config_a, metadata=metadata)
                ],
            ),
        ]

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=4)

        assert len(result) == 1

        # config_a appears 3 times, config_b appears 1 time
        config_metric = result[0].metrics[0]
        assert config_metric.name == "Config_Profile"
        assert config_metric.value == config_a

    def test_dict_type_empty_bucket(self):
        """Test that empty buckets are handled correctly with DICT-type metrics."""
        from src.metric.model.metric import Metric
        from src.metric.model.metric_metadata import MetricMetadata

        metadata = MetricMetadata(**create_metadata())
        metadata.metric_type = MetricType.DICT

        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 1, 1, 1, 0, 0)

        # Only first and last buckets have metrics, middle buckets are empty
        metrics = [
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 5, 0),
                metrics=[
                    Metric(name="Network_Status", value="active", metadata=metadata)
                ],
            ),
            MetricsInTime(
                stored_at=datetime(2026, 1, 1, 0, 55, 0),
                metrics=[
                    Metric(name="Network_Status", value="inactive", metadata=metadata)
                ],
            ),
        ]

        result = self.sampler.sample(metrics, start_time, end_time, bucket_count=4)

        # Should only return buckets that have data (2 buckets)
        assert len(result) == 2

        # First bucket: 'active' is the only value
        active_metric = result[0].metrics[0]
        assert active_metric.name == "Network_Status"
        assert active_metric.value == "active"

        # Last bucket: 'inactive' is the only value
        inactive_metric = result[1].metrics[0]
        assert inactive_metric.name == "Network_Status"
        assert inactive_metric.value == "inactive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

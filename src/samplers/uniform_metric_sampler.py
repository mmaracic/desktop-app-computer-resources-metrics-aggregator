"""Uniform metric sampler for time-based sampling of metrics."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.metric.model.metric import Metric
from src.metric.model.metric_type import MetricType
from src.metric.model.metrics_in_time import MetricsInTime
from src.samplers.metric_sampler import MetricSampler


class UniformMetricSampler(MetricSampler):
    """Uniformly samples metrics into a specified number of time buckets.

    Each bucket represents approximately the same time interval.
    For each bucket, metrics are grouped by their name (e.g., CPU_Usage, RAM_Usage),
    and the maximum value for each metric type is selected. For DICT-type metrics,
    the most frequently occurring value (mode) is selected instead. The resulting
    MetricsInTime object contains one metric per unique metric type, with the
    median timestamp from all source metrics in that bucket.

    Example:
        If a bucket contains:
            - CPU_Usage values: [50.0, 75.0, 90.0] at different timestamps
            - RAM_Usage values: [30.0, 40.0, 60.0] at different timestamps

        The result will be a single MetricsInTime with:
            - CPU_Usage=90.0 (maximum)
            - RAM_Usage=60.0 (maximum)
            - stored_at = median of all source timestamps in the bucket

    Example for DICT metrics:
        If a bucket contains:
            - Network_Status values: ['active', 'inactive', 'active', 'active']
              at different timestamps (DICT type)

        The result will be:
            - Network_Status='active' (most frequent value)
            - stored_at = median of all source timestamps in the bucket
    """

    def sample(
        self,
        metrics: list[MetricsInTime],
        start_time: datetime,
        end_time: datetime,
        bucket_count: int,
    ) -> list[MetricsInTime]:
        """Uniformly samples metrics into a specified number of time buckets.

        The sampling algorithm divides the time range into equal intervals (buckets).
        For each bucket:
            1. Identify all MetricsInTime objects within the bucket's time range
            2. Extract all individual Metric objects from those MetricsInTime objects
            3. Group metrics by their name (e.g., CPU_Usage, RAM_Usage)
            4. Select the maximum value for each metric type
            5. Reassemble into a single MetricsInTime with median timestamp

        Args:
            metrics: List of MetricsInTime objects containing computer resource metrics.
            start_time: Start of the time range to sample.
            end_time: End of the time range to sample.
            bucket_count: Number of time buckets to create.

        Returns:
            List of sampled MetricsInTime objects, one per bucket (if data exists).
            Each returned MetricsInTime contains at most one metric per unique metric name.
            For non-DICT metrics, the maximum value is selected. For DICT-type metrics,
            the most frequently occurring value (mode) is selected.
            The stored_at timestamp is the median of all source timestamps in the bucket
            (the upper median when the count is even).

        Raises:
            ValueError: If bucket_count <= 0 or end_time is before start_time.
            A zero-length range collapses into a single bucket.
        """
        if bucket_count <= 0:
            raise ValueError("bucket_count must be greater than 0")
        if end_time < start_time:
            raise ValueError("end_time must not be before start_time")
        if not metrics:
            return []

        total_duration = (end_time - start_time).total_seconds()
        bucket_duration_seconds = total_duration / bucket_count

        sampled_metrics: list[MetricsInTime] = []
        sorted_metrics = sorted(metrics, key=lambda m: m.stored_at)

        bucket_groups = self._divide_into_buckets(
            sorted_metrics,
            start_time,
            bucket_count,
            bucket_duration_seconds,
            total_duration,
        )
        # Process each bucket and create sampled MetricsInTime objects
        for bucket_index in sorted(bucket_groups.keys()):
            bucket_metricsintime = bucket_groups[bucket_index]

            # Extract all individual metrics from these MetricsInTime objects
            all_metrics: list[Metric] = []
            timestamps: list[datetime] = []
            for mti in bucket_metricsintime:
                all_metrics.extend(mti.metrics)
                timestamps.append(mti.stored_at)

            # Group metrics by name and select appropriate value for each metric type
            metric_name_selected_values: dict[str, list[Metric]] = {}
            for metric in all_metrics:
                metric_name = metric.name
                if metric_name not in metric_name_selected_values:
                    metric_name_selected_values[metric_name] = []
                metric_name_selected_values[metric_name].append(metric)

            # Select the representative metric for each metric name within this bucket
            metric_name_selected_metric = self._select_bucket_values(
                metric_name_selected_values,
            )

            # Reassemble into a single MetricsInTime object
            if metric_name_selected_metric and timestamps:
                # Use median timestamp as the representative time
                sorted_timestamps = sorted(timestamps)
                median_index = len(sorted_timestamps) // 2
                median_time = sorted_timestamps[median_index]

                selected_metrics = list(metric_name_selected_metric.values())
                sampled_metrics.append(
                    MetricsInTime(stored_at=median_time, metrics=selected_metrics),
                )

        return sampled_metrics

    def _divide_into_buckets(
        self,
        sorted_metrics: list[MetricsInTime],
        start_time: datetime,
        bucket_count: int,
        bucket_duration_seconds: float,
        total_duration: float,
    ) -> dict[int, list[MetricsInTime]]:
        bucket_groups: dict[int, list[MetricsInTime]] = {}

        for mti in sorted_metrics:
            time_offset_seconds = (mti.stored_at - start_time).total_seconds()
            if time_offset_seconds < 0 or time_offset_seconds > total_duration:
                continue

            # A zero-length range collapses into a single bucket.
            if bucket_duration_seconds == 0:
                bucket_index = 0
            else:
                # end_time is inclusive and belongs to the last bucket.
                bucket_index = min(
                    int(time_offset_seconds / bucket_duration_seconds),
                    bucket_count - 1,
                )
            bucket_groups.setdefault(bucket_index, []).append(mti)
        return bucket_groups

    def _select_bucket_values(
        self, metric_name_selected_values: dict[str, list[Metric]]
    ) -> dict[str, Metric]:
        # Select the appropriate value based on metric type
        metric_name_selected_metric: dict[str, Metric] = {}
        for metric_name, metrics_list in metric_name_selected_values.items():
            # Get the metadata to determine the metric type
            first_metric = metrics_list[0]
            metric_type = first_metric.metadata.metric_type

            if metric_type == MetricType.DICT:
                # Mode of the values; ties resolve to the first one seen.
                counts: dict[Any, int] = {}
                first_by_key: dict[Any, Metric] = {}
                for m in metrics_list:
                    key = self._make_hashable(m.value)
                    counts[key] = counts.get(key, 0) + 1
                    first_by_key.setdefault(key, m)
                best_key = max(counts, key=counts.__getitem__)
                metric_name_selected_metric[metric_name] = first_by_key[best_key]
            else:
                # For other types (INTEGER, FLOAT, STRING), select the maximum value
                max_metric = max(metrics_list, key=lambda m: m.value)
                metric_name_selected_metric[metric_name] = max_metric
        return metric_name_selected_metric

    def _make_hashable(self, value: Any) -> Any:
        """Convert nested dicts/lists into a hashable representation."""
        if isinstance(value, dict):
            items = sorted(
                ((repr(k), self._make_hashable(v)) for k, v in value.items()),
                key=lambda kv: kv[0],
            )
            return ("dict", tuple(items))
        if isinstance(value, (list, tuple)):
            return ("seq", tuple(self._make_hashable(i) for i in value))
        return value

from abc import ABC, abstractmethod
from datetime import datetime

from src.metric.model.metrics_in_time import MetricsInTime


class MetricSampler(ABC):
    """Abstract base class for metric samplers."""

    @abstractmethod
    def sample(
        self,
        metrics: list[MetricsInTime],
        start_time: datetime,
        end_time: datetime,
        bucket_count: int,
    ) -> list[MetricsInTime]:
        pass

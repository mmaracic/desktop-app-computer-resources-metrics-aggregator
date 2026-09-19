"""Model representing a batch of metrics that has been persisted."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_serializer

from .metric import Metric


class MetricsInTime(BaseModel):
    """Represents a batch of metrics that has been stored at a specific point in time."""

    stored_at: datetime
    metrics: list[Metric]

    @field_serializer("stored_at")
    def _serialize_stored_at(self, stored_at: datetime) -> str:
        """Serialize the stored_at timestamp to an ISO 8601 string for JSON output."""
        return stored_at.isoformat()

    @field_serializer("metrics")
    def _serialize_metrics(self, metrics: list[Metric]) -> list[dict[str, Any]]:
        """Serialize each metric to only its name and value; the remaining static metadata is reconstructed."""
        return [{"name": metric.name, "value": metric.value} for metric in metrics]

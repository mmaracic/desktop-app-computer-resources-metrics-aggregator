from typing import Any

from pydantic import BaseModel, Field, field_serializer, field_validator

from .component_type import ComponentType
from .metric_type import MetricType


class MetricMetadata(BaseModel):
    """Represents metadata for a single computer resource metric.

    Attributes:
        metric_type (MetricType): The type of the metric (e.g., Counter, Gauge).
        min_value (Any): The minimum (safe) value of the metric.
        max_value (Any): The maximum (safe) value of the metric.
        alias (str): A human-readable alias for the metric (max 80 characters).
        description (str): Extended explanation of the metric.
        component_type (ComponentType): The hardware component this metric belongs to.

    """

    metric_type: MetricType
    alias: str
    description: str
    component_type: ComponentType
    warning_threshold: Any | None = Field(default=None)
    critical_threshold: Any | None = Field(default=None)

    @field_validator("alias")
    @classmethod
    def _validate_alias_length(cls, alias: str) -> str:
        """Ensure the alias does not exceed the maximum allowed length."""
        if len(alias) > 80:
            raise ValueError(f"Alias must not exceed 80 characters, got {len(alias)}")
        return alias

    @field_serializer("metric_type")
    def _serialize_metric_type(self, metric_type: MetricType) -> str:
        """Serialize the metric type enum to its plain name for JSON output."""
        return metric_type.name

    @field_serializer("component_type")
    def _serialize_component_type(self, component_type: ComponentType) -> str:
        """Serialize the component type enum to its plain name for JSON output."""
        return component_type.name


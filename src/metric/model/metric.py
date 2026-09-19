from typing import Any

from pydantic import BaseModel

from .metric_metadata import MetricMetadata


class Metric(BaseModel):
    """Represents a single computer resource metric.

    Attributes:
        name (str): The name of the metric (e.g., "CPU_Usage").
        value (Any): The actual value of the metric.

    """

    name: str
    value: Any
    metadata: MetricMetadata

    def get_alias(self) -> str:
        """Get the human-readable alias for the metric.

        Returns:
            str: The alias of the metric.

        """
        return self.metadata.alias or self.name

    def __str__(self) -> str:
        """Return a string representation of the metric."""
        return f"{self.name}={self.value}"

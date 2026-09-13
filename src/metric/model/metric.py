from typing import Any

from pydantic import BaseModel

from .component_type import ComponentType
from .metric_type import MetricType


class Metric(BaseModel):
    """
    Represents a single computer resource metric.

    Attributes:
        _name (str): The name of the metric (e.g., "CPU_Usage").
        _type (MetricType): The type of the metric (e.g., Counter, Gauge).
        _value (Any): The actual value of the metric.
        _min_value (Any): The minimum (safe) value of the metric.
        _max_value (Any): The maximum (safe) value of the metric.
        _alias (str): A human-readable alias for the metric (max 80 characters).
        _description (str): Extended explanation of the metric.
        _component_type (ComponentType): The hardware component this metric belongs to.
    """

    _name: str
    _metric_type: MetricType
    _value: Any
    _min_value: Any
    _max_value: Any
    _alias: str
    _description: str
    _component_type: ComponentType

    def __init__(
        self,
        name: str,
        metric_type: MetricType,
        value: Any,
        alias: str,
        description: str,
        component_type: ComponentType,
        min_value: Any|None = None,
        max_value: Any|None = None,
    ):
        """
        Initialize a new Metric instance.

        Args:
            name (str): The name of the metric.
            metric_type (MetricType): The type of the metric.
            value (any): The value of the metric.
            min_value (any, optional): The minimum (safe) value of the metric. Defaults to None.
            max_value (any, optional): The maximum (safe) value of the metric. Defaults to None.
            alias (str): A human-readable alias for the metric (max 80 characters).
            description (str): Extended explanation of the metric.
            component_type (ComponentType): The hardware component this metric belongs to.
        """
        super().__init__()
        self._name = name
        self._metric_type = metric_type
        self._value = value
        self._min_value = min_value
        self._max_value = max_value
        if len(alias) > 80:
            raise ValueError(f"Alias must not exceed 80 characters, got {len(alias)}")
        self._alias = alias
        self._description = description
        self._component_type = component_type

    def get_alias(self) -> str:
        """
        Get the human-readable alias for the metric.

        Returns:
            str: The alias of the metric.
        """
        return self._alias if self._alias else self._name

    def __str__(self) -> str:
        """Return a string representation of the metric."""
        return f"{self._name}={self._value}"

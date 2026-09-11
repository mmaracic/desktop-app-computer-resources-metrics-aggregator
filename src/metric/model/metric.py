
from pydantic import BaseModel

from .metric_type import MetricType


class Metric(BaseModel):
    """
    Represents a single computer resource metric.

    Attributes:
        _name (str): The name of the metric (e.g., "CPU_Usage").
        _type (MetricType): The type of the metric (e.g., Counter, Gauge).
        _value (any): The actual value of the metric.
        _min_value (any): The minimum (safe) value of the metric.
        _max_value (any): The maximum (safe) value of the metric.
    """
    _name: str
    _type: MetricType
    _value: any
    _min_value: any
    _max_value: any

    def __init__(self, name: str, type: MetricType, value: any, min_value: any = None, max_value: any = None):
        """
        Initialize a new Metric instance.

        Args:
            name (str): The name of the metric.
            type (MetricType): The type of the metric.
            value (any): The value of the metric.
            min_value (any, optional): The minimum (safe) value of the metric. Defaults to None.
            max_value (any, optional): The maximum (safe) value of the metric. Defaults to None.
        """
        self._name = name
        self._type = type
        self._value = value
        self._min_value = min_value
        self._max_value = max_value

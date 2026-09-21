from pydantic import BaseModel


class MetricConfig(BaseModel):
    """Configuration model for a single metric.

    This class defines the configuration settings for individual metrics,
    including their display properties and activation state.

    Attributes:
        name: The unique identifier or display name of the metric.
        enabled: Whether the metric is currently active and being collected.
        order: The display order of the metric in dashboards or lists.
        color: The color used to represent this metric in visualizations.

    """

    name: str
    enabled: bool
    order: int
    color: str

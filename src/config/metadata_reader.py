import json
from pathlib import Path

from src.metric.model.component_type import ComponentType
from src.metric.model.metric_metadata import MetricMetadata
from src.metric.model.metric_type import MetricType


class MetadataReader:
    """Reads metric metadata definitions from a JSON file into `MetricMetadata` models."""

    def __init__(
        self,
        file_path: str | Path,
    ) -> None:
        self.file_path = Path(file_path)

    def read(self) -> dict[str, MetricMetadata]:
        """Read the metadata JSON file and return a dictionary keyed by metric name.

        Returns:
            dict[str, MetricMetadata]: Mapping of metric name to its parsed metadata.

        """
        with self.file_path.open("r", encoding="utf-8") as f:
            raw_metadata: dict[str, dict] = json.load(f)

        return {
            name: MetricMetadata(
                metric_type=MetricType[entry["metric_type"]],
                warning_threshold=entry.get("warning_threshold"),
                critical_threshold=entry.get("critical_threshold"),
                alias=entry["alias"],
                description=entry["description"],
                component_type=ComponentType[entry["component_type"]],
            )
            for name, entry in raw_metadata.items()
        }

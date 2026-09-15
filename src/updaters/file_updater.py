import json
from datetime import datetime
from pathlib import Path

from src.metric.metric_updater import MetricUpdater
from src.metric.model.metric import Metric
from src.updaters.model.stored_metrics import StoredMetrics


class FileUpdater(MetricUpdater):
    def __init__(self, file_name: str):
        self.file_name = file_name

    def update(self, metrics: list[Metric]):
        # Build filename from class filename, current folder, and current date
        timestamp = datetime.now().strftime("%Y%m%d")
        output_file = Path(f"{self.file_name}_{timestamp}.json")

        # Create StoredMetrics object with the provided metrics and current timestamp
        stored_metrics_obj = StoredMetrics(metrics=metrics, stored_at=datetime.now())

        # Field serializers on the model ensure datetime/enum values are JSON-serializable
        metrics_data = stored_metrics_obj.model_dump()

        # Append as a JSON Line so multiple updates in the same day accumulate in one file
        with output_file.open("a") as f:
            f.write(json.dumps(metrics_data))
            f.write("\n")

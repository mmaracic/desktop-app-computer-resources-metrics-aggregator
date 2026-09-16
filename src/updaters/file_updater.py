import json
from datetime import UTC, datetime
from pathlib import Path

from src.metric.metric_updater import MetricUpdater
from src.metric.model.metric import Metric
from src.storage.disk_text_file_storage import DiskTextFileStorage
from src.updaters.model.stored_metrics import StoredMetrics


class FileUpdater(MetricUpdater):
    def __init__(self, file_name: str, base_path: str = "."):
        self.file_name = file_name
        self.storage = DiskTextFileStorage(base_path)

    def update(self, metrics: list[Metric]):
        # Build filename from class filename, current folder, and current date
        timestamp = datetime.now(UTC).strftime("%Y%m%d")
        output_file = Path(f"{self.file_name}_{timestamp}.json")

        # Create StoredMetrics object with the provided metrics and current timestamp
        stored_metrics_obj = StoredMetrics(metrics=metrics, stored_at=datetime.now(UTC))

        # Field serializers on the model ensure datetime/enum values are JSON-serializable
        metrics_data = stored_metrics_obj.model_dump()

        # Append as a JSON Line so multiple updates in the same day accumulate in one file
        self.storage.save_file(str(output_file), json.dumps(metrics_data) + "\n")

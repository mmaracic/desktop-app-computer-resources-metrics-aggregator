import json
from pathlib import Path

from src.metric.metric_updater import MetricUpdater
from src.metric.model.metrics_in_time import MetricsInTime
from src.storage.disk_text_file_storage import DiskTextFileStorage


class FileUpdater(MetricUpdater):
    def __init__(self, file_name: str, storage: DiskTextFileStorage) -> None:
        self.file_name = file_name
        self.storage = storage

    def update(self, metrics_in_time: MetricsInTime) -> None:
        # Build filename from class filename, current folder, and date only (no time)
        date_str = metrics_in_time.stored_at.strftime("%Y%m%d")
        output_file = Path(f"{self.file_name}_{date_str}.json")

        # Field serializers on the metrics_in_time model ensure datetime/enum values are JSON-serializable
        metrics_data = metrics_in_time.model_dump()

        # Append as a JSON Line so multiple updates in the same day accumulate in one file
        self.storage.save_file(str(output_file), json.dumps(metrics_data) + "\n")

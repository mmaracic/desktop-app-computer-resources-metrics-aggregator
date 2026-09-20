import json
import logging
from datetime import datetime
from pathlib import Path

from src.metric.model.metric import Metric
from src.metric.model.metric_metadata import MetricMetadata
from src.metric.model.metrics_in_time import MetricsInTime
from src.service.utils_service import UtilsService
from src.storage.azure_blob_storage import AzureBlobStorage
from src.storage.disk_text_file_storage import DiskTextFileStorage

logger = logging.getLogger(__name__)


class MetricsService:
    def __init__(
        self,
        azure_storage: AzureBlobStorage | None,
        disk_storage: DiskTextFileStorage,
        base_file_name: str,
    ) -> None:
        """Initialize the metrics service with optional Azure storage and local disk storage."""
        self.azure_storage = azure_storage
        self.disk_storage = disk_storage
        self.base_file_name = base_file_name

    def _load_metrics_from_file(self, file_path: str) -> list[MetricsInTime]:
        """Load metrics from a JSON Lines file (one MetricsInTime object per line).

        Args:
            file_path (str): The path to the JSON file.

        Returns:
            list[MetricsInTime]: List of parsed MetricsInTime objects.

        """
        metrics_in_time_list: list[MetricsInTime] = []

        try:
            file_content = self.disk_storage.read_file(file_path)
            lines = file_content.strip().split("\n")

            for line in lines:
                if not line.strip():
                    continue

                data = json.loads(line)

                stored_at = datetime.fromisoformat(data["stored_at"])

                metrics = []
                for metric_data in data.get("metrics", []):
                    metric = Metric(
                        name=metric_data["name"],
                        value=metric_data["value"],
                        metadata=MetricMetadata(**metric_data.get("metadata", {})),
                    )
                    metrics.append(metric)

                metrics_in_time_list.append(
                    MetricsInTime(stored_at=stored_at, metrics=metrics),
                )

        except (KeyError, ValueError) as e:
            logger.warning("Failed to load metrics from file %s: %s", file_path, e)

        return metrics_in_time_list

    def _filter_metrics_by_datetime_range(
        self,
        metrics_in_time: list[MetricsInTime],
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> list[MetricsInTime]:
        """Filter metrics from a list of MetricsInTime objects that fall within the datetime range.

        Args:
            metrics_in_time (list[MetricsInTime]): The batch of metrics to filter.
            start_datetime (datetime): The start of the datetime range (inclusive).
            end_datetime (datetime): The end of the datetime range (inclusive).

        Returns:
            list[MetricsInTime]: List of MetricsInTime objects that fall within the datetime range.

        """
        return [
            mit
            for mit in metrics_in_time
            if start_datetime <= mit.stored_at <= end_datetime
        ]

    def retrieve_metrics_by_datetime_range(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        container_name: str | None = None,
    ) -> list[MetricsInTime]:
        """Retrieve MetricsInTime data from both local and Azure storage within a datetime range.

        Local files always take precedence over Azure files to avoid downloading files that are already present locally.

        Args:
            start_datetime (datetime): The start of the datetime range (inclusive).
            end_datetime (datetime): The end of the datetime range (inclusive).
            container_name (str | None): Optional Azure container name. If provided, Azure files will be considered
                                         for files not present locally.

        Returns:
            list[MetricsInTime]: List of MetricsInTime objects containing metrics within the datetime range.
                                 Each MetricsInTime represents a unique timestamp with its associated metrics.

        """
        logger.info(
            "Retrieving metrics from %s to %s",
            start_datetime.isoformat(),
            end_datetime.isoformat(),
        )

        # Collect all file paths (local and Azure) that might contain relevant data
        candidate_files: dict[
            str,
            str,
        ] = {}  # file_name -> full local path; azure files will be downloaded and converted to local if needed

        # Get local files
        local_files = self.disk_storage.list_files()
        logger.info("Found %d local files", len(local_files))

        for file_name in local_files:
            parsed_datetime = UtilsService.parse_datetime_from_filename(
                file_name=file_name, base_file_name=self.base_file_name,
            )
            if parsed_datetime and start_datetime <= parsed_datetime <= end_datetime:
                full_path = str(Path(self.disk_storage.base_path) / file_name)
                candidate_files[file_name] = full_path

        # Get Azure files that are missing locally if container name is provided
        if self.azure_storage and container_name:
            azure_files = self.azure_storage.get_container_blobs(container_name)

            for blob in azure_files:
                parsed_datetime = UtilsService.parse_datetime_from_filename(
                    file_name=blob.name,
                    base_file_name=self.base_file_name,
                )
                if (
                    parsed_datetime
                    and start_datetime <= parsed_datetime <= end_datetime
                    and blob.name not in candidate_files
                ):
                    logger.info(
                        "Azure blob in range and not present locally: %s",
                        blob.name,
                    )
                    data_blob = self.azure_storage.download_blob(blob)
                    if not data_blob or not data_blob.data:
                        logger.warning(
                            "Failed to download Azure blob or empty data: %s",
                            blob.name,
                        )
                        continue
                    json_data = json.loads(data_blob.data)
                    self.disk_storage.save_file(blob.name, json_data)
                    logger.info(
                        "Downloaded and saved Azure blob locally: %s",
                        blob.name,
                    )
                    candidate_files[blob.name] = str(
                        Path(self.disk_storage.base_path) / blob.name,
                    )

        # Process local files and extract metrics in time within the specified datetime range
        result_metrics_in_time: list[MetricsInTime] = []

        for file_name, full_path in candidate_files.items():
            try:
                loaded_metrics = self._load_metrics_from_file(full_path)
                logger.info(
                    "Loaded %d metrics from file: %s",
                    len(loaded_metrics),
                    file_name,
                )

                # Filter metrics within the datetime range
                filtered_metrics = self._filter_metrics_by_datetime_range(
                    loaded_metrics,
                    start_datetime,
                    end_datetime,
                )
                result_metrics_in_time.extend(filtered_metrics)
            except Exception:
                logger.exception("Failed to process file %s", full_path)

        logger.info(
            "Retrieved %d MetricsInTime objects",
            len(result_metrics_in_time),
        )
        return result_metrics_in_time

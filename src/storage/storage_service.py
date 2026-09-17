import logging
import re
from datetime import UTC, datetime, timedelta

from src.storage.azure_blob_storage import AzureBlobStorage, RepoBlob, StorageTier
from src.storage.disk_text_file_storage import DiskTextFileStorage

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(
        self,
        azure_storage: AzureBlobStorage,
        disk_storage: DiskTextFileStorage,
        base_file_name: str,
    ):
        self.azure_storage = azure_storage
        self.disk_storage = disk_storage
        self.base_file_name = base_file_name

    def upload_local_files_to_azure(self, container_name: str):
        local_files = self.disk_storage.list_files()
        azure_files = self.azure_storage.list_files()
        timestamp = datetime.now(UTC).strftime("%Y%m%d")
        today_pattern = re.compile(
            f"^{re.escape(self.base_file_name)}_{timestamp}\\.json$"
        )

        for file_name in local_files:
            if file_name not in azure_files and file_name:
                # Skip today's file to avoid redundant uploads (it will be updated during the day)
                if today_pattern.match(file_name):
                    continue
                logger.info("Uploading file: %s", file_name)
                file_content = self.disk_storage.read_file(file_name)
                blob = RepoBlob(
                    name=file_name,
                    container=container_name,
                    size=len(file_content),
                    data=file_content.encode("utf-8"),
                )
                self.azure_storage.upload_blob(blob, False)
                logger.info("Successfully uploaded file: %s", file_name)

    def change_tier_of_blobs_in_azure(self, container_name: str):
        azure_files = self.azure_storage.get_container_blobs(container_name)
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)

        for blob in azure_files:
            file_name = blob.name
            current_tier = self.azure_storage.get_blob_tier(blob)

            if current_tier not in (StorageTier.HOT, StorageTier.COLD):
                raise ValueError(
                    f"Blob {file_name} is in tier {current_tier}, only Hot and Cold tiers are allowed"
                )

            if (
                current_tier == StorageTier.HOT
                and blob.created_at
                and blob.created_at < seven_days_ago
            ):
                logger.info(
                    "Blob %s is in Hot tier and older than 7 days, changing to Cold",
                    file_name,
                )
                self.azure_storage.set_blob_tier(blob, StorageTier.COLD)
            elif current_tier == StorageTier.HOT:
                logger.info(
                    "Blob %s is in Hot tier but less than 7 days old, keeping as is",
                    file_name,
                )
            elif current_tier == StorageTier.COLD:
                logger.info("Blob %s is already in Cold tier, keeping as is", file_name)

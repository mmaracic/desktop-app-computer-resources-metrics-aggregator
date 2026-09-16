"""Azure Blob Storage repository implementation."""

from enum import Enum

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient
from pydantic import BaseModel


class StorageTier(str, Enum):
    """Azure Blob Storage tier options."""

    HOT = "Hot"
    COOL = "Cool"
    COLD = "Cold"
    ARCHIVE = "Archive"


class RepoBlob(BaseModel):
    """Data model for Azure Blob Storage repository configuration."""

    name: str
    container: str
    size: int
    data: bytes | None = None
    tier: StorageTier = StorageTier.HOT


class AzureBlobStorage:
    """Repository for Azure Blob Storage interactions."""

    def __init__(
        self,
        connection_string: str,
    ) -> None:
        """Initialize Azure Blob Repository with connection string and container name."""
        self.connection_string = connection_string
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string,
        )

    def get_container_list(self) -> list[str]:
        """Get a list of container names in the Blob Storage account.

        Returns:
            list[str]: List of container names.

        """
        containers = self.blob_service_client.list_containers()
        return [container.name for container in containers]

    def is_container(self, container_name: str) -> bool:
        """Check if a container exists in the Blob Storage account.

        Args:
            container_name (str): The name of the container.

        Returns:
            bool: True if the container exists, False otherwise.

        """
        containers = self.get_container_list()
        return container_name in containers

    def create_container(self, container_name: str) -> None:
        """Create a new container in the Blob Storage account.

        Args:
            container_name (str): The name of the container to create.

        """
        self.blob_service_client.create_container(container_name)

    def get_container_blobs(self, container_name: str) -> list[RepoBlob]:
        """Get a list of blob names in the specified container.

        Args:
            container_name (str): The name of the container.

        Returns:
            list[str]: List of blob names.

        """
        container_client = self.blob_service_client.get_container_client(container_name)
        blobs = container_client.list_blobs()
        return [
            RepoBlob(name=blob.name, container=container_name, size=blob.size)
            for blob in blobs
        ]

    def upload_blob(self, blob: RepoBlob, overwrite: bool = True) -> bool:
        """Upload a blob to the specified container.

        Args:
            blob (RepoBlob): The blob to upload.
            overwrite (bool): Whether to overwrite the blob if it already exists.

        """
        container_client = self.blob_service_client.get_container_client(blob.container)
        if not container_client.exists():
            self.create_container(blob.container)
        try:
            container_client.upload_blob(
                name=blob.name,
                data=blob.data,
                overwrite=False,
                metadata={"tier": blob.tier.value},
            )
        except ResourceExistsError:
            if overwrite:
                container_client.upload_blob(
                    name=blob.name,
                    data=blob.data,
                    overwrite=True,
                    metadata={"tier": blob.tier.value},
                )
                return True
        return False

    def download_blob(self, blob: RepoBlob) -> RepoBlob:
        """Download a blob from the specified container.

        Args:
            blob (RepoBlob): The blob to download.

        Returns:
            RepoBlob: The downloaded blob with data.

        """
        container_client = self.blob_service_client.get_container_client(blob.container)
        blob_client = container_client.get_blob_client(blob.name)
        downloader = blob_client.download_blob()
        return RepoBlob(
            name=blob.name,
            container=blob.container,
            size=downloader.properties.size,
            data=downloader.readall(),
        )

    def get_blob_tier(self, blob: RepoBlob) -> StorageTier | None:
        """Get the storage tier of a blob.

        Args:
            blob (RepoBlob): The blob to check.

        Returns:
            StorageTier | None: The storage tier if available, None otherwise.

        """
        container_client = self.blob_service_client.get_container_client(blob.container)
        blob_client = container_client.get_blob_client(blob.name)
        properties = blob_client.get_blob_properties()
        tier = properties.blob_tier
        return tier if tier else None

    def set_blob_tier(self, blob: RepoBlob, tier: StorageTier) -> bool:
        """Set the storage tier for a blob.

        Args:
            blob (RepoBlob): The blob to update.
            tier (StorageTier): The new storage tier.

        Returns:
            bool: True if successful, False otherwise.

        """
        container_client = self.blob_service_client.get_container_client(blob.container)
        blob_client = container_client.get_blob_client(blob.name)
        try:
            blob_client.set_standard_blob_tier(tier)
            return True
        except ResourceExistsError:
            return False

"""Unit tests for StorageService, ensuring today's files are not uploaded to Azure."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.storage.azure_blob_storage import AzureBlobStorage, RepoBlob, StorageTier
from src.storage.disk_text_file_storage import DiskTextFileStorage
from src.storage.storage_service import StorageService


class MockAzureStorage(AzureBlobStorage):
    """Mock Azure Blob Storage for testing purposes."""

    def __init__(self) -> None:
        """Initialize the mock Azure storage without connecting to actual Azure."""
        # Don't call parent __init__ to avoid actual Azure connection
        self.connection_string = "mock_connection_string"
        self.blob_service_client = None
        self.uploaded_files: list[str] = []
        self.uploaded_content: dict[str, bytes] = {}
        self.list_files_result: list[str] = []
        self.container_blobs_result: list[RepoBlob] = []
        self.blob_tiers: dict[str, StorageTier] = {}
        self.tier_changes: list[tuple[str, StorageTier]] = []

    def upload_blob(self, blob: RepoBlob, overwrite: bool = True) -> bool:
        """Mock upload_blob method that records uploaded files."""
        self.uploaded_files.append(blob.name)
        self.uploaded_content[blob.name] = blob.data or b""
        return True

    def list_files(self) -> list[str]:
        """Mock list_files method that returns pre-defined results."""
        return self.list_files_result

    def get_container_blobs(self, container_name: str) -> list[RepoBlob]:  # noqa: ARG002
        """Mock get_container_blobs method that returns pre-defined results."""
        return self.container_blobs_result

    def get_blob_tier(self, blob: RepoBlob) -> StorageTier | None:
        """Mock get_blob_tier method that returns pre-defined tiers by blob name."""
        return self.blob_tiers.get(blob.name)

    def set_blob_tier(self, blob: RepoBlob, tier: StorageTier) -> bool:
        """Mock set_blob_tier method that records tier changes."""
        self.tier_changes.append((blob.name, tier))
        self.blob_tiers[blob.name] = tier
        return True


def _build_mock_disk_storage(base_path: Path) -> DiskTextFileStorage:
    """Build a mock DiskTextFileStorage with test files."""
    storage = DiskTextFileStorage(str(base_path))
    base_path.mkdir(parents=True, exist_ok=True)

    # Create some test files
    (base_path / "yesterday_metrics_20260916.json").write_text('{"data": "old"}\n')
    (base_path / "other_file.json").write_text('{"data": "other"}\n')

    return storage


def _get_today_timestamp() -> str:
    """Get today's timestamp in YYYYMMDD format."""
    return datetime.now(UTC).strftime("%Y%m%d")


@patch("src.storage.storage_service.datetime")
def test_upload_skips_todays_file(mock_datetime: MagicMock, tmp_path: Path) -> None:
    """Test that today's file is skipped during upload to avoid redundant uploads."""
    # Setup mock datetime
    fixed_date = datetime(2026, 9, 17, 12, 0, 0, tzinfo=UTC)
    mock_datetime.now.return_value = fixed_date

    # Create mock storages
    azure_storage = MockAzureStorage()
    disk_storage = _build_mock_disk_storage(tmp_path)

    # Set up Azure storage to return empty list (no files exist in Azure)
    azure_storage.list_files_result = []

    # Create service with today's filename
    base_file_name = "daily_metrics"
    service = StorageService(azure_storage, disk_storage, base_file_name)

    # Execute upload
    service.upload_local_files_to_azure("test-container")

    # Verify that today's file was NOT uploaded
    today_timestamp = _get_today_timestamp()
    today_file_pattern = f"{base_file_name}_{today_timestamp}.json"
    assert today_file_pattern not in azure_storage.uploaded_files, (
        "Today's file should be skipped"
    )

    # Verify that other files were uploaded, along with their content
    assert "yesterday_metrics_20260916.json" in azure_storage.uploaded_files
    assert azure_storage.uploaded_content["yesterday_metrics_20260916.json"] == (
        b'{"data": "old"}\n'
    )


@patch("src.storage.storage_service.datetime")
def test_upload_skips_todays_file_when_exists_in_azure(
    mock_datetime: MagicMock,
    tmp_path: Path,
) -> None:
    """Test that today's file is skipped when it already exists in Azure."""
    # Setup mock datetime
    fixed_date = datetime(2026, 9, 17, 12, 0, 0, tzinfo=UTC)
    mock_datetime.now.return_value = fixed_date

    # Create mock storages
    azure_storage = MockAzureStorage()
    disk_storage = _build_mock_disk_storage(tmp_path)

    # Set up Azure storage to return today's file (simulating it already exists in Azure)
    today_timestamp = _get_today_timestamp()
    azure_storage.list_files_result = [f"daily_metrics_{today_timestamp}.json"]

    # Create service with today's filename
    base_file_name = "daily_metrics"
    service = StorageService(azure_storage, disk_storage, base_file_name)

    # Execute upload - should skip today's file (not raise exception)
    service.upload_local_files_to_azure("test-container")

    # Verify that non-today files were uploaded
    assert "yesterday_metrics_20260916.json" in azure_storage.uploaded_files
    assert "other_file.json" in azure_storage.uploaded_files
    # Today's file should NOT be uploaded (skipped because it exists in Azure)
    assert f"daily_metrics_{today_timestamp}.json" not in azure_storage.uploaded_files


@patch("src.storage.storage_service.datetime")
def test_upload_handles_empty_file_list(
    mock_datetime: MagicMock,
    tmp_path: Path,
) -> None:
    """Test that upload handles empty file list gracefully."""
    # Setup mock datetime
    fixed_date = datetime(2026, 9, 17, 12, 0, 0, tzinfo=UTC)
    mock_datetime.now.return_value = fixed_date

    # Create mock storages with empty disk storage
    azure_storage = MockAzureStorage()
    disk_storage = DiskTextFileStorage(str(tmp_path))

    # Set up Azure storage to return empty list
    azure_storage.list_files_result = []

    # Create service
    base_file_name = "daily_metrics"
    service = StorageService(azure_storage, disk_storage, base_file_name)

    # Execute upload - should not raise any exceptions
    service.upload_local_files_to_azure("test-container")

    # Verify no files were uploaded
    assert azure_storage.uploaded_files == []


@patch("src.storage.storage_service.datetime")
def test_upload_skips_empty_filenames(mock_datetime: MagicMock, tmp_path: Path) -> None:
    """Test that empty filenames are skipped during upload."""
    # Setup mock datetime
    fixed_date = datetime(2026, 9, 17, 12, 0, 0, tzinfo=UTC)
    mock_datetime.now.return_value = fixed_date

    # Create mock storages
    azure_storage = MockAzureStorage()
    disk_storage = _build_mock_disk_storage(tmp_path)

    # Set up Azure storage to return empty list
    azure_storage.list_files_result = []

    # Execute upload
    service = StorageService(azure_storage, disk_storage, "daily_metrics")
    service.upload_local_files_to_azure("test-container")

    # Verify that only non-empty files were uploaded
    assert "yesterday_metrics_20260916.json" in azure_storage.uploaded_files
    assert "" not in azure_storage.uploaded_files


@patch("src.storage.storage_service.datetime")
def test_upload_pattern_matching_with_special_characters(
    mock_datetime: MagicMock,
    tmp_path: Path,
) -> None:
    """Test that filename pattern matching works with special characters."""
    # Setup mock datetime
    fixed_date = datetime(2026, 9, 17, 12, 0, 0, tzinfo=UTC)
    mock_datetime.now.return_value = fixed_date

    # Create mock storages with filename containing special characters
    azure_storage = MockAzureStorage()
    disk_storage = DiskTextFileStorage(str(tmp_path))

    # Create a file with special characters in the name
    (tmp_path / "daily-metrics_v2.json").write_text('{"data": "special"}\n')

    # Set up Azure storage to return empty list
    azure_storage.list_files_result = []

    # Create service with filename containing special characters
    base_file_name = "daily-metrics_v2"
    service = StorageService(azure_storage, disk_storage, base_file_name)

    # Execute upload
    service.upload_local_files_to_azure("test-container")

    # Verify that the file with special characters was uploaded (not today's pattern)
    today_timestamp = _get_today_timestamp()
    today_pattern = f"daily-metrics_v2_{today_timestamp}.json"
    assert "daily-metrics_v2.json" in azure_storage.uploaded_files
    assert today_pattern not in azure_storage.uploaded_files


@patch("src.storage.storage_service.datetime")
def test_upload_does_not_reupload_existing_azure_files(
    mock_datetime: MagicMock,
    tmp_path: Path,
) -> None:
    """Test that files already present in Azure are not re-uploaded."""
    fixed_date = datetime(2026, 9, 17, 12, 0, 0, tzinfo=UTC)
    mock_datetime.now.return_value = fixed_date

    azure_storage = MockAzureStorage()
    disk_storage = _build_mock_disk_storage(tmp_path)

    # Simulate that other_file.json already exists in Azure
    azure_storage.container_blobs_result = [
        RepoBlob(name="other_file.json", container="test", size=0, data=b"")
    ]

    service = StorageService(azure_storage, disk_storage, "daily_metrics")
    service.upload_local_files_to_azure("test-container")

    assert "other_file.json" not in azure_storage.uploaded_files
    assert "yesterday_metrics_20260916.json" in azure_storage.uploaded_files


def _make_blob(name: str, created_at: datetime) -> RepoBlob:
    return RepoBlob(
        name=name,
        container="test-container",
        size=10,
        created_at=created_at,
    )


@patch("src.storage.storage_service.datetime")
def test_change_tier_moves_old_hot_blob_to_cold(
    mock_datetime: MagicMock,
    tmp_path: Path,
) -> None:
    """Test that a Hot blob older than 7 days is moved to Cold tier."""
    fixed_date = datetime(2026, 9, 17, 12, 0, 0, tzinfo=UTC)
    mock_datetime.now.return_value = fixed_date

    azure_storage = MockAzureStorage()
    disk_storage = DiskTextFileStorage(str(tmp_path))

    old_blob = _make_blob("old_hot.json", datetime(2026, 9, 1, tzinfo=UTC))
    azure_storage.container_blobs_result = [old_blob]
    azure_storage.blob_tiers = {"old_hot.json": StorageTier.HOT}

    service = StorageService(azure_storage, disk_storage, "daily_metrics")
    service.change_tier_of_blobs_in_azure("test-container")

    assert azure_storage.tier_changes == [("old_hot.json", StorageTier.COLD)]


@patch("src.storage.storage_service.datetime")
def test_change_tier_keeps_recent_hot_blob(
    mock_datetime: MagicMock,
    tmp_path: Path,
) -> None:
    """Test that a Hot blob newer than 7 days is left unchanged."""
    fixed_date = datetime(2026, 9, 17, 12, 0, 0, tzinfo=UTC)
    mock_datetime.now.return_value = fixed_date

    azure_storage = MockAzureStorage()
    disk_storage = DiskTextFileStorage(str(tmp_path))

    recent_blob = _make_blob("recent_hot.json", datetime(2026, 9, 15, tzinfo=UTC))
    azure_storage.container_blobs_result = [recent_blob]
    azure_storage.blob_tiers = {"recent_hot.json": StorageTier.HOT}

    service = StorageService(azure_storage, disk_storage, "daily_metrics")
    service.change_tier_of_blobs_in_azure("test-container")

    assert azure_storage.tier_changes == []


@patch("src.storage.storage_service.datetime")
def test_change_tier_keeps_cold_blob_unchanged(
    mock_datetime: MagicMock,
    tmp_path: Path,
) -> None:
    """Test that a Cold blob is left unchanged regardless of age."""
    fixed_date = datetime(2026, 9, 17, 12, 0, 0, tzinfo=UTC)
    mock_datetime.now.return_value = fixed_date

    azure_storage = MockAzureStorage()
    disk_storage = DiskTextFileStorage(str(tmp_path))

    cold_blob = _make_blob("cold.json", datetime(2026, 1, 1, tzinfo=UTC))
    azure_storage.container_blobs_result = [cold_blob]
    azure_storage.blob_tiers = {"cold.json": StorageTier.COLD}

    service = StorageService(azure_storage, disk_storage, "daily_metrics")
    service.change_tier_of_blobs_in_azure("test-container")

    assert azure_storage.tier_changes == []


@patch("src.storage.storage_service.datetime")
def test_change_tier_raises_for_disallowed_tier(
    mock_datetime: MagicMock,
    tmp_path: Path,
) -> None:
    """Test that a blob in a tier other than Hot or Cold raises ValueError."""
    fixed_date = datetime(2026, 9, 17, 12, 0, 0, tzinfo=UTC)
    mock_datetime.now.return_value = fixed_date

    azure_storage = MockAzureStorage()
    disk_storage = DiskTextFileStorage(str(tmp_path))

    archive_blob = _make_blob("archive.json", datetime(2026, 1, 1, tzinfo=UTC))
    azure_storage.container_blobs_result = [archive_blob]
    azure_storage.blob_tiers = {"archive.json": StorageTier.ARCHIVE}

    service = StorageService(azure_storage, disk_storage, "daily_metrics")

    import pytest

    with pytest.raises(ValueError, match="only Hot and Cold tiers are allowed"):
        service.change_tier_of_blobs_in_azure("test-container")


@patch("src.storage.storage_service.datetime")
def test_change_tier_handles_no_blobs(
    mock_datetime: MagicMock,
    tmp_path: Path,
) -> None:
    """Test that an empty container blob list does not raise or change anything."""
    fixed_date = datetime(2026, 9, 17, 12, 0, 0, tzinfo=UTC)
    mock_datetime.now.return_value = fixed_date

    azure_storage = MockAzureStorage()
    disk_storage = DiskTextFileStorage(str(tmp_path))
    azure_storage.container_blobs_result = []

    service = StorageService(azure_storage, disk_storage, "daily_metrics")
    service.change_tier_of_blobs_in_azure("test-container")

    assert azure_storage.tier_changes == []

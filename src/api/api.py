"""This module defines the API routes for the FastAPI application."""

from fastapi import APIRouter, HTTPException, Request

from src.config.metric_config import MetricConfig
from src.config.metric_config_reader_writer import MetricConfigReaderWriter
from src.metric.model.metrics_in_time import MetricsInTime
from src.service.metrics_service import MetricsService
from src.service.utils_service import UtilsService

# Error messages for consistency
METRICS_SERVICE_NOT_INITIALIZED = "MetricsService not initialized"
CONFIG_READER_WRITER_NOT_INITIALIZED = "Config reader/writer not initialized"

router = APIRouter()


@router.get(
    "/metrics/range",
)
def get_metrics_by_datetime_range(
    request: Request,
    start_datetime: str,
    end_datetime: str,
    container_name: str | None,
) -> list[MetricsInTime]:
    """Retrieve metrics within a datetime range.

    Local files always take precedence over Azure files.
    Azure files will only be considered if not present locally.

    Args:
        request: The FastAPI request object, used to access app.state.storage_service.
        start_datetime: The start of the datetime range (inclusive).
                       Format: ISO 8601 (e.g., "2024-01-01T00:00:00Z")
        end_datetime: The end of the datetime range (inclusive).
                     Format: ISO 8601 (e.g., "2024-12-31T23:59:59Z")
        container_name: Optional Azure container name. If provided, the API will also
                       check Azure Blob Storage for files not present locally.

    Returns:
        A list of MetricsInTime objects.

    Raises:
        HTTPException: If datetime parameters are invalid or if there's an error
                      retrieving data from storage.

    """
    # Get storage service from app.state
    metrics_service: MetricsService = request.app.state.metrics_service

    if metrics_service is None:
        raise HTTPException(
            status_code=500,
            detail=METRICS_SERVICE_NOT_INITIALIZED,
        )

    # Parse datetime strings
    try:
        start_dt = UtilsService.parse_datetime_from_string(start_datetime)
        end_dt = UtilsService.parse_datetime_from_string(end_datetime)
    except ValueError as e:
        raise ValueError(f"Invalid datetime format. Use ISO 8601 format: {e}") from e

    if start_dt > end_dt:
        raise ValueError("start_datetime must be before or equal to end_datetime")

    try:
        return metrics_service.retrieve_metrics_by_datetime_range(
            start_datetime=start_dt,
            end_datetime=end_dt,
            container_name=container_name,
        )
    except Exception as e:
        raise RuntimeError(f"Error retrieving metrics: {e}") from e


@router.get("/metrics/config")
def get_metric_configs(request: Request) -> list[MetricConfig]:
    """Retrieve all metric configurations.

    Returns the current metric configurations stored in the configuration file.
    If no configurations exist, returns an empty list with a success message.

    Args:
        request: The FastAPI request object, used to access app.state.config_reader_writer.

    Raises:
        HTTPException: If the config reader/writer is not initialized.

    """
    # Get config reader/writer from app.state
    config_reader_writer: MetricConfigReaderWriter = (
        request.app.state.config_reader_writer
    )
    if config_reader_writer is None:
        raise HTTPException(
            status_code=500,
            detail=CONFIG_READER_WRITER_NOT_INITIALIZED,
        )

    try:
        return config_reader_writer.read_configs()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving metric configurations: {e}",
        ) from e


@router.post("/metrics/config")
def store_metric_configs(request: Request, body: list[MetricConfig]) -> None:
    """Store or override all metric configurations.

    This endpoint allows storing a complete set of metric configurations,
    overriding any existing configurations. It does not support partial updates.

    Args:
        request: The FastAPI request object, used to access app.state.config_reader_writer.
        body: The request body containing the list of MetricConfig objects to store.

    Raises:
        HTTPException: If the config reader/writer is not initialized or if validation fails.

    Example:
        POST /metrics/config
        Body: [{"name": "gpu_utilization", "enabled": true, "order": 1, "color": "#00ff00"}]

    """
    # Validate the request body
    if not body or len(body) == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one metric configuration must be provided",
        )

    # Get config reader/writer from app.state
    config_reader_writer: MetricConfigReaderWriter = (
        request.app.state.config_reader_writer
    )
    if config_reader_writer is None:
        raise HTTPException(
            status_code=500,
            detail=CONFIG_READER_WRITER_NOT_INITIALIZED,
        )

    try:
        # Write the configurations (this will override any existing ones)
        config_reader_writer.write_configs(body)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error storing metric configurations: {e}",
        ) from e

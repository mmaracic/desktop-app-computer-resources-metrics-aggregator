"""This module defines the API routes for the FastAPI application."""

from fastapi import APIRouter, Request

from src.metric.model.metrics_in_time import MetricsInTime
from src.service.metrics_service import MetricsService
from src.service.utils_service import UtilsService

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
        raise RuntimeError("MetricsService not initialized")

    # Parse datetime strings
    try:
        start_dt = UtilsService.parse_datetime_from_string(start_datetime)
        end_dt = UtilsService.parse_datetime_from_string(end_datetime)
    except ValueError as e:
        raise ValueError(f"Invalid datetime format. Use ISO 8601 format: {e}")

    if start_dt > end_dt:
        raise ValueError("start_datetime must be before or equal to end_datetime")

    try:
        return metrics_service.retrieve_metrics_by_datetime_range(
            start_datetime=start_dt,
            end_datetime=end_dt,
            container_name=container_name,
        )
    except Exception as e:
        raise RuntimeError(f"Error retrieving metrics: {e}")

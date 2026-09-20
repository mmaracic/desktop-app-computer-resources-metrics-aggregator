"""Unit tests for UtilsService."""

from datetime import UTC, datetime

import pytest

from src.service.utils_service import UtilsService


def test_parse_datetime_from_valid_filename() -> None:
    """Test parsing a valid date from valid  filename."""
    service = UtilsService()

    file_name = "daily_metrics_20260919.json"
    result = service.parse_datetime_from_filename(file_name, "daily_metrics")

    assert result is not None
    expected = datetime(2026, 9, 19, 0, 0, 0, tzinfo=UTC)
    assert result == expected


def test_fail_to_parse_invalid_filename() -> None:
    """Test parsing a valid date from an invalid filename."""
    service = UtilsService()

    file_name = "invalid_filename.json"
    result = service.parse_datetime_from_filename(file_name, "daily_metrics")

    assert result is None


def test_fail_to_parse_invalid_date_from_valid_filename() -> None:
    """Test parsing an invalid date from a valid filename."""
    service = UtilsService()

    file_name = "daily_metrics_20261319.json"  # Invalid month 13
    with pytest.raises(ValueError, match="unconverted data"):
        service.parse_datetime_from_filename(file_name, "daily_metrics")


def test_parse_datetime_from_filename_with_time() -> None:
    """Test parsing a valid date and time from a valid filename."""
    service = UtilsService()

    file_name = "daily_metrics_20260919_123456.json"
    result = service.parse_datetime_from_filename(
        file_name, "daily_metrics", "%Y%m%d_%H%M%S",
    )

    assert result is not None
    expected = datetime(2026, 9, 19, 12, 34, 56, tzinfo=UTC)
    assert result == expected

def test_parse_datetime_from_string() -> None:
    """Test parsing a valid date from string."""
    service = UtilsService()

    datetime_string = "2026-09-19T20:51:01.850585+00:00"
    result = service.parse_datetime_from_string(datetime_string)

    assert result is not None
    expected = datetime(2026, 9, 19, 20, 51, 1, 850585, tzinfo=UTC)
    assert result == expected

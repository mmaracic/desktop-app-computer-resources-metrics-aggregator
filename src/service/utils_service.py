import re
from datetime import UTC, datetime

DATE_FORMAT = "%Y%m%d"
DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"


class UtilsService:
    @staticmethod
    def parse_datetime_from_filename(
        file_name: str,
        base_file_name: str,
        date_format: str = DATE_FORMAT,
    ) -> datetime | None:
        """Parse the datetime from a filename.

        Expected format: {base_file_name}_{YYYYMMDD}.json or {base_file_name}_{YYYYMMDD}_{HHMMSS}.json

        Args:
            file_name (str): The name of the file.
            base_file_name (str): The base name of the file without the date and extension.
            date_format (str): The format of the date in the filename. Defaults to DATE_FORMAT.

        Returns:
            datetime | None: The parsed datetime if successful, None otherwise.

        """
        pattern = re.compile(
            rf"^{re.escape(base_file_name)}_(.+)\.json$",
        )
        match = pattern.match(file_name)
        if not match:
            return None

        date_time_part = match.group(1)
        return datetime.strptime(date_time_part, date_format).replace(tzinfo=UTC)

    @staticmethod
    def parse_datetime_from_string(date_string: str) -> datetime:
        """Parse a datetime from an ISO 8601 string.

        Args:
            date_string (str): The datetime string in ISO 8601 format.

        Returns:
            datetime: The parsed datetime with UTC timezone.

        Raises:
            ValueError: If the date_string is not in a valid ISO 8601 format.

        """
        return datetime.strptime(date_string, DATE_TIME_FORMAT).replace(tzinfo=UTC)

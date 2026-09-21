import json
import logging
from pathlib import Path

from src.config.metric_config import MetricConfig

logger = logging.getLogger(__name__)


class MetricConfigReaderWriter:
    """Handles reading and writing metric configurations from/to a JSON file.

    This class provides methods to persist metric configurations to disk and
    load them back, with graceful handling of missing or corrupted files.

    The configuration file is stored in the project root directory as
    `metric_config.json`.

    Attributes:
        config_file_path: The absolute path to the metric configuration file.

    Example:
        >>> reader = MetricConfigReaderWriter()
        >>> configs = reader.read_configs()
        >>> if configs:
        ...     reader.update_config(configs[0], new_value=100)
        >>> reader.write_configs(configs)

    """

    def __init__(self, config_file_path: str | Path | None = None) -> None:
        """Initialize the MetricConfigReaderWriter.

        Args:
            config_file_path: Optional path to the configuration file.
                If not provided, defaults to `metric_config.json` in the project root.

        """
        self.config_file_path = (
            Path(config_file_path)
            if config_file_path
            else Path(__file__).parent.parent.parent / "metric_config.json"
        )

    def read_configs(self) -> list[MetricConfig]:
        """Read metric configurations from the JSON file.

        If the file does not exist or is empty, returns an empty list.

        Returns:
            A list of MetricConfig objects, or an empty list if there is no file.

        Example:
            >>> reader = MetricConfigReaderWriter()
            >>> configs = reader.read_configs()
            >>> for config in configs:
            ...     print(f"{config.name}: {config.enabled}")

        """
        if not self.config_file_path.exists():
            logger.debug(
                "Configuration file not found: %s. Returning empty list.",
                self.config_file_path,
            )
            return []

        with open(self.config_file_path, encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            logger.warning(
                "Configuration file does not contain a list. "
                "Content type: %s. Returning empty list.",
                type(data).__name__,
            )
            return []
        return [
            MetricConfig.model_validate(item) for item in data if isinstance(item, dict)
        ]

    def write_configs(self, configs: list[MetricConfig]) -> bool:
        """Write metric configurations to the JSON file.

        Overwrites any existing file with the new configurations.
        If writing fails for any reason, logs an error and returns False.

        Args:
            configs: A list of MetricConfig objects to write to the file.

        Returns:
            True if the write was successful, False otherwise.

        """
        try:
            # Convert configs to a list of dictionaries
            data = [config.model_dump() for config in configs]

            # Write to file with pretty formatting
            with open(self.config_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(
                "Successfully wrote %s metric configurations to %s",
                len(configs),
                self.config_file_path,
            )
            return True

        except Exception:
            logger.exception(
                "Failed to write metric configurations to %s.",
                self.config_file_path,
            )
            return False

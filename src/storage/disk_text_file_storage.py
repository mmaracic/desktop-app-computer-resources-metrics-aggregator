"""Repository for local disk storage interactions."""

import os
import re
from pathlib import Path


class DiskTextFileStorage:
    """DiskTextFileStorage repository for local disk storage interactions."""

    def __init__(self, base_path: str, metric_filename: str = "daily_metrics") -> None:
        """Initialize Disk Storage repository with a base path and metric filename pattern.

        Args:
            base_path (str): The base directory path for storing files.
            metric_filename (str): Base name of metric files. Files matching pattern
                                  {metric_filename}_YYYYMMDD.json will be returned.

        """
        self.base_path = Path(base_path).resolve()
        # Pattern matches files like: daily_metrics_20260919.json
        escaped_name = re.escape(metric_filename)
        self.file_pattern = re.compile(rf"^{escaped_name}_\d{{8}}\.json$")

    def list_files(self) -> list[str]:
        """List all metric data files in the base directory matching the configured pattern.

        Returns:
            list[str]: List of file paths relative to the base directory.

        """
        file_list = []
        for root, _, files in os.walk(self.base_path):
            for file in files:
                if self.file_pattern.match(file):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.base_path)
                    file_list.append(str(rel_path))
        return file_list

    def save_file(self, file_name: str, data: str) -> None:
        """Save a file to the local disk.

        Args:
            file_name (str): The name of the file to save.
            data (str): The file data to write.

        """
        file_path = self.base_path / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if file_path.exists() else "w"
        with file_path.open(mode=mode, encoding="utf-8") as f:
            f.write(data)

    def read_file(self, file_name: str) -> str:
        """Read a file from the local disk.

        Args:
            file_name (str): The name of the file to read.

        Returns:
            str: The file data.

        """
        file_path = self.base_path / file_name
        with file_path.open(encoding="utf-8") as f:
            return f.read()

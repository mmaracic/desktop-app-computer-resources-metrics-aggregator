class DiskTextFileStorage:
    """Repository for local disk storage interactions."""

    def __init__(self, base_path: str) -> None:
        """Initialize Disk Storage repository with a base path.

        Args:
            base_path (str): The base directory path for storing files.

        """
        self.base_path = base_path

    def list_files(self) -> list[str]:
        """List all files in the base directory.

        Returns:
            list[str]: List of file paths relative to the base directory.

        """
        import os

        file_list = []
        for root, _, files in os.walk(self.base_path):
            for file in files:
                file_list.append(
                    os.path.relpath(os.path.join(root, file), self.base_path),
                )
        return file_list

    def save_file(self, file_name: str, data: str) -> None:
        """Save a file to the local disk.

        Args:
            file_name (str): The name of the file to save.
            data (str): The file data to write.

        """
        import os

        file_path = os.path.join(self.base_path, file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if os.path.exists(file_path):
            mode = "a"
        else:
            mode = "w"
        with open(file_path, mode, encoding="utf-8") as f:
            f.write(data)

    def read_file(self, file_name: str) -> str:
        """Read a file from the local disk.

        Args:
            file_name (str): The name of the file to read.

        Returns:
            str: The file data.

        """
        import os

        file_path = os.path.join(self.base_path, file_name)
        with open(file_path, encoding="utf-8") as f:
            return f.read()

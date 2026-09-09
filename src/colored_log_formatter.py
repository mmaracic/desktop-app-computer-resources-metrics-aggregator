"""Colored log formatter using ANSI escape codes."""

import logging
from enum import StrEnum


class AnsiColor(StrEnum):
    """ANSI escape codes for terminal colors."""

    RESET = "\033[0m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BRIGHT_RED = "\033[91m"


_LEVEL_COLORS: dict[int, AnsiColor] = {
    logging.DEBUG: AnsiColor.CYAN,
    logging.INFO: AnsiColor.GREEN,
    logging.WARNING: AnsiColor.YELLOW,
    logging.ERROR: AnsiColor.RED,
    logging.CRITICAL: AnsiColor.BRIGHT_RED,
}


class ColoredLogFormatter(logging.Formatter):
    """Log formatter that colorizes the level name using ANSI escape codes."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with a colorized level name."""
        original_levelname: str = record.levelname
        color: AnsiColor = _LEVEL_COLORS.get(record.levelno, AnsiColor.RESET)
        record.levelname = f"{color}{record.levelname}{AnsiColor.RESET}"
        result: str = super().format(record)
        record.levelname = original_levelname
        return result

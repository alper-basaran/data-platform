import logging
import os

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
DEFAULT_LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def configure_logging(level: str | int | None = None) -> None:
    resolved_level: str | int = level or os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)
    root_logger = logging.getLogger()

    if root_logger.handlers:
        root_logger.setLevel(resolved_level)
        return

    logging.basicConfig(
        level=resolved_level,
        format=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_LOG_DATE_FORMAT,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

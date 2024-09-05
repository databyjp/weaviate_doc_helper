# Filepath: /src/weaviate_agent_demo/setup.py
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler


CLAUDE_SONNET = "claude-3-5-sonnet-20240620"
CLAUDE_HAIKU = "claude-3-haiku-20240307"
CLAUDE_MODEL = CLAUDE_SONNET
CLAUDE_LOGFILE = "logs/claude_logs.log"
APP_LOGFILE = "logs/app.log"

COLLECTION_NAME_CHUNKS = "Chunk"
COLLECTION_NAME_CACHED_ANSWERS = "Answers"


def configure_logging(
    log_file=APP_LOGFILE,
    max_file_size=1024 * 1024,
    backup_count=5,
    excluded_loggers=None,
):
    logfile_path = Path(log_file)
    logfile_path.parent.mkdir(parents=True, exist_ok=True)
    logfile_path.touch(exist_ok=True)

    if excluded_loggers is None:
        excluded_loggers = [
            "httpx",
            "httpcore",
            "asyncio",
            "grpc",
        ]  # Default loggers to exclude

    # Configure root logger
    logging.basicConfig(level=logging.DEBUG)
    root_logger = logging.getLogger()

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatters
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File Handler (with rotation)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_file_size, backupCount=backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Create a filter to exclude specified loggers
    class ExcludeLoggerFilter(logging.Filter):
        def filter(self, record):
            return not any(
                record.name.startswith(logger) for logger in excluded_loggers
            )

    # Add the filter to both handlers
    exclude_filter = ExcludeLoggerFilter()
    file_handler.addFilter(exclude_filter)
    console_handler.addFilter(exclude_filter)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info("Logging configured.")


# Configure logging when this module is imported
configure_logging()


def get_logger(name):
    return logging.getLogger(name)

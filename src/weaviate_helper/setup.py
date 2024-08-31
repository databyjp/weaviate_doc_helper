import logging


CLAUDE_MODEL = "claude-3-5-sonnet-20240620"
COLLECTION_NAME = "Chunk"


def setup_logging():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    return logger

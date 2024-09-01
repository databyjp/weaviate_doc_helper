# Filepath: demo.py
from weaviate_helper.coder import ask_llm_base
from weaviate_helper.prompts import SYSTEM_MSGS
from weaviate_helper.setup import get_logger
import logging


logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)


for user_query in [
    "How do I connect to an embedded Weaviate instance?",
    "What is multi-tenancy?",
    "How do I use filters in hybrid search with Python v4 client?",
]:
    r = ask_llm_base(
        user_query, SYSTEM_MSGS.WEAVIATE_EXPERT_SUPPORT.value, log_to_file=True
    )
    r = ask_llm_base(
        user_query,
        SYSTEM_MSGS.WEAVIATE_EXPERT_SUPPORT_WITH_TOOLS.value,
        use_tools=True,
        log_to_file=True,
    )

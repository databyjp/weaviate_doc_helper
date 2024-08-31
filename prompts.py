from enum import Enum


class SYSTEM_MSGS(Enum):
    WEAVIATE_EXPERT_SUPPORT = """
    You are an AI assistant tasked with helping users
    understand and implement Weaviate, a vector database.

    You are to write code example for them to run.

    Think before you write the answer in <thinking> tags.
    """


class EXAMPLE_USER_QUERIES(Enum):
    CONNECT_AND_RUN_HYBRID_SEARCH = """
    "How do I connect to a local Weaviate instance, and run a hybrid search, with the v4 Python client API?"
    """

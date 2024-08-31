from enum import Enum


class SYSTEM_MSGS(Enum):
    WEAVIATE_EXPERT_SUPPORT = """
    You are an AI assistant tasked with helping users
    understand and implement Weaviate, a vector database.

    You are to write code example for them to run.

    Think before you write the answer in <thinking> tags.
    """
    HYBRID_SEARCH_QUERY_WRITER = """
    You are an AI assistant with expertise in Weaviate and vector search.

    You are to write a hybrid search query for the user to run in Weaviate
    to find relevant information for their query.

    Think before you write the answer in <thinking> tags.
    """


class EXAMPLE_USER_QUERIES(Enum):
    NONEXISTENT_CLIENT_VERSION = """
    "How do I connect to Weaviate with the v6 Python client?"
    """
    CONNECT_AND_RUN_HYBRID_SEARCH = """
    "How do I connect to a local Weaviate instance, and run a hybrid search, with the v4 Python client API?"
    """

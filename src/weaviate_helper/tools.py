from .db import _search_generic
from typing import List


def _format_query(
    query: str,
) -> str:
    """
    Format & display the query.

    Args:
        query: A string representing the identified query term.
    """
    return query


def _get_weaviate_connection_snippet() -> str:
    """Get a code snippet for connecting to Weaviate."""
    return """
    # ===== CONNECT TO A CLOUD INSTANCE OF WEAVIATE =====
    import weaviate
    from weaviate.classes.init import Auth

    # Load API keys as required  # Recommended: save to an environment variable
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    cohere_key = os.getenv("COHERE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,                       # `weaviate_url`: your Weaviate URL
        auth_credentials=Auth.api_key(weaviate_key),    # `weaviate_key`: your Weaviate API key
        headers={
            "X-Anthropic-Api-Key": anthropic_key
            "X-Cohere-Api-Key": cohere_key
            "X-OpenAI-Api-Key": openai_key
        }
    )
    # ===== END OF CODE SNIPPET =====

    # ===== CONNECT TO A LOCAL INSTANCE OF WEAVIATE =====
    import weaviate

    client = weaviate.connect_to_local(
        headers={
            "X-Anthropic-Api-Key": anthropic_key
            "X-Cohere-Api-Key": cohere_key
            "X-OpenAI-Api-Key": openai_key
        }
    )
    # ===== END OF CODE SNIPPET =====
    """


def _search_text(query: str) -> List[str]:
    """
    Search Weaviate documentation text prose.
    Note this search does not include code examples.

    Args:
        query: The query string.
    Returns:
        A list of strings from the documentation text.
    """
    return _search_generic(query, "text")


def _search_code(query: str) -> List[str]:
    """
    Search Weaviate documentation code examples.
    Note this search does not include the associated prose.

    Args:
        query: The query string.
    Returns:
        A list of strings from the documentation code examples.
    """
    return _search_generic(query, "code")


def _search_any(query: str) -> List[str]:
    """
    Search Weaviate documentation code and text.

    Args:
        query: The query string.
    Returns:
        A list of strings from the documentation.
    """
    return _search_generic(query, "any")

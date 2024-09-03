# File: src/weaviate_agent_demo/tools.py
from .db import _search_generic
from typing import List
from anthropic.types import Message
from anthropic.types.text_block import TextBlock
from anthropic.types.tool_use_block import ToolUseBlock
from .setup import CLAUDE_MODEL, get_logger
from .prompts import SYSTEM_MSGS
import claudette
import logging


logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)


def _format_query_validity(
    is_valid: bool,
    reason: str,
) -> bool:
    """
    Format & display a boolean output.

    Args:
        is_valid: A boolean value.
        reason: A string explaining why the query is valid or invalid.
    """
    return {
        "is_valid": is_valid,
        "reason": reason,
    }


def _format_decomposed_query(
    queries: List[str],
) -> List[str]:
    """
    Format & display a list of one or more sub-queries.

    Args:
        queries: The list of one or more sub-queries.
    Returns:
        A list of one or more sub-queries.
        It could be just the original query as a list of one element, or a list of multiple queries.
    """
    return [queries]


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


def _decompose_search_query(user_query: str) -> List[str]:
    """
    Decompose a query into a list of sub-queries.
    This can be useful where a search query may comprise multiple ideas or concepts.
    Then, you can perform a search for each sub-query, and combine the results.

    Args:
        query: The query string.
    Returns:
        A list of smaller, more focused queries.
    """
    prompt = f"""
    The user want the following question to be answered.
    <user_query>{user_query}</user_query>
    We want to perform searches to find related documentation and code snippets.
    Would we be better served by searching for multiple, more focused queries?

    If so, please provide a list of sub-queries.
    """

    chat = claudette.Chat(
        model=CLAUDE_MODEL,
        sp=SYSTEM_MSGS.SEARCH_QUERY_DECOMPOSER.value,
        tools=[_format_decomposed_query],
    )

    r: Message = chat(prompt)

    for block in r.content:
        if isinstance(block, TextBlock):
            logger.debug(f"TextBlock: {block.text}")
        elif isinstance(block, ToolUseBlock):
            logger.debug(f"Using tool: {block.name}")
            logger.debug(f"Tool input: {block.input}")
            return block.input["queries"]

    logger.debug("No tool use block found, returning the original query.")
    return [user_query]

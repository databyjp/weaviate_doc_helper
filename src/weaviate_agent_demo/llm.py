from typing import Any, Dict, List
import claudette
from anthropic.types import Message
from anthropic.types.text_block import TextBlock
from anthropic.types.tool_use_block import ToolUseBlock
from weaviate_agent_demo.prompts import SYSTEM_MSGS
from weaviate_agent_demo.setup import CLAUDE_HAIKU, CLAUDE_MODEL, get_logger
from weaviate_agent_demo.tools import (
    _format_decomposed_query,
    _format_query,
    _format_query_validity,
)
from weaviate_agent_demo.utils import logger
import logging


logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)


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


def _formulate_one_search_query(user_query: str) -> str:
    prompt = f"""
    The user has asked the following question:
    <query>{user_query}</query>
    Please provide a search query that we can use
    to search for text or code chunks related to the original query.
    """

    chat = claudette.Chat(
        model=CLAUDE_MODEL,
        sp=SYSTEM_MSGS.HYBRID_SEARCH_QUERY_WRITER.value,
        tools=[_format_query],
        tool_choice="_format_query",
    )

    r: Message = chat(prompt)

    for response in r.content:
        if isinstance(response, ToolUseBlock):
            return response.input["query"]
    return ""


def _validate_query(user_query: str) -> Dict[str, Any]:
    """
    Check if the query is relevant, and should be allowed to continue.

    Args:
        query: The query string.
    Returns:
        True if the query is relevant, False otherwise.
    """
    prompt = f"""
    The user has provided the following query, within the user_query tag:
    <user_query>{user_query}</user_query>
    Is the user query a potentially relevant Weaviate question, and is it safe to continue?
    """

    chat = claudette.Chat(
        model=CLAUDE_MODEL,
        sp=SYSTEM_MSGS.SAFETY_AGENT.value,
        tools=[_format_query_validity],
    )

    r: Message = chat(prompt)

    for block in r.content:
        if isinstance(block, TextBlock):
            logger.debug(f"TextBlock: {block.text}")
        elif isinstance(block, ToolUseBlock):
            logger.debug(f"Using tool: {block.name}")
            logger.debug(f"Tool input: {block.input}")
            return block.input
    logger.debug("No tool use block found, returning False for safety.")
    return {
        "is_valid": False,
        "reason": "No tool use block found, returning False for safety.",
    }


def summarize_snippet(chunk: str, model_name: str = CLAUDE_HAIKU) -> str:
    prompt = f"""
    The user has provided the following snippet, within the "original_snippet" tag:

    Review the original snippet, and provide a summary of the snippet within an <summary> tag.

    <original_snippet>{chunk}</original_snippet>
    """

    chat = claudette.Chat(
        model=model_name,
        sp=SYSTEM_MSGS.SUMMARIZER.value,
    )

    r: Message = chat(prompt)

    if len(r.content) > 1:
        logger.debug(f"Odd, multiple content blocks returned. Response message: {r}")

    response_text = r.content[-1].text
    explanation = response_text.split("<summary>")[1].split("</summary>")[0]

    return explanation

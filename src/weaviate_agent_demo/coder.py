# Filepath: /src/weaviate_agent_demo/coder.py
import claudette
from typing import List, Optional
from anthropic.types import Message
from anthropic.types.text_block import TextBlock

from .llm import _decompose_search_query, _formulate_one_search_query, _validate_query
from .setup import CLAUDE_MODEL, get_logger
from .tools import (
    _get_weaviate_connection_snippet,
    _search_any,
    _search_code,
    _search_text,
)
from .utils import _log_claude_to_file
from .db import _add_answer_to_cache, _search_multiple
from .prompts import SYSTEM_MSGS
import logging


logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)


def get_tools(use_tools: bool = True) -> Optional[List[str]]:
    return [_search_text, _search_code] if use_tools else None


def generate_prompt(
    user_query: str, use_search: bool, use_reformulation: bool, search_results: str
) -> str:
    """
    Generate the prompt for the LLM based on the given parameters.

    Args:
    user_query (str): The original query from the user
    use_search (bool): Whether to use search results
    use_reformulation (bool): Whether the query was reformulated
    search_results (str): The results from the search (if applicable)

    Returns:
    str: The generated prompt
    """
    prompt = f"""
    The user has asked the following question:
    <query>{user_query}</query>
    """

    if use_search or use_reformulation:
        prompt += f"""
        Please answer the question using the search results below,
        and no other information.
        <search_results>{search_results}</search_results>
        """
    else:
        prompt += """
        Please answer the question, using the array of tools included.
        """

    return prompt


def ask_llm_base(
    user_query: str,
    system_prompt,
    use_search=False,
    use_reformulation=False,
    use_tools=False,
    max_steps=5,
    log_to_file=False,
    safety_check=False,
) -> Message:
    if safety_check:
        validity_assessment = _validate_query(user_query)
        if not validity_assessment["is_valid"]:
            logger.debug(f"Query '{user_query}' is not validated to continue.")
            logger.debug(f"Reason: {validity_assessment['reason']}")
            raise ValueError(f"Query '{user_query}' is not validated to continue.")

    processed_query = (
        _formulate_one_search_query(user_query) if use_reformulation else user_query
    )

    # Only use the search here if we are not using tool calling.
    # If using tool calling, the LLM will perform the search(es) itself.
    search_results = (
        _search_any(processed_query) if use_search or use_reformulation else ""
    )

    prompt = generate_prompt(user_query, use_search, use_reformulation, search_results)
    logger.debug(f"Prompt: {prompt}")

    chat = claudette.Chat(
        model=CLAUDE_MODEL, sp=system_prompt, tools=get_tools(use_tools)
    )

    if use_tools:
        r: Message = chat.toolloop(prompt, max_steps=max_steps)
    else:
        r: Message = chat(prompt)

    if log_to_file:
        _log_claude_to_file(
            user_query,
            use_tools,
            use_search,
            use_reformulation,
            processed_query,
            search_results,
            r,
        )

    logger.debug(f"Response: {r}")
    return r


def _ask_weaviate_agent(
    user_query: str,
    max_steps=5,
    add_to_cache=True,
) -> Message:
    validity_assessment = _validate_query(user_query)
    if not validity_assessment["is_valid"]:
        logger.debug(f"Query '{user_query}' is not validated to continue.")
        logger.debug(f"Reason: {validity_assessment['reason']}")
        raise ValueError(f"Query '{user_query}' is not validated to continue.")

    decomposed_queries = _decompose_search_query(user_query)

    search_results = _search_multiple(decomposed_queries)
    search_results.append(_get_weaviate_connection_snippet())

    prompt = f"""
    The user has asked the following question:
    <user_query>{user_query}</user_query>

    Please answer the question, using the provided text.
    <provided_text>{search_results}</provided_text>

    If you require further information, use the provided tools.
    """
    logger.debug(f"Prompt: {prompt}")

    system_prompt = SYSTEM_MSGS.WEAVIATE_EXPERT_FINAL.value
    chat = claudette.Chat(model=CLAUDE_MODEL, sp=system_prompt, tools=get_tools())

    r: Message = chat.toolloop(prompt, max_steps=max_steps)

    _log_claude_to_file(
        user_query,
        use_tools=True,
        use_search=False,
        use_reformulation=False,
        search_query=";".join(decomposed_queries),
        search_results=None,
        response=r,
    )

    logger.debug(f"Response: {r}")

    if add_to_cache:
        # Add "user_query" & response to Weaviate to cache the results.
        # If a similar query is asked again, we can use the cached results.
        if isinstance(r.content[-1], TextBlock):
            _add_answer_to_cache(user_query, r.content[-1].text)

    return r

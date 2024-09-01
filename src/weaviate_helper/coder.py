# Filepath: /src/weaviate_helper/coder.py
import claudette
from anthropic.types import Message
from anthropic.types.text_block import TextBlock
from anthropic.types.tool_use_block import ToolUseBlock
from typing import Union
from datetime import datetime
from .setup import CLAUDE_MODEL, CLAUDE_LOGFILE, get_logger
from .tools import (
    _get_weaviate_connection_snippet,
    _search_any,
    _search_code,
    _search_text,
)
from .utils import _get_search_query, _validate_query
import logging


logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)


def log_claude_to_file(user_query, use_tools, use_search, use_reformulation, search_query, search_results, response):
    with open(CLAUDE_LOGFILE, "a") as f:
        f.write("\n\n")
        f.write("*" * 80)
        f.write(f"Model: {CLAUDE_MODEL}\n")
        f.write(f"Timestamp: {datetime.now()}\n")
        f.write(f"User query: {user_query}\n")
        f.write(f"Use tools: {use_tools}\n")
        f.write(f"Use search: {use_search}\n")
        f.write(f"Use reformulation: {use_reformulation}\n")
        f.write(f"Search query: {search_query}\n")
        f.write(f"Search results: {search_results}\n")
        f.write(f"Raw Response:\n")
        f.write(f"{response.to_json(indent=2)}\n")
        f.write(f"Formatted Response:\n")
        for block in response.content:
            if isinstance(block, TextBlock):
                f.write(f"{block.type}\n")
                f.write(f"{block.text}\n")
            elif isinstance(block, ToolUseBlock):
                f.write(f"{block.type}\n")
                f.write(f"{block.name}\n")
                f.write(f"{block.input}\n")


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

    search_query = _get_search_query(user_query) if use_reformulation else user_query
    search_results = (
        _search_any(search_query) if use_search or use_reformulation else ""
    )

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
    elif use_tools:
        prompt += """
        Please answer the question, using the array of tools included.
        """

    logger.debug(f"Prompt: {prompt}")

    tools = (
        [_get_weaviate_connection_snippet, _search_text, _search_code]
        if use_tools
        else None
    )
    chat = claudette.Chat(model=CLAUDE_MODEL, sp=system_prompt, tools=tools)

    if use_tools:
        r: Message = chat.toolloop(prompt, max_steps=max_steps)
    else:
        r: Message = chat(prompt)

    if log_to_file:
        log_claude_to_file(user_query, use_tools, use_search, use_reformulation, search_query, search_results, r)

    logger.debug(f"Response: {r}")
    return r

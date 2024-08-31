import claudette
from anthropic.types import Message
from anthropic.types.text_block import TextBlock
from anthropic.types.tool_use_block import ToolUseBlock
from .prompts import SYSTEM_MSGS
from .setup import CLAUDE_MODEL, setup_logging
from .tools import (
    _get_weaviate_connection_snippet,
    _search_any,
    _search_code,
    _search_text,
)
from .utils import _get_search_query
import click

logger = setup_logging()


def process_response(r: Message):
    for block in r.content:
        if isinstance(block, TextBlock):
            click.echo(block.text)
        elif isinstance(block, ToolUseBlock):
            click.echo(f"Using tool: {block.name}")
            click.echo(f"Tool input: {block.input}")


def ask_llm_base(
    user_query: str,
    system_prompt,
    use_search=False,
    use_reformulation=False,
    use_tools=False,
    max_steps=5,
):
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

    logger.debug(f"Response: {r}")
    process_response(r)


@click.command()
@click.option(
    "--user-query", prompt="Enter your query", help="The user query for code generation"
)
def ask_llm(user_query: str):
    ask_llm_base(user_query, SYSTEM_MSGS.WEAVIATE_EXPERT_SUPPORT.value)


@click.command()
@click.option(
    "--user-query", prompt="Enter your query", help="The user query for code generation"
)
def ask_basic_ragbot(user_query: str):
    ask_llm_base(user_query, SYSTEM_MSGS.WEAVIATE_EXPERT_SUPPORT.value, use_search=True)


@click.command()
@click.option(
    "--user-query", prompt="Enter your query", help="The user query for code generation"
)
def ask_ragbot_with_reformulation(user_query: str):
    ask_llm_base(
        user_query,
        SYSTEM_MSGS.WEAVIATE_EXPERT_SUPPORT.value,
        use_search=True,
        use_reformulation=True,
    )


@click.command()
@click.option(
    "--user-query", prompt="Enter your query", help="The user query for code generation"
)
def ask_ragbot_with_tools(user_query: str):
    ask_llm_base(
        user_query, SYSTEM_MSGS.WEAVIATE_EXPERT_SUPPORT_WITH_TOOLS.value, use_tools=True
    )

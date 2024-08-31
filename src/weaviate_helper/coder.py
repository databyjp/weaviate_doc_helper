import claudette
from anthropic.types import Message
from anthropic.types.text_block import TextBlock
from anthropic.types.tool_use_block import ToolUseBlock
from .prompts import SYSTEM_MSGS
from .setup import CLAUDE_MODEL, setup_logging
from .tools import _get_weaviate_connection_snippet, _search_any, _search_code, _search_text
import click


logger = setup_logging()


@click.command()
@click.option(
    "--user-query", prompt="Enter your query", help="The user query for code generation"
)
def ask_llm(user_query: str):
    prompt = f"""
    The user has asked the following question:
    <query>{user_query}</query>
    """
    logger.debug(f"Prompt: {prompt}")

    chat = claudette.Chat(
        model=CLAUDE_MODEL,
        sp=SYSTEM_MSGS.WEAVIATE_EXPERT_SUPPORT.value,
    )

    r: Message = chat(prompt)
    logger.debug(f"Response: {r}")

    for block in r.content:
        click.echo(block.text)


@click.command()
@click.option(
    "--user-query", prompt="Enter your query", help="The user query for code generation"
)
def ask_basic_ragbot(user_query: str):
    search_results = _search_any(user_query)

    prompt = f"""
    The user has asked the following question:
    <query>{user_query}</query>

    Please answer the question using the search results below,
    and no other information.
    <search_results>{search_results}</search_results>
    """
    logger.debug(f"Prompt: {prompt}")

    chat = claudette.Chat(
        model=CLAUDE_MODEL,
        sp=SYSTEM_MSGS.WEAVIATE_EXPERT_SUPPORT.value,
    )

    r: Message = chat(prompt)
    logger.debug(f"Response: {r}")

    for block in r.content:
        click.echo(block.text)


@click.command()
@click.option(
    "--user-query", prompt="Enter your query", help="The user query for code generation"
)
def ask_ragbot_with_reformulation(user_query: str):
    search_results = _search_any(user_query)

    prompt = f"""
    The user has asked the following question:
    <query>{user_query}</query>

    Please answer the question using the search results below,
    and no other information.
    <search_results>{search_results}</search_results>
    """
    logger.debug(f"Prompt: {prompt}")

    chat = claudette.Chat(
        model=CLAUDE_MODEL,
        sp=SYSTEM_MSGS.WEAVIATE_EXPERT_SUPPORT.value,
    )

    r: Message = chat(prompt)
    logger.debug(f"Response: {r}")

    for block in r.content:
        click.echo(block.text)


@click.command()
@click.option(
    "--user-query", prompt="Enter your query", help="The user query for code generation"
)
def ask_ragbot_with_tools(user_query: str):
    prompt = f"""
    The user has asked the following question:
    <query>{user_query}</query>

    Please answer the question, using the array of tools included.
    """
    logger.debug(f"Prompt: {prompt}")

    chat = claudette.Chat(
        model=CLAUDE_MODEL,
        sp=SYSTEM_MSGS.WEAVIATE_EXPERT_SUPPORT_WITH_TOOLS.value,
        tools=[_get_weaviate_connection_snippet, _search_text, _search_code]
    )

    r: Message = chat.toolloop(prompt, max_steps=5)
    logger.debug(f"Response: {r}")

    for block in r.content:
        if isinstance(block, TextBlock):
            click.echo(block.text)
        elif isinstance(block, ToolUseBlock):
            click.echo(f"Using tool: {block.name}")
            click.echo(f"Using tool: {block.input}")

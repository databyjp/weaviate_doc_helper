import claudette
from anthropic.types import Message
from .prompts import SYSTEM_MSGS
from .setup import CLAUDE_MODEL, setup_logging
from .db import search_any
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
    search_results = search_any(user_query)

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

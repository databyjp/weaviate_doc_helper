# File: src/weaviate_helper/cli.py
import click
from .coder import ask_llm_base
from .prompts import SYSTEM_MSGS
from anthropic.types import Message
from anthropic.types.text_block import TextBlock
from anthropic.types.tool_use_block import ToolUseBlock


def process_response(r: Message):
    for block in r.content:
        if isinstance(block, TextBlock):
            click.echo(block.text)
        elif isinstance(block, ToolUseBlock):
            click.echo(f"Using tool: {block.name}")
            click.echo(f"Tool input: {block.input}")


@click.command()
@click.option(
    "--user-query", prompt="Enter your query", help="The user query for code generation"
)
def ask_llm(user_query: str):
    r = ask_llm_base(user_query, SYSTEM_MSGS.WEAVIATE_EXPERT_SUPPORT.value)
    process_response(r)


@click.command()
@click.option(
    "--user-query", prompt="Enter your query", help="The user query for code generation"
)
def ask_basic_ragbot(user_query: str):
    r = ask_llm_base(
        user_query, SYSTEM_MSGS.WEAVIATE_EXPERT_SUPPORT.value, use_search=True
    )
    process_response(r)


@click.command()
@click.option(
    "--user-query", prompt="Enter your query", help="The user query for code generation"
)
def ask_ragbot_with_reformulation(user_query: str):
    r = ask_llm_base(
        user_query,
        SYSTEM_MSGS.WEAVIATE_EXPERT_SUPPORT.value,
        use_search=True,
        use_reformulation=True,
    )
    process_response(r)


@click.command()
@click.option(
    "--user-query", prompt="Enter your query", help="The user query for code generation"
)
def ask_ragbot_with_tools(user_query: str):
    r = ask_llm_base(
        user_query, SYSTEM_MSGS.WEAVIATE_EXPERT_SUPPORT_WITH_TOOLS.value, use_tools=True
    )
    process_response(r)


@click.command()
@click.option(
    "--user-query", prompt="Enter your query", help="The user query for code generation"
)
def safely_ask_ragbot_with_tools(user_query: str):
    r = ask_llm_base(
        user_query,
        SYSTEM_MSGS.WEAVIATE_EXPERT_SUPPORT_WITH_TOOLS.value,
        use_tools=True,
        safety_check=True,
    )
    process_response(r)

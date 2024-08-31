import claudette
from anthropic.types import Message
from prompts import SYSTEM_MSGS
from setup import CLAUDE_MODEL, setup_logging
import click


logger = setup_logging()


@click.command()
@click.option(
    "--user-query", prompt="Enter your query", help="The user query for code generation"
)
def generate_code(user_query: str):
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


if __name__ == "__main__":
    #Try: "How do I connect to a local Weaviate instance, and run a hybrid search, with the v4 Python client API?"
    generate_code()

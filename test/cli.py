import pytest
from click.testing import CliRunner
from weaviate_agent_demo.cli import (
    ask_llm,
    ask_basic_ragbot,
    ask_ragbot_with_reformulation,
    ask_ragbot_with_tools,
    safely_ask_ragbot_with_tools,
)


query = "How do I connect to a local Weaviate instance, and run a hybrid search, with the v4 Python client API?"


@pytest.fixture
def runner():
    return CliRunner()


def test_ask_llm(runner):
    result = runner.invoke(ask_llm, input=query)
    assert result.exit_code == 0


def test_ask_basic_ragbot(runner):
    result = runner.invoke(ask_basic_ragbot, input=query)
    assert result.exit_code == 0


def test_ask_ragbot_with_reformulation(runner):
    result = runner.invoke(ask_ragbot_with_reformulation, input=query)
    assert result.exit_code == 0


def test_ask_ragbot_with_tools(runner):
    result = runner.invoke(ask_ragbot_with_tools, input=query)
    assert result.exit_code == 0


def test_safely_ask_ragbot_with_tools(runner):
    result = runner.invoke(safely_ask_ragbot_with_tools, input=query)
    assert result.exit_code == 0

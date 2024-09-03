# Weaviate Agent Demo

AI-powered demo app to help you use Weaviate, with a twist.

To install it, `pip` install the package with:

```shell
pip install weaviate-agent-demo
```

## CLI commands

Then, try out the different CLI commands set up in `src/weaviate_agent_demo/cli.py`, or in `pyproject.toml`.

e.g.:
- ask_llm
- ask_basic_ragbot
- ask_ragbot_with_reformulation
- ask_ragbot_with_tools
- safely_ask_ragbot_with_tools
- ask_weaviate_agent

## Dev setup

1. Clone the repo:
   ```shell
   git clone https://github.com/yourusername/weaviate-agent-demo.git
   cd weaviate-agent-demo
   ```

2. Install Poetry (if not already installed):
   ```shell
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Install the project dependencies with Poetry:
   ```shell
   poetry install
   ```

4. Activate the virtual environment:
   ```shell
   poetry shell
   ```

5. Run a Weaviate instance (e.g., with Docker):

6. Run the files in `src/weaviate_agent_demo/db_setup` to ingest data:
   ```shell
   python src/weaviate_agent_demo/db_setup/1_create_collection.py
   python src/weaviate_agent_demo/db_setup/2_import.py
   ```

7. You can now use the CLI commands, for example:
   ```shell
   ask_llm
   ```

   Then, when prompted - try queries like "How do I connect to Weaviate", or "How do I use filters with dates in hybrid search?"

## Streamlit app

There is also a Streamlit app available. Try it with:

```shell
streamlit run app.py
```

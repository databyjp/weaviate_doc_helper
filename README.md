# Weaviate helper

AI-powered helper app for using Weaviate, with a twist:

- The app is of varying levels of intelligence and use...

Try out the different CLI commands set up in `src/weaviate_agent_demo/cli.py`, or in `pyproject.toml`.

e.g.:
- ask_llm
- ask_basic_ragbot
- ask_ragbot_with_reformulation
- ask_ragbot_with_tools
- safely_ask_ragbot_with_tools

## Dev setup

1. Clone the repo
1. Install dependencies with `pip install -r requirements.txt`
1. Install locally for dev with `pip install -e . --config-settings editable_mode=strict`
1. Clone the `weaviate-io` repo into `data` folder
1. Run a Weaviate instance (e.g. with Docker)
1. Run the files in `src/weaviate_agent_demo/db_setup` to ingest data

## Notes:

- LLM almost always refuses to decompose a query into sub-queries, regardless of how complex the query is.
    -

import streamlit as st
import os


# Read the secret from Streamlit's secrets
st.secrets.load_if_toml_exists()

if st.secrets.has_key("COHERE_APIKEY"):
    cohere_apikey = st.secrets["COHERE_APIKEY"]
    openai_apikey = st.secrets["OPENAI_APIKEY"]
    claude_apikey = st.secrets["ANTHROPIC_API_KEY"]

    # Set the secret as an environment variable
    os.environ["COHERE_APIKEY"] = cohere_apikey
    os.environ["OPENAI_APIKEY"] = openai_apikey
    os.environ["ANTHROPIC_API_KEY"] = claude_apikey


import claudette
from anthropic.types import Message
from anthropic.types.text_block import TextBlock
from weaviate_agent_demo.setup import CLAUDE_MODEL, get_logger
from weaviate_agent_demo.coder import get_tools
from weaviate_agent_demo.tools import (
    _decompose_search_query,
    _get_weaviate_connection_snippet,
)
from weaviate_agent_demo.utils import _validate_query, _log_claude_to_file
from weaviate_agent_demo.db import _add_answer_to_cache, _search_multiple
from weaviate_agent_demo.prompts import SYSTEM_MSGS
import hashlib
import logging


logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)


# Function to hash the password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Pre-computed hash of the correct password
# Here to prevent abuse of the deployed app & its api keys
CORRECT_HASH = "a6d29a66e958a9cba8c068ba38dfcf1ee781f659f5bc9b84cfdcb6fa10198bb3"


# Password input
password = st.text_input("Enter the password", type="password")

if st.button("Login"):
    if hash_password(password) != CORRECT_HASH:
        st.error("Incorrect password. Please try again.")
    else:
        def message_to_markdown(message: Message) -> str:
            """
            Convert a message to a markdown string.
            """

            output = message.content[-1].text

            output = output.replace("<code_example>", "```python")
            output = output.replace("</code_example>", "```")

            return output


        st.header("Weaviate Helper")

        user_query = st.text_input(label="Can I help you with Weaviate or the Python client V4?")


        if user_query:
            with st.chat_message("user"):
                st.write(user_query)

            with st.spinner("Validating the query for safety & relevance..."):
                validity_assessment = _validate_query(user_query)
            if not validity_assessment["is_valid"]:
                logger.debug(f"Query '{user_query}' is not validated to continue.")
                logger.debug(f"Reason: {validity_assessment['reason']}")
                st.warning(f"Query '{user_query}' is not validated to continue.")
                st.write(f"Reason: {validity_assessment['reason']}")
            else:
                with st.chat_message("assistant"):
                    st.write(
                        f"Great, the query has been validated as safe & relevant. Continuing."
                    )

                with st.spinner(
                    f"Decomposing the query:\n '{user_query}' into sub-queries. Please wait..."
                ):
                    decomposed_queries = _decompose_search_query(user_query)

                with st.chat_message("assistant"):
                    for query in decomposed_queries:
                        st.write(f"Sub-query: {query}")

                # Perform manual search & combine results with decomposed_queries
                search_results = _search_multiple(decomposed_queries)
                search_results.append(_get_weaviate_connection_snippet())

                with st.container(height=300):
                    st.write(f"Results from manual search:")
                    for i, result in enumerate(search_results):
                        with st.expander(f"Result {i}"):
                            st.text(result)

                prompt = f"""
                The user has asked the following question:
                <user_query>{user_query}</user_query>

                Please answer the question, using the provided text.
                <provided_text>{search_results}</provided_text>

                If you require further information, use the provided tools.
                """
                logger.debug(f"Prompt: {prompt}")

                system_prompt = SYSTEM_MSGS.WEAVIATE_EXPERT_FINAL.value

                st.write(f"Prompting our LLM with the following inputs:")
                with st.expander("Prompt"):
                    st.write(prompt)
                with st.expander("System Prompt"):
                    st.write(system_prompt)

                with st.spinner("Asking the AI assistant. Please wait..."):
                    chat = claudette.Chat(model=CLAUDE_MODEL, sp=system_prompt, tools=get_tools())
                    r: Message = chat.toolloop(prompt, max_steps=5)

                with st.chat_message("assistant"):
                    st.write(f"Response:")
                    st.markdown(message_to_markdown(r))

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

                # Add "user_query" & response to Weaviate to cache the results.
                # If a similar query is asked again, we can use the cached results.
                if isinstance(r.content[-1], TextBlock):
                    _add_answer_to_cache(user_query, r.content[-1].text)

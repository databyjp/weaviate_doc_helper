import streamlit as st
import claudette
from anthropic.types import Message
from anthropic.types.text_block import TextBlock
from weaviate_helper.setup import CLAUDE_MODEL, get_logger
from weaviate_helper.coder import get_tools
from weaviate_helper.tools import (
    _decompose_search_query, _get_weaviate_connection_snippet
)
from weaviate_helper.utils import _validate_query, _log_claude_to_file
from weaviate_helper.db import _add_answer_to_cache, _search_multiple
from weaviate_helper.prompts import SYSTEM_MSGS
import logging
from anthropic.types import Message


logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)


def message_to_markdown(message: Message) -> str:
    """
    Convert a message to a markdown string.
    """

    output = message.content[-1].text

    output = output.replace("<code_example>", "```python")
    output = output.replace("</code_example>", "```")

    return output


st.header("Weaviate Helper")

user_query = st.text_input(label="What do you want to know about Weaviate?")


if user_query:
    with st.chat_message("user"):
        st.write(user_query)

    with st.spinner("Validating the query for safety & relevance..."):
        validity_assessment = _validate_query(user_query
                                          )
    if not validity_assessment["is_valid"]:
        logger.debug(f"Query '{user_query}' is not validated to continue.")
        logger.debug(f"Reason: {validity_assessment['reason']}")
        st.warning(f"Query '{user_query}' is not validated to continue.")
        st.write(f"Reason: {validity_assessment['reason']}")
    else:
        with st.chat_message("assistant"):
            st.write(f"Great, the query has been validated as safe & relevant. Continuing.")

        with st.spinner(f"Decomposing the query:\n '{user_query}' into sub-queries. Please wait..."):
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
        """
        logger.debug(f"Prompt: {prompt}")

        system_prompt = SYSTEM_MSGS.WEAVIATE_EXPERT_SUPPORT.value

        st.write(f"Prompting our LLM with the following inputs:")
        with st.expander("Prompt"):
            st.write(prompt)
        with st.expander("System Prompt"):
            st.write(system_prompt)

        with st.spinner("Asking the AI assistant. Please wait..."):
            chat = claudette.Chat(model=CLAUDE_MODEL, sp=system_prompt)
            r: Message = chat(prompt)

        with st.chat_message("assistant"):
            st.write(f"Response:")
            st.markdown(message_to_markdown(r))

        _log_claude_to_file(
            user_query,
            use_tools=False,
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


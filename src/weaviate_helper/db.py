# File: src/weaviate_helper/db.py
import weaviate
from weaviate import WeaviateClient
import os
from typing import List, Literal
import claudette
from anthropic.types import Message
from .setup import CLAUDE_MODEL, COLLECTION_NAME, get_logger
from .prompts import SYSTEM_MSGS
from weaviate.classes.query import Filter
import logging


logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)


def connect_to_weaviate() -> WeaviateClient:
    cohere_apikey = os.environ["COHERE_APIKEY"]
    openai_apikey = os.environ["OPENAI_APIKEY"]

    logger.debug("Connecting to Weaviate...")
    client = weaviate.connect_to_local(
        port=8280,
        grpc_port=50251,
        headers={
            "X-Cohere-Api-Key": cohere_apikey,
            "X-OpenAI-Api-Key": openai_apikey,
        },
    )
    return client


def _format_extracted_queries(
    queries: List[str],
) -> List[str]:
    """
    Format & display identified query terms.

    Args:
        queries: A list of strings representing the identified query terms.
    """
    return queries


def get_queries(original_query: str) -> List[str]:
    """Get a list of queries based on the original query."""

    prompt = f"""
    The user would like to search the Weaviate documentation for aspects relevant to this: <original_query>{original_query}</original_query>

    Please provide a list of 1 to 5 queries, separated by commas,
    that we can use to search for text or code chunks related to the following original query.
    """

    chat = claudette.Chat(
        model=CLAUDE_MODEL,
        sp=SYSTEM_MSGS.SEARCH_QUERY_PARSER.value,
        tools=[_format_extracted_queries],
        tool_choice="_format_extracted_queries",
    )

    r: Message = chat(prompt)

    return r.content[-1].input["queries"]


def filter_search_results():
    pass


def _response_obj_to_str(response_obj) -> str:
    """Convert a response object to a string."""
    response_text = f"""
    <file_path>{response_obj.properties["filepath"]}</file_path>
    <chunk>{response_obj.properties["chunk"]}</chunk>
    <chunk_no>{response_obj.properties["chunk_no"]}</chunk_no>
    <document_type>{response_obj.properties["doctype"]}</document_type>
    <lines>L{response_obj.properties["line_start"]}-L{response_obj.properties["line_end"]}</lines>
    """
    return response_text


def _search_generic(query: str, doctype: Literal["code", "text", "any"]) -> List[str]:
    """Search for a query in Weaviate.

    Args:
        query: The query to search for.
        doctype: The type of document to search for. (Used to filter the search results.)
    """
    logger.debug(f"Searching for query: {query} in Weaviate, in doctype: {doctype}")
    with connect_to_weaviate() as weaviate_client:
        collection = weaviate_client.collections.get(COLLECTION_NAME)

        if doctype == "any":
            filter = None
        else:
            filter = Filter.by_property("doctype").equal(doctype)

        response = collection.query.hybrid(
            query=query,
            filters=filter,
            limit=3,
            alpha=0.5,
            target_vector="chunk",
        )
    logger.debug(f"Search results: {response}")
    response_text = [_response_obj_to_str(o) for o in response.objects]
    return response_text

import weaviate
from weaviate import WeaviateClient
import os
from typing import List, Literal
import claudette
from anthropic.types import Message
from .setup import CLAUDE_MODEL, setup_logging, COLLECTION_NAME
from .prompts import SYSTEM_MSGS
from weaviate.classes.query import Filter


logger = setup_logging()


def connect_to_weaviate() -> WeaviateClient:
    cohere_apikey = os.environ["COHERE_APIKEY"]
    openai_apikey = os.environ["OPENAI_APIKEY"]

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
        tool_choice="_format_extracted_queries"
    )

    r: Message = chat(prompt)

    return r.content[-1].input["queries"]


def filter_search_results():
    pass


def _response_obj_to_str(response_obj) -> str:
    """Convert a response object to a string."""
    response_text = f'''
    <file_path>{response_obj.properties["filepath"]}</file_path>
    <chunk>{response_obj.properties["chunk"]}</chunk>
    <chunk_no>{response_obj.properties["chunk_no"]}</chunk_no>
    <document_type>{response_obj.properties["doctype"]}</document_type>
    <lines>L{response_obj.properties["line_start"]}-L{response_obj.properties["line_end"]}</lines>
    '''
    return response_text


def _search_generic(query: str, doctype: Literal["code", "text", "any"]) -> List[str]:
    """Perform a generic search on Weaviate."""
    with connect_to_weaviate() as weaviate_client:
        collection = weaviate_client.collections.get(COLLECTION_NAME)

        if doctype == "any":
            filter = None
        else:
            filter = Filter.by_property("doctype").equal(doctype)

        response = collection.query.hybrid(
            query=query,
            filters=filter,
            limit=2,
            alpha=0.5,
            target_vector="chunk",
        )
    return [_response_obj_to_str(o) for o in response.objects]


def _get_weaviate_connection_snippet() -> str:
    """Get a code snippet for connecting to Weaviate."""
    return """
    # ===== CONNECT TO A CLOUD INSTANCE OF WEAVIATE =====
    import weaviate
    from weaviate.classes.init import Auth

    # Load API keys as required  # Recommended: save to an environment variable
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    cohere_key = os.getenv("COHERE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,                       # `weaviate_url`: your Weaviate URL
        auth_credentials=Auth.api_key(weaviate_key),    # `weaviate_key`: your Weaviate API key
        headers={
            "X-Anthropic-Api-Key": anthropic_key
            "X-Cohere-Api-Key": cohere_key
            "X-OpenAI-Api-Key": openai_key
        }
    )
    # ===== END OF CODE SNIPPET =====

    # ===== CONNECT TO A LOCAL INSTANCE OF WEAVIATE =====
    import weaviate

    client = weaviate.connect_to_local(
        headers={
            "X-Anthropic-Api-Key": anthropic_key
            "X-Cohere-Api-Key": cohere_key
            "X-OpenAI-Api-Key": openai_key
        }
    )
    # ===== END OF CODE SNIPPET =====
    """

def search_text(query: str) -> List[str]:
    """Search text in Weaviate documentation."""
    return _search_generic(query, "text")

def search_code(query: str) -> List[str]:
    """Search code in Weaviate documentation."""
    return _search_generic(query, "code")

def search_any(query: str) -> List[str]:
    """Search any type in Weaviate documentation."""
    return _search_generic(query, "any")

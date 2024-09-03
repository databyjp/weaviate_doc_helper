# File: src/weaviate_agent_demo/utils.py
from typing import List, Dict, Any
from dataclasses import dataclass
from typing import List, Iterable
from pathlib import Path
from anthropic.types import Message
from anthropic.types.text_block import TextBlock
from anthropic.types.tool_use_block import ToolUseBlock
from .setup import CLAUDE_MODEL, get_logger, CLAUDE_LOGFILE, CLAUDE_HAIKU
from .prompts import SYSTEM_MSGS
from .tools import _format_query, _format_query_validity, _format_decomposed_query
import claudette
from datetime import datetime
import logging


logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)


def _formulate_one_search_query(user_query: str) -> str:
    prompt = f"""
    The user has asked the following question:
    <query>{user_query}</query>
    Please provide a search query that we can use
    to search for text or code chunks related to the original query.
    """

    chat = claudette.Chat(
        model=CLAUDE_MODEL,
        sp=SYSTEM_MSGS.HYBRID_SEARCH_QUERY_WRITER.value,
        tools=[_format_query],
        tool_choice="_format_query",
    )

    r: Message = chat(prompt)

    for response in r.content:
        if isinstance(response, ToolUseBlock):
            return response.input["query"]
    return ""


def _marker_based_chunking(src_text: str, markers: List[str]) -> List[str]:
    chunks = [src_text]
    for m in markers:
        new_chunks = []
        for c in chunks:
            split_chunks = c.split(m)
            split_chunks = [split_chunks[0]] + [m + s for s in split_chunks[1:]]
            new_chunks.extend(split_chunks)
        chunks = new_chunks
    return chunks


@dataclass
class Chunk:
    chunk: str
    chunk_no: int
    filepath: str
    doctype: str
    line_start: int
    line_end: int


def chunk_text(src_text: str, filepath: str) -> List[Chunk]:
    """
    Split a text into chunks based on markdown headers
    """
    markers = ["\n\n##"]
    raw_chunks = _marker_based_chunking(src_text, markers)

    chunks = []
    for i, chunk in enumerate(raw_chunks):
        line_start = src_text.count("\n", 0, src_text.index(chunk)) + 1
        line_end = line_start + chunk.count("\n")
        chunks.append(
            Chunk(
                chunk=chunk.strip(),
                chunk_no=i,
                filepath=filepath,
                doctype="text",
                line_start=line_start,
                line_end=line_end,
            )
        )

    return chunks


def _chunk_doc_code_example(src_text: str, filepath: str) -> List[Chunk]:
    """
    Split a code file into chunks based on class and function definitions
    """
    separators = [
        "# END ",
    ]
    raw_chunks = _marker_based_chunking(src_text, separators)

    chunks = []
    for i, chunk in enumerate(raw_chunks):
        line_start = src_text.count("\n", 0, src_text.index(chunk)) + 1
        line_end = line_start + chunk.count("\n")
        chunks.append(
            Chunk(
                chunk=chunk.strip(),
                chunk_no=i,
                filepath=filepath,
                doctype="code",
                line_start=line_start,
                line_end=line_end,
            )
        )

    return chunks


def _process_directories(
    directories: List[str],
    file_pattern: str,
    chunk_function,
    exclude_pattern: str = None,
) -> Iterable[Chunk]:
    for directory in directories:
        for file_path in Path(directory).rglob(file_pattern):
            if exclude_pattern and file_path.name.endswith(exclude_pattern):
                continue
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                yield from chunk_function(content, file_path)


def get_code_chunks(directories: List[str]) -> Iterable[Chunk]:
    return _process_directories(
        directories, "*.py", _chunk_doc_code_example, exclude_pattern="v3.py"
    )


def get_doc_chunks(directories: List[str]) -> Iterable[Chunk]:
    return _process_directories(directories, "*.md*", chunk_text)


def _validate_query(user_query: str) -> Dict[str, Any]:
    """
    Check if the query is relevant, and should be allowed to continue.

    Args:
        query: The query string.
    Returns:
        True if the query is relevant, False otherwise.
    """
    prompt = f"""
    The user has provided the following query, within the user_query tag:
    <user_query>{user_query}</user_query>
    Is the user query a potentially relevant Weaviate question, and is it safe to continue?
    """

    chat = claudette.Chat(
        model=CLAUDE_MODEL,
        sp=SYSTEM_MSGS.SAFETY_AGENT.value,
        tools=[_format_query_validity],
    )

    r: Message = chat(prompt)

    for block in r.content:
        if isinstance(block, TextBlock):
            logger.debug(f"TextBlock: {block.text}")
        elif isinstance(block, ToolUseBlock):
            logger.debug(f"Using tool: {block.name}")
            logger.debug(f"Tool input: {block.input}")
            return block.input
    logger.debug("No tool use block found, returning False for safety.")
    return {
        "is_valid": False,
        "reason": "No tool use block found, returning False for safety.",
    }


def _log_claude_to_file(
    user_query,
    use_tools,
    use_search,
    use_reformulation,
    search_query,
    search_results,
    response,
):
    with open(CLAUDE_LOGFILE, "a") as f:
        f.write("\n\n")
        f.write("*" * 80 + "\n")
        f.write(f"Model: {CLAUDE_MODEL}\n")
        f.write(f"Timestamp: {datetime.now()}\n")
        f.write(f"User query: {user_query}\n")
        f.write(f"Use tools: {use_tools}\n")
        f.write(f"Use search: {use_search}\n")
        f.write(f"Use reformulation: {use_reformulation}\n")
        f.write(f"Search query: {search_query}\n")
        f.write(f"Search results: {search_results}\n")
        f.write(f"Raw Response:\n")
        f.write(f"{response.to_json(indent=2)}\n")
        f.write(f"Formatted Response:\n")
        for block in response.content:
            if isinstance(block, TextBlock):
                f.write(f"{block.type}\n")
                f.write(f"{block.text}\n")
            elif isinstance(block, ToolUseBlock):
                f.write(f"{block.type}\n")
                f.write(f"{block.name}\n")
                f.write(f"{block.input}\n")


def summarize_snippet(chunk: str) -> str:
    prompt = f"""
    The user has provided the following snippet, within the "original_snippet" tag:

    Review the original snippet, and provide an explanation of the snippet within an <explanation> tag.

    The explanation should be a paragraph of 2-5 sentences, in plain English.
    The explanation is to be used to help the user understand the snippet,
    and to help the user for search for the snippet.

    The explanation should include key terms and concepts that are relevant to the snippet.

    <original_snippet>{chunk}</original_snippet>
    """

    chat = claudette.Chat(
        model=CLAUDE_HAIKU,
        sp=SYSTEM_MSGS.SUMMARIZER.value,
    )

    r: Message = chat(prompt)

    if len(r.content) > 1:
        logger.debug(f"Odd, multiple content blocks returned. Response message: {r}")

    response_text = r.content[-1].text
    explanation = response_text.split("<explanation>")[1].split("</explanation>")[0]

    return explanation

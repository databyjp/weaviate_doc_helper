from typing import List
from dataclasses import dataclass
from typing import List, Iterable
from pathlib import Path
from anthropic.types.text_block import TextBlock
from anthropic.types.tool_use_block import ToolUseBlock
from anthropic.types import Message
from .setup import CLAUDE_MODEL
from .prompts import SYSTEM_MSGS
from .tools import _format_query
import claudette


def _get_search_query(user_query: str) -> str:
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
        tool_choice="_format_query"
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

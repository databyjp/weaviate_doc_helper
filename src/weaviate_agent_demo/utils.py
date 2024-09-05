# File: src/weaviate_agent_demo/utils.py
from typing import List
from dataclasses import dataclass
from typing import List, Iterable
import hashlib
from pathlib import Path
from anthropic.types.text_block import TextBlock
from anthropic.types.tool_use_block import ToolUseBlock
from .setup import CLAUDE_MODEL, get_logger, CLAUDE_LOGFILE
from .tools import _format_decomposed_query
from datetime import datetime
import logging


logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)


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


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

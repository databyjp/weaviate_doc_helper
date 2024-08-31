import os
import weaviate
from weaviate import WeaviateClient
from typing import List
from dataclasses import dataclass
from typing import List, Iterable
from pathlib import Path


def marker_based_chunking(src_text: str, markers: List[str]) -> List[str]:
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
    raw_chunks = marker_based_chunking(src_text, markers)

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


def chunk_doc_code_example(src_text: str, filepath: str) -> List[Chunk]:
    """
    Split a code file into chunks based on class and function definitions
    """
    separators = [
        "# END ",
    ]
    raw_chunks = marker_based_chunking(src_text, separators)

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


def process_directories(
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
    return process_directories(
        directories, "*.py", chunk_doc_code_example, exclude_pattern="v3.py"
    )


def get_doc_chunks(directories: List[str]) -> Iterable[Chunk]:
    return process_directories(directories, "*.md*", chunk_text)

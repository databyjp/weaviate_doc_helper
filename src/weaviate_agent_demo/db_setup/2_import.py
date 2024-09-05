from weaviate_agent_demo.llm import summarize_snippet
from weaviate_agent_demo.utils import get_code_chunks, get_doc_chunks
from weaviate_agent_demo.db import connect_to_weaviate
from weaviate_agent_demo.setup import COLLECTION_NAME_CHUNKS
from weaviate.util import generate_uuid5
from tqdm import tqdm


code_directories = [
    "data/weaviate-io/_includes/code/connections",
    "data/weaviate-io/_includes/code/howto",
    "data/weaviate-io/_includes/code/starter-guides",
]
doc_directories = [
    "data/weaviate-io/developers/weaviate/concepts",
    "data/weaviate-io/developers/weaviate/config-refs",
    "data/weaviate-io/developers/weaviate/configuration",
    "data/weaviate-io/developers/weaviate/manage-data",
    "data/weaviate-io/developers/weaviate/search",
    "data/weaviate-io/developers/weaviate/starter-guides",
]


code_chunks = get_code_chunks(code_directories)
doc_chunks = get_doc_chunks(doc_directories)


client = connect_to_weaviate()

chunks = client.collections.get(COLLECTION_NAME_CHUNKS)

with chunks.batch.fixed_size(batch_size=100) as batch:
    for chunks_gen in [code_chunks, doc_chunks]:
        for c in tqdm(chunks_gen):
            obj_uuid = generate_uuid5(c.chunk + str(c.filepath) + str(c.chunk_no))

            if not chunks.data.exists(obj_uuid):
                if c.doctype == "code":
                    chunk_summary = summarize_snippet(
                        c.chunk
                    )  # Use LLM to summarize the code
                else:
                    chunk_summary = c.chunk[
                        :2048
                    ]  # For text, just use the first 2048 characters

                batch.add_object(
                    properties={
                        "chunk": c.chunk[:2048],  # In case the chunk is too long
                        "chunk_summary": chunk_summary,
                        "chunk_raw": c.chunk,
                        "chunk_no": c.chunk_no,
                        "filepath": str(c.filepath),
                        "doctype": c.doctype,
                        "line_start": c.line_start,
                        "line_end": c.line_end,
                    },
                    uuid=obj_uuid,
                )
            else:
                print(f"Skipping {obj_uuid} because it already exists")
                continue

        if batch.number_errors > 50:
            print("Too many errors, stopping")
            break


if len(chunks.batch.failed_objects) > 0:
    print(chunks.batch.failed_objects[:3])

client.close()

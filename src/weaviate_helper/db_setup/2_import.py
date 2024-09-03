from weaviate_helper.utils import get_code_chunks, get_doc_chunks, explain_code_snippet
from weaviate_helper.db import connect_to_weaviate
from weaviate_helper.setup import COLLECTION_NAME
from weaviate.util import generate_uuid5


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

chunks = client.collections.get(COLLECTION_NAME)

with chunks.batch.fixed_size(batch_size=100) as batch:
    for chunks_gen in [code_chunks, doc_chunks]:
        for c in chunks_gen:
            obj_uuid = generate_uuid5(c.chunk + str(c.filepath) + str(c.chunk_no))

            if not chunks.data.exists(obj_uuid):
                if c.doctype == "code":
                    chunk_summary = explain_code_snippet(c.chunk)
                else:
                    chunk_summary = c.chunk
                batch.add_object(
                    properties={
                        "chunk": c.chunk,
                        "chunk_no": c.chunk_no,
                        "chunk_summary": chunk_summary,
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

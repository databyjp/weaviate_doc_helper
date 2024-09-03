from weaviate_agent_demo.db import connect_to_weaviate
from weaviate_agent_demo.setup import COLLECTION_NAME_CHUNKS
from weaviate.classes.query import Filter

client = connect_to_weaviate()

chunks = client.collections.get(COLLECTION_NAME_CHUNKS)

print(chunks.aggregate.over_all(total_count=True))

for doctype in ["doc", "code"]:
    response = chunks.query.hybrid(
        query="hybrid search",
        alpha=0.75,
        target_vector="chunk",
        filters=Filter.by_property("doctype").equal(doctype),
        limit=5,
    )

    for o in response.objects:
        print("\n\n\n")
        print(o.properties)

client.close()

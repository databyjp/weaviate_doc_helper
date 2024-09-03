from weaviate_helper.db import connect_to_weaviate
from weaviate_helper.setup import COLLECTION_NAME
from weaviate.classes.query import Filter

client = connect_to_weaviate()

chunks = client.collections.get(COLLECTION_NAME)

print(chunks.aggregate.over_all(total_count=True))

for doctype in ["doc", "code"]:
    response = chunks.query.hybrid(
        query="target_vector",
        alpha=0.75,
        target_vector="chunk_summary",
        filters=Filter.by_property("doctype").equal(doctype),
        limit=5,
    )

    for o in response.objects:
        print("\n\n\n")
        print(o.properties)

client.close()

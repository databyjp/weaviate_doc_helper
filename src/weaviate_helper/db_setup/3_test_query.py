from ..db import connect_to_weaviate
from ..setup import COLLECTION_NAME
from weaviate.classes.query import Filter

client = connect_to_weaviate()

chunks = client.collections.get(COLLECTION_NAME)

print(chunks.aggregate.over_all(total_count=True))

for doctype in ["doc", "code"]:
    response = chunks.query.hybrid(
        query="target_vector",
        alpha=0.75,
        target_vector=["filepath", "chunk"],
        filters=Filter.by_property("doctype").equal(doctype),
        limit=5,
    )

    for o in response.objects:
        print("\n\n\n")
        print(o.properties)

client.close()

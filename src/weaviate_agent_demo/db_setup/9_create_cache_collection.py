from weaviate.classes.config import Property, DataType, Configure
from weaviate_agent_demo.setup import COLLECTION_NAME_CACHED_ANSWERS
from weaviate_agent_demo import db

client = db.connect_to_weaviate()

default_vindex_config = Configure.VectorIndex.hnsw(
    quantizer=Configure.VectorIndex.Quantizer.bq()
)

client.collections.delete(COLLECTION_NAME_CACHED_ANSWERS)

cached_answers = client.collections.create(
    name=COLLECTION_NAME_CACHED_ANSWERS,
    properties=[
        Property(name="user_query", data_type=DataType.TEXT),
        Property(name="answer", data_type=DataType.TEXT),
        Property(name="timestamp", data_type=DataType.DATE),
    ],
    vectorizer_config=[
        Configure.NamedVectors.text2vec_cohere(
            name="user_query",
            source_properties=["user_query"],
            vector_index_config=default_vindex_config,
        ),
    ],
    generative_config=Configure.Generative.cohere(model="command-r"),
)

client.close()

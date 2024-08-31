from weaviate.classes.config import Property, DataType, Configure
from weaviate_helper.setup import COLLECTION_NAME
from weaviate_helper import db

client = db.connect_to_weaviate()

default_vindex_config = Configure.VectorIndex.hnsw(
    quantizer=Configure.VectorIndex.Quantizer.sq(training_limit=10000)
)

client.collections.delete(COLLECTION_NAME)

codechunks = client.collections.create(
    name=COLLECTION_NAME,
    properties=[
        Property(name="chunk", data_type=DataType.TEXT),
        Property(name="chunk_no", data_type=DataType.INT),
        Property(name="filepath", data_type=DataType.TEXT),
        Property(name="doctype", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="line_start", data_type=DataType.INT),
        Property(name="line_end", data_type=DataType.INT),
    ],
    vectorizer_config=[
        Configure.NamedVectors.text2vec_cohere(
            name="filepath",
            source_properties=["filepath"],
            vector_index_config=default_vindex_config,
        ),
        Configure.NamedVectors.text2vec_cohere(
            name="chunk",
            source_properties=["chunk"],
            vector_index_config=default_vindex_config,
        ),
    ],
)

client.close()

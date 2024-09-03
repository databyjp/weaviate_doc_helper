from weaviate.classes.config import Property, DataType, Configure
from weaviate_agent_demo.setup import COLLECTION_NAME_CHUNKS
from weaviate_agent_demo import db

with db.connect_to_weaviate() as client:
    default_vindex_config = Configure.VectorIndex.hnsw(
        quantizer=Configure.VectorIndex.Quantizer.sq(training_limit=25000)
    )

    client.collections.delete(COLLECTION_NAME_CHUNKS)

    codechunks = client.collections.create(
        name=COLLECTION_NAME_CHUNKS,
        properties=[
            Property(name="chunk", data_type=DataType.TEXT),
            Property(name="chunk_raw", data_type=DataType.TEXT),
            Property(name="chunk_no", data_type=DataType.INT),
            Property(name="chunk_summary", data_type=DataType.TEXT),
            Property(name="filepath", data_type=DataType.TEXT),
            Property(name="doctype", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="line_start", data_type=DataType.INT),
            Property(name="line_end", data_type=DataType.INT),
        ],
        vectorizer_config=[
            Configure.NamedVectors.text2vec_cohere(
                name="chunk_summary",
                source_properties=["chunk_summary", "filepath"],
                vector_index_config=default_vindex_config,
            ),
            Configure.NamedVectors.text2vec_cohere(
                name="chunk",
                source_properties=["chunk"],
                vector_index_config=default_vindex_config,
            ),
        ],
        generative_config=Configure.Generative.cohere(model="command-r"),
    )

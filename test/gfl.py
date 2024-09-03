from weaviate_helper.utils import explain_code_snippet

collection_creation = """
from weaviate.classes.config import Configure, Property, DataType

client.collections.create(
    "ArticleNV",
    # highlight-start
    vectorizer_config=[
        # Set a named vector
        Configure.NamedVectors.text2vec_cohere(  # Use the "text2vec-cohere" vectorizer
            name="title", source_properties=["title"]       # Set the source property(ies)
        ),
        # Set another named vector
        Configure.NamedVectors.text2vec_openai(  # Use the "text2vec-openai" vectorizer
            name="body", source_properties=["body"]         # Set the source property(ies)
        ),
        # Set another named vector
        Configure.NamedVectors.text2vec_openai(  # Use the "text2vec-openai" vectorizer
            name="title_country", source_properties=["title", "country"] # Set the source property(ies)
        )
    ],
    # highlight-end
    properties=[  # Define properties
        Property(name="title", data_type=DataType.TEXT),
        Property(name="body", data_type=DataType.TEXT),
        Property(name="country", data_type=DataType.TEXT),
    ],
)
"""

hybrid_search_snippet = """
from weaviate.classes.query import HybridVector, Move, HybridFusion

jeopardy = client.collections.get("JeopardyQuestion")
response = jeopardy.query.hybrid(
    query="California",
    # highlight-start
    vector=HybridVector.near_text(
        query="large animal",
        move_away=Move(force=0.5, concepts=["mammal", "terrestrial"]),
    ),
    # highlight-end
    alpha=0.75,
    limit=5,
)
"""

print(explain_code_snippet(collection_creation))
print(explain_code_snippet(hybrid_search_snippet))

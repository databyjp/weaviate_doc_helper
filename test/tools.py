from weaviate_agent_demo.llm import _decompose_search_query


# print(_decompose_search_query("How do I connect to weaviate, then perform hybrid search with named vectors, then see the scores of the resulting hybrid search?"))
# print(_decompose_search_query("multi-tenant collection ollama vectorizer openai generative module v4 Python client API"))
# print(_decompose_search_query("How do I connect to a local Weaviate instance and set up a multi-tenant collection with the ollama vectorizer and an openai generative module? Then how can I run a hybrid search on the collection and see the search result scores? Also, how do the hybrid search results get combined together? The examples should use the v4 Python client API."))
print(
    _decompose_search_query(
        "How do I connect to weaviate, then perform hybrid search with named vectors, then see the scores of the resulting hybrid search?"
    )
)

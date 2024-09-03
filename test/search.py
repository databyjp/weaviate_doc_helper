from weaviate_agent_demo.db import search_any


assert (
    type(search_any("How do I connect to Weaviate and perform a hybrid search?"))
    == list
)
assert (
    type(search_any("How do I connect to Weaviate and perform a hybrid search?")[0])
    == str
)

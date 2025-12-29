from opensearch_client import get_opensearch_client

INDEX_NAME = "policyguard-vectors"


def create_index():
    client = get_opensearch_client()

    # ✅ FIXED: keyword argument
    if client.indices.exists(index=INDEX_NAME):
        return

    index_body = {
        "settings": {
            "index": {
                "knn": True
            }
        },
        "mappings": {
            "properties": {
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 768
                },
                "content": {"type": "text"},
                "document": {"type": "keyword"},
                "section": {"type": "keyword"},
                "chunk_hash": {"type": "keyword"}
            }
        }
    }

    client.indices.create(index=INDEX_NAME, body=index_body)
    print(f"✅ OpenSearch index '{INDEX_NAME}' created")

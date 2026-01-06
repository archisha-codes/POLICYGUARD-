from opensearch_client import get_opensearch_client

INDEX_NAME = "policyguardvectorsearch-v2"


def create_index():
    client = get_opensearch_client()

    index_body = {
        "mappings": {
            "properties": {
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 768,
                },
                "content": {"type": "text"},
                "document": {"type": "keyword"},
                "section": {"type": "keyword"},
                "chunk_hash": {"type": "keyword"},
            }
        }
    }

    try:
        # Try to create the index directly
        client.indices.create(index=INDEX_NAME, body=index_body)
        print(f"✅ OpenSearch index '{INDEX_NAME}' created")
    except Exception as e:
        # If index already exists, OpenSearch returns an error like resource_already_exists_exception
        msg = str(e)
        if "resource_already_exists_exception" in msg or "already exists" in msg:
            print(f"ℹ️ OpenSearch index '{INDEX_NAME}' already exists, skipping creation")
        else:
            print(f"⚠️ Index creation failed: {e}")
            raise e
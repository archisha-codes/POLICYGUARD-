import logging
import time
from opensearch_client import get_opensearch_client
from run_embeddings_on_chunks import load_chunks, generate_embeddings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INDEX_NAME = "policyguardvectorsearch"

def reset_index():
    client = get_opensearch_client()
    
    # 1. DELETE EXISTING BROKEN INDEX
    try:
        logger.info(f"🗑️ Deleting index '{INDEX_NAME}'...")
        client.indices.delete(index=INDEX_NAME)
        logger.info("✅ Index deleted.")
        time.sleep(5) # Wait for deletion to propagate
    except Exception as e:
        logger.warning(f"Index deletion skipped (maybe didn't exist): {e}")

    # 2. CREATE INDEX WITH CORRECT KNN SETTINGS
    # This is the critical part missing before!
    index_body = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 100
            }
        },
        "mappings": {
            "properties": {
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 768,
                    "method": {
                        "name": "hnsw",
                        "engine": "nmslib",
                        "space_type": "cosinesimil"
                    }
                },
                "content": {"type": "text"},
                "document": {"type": "keyword"},
                "section": {"type": "keyword"},
                "chunk_hash": {"type": "keyword"},
                "citation": {"type": "text"},
                "source": {"type": "keyword"},
                "regulation": {"type": "keyword"}
            }
        }
    }

    try:
        logger.info(f"🔨 Creating new index '{INDEX_NAME}' with KNN settings...")
        client.indices.create(index=INDEX_NAME, body=index_body)
        logger.info("✅ Index created successfully with Vector support.")
    except Exception as e:
        logger.error(f"❌ Failed to create index: {e}")
        raise e

if __name__ == "__main__":
    # 1. Reset
    reset_index()
    
    # 2. Re-ingest Data
    logger.info("🔄 Re-running ingestion pipeline...")
    chunks = load_chunks()
    generate_embeddings(chunks)
    logger.info("🎉 Repair Complete! Restart your backend now.")
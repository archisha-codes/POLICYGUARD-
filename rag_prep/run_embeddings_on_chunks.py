import json
import logging
from sentence_transformers import SentenceTransformer
from opensearch_client import get_opensearch_client
from opensearch_index import create_index, INDEX_NAME
import os
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

CHUNK_FILE = "chunked_output.json"

def load_chunks():
    """
    Loads chunks from the chunked_output.json file.
    """
    try:
        with open(CHUNK_FILE, "r", encoding="utf-8") as f:
            chunks = json.load(f)
            logger.info(f"Successfully loaded {len(chunks)} chunks from {CHUNK_FILE}")
            return chunks
    except FileNotFoundError:
        logger.error(f"Chunk file not found: {CHUNK_FILE}")
        logger.error("Please run run_chunking_on_data.py first to generate chunks.")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {CHUNK_FILE}")
        raise

def chunk_exists(client, chunk_hash):
    """
    Checks if a chunk hash already exists in OpenSearch.
    Returns True if chunk exists, False otherwise.
    """
    try:
        query = {
            "size": 1,
            "query": {
                "term": {
                    "chunk_hash": chunk_hash
                }
            }
        }
        response = client.search(index=INDEX_NAME, body=query)
        return response["hits"]["total"]["value"] > 0
    except Exception as e:
        logger.warning(f"Error checking if chunk exists: {str(e)}")
        return False

def generate_embeddings(chunks):
    """
    Generates embeddings for new chunks and indexes them in OpenSearch.
    
    Process:
    1. Initialize SentenceTransformer model
    2. Get OpenSearch client with error handling
    3. Create index if not exists
    4. Check which chunks are new (not already embedded)
    5. Generate embeddings for new chunks only
    6. Index new embeddings in OpenSearch
    """
    try:
        logger.info("Initializing SentenceTransformer model...")
        model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
        logger.info("Model loaded successfully")
        
    except Exception as e:
        logger.error(f"Failed to load SentenceTransformer model: {str(e)}")
        raise
    
    try:
        logger.info("Connecting to OpenSearch...")
        client = get_opensearch_client()
        logger.info("OpenSearch connection successful")
        
    except Exception as e:
        logger.error(f"Failed to connect to OpenSearch: {str(e)}")
        logger.error("Please check your AWS credentials and OpenSearch configuration.")
        raise
    
    try:
        logger.info(f"Creating/checking OpenSearch index: {INDEX_NAME}")
        create_index()
        logger.info("Index creation/check complete")
        
    except Exception as e:
        logger.error(f"Failed to create index: {str(e)}")
        logger.error("Check your data access policies and IAM permissions.")
        raise
    
    # Filter new chunks
    logger.info(f"Checking {len(chunks)} chunks for duplicates...")
    new_chunks = []
    duplicate_count = 0
    
    for chunk in chunks:
        if chunk_exists(client, chunk["chunk_hash"]):
            duplicate_count += 1
        else:
            new_chunks.append(chunk)
    
    if duplicate_count > 0:
        logger.info(f"Found {duplicate_count} duplicate chunks (already embedded)")
    
    if not new_chunks:
        logger.info("No new chunks to embed - all chunks are already indexed")
        return
    
    try:
        logger.info(f"Generating embeddings for {len(new_chunks)} new chunks...")
        texts = [c["content"] for c in new_chunks]
        
        embeddings = model.encode(
            texts,
            batch_size=16,
            normalize_embeddings=True,
            show_progress_bar=True
        )
        logger.info(f"Successfully generated {len(embeddings)} embeddings")
        
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {str(e)}")
        raise
    
    # Index embeddings in OpenSearch
    indexed_count = 0
    failed_count = 0
    
    logger.info(f"Indexing {len(new_chunks)} embeddings into OpenSearch...")
    
    for i, chunk in enumerate(new_chunks):
        try:
            doc = {
                "chunk_hash": chunk["chunk_hash"],
                "content": chunk["content"],
                "embedding": embeddings[i].tolist(),
                "document": chunk["metadata"]["document"],
                "section": chunk["metadata"]["section"]
            }
            client.index(index=INDEX_NAME, body=doc)
            indexed_count += 1
            
        except Exception as e:
            failed_count += 1
            logger.warning(f"Failed to index chunk {i}: {str(e)}")
    
    logger.info(f"Indexing complete: {indexed_count} successful, {failed_count} failed")
    
    if failed_count > 0:
        logger.warning(f"Some chunks failed to index. Check permissions and connection.")
    else:
        logger.info(f"Successfully indexed all {indexed_count} new vectors into OpenSearch")

if __name__ == "__main__":
    try:
        logger.info("Starting embedding pipeline...")
        chunks = load_chunks()
        logger.info(f"Loaded {len(chunks)} chunks")
        generate_embeddings(chunks)
        logger.info("Embedding pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        exit(1)

import logging
import os
from typing import List, Dict, Any
from opensearchpy import OpenSearch, RequestsHttpConnection
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# --- CONFIGURATION (Loaded from Env) ---
# Check for OPENSEARCH_URL first (for local dev), then fallback to VPC ENDPOINT
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL")
OPENSEARCH_HOST = os.getenv("OPENSEARCH_ENDPOINT", "vpc-pawan-opensearch-ld3enoqfwqrcbnm6ylx55bikjm.ap-south-1.es.amazonaws.com")
INDEX_NAME = os.getenv("OPENSEARCH_INDEX", "stream-events")
OS_USER = os.getenv("OPENSEARCH_USERNAME", "master-user")
OS_PASS = os.getenv("OPENSEARCH_PASSWORD", "J*%*4Sxb!zP%LU$GzM[#")
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"

def _to_bool(v: str | None, default: bool) -> bool:
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")

class RAGPipeline:
    """
    Enterprise RAG Pipeline that connects to AWS OpenSearch via VPC Endpoint or Local Instance.
    """
    
    def __init__(self):
        self.model = None
        self.client = None
        
        logger.info("🔌 Initializing OpenSearch Connection...")
        self._init_opensearch()
        logger.info("🧠 Loading Embedding Model (this may take a moment)...")
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("✅ RAG Pipeline Initialized Successfully")

    def _init_opensearch(self):
        """Initialize AWS OpenSearch Client with Basic Authentication"""
        
        # 1. Determine Host Strategy (Local URL vs Cloud VPC Endpoint)
        if OPENSEARCH_URL:
            hosts = [OPENSEARCH_URL]
        else:
            hosts = [{'host': OPENSEARCH_HOST, 'port': 443}]

        # 2. Determine SSL Verification Strategy (Disable for localhost by default)
        default_verify = False if (OPENSEARCH_URL and "localhost" in OPENSEARCH_URL) else True
        verify_certs = _to_bool(os.getenv("OPENSEARCH_VERIFY_CERTS"), default_verify)

        # 3. Initialize robust client
        self.client = OpenSearch(
            hosts=hosts,
            http_auth=(OS_USER, OS_PASS) if (OS_USER and OS_PASS) else None,
            use_ssl=True,
            verify_certs=verify_certs,
            ssl_show_warn=False,
            connection_class=RequestsHttpConnection,
            pool_maxsize=20,
            timeout=60,               # Increased timeout to 60s
            max_retries=3,            # Added network retries
            retry_on_timeout=True     # Tolerate minor network blips
        )

    def query(self, query_text: str, top_k: int = 3) -> List[Dict]:
        """
        Search OpenSearch for relevant compliance rules.
        """
        try:
            # 1. Generate Vector
            query_vector = self.model.encode(query_text).tolist()

            # 2. Construct k-NN Query
            query_body = {
                "size": top_k,
                "query": {
                    "knn": {
                        "embedding": {  
                            "vector": query_vector,
                            "k": top_k
                        }
                    }
                },
                "_source": ["text", "citation", "source", "regulation"]
            }

            # 3. Execute Search
            response = self.client.search(
                body=query_body,
                index=INDEX_NAME
            )

            # 4. Format Results
            results = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                results.append({
                    "text": source.get('text', ''),
                    "citation": source.get('citation', 'Unknown Regulation'),
                    "source": source.get('source', 'Regulatory DB'),
                    "regulation": source.get('regulation', 'RBI'),
                    "score": hit['_score']
                })
            
            logger.info(f"🔍 Found {len(results)} citations in OpenSearch")
            return results

        except Exception as e:
            logger.error(f"❌ Search Error: {e}")
            raise e

# Singleton Instance
_rag_instance = None

def get_rag_pipeline():
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGPipeline()
    return _rag_instance
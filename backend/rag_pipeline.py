import logging
import os
import json
import math
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# --- CONFIGURATION (Loaded from Env) ---
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL")
OPENSEARCH_HOST = os.getenv("OPENSEARCH_ENDPOINT")
INDEX_NAME = os.getenv("OPENSEARCH_INDEX", "stream-events")
OS_USER = os.getenv("OPENSEARCH_USERNAME")
OS_PASS = os.getenv("OPENSEARCH_PASSWORD")
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"

def _to_bool(v: str | None, default: bool) -> bool:
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


class LocalVectorStore:
    """
    Zero-cost, self-hosted in-memory vector store.
    Loads pre-computed RBI Master Circular chunk embeddings from rag_prep.
    """
    def __init__(self):
        self.chunks = []
        self.load_dataset()

    def load_dataset(self):
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "..", "rag_prep", "chunk_embeddings.json"),
            os.path.join(os.path.dirname(__file__), "..", "rag_prep", "chunked_output.json"),
            os.path.join(os.getcwd(), "rag_prep", "chunk_embeddings.json"),
            os.path.join(os.getcwd(), "rag_prep", "chunked_output.json"),
            os.path.join(os.getcwd(), "..", "rag_prep", "chunk_embeddings.json"),
            os.path.join(os.getcwd(), "..", "rag_prep", "chunked_output.json"),
        ]

        loaded = False
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                try:
                    logger.info(f"📂 Loading Local RBI Regulatory Dataset from: {abs_path}")
                    with open(abs_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.chunks = data
                            loaded = True
                            logger.info(f"✅ Loaded {len(self.chunks)} RBI regulatory chunks into Local Vector Store.")
                            break
                except Exception as e:
                    logger.warning(f"Failed loading dataset from {abs_path}: {e}")

        if not loaded or not self.chunks:
            logger.warning("⚠️ No pre-computed vector file found. Seeding core RBI Master Circular fallback rules.")
            self.chunks = [
                {
                    "content": "RBI Master Circular - KYC & AML: Mandatory Customer Due Diligence (CDD) required for high-value transactions (> ₹50,000 / $10,000). Official Valid Documents (OVD) like PAN/Aadhaar required.",
                    "metadata": {"document": "RBI Master Circular KYC/AML 2025", "section": "Section 3.2 - Customer Identification", "source": "RBI"}
                },
                {
                    "content": "PMLA 2002 Guidelines: Cash transactions above ₹10,00,000 or suspicious structuring pattern (rapid sequential transfers avoiding ₹10K threshold) must be flagged and reported to FIU-IND.",
                    "metadata": {"document": "Prevention of Money Laundering Act", "section": "Section 12 - Maintenance of Records", "source": "PMLA"}
                },
                {
                    "content": "FATF Sanction Guidelines: Transactions involving high-risk jurisdictions, OFAC sanctioned entities, or prohibited counterparties must be immediately frozen and escalated.",
                    "metadata": {"document": "FATF Guidance on Financial Sanctions", "section": "Recommendation 6 - Targeted Financial Sanctions", "source": "FATF"}
                }
            ]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def search(self, query_text: str, query_vector: List[float] = None, top_k: int = 3) -> List[Dict]:
        results = []
        words = set(query_text.lower().split())

        for idx, chunk in enumerate(self.chunks):
            content = chunk.get("content") or chunk.get("text") or ""
            metadata = chunk.get("metadata", {})
            doc_name = metadata.get("document", "RBI Policy Data")
            sec_name = metadata.get("section", f"Section {idx + 1}")
            source_name = metadata.get("source", "RBI Circular")

            score = 0.0
            # 1. Vector similarity if embedding vector exists
            chunk_emb = chunk.get("embedding")
            if query_vector and chunk_emb and isinstance(chunk_emb, list):
                score = self._cosine_similarity(query_vector, chunk_emb)
            else:
                # 2. Keyword score fallback
                content_lower = content.lower()
                matches = sum(1 for w in words if w in content_lower)
                score = matches / (len(words) + 1.0)

            results.append({
                "text": content,
                "citation": f"{doc_name} - {sec_name}",
                "source": source_name,
                "regulation": "RBI / PMLA",
                "document": doc_name,
                "section": sec_name,
                "score": round(score, 4)
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


class RAGPipeline:
    """
    Enterprise RAG Pipeline with automatic fallback to self-hosted Local Vector Index.
    Does not require a paid vector DB or AWS OpenSearch.
    """
    def __init__(self):
        self._model = None
        self._model_loaded = False
        self.opensearch_client = None
        self.local_store = LocalVectorStore()

        # Try initializing OpenSearch if explicitly configured
        if OPENSEARCH_URL or OPENSEARCH_HOST:
            self._init_opensearch()

    @property
    def model(self):
        if not self._model_loaded:
            self._model_loaded = True
            try:
                if os.getenv("ENABLE_HEAVY_EMBEDDINGS", "false").lower() in ("true", "1"):
                    from sentence_transformers import SentenceTransformer
                    logger.info(f"🧠 Loading Local Embedding Model '{EMBEDDING_MODEL}'...")
                    self._model = SentenceTransformer(EMBEDDING_MODEL)
                    logger.info("✅ Embedding Model Loaded Successfully")
                else:
                    logger.info("⚡ Fast Mode: Using high-speed statutory rule retrieval for instant cloud startup.")
                    self._model = None
            except Exception as e:
                logger.warning(f"SentenceTransformer not available ({e}). Using keyword-based local search.")
                self._model = None
        return self._model

    def _init_opensearch(self):
        try:
            from opensearchpy import OpenSearch, RequestsHttpConnection
            hosts = [OPENSEARCH_URL] if OPENSEARCH_URL else [{'host': OPENSEARCH_HOST, 'port': 443}]
            verify_certs = _to_bool(os.getenv("OPENSEARCH_VERIFY_CERTS"), True)

            self.opensearch_client = OpenSearch(
                hosts=hosts,
                http_auth=(OS_USER, OS_PASS) if (OS_USER and OS_PASS) else None,
                use_ssl=True,
                verify_certs=verify_certs,
                connection_class=RequestsHttpConnection,
                timeout=10,
                max_retries=1
            )
            logger.info("🔌 Connected to OpenSearch Cluster.")
        except Exception as e:
            logger.warning(f"OpenSearch Connection failed: {e}. Defaulting to Local Vector Store.")
            self.opensearch_client = None

    def query(self, query_text: str, top_k: int = 3) -> List[Dict]:
        """Search OpenSearch or Local Vector Store for relevant compliance rules."""
        # 1. Try OpenSearch if active
        if self.opensearch_client:
            try:
                query_vector = self.model.encode(query_text).tolist() if self.model else []
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
                response = self.opensearch_client.search(body=query_body, index=INDEX_NAME)
                results = []
                for hit in response['hits']['hits']:
                    src = hit['_source']
                    results.append({
                        "text": src.get('text', ''),
                        "citation": src.get('citation', 'RBI Regulation'),
                        "source": src.get('source', 'RBI'),
                        "regulation": src.get('regulation', 'RBI'),
                        "score": round(hit['_score'], 4)
                    })
                if results:
                    return results
            except Exception as e:
                logger.warning(f"OpenSearch query failed: {e}. Falling back to Local Vector Store.")

        # 2. Local Self-Hosted Vector Search Fallback
        query_vec = None
        if self.model:
            try:
                query_vec = self.model.encode(query_text).tolist()
            except Exception as e:
                logger.warning(f"Query encoding failed: {e}")

        results = self.local_store.search(query_text, query_vector=query_vec, top_k=top_k)
        logger.info(f"🔍 Local RAG search returned {len(results)} RBI policy citations.")
        return results


# Singleton Instance
_rag_instance = None

def get_rag_pipeline() -> RAGPipeline:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGPipeline()
    return _rag_instance
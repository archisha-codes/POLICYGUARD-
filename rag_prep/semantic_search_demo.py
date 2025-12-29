from sentence_transformers import SentenceTransformer
from opensearch_client import get_opensearch_client
from opensearch_index import INDEX_NAME

# ---------------- CONFIG ----------------
TOP_K = 5
# ---------------------------------------


def semantic_search(query):
    """
    Performs semantic search over OpenSearch vector index
    """
    model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    client = get_opensearch_client()

    # ✅ SAFETY CHECK: ensure index exists
    if not client.indices.exists(index=INDEX_NAME):
        raise RuntimeError(
            f"OpenSearch index '{INDEX_NAME}' not found. "
            "Run embedding pipeline first (run_embeddings_on_chunks.py)."
        )

    # Generate query embedding
    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    ).tolist()

    # OpenSearch KNN query
    response = client.search(
        index=INDEX_NAME,
        body={
            "size": TOP_K,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": TOP_K
                    }
                }
            }
        }
    )

    results = []

    for hit in response["hits"]["hits"]:
        source = hit["_source"]

        results.append({
            "score": round(hit["_score"], 3),
            "document": source.get("document"),
            "section": source.get("section"),
            "content": source.get("content")
        })

    return results


# ---------------- DEMO ----------------
if __name__ == "__main__":
    query = "What are the KYC requirements for customer identity verification?"

    print(f"\n🔍 Query: {query}")
    print("\nTop relevant regulatory sections:\n")

    results = semantic_search(query)

    for i, r in enumerate(results, 1):
        print(f"--- RESULT {i} ---")
        print(f"Score: {r['score']}")
        print(f"Document: {r['document']}")
        print(f"Section: {r['section']}")
        print(f"Content Preview: {r['content'][:300]}\n")

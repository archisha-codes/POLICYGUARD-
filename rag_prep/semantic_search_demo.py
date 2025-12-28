import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

EMBEDDING_FILE = "chunk_embeddings.json"

def load_data():
    with open(EMBEDDING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def semantic_search(query, data, top_k=5):
    model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    chunk_embeddings = np.array(
        [chunk["embedding"] for chunk in data]
    )

    similarities = cosine_similarity(
        [query_embedding],
        chunk_embeddings
    )[0]

    top_indices = similarities.argsort()[-top_k:][::-1]

    results = []
    for idx in top_indices:
        results.append({
            "score": float(similarities[idx]),
            "document": data[idx]["metadata"]["document"],
            "section": data[idx]["metadata"]["section"],
            "content": data[idx]["content"][:300]
        })

    return results

if __name__ == "__main__":
    data = load_data()

    query = "What are the KYC requirements for customer identity verification?"

    results = semantic_search(query, data)

    print("\n🔍 Query:", query)
    print("\nTop relevant regulatory sections:\n")

    for i, res in enumerate(results, 1):
        print(f"--- RESULT {i} ---")
        print("Score:", round(res["score"], 3))
        print("Document:", res["document"])
        print("Section:", res["section"])
        print("Content Preview:", res["content"])
        print()

import json

# After you compute `results`
ui_results = []

for r in results:
    ui_results.append({
        "compliance_status": "NON_COMPLIANT",  # mock for now
        "risk_score": int((1 - r["score"]) * 100),
        "confidence_score": int(r["score"] * 100),
        "policy_coverage_percentage": 50,  # placeholder
        "justification": "Relevant RBI regulation retrieved via semantic search.",
        "evidence": r["content"],
        "metadata": {
            "document": r["document"],
            "section": r["section"],
            "similarity_score": round(r["score"], 3)
        }
    })

with open("ui_search_results.json", "w", encoding="utf-8") as f:
    json.dump(ui_results, f, indent=2, ensure_ascii=False)

print("\nUI search results saved to ui_search_results.json")

import json
from sentence_transformers import SentenceTransformer
from opensearch_client import get_opensearch_client
from opensearch_index import create_index, INDEX_NAME

CHUNK_FILE = "chunked_output.json"


def load_chunks():
    with open(CHUNK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def chunk_exists(client, chunk_hash):
    """
    Checks if a chunk hash already exists in OpenSearch
    """
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


def generate_embeddings(chunks):
    model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

    client = get_opensearch_client()
    create_index()

    new_chunks = []

    for chunk in chunks:
        if chunk_exists(client, chunk["chunk_hash"]):
            continue
        new_chunks.append(chunk)

    if not new_chunks:
        print("✅ No new chunks to embed")
        return

    print(f"➕ Embedding {len(new_chunks)} new chunks")

    texts = [c["content"] for c in new_chunks]

    embeddings = model.encode(
        texts,
        batch_size=16,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    for i, chunk in enumerate(new_chunks):
        doc = {
            "chunk_hash": chunk["chunk_hash"],
            "content": chunk["content"],
            "embedding": embeddings[i].tolist(),
            "document": chunk["metadata"]["document"],
            "section": chunk["metadata"]["section"]
        }

        client.index(index=INDEX_NAME, body=doc)

    print(f"✅ Indexed {len(new_chunks)} new vectors into OpenSearch")


if __name__ == "__main__":
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks")

    generate_embeddings(chunks)

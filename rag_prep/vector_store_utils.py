import json
import os
import hashlib

VECTOR_STORE_PATH = "chunk_embeddings.json"


def load_vector_store():
    if not os.path.exists(VECTOR_STORE_PATH):
        return []
    with open(VECTOR_STORE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_vector_store(vectors):
    with open(VECTOR_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(vectors, f, indent=2, ensure_ascii=False)


def hash_chunk(content, metadata):
    """
    Generates a stable hash for a chunk based on content + metadata
    """
    hash_input = content + metadata["document"] + metadata["section"]
    return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()


def existing_hashes(vectors):
    return set(v["chunk_hash"] for v in vectors)

import json
from sentence_transformers import SentenceTransformer

CHUNK_FILE = "chunked_output.json"
OUTPUT_FILE = "chunk_embeddings.json"

def load_chunks():
    with open(CHUNK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_embeddings(chunks):
    model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")


    texts = [chunk["content"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        batch_size=16,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    return embeddings

if __name__ == "__main__":
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks")

    embeddings = generate_embeddings(chunks)
    print("Embeddings generated")

    # attach embeddings back to chunks
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[i].tolist()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"Embeddings saved to {OUTPUT_FILE}")

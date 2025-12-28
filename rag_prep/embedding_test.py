
"""
Embedding generation test using Sentence-Transformers
Phase-1 validation
"""

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def generate_embeddings(chunks):
    texts = [c["content"] for c in chunks]
    embeddings = model.encode(
        texts,
        batch_size=16,
        normalize_embeddings=True
    )
    return embeddings
from sklearn.metrics.pairwise import cosine_similarity

similarity = cosine_similarity(
    [embeddings[0]],
    [embeddings[1]]
)

print("Similarity between similar rules:", similarity[0][0])
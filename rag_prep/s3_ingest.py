from run_chunking_on_data import run_chunking
from run_embeddings_on_chunks import generate_embeddings
from s3_loader import download_pdfs_from_s3

# ========== CONFIG ==========
S3_BUCKET_NAME = "policyguard-regulatory-pdfs"
S3_PREFIX = "rbi/"
# ============================


def run_full_rag_prep_pipeline():
    """
    End-to-end pipeline:
    S3 → Chunking → Embeddings → OpenSearch
    """
    print("\n🚀 Starting full RAG ingestion pipeline")

    download_pdfs_from_s3(S3_BUCKET_NAME, S3_PREFIX)

    print("\n📄 Running heading-aware chunking")
    chunks = run_chunking()

    print("\n🔢 Generating embeddings and indexing into OpenSearch")
    generate_embeddings(chunks)

    print("\n✅ RAG preparation completed successfully")


if __name__ == "__main__":
    run_full_rag_prep_pipeline()

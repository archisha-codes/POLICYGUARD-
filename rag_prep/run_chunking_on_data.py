import os
import json
import pdfplumber
from chunking_strategy import chunk_by_heading
from vector_store_utils import hash_chunk
from s3_loader import download_pdfs_from_s3

# ===================== CONFIG =====================
USE_S3 = True
S3_BUCKET = "policyguard-raw-data-1"
S3_PREFIX = "metadata/"
# =================================================

DATA_DIRS = {
    "../data": "local",
    "../data/s3": "s3"
}


def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def run_chunking():
    all_chunks = []

    for data_dir, source in DATA_DIRS.items():
        if not os.path.exists(data_dir):
            continue

        for file in os.listdir(data_dir):
            if not file.lower().endswith(".pdf"):
                continue

            pdf_path = os.path.join(data_dir, file)
            print(f"\n📄 Processing PDF: {file} (source: {source})")

            text = extract_text_from_pdf(pdf_path)
            chunks = chunk_by_heading(text, file)
            print(f"🔹 Chunks created: {len(chunks)}")

            for c in chunks:
                # ✅ Inject correct source
                c["metadata"]["source"] = source

                # ✅ Stable hash
                c["chunk_hash"] = hash_chunk(
                    c["content"],
                    c["metadata"]
                )

                all_chunks.append(c)

    return all_chunks


if __name__ == "__main__":

    if USE_S3:
        print("\n⬇️ Fetching PDFs from S3")
        download_pdfs_from_s3(S3_BUCKET, S3_PREFIX)

    chunks = run_chunking()

    with open("chunked_output.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Total chunks created: {len(chunks)}")
    print("📦 Chunked output saved to chunked_output.json")

    for i, chunk in enumerate(chunks[:5], 1):
        print(f"\n--- CHUNK {i} ---")
        print("PDF:", chunk["metadata"]["document"])
        print("SECTION:", chunk["metadata"]["section"])
        print("SOURCE:", chunk["metadata"]["source"])
        print("HASH:", chunk["chunk_hash"][:12], "...")
        print("CONTENT PREVIEW:", chunk["content"][:200])

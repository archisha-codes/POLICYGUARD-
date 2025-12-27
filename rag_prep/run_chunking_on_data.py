import os
import json
import pdfplumber
from chunking_strategy import chunk_by_heading

DATA_DIR = "../data"

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

    for file in os.listdir(DATA_DIR):
        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(DATA_DIR, file)
            print(f"\nProcessing PDF: {file}")

            text = extract_text_from_pdf(pdf_path)

            chunks = chunk_by_heading(text, file)
            print(f"Chunks created: {len(chunks)}")

            for c in chunks:
                all_chunks.append(c)

    return all_chunks


if __name__ == "__main__":
    chunks = run_chunking()

    # Save chunks to JSON (proof artifact)
    with open("chunked_output.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"\nTotal chunks created: {len(chunks)}")
    print("Chunked output saved to chunked_output.json")

    # Preview first 5 chunks
    for i, chunk in enumerate(chunks[:5], 1):
        print(f"\n--- CHUNK {i} ---")
        print("PDF:", chunk["metadata"]["document"])
        print("SECTION:", chunk["metadata"]["section"])
        print("CONTENT PREVIEW:", chunk["content"][:200])


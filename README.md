
# POLICYGUARD – Phase-1 (RAG Preparation & Compliance Intelligence)

PolicyGuard is a **Regulatory Compliance Intelligence System** that ingests regulatory PDFs (KYC/AML/RBI), prepares them for **Retrieval-Augmented Generation (RAG)**, and enables **semantic compliance analysis**.
This repository contains **Phase-1**, focused on data ingestion, chunking, embeddings, and semantic retrieval.

---

## 📌 Phase-1 Scope (What is implemented)

* Regulatory PDF ingestion (Local & AWS S3)
* Heading-aware chunking of legal documents
* Incremental embedding generation with hashing
* Vector storage in OpenSearch (KNN)
* Semantic search over regulatory text
* Frontend dashboard foundation (React + Tailwind)

---

## 🧠 Architecture Overview (How it works)

```
S3 / Local PDFs
      ↓
Heading-Aware Chunking
      ↓
Stable Hashing (deduplication)
      ↓
Sentence Embeddings
      ↓
OpenSearch Vector Index (Docker)
      ↓
Semantic Search API
      ↓
Compliance Dashboard UI
```

---

## 📂 Project Structure (Relevant)

```
rag_prep/
 ├─ run_chunking_on_data.py
 ├─ run_embeddings_on_chunks.py
 ├─ semantic_search_demo.py
 ├─ s3_loader.py
 ├─ vector_store_utils.py
 ├─ opensearch_client.py
 ├─ opensearch_index.py

policyguard-ui/
 ├─ src/components/
 ├─ src/pages/
```

---

## 🔹 Why each component exists

### Chunking

Regulatory documents are long and structured.
Chunking by headings preserves **legal context**, improving retrieval accuracy.

### Hashing

Each chunk gets a **stable hash** → prevents re-embedding duplicate content.

### Embeddings

Semantic embeddings enable meaning-based search instead of keyword matching.

### OpenSearch

Acts as the **vector database** for fast KNN search over embeddings.

### S3 Support

Allows **automated ingestion** of scraped PDFs uploaded by other team members.

---

## 🐳 Docker Usage (Why & Where)

Docker is used to run **OpenSearch locally** without manual installation.

### Start OpenSearch

```bash
docker run -d --name policyguard-opensearch \
-p 9200:9200 -p 9600:9600 \
-e "discovery.type=single-node" \
-e "plugins.security.disabled=true" \
opensearchproject/opensearch:2.11.0
```

OpenSearch runs at:

```
http://localhost:9200
```

---

## ☁️ AWS Usage (Why & Where)

AWS S3 is used as **central regulatory storage**.

### One-time AWS setup

```bash
aws configure
```

Or via environment variables (PowerShell):

```powershell
setx AWS_ACCESS_KEY_ID "your_key"
setx AWS_SECRET_ACCESS_KEY "your_secret"
setx AWS_DEFAULT_REGION "ap-south-1"
```

Restart PowerShell after this.

---

## ▶️ How to Run (Step-by-Step)

### 1️⃣ Ingest PDFs (Local or S3)

Edit in `run_chunking_on_data.py`:

```python
USE_S3 = True
S3_BUCKET = "policyguard-raw-data-1"
S3_PREFIX = "metadata/"
```

Run:

```bash
python run_chunking_on_data.py
```

✔ Downloads PDFs from S3
✔ Chunks them
✔ Saves `chunked_output.json`

---

### 2️⃣ Generate Embeddings & Store in OpenSearch

```bash
python run_embeddings_on_chunks.py
```

✔ Creates OpenSearch index
✔ Embeds only **new chunks**
✔ Updates vector store incrementally

---

### 3️⃣ Semantic Search Demo

```bash
python semantic_search_demo.py
```

✔ Retrieves top-K regulatory sections using KNN
✔ Confirms RAG retrieval works

---

### 4️⃣ Frontend UI (Optional)

```bash
cd policyguard-ui
npm install
npm run dev
```

Dashboard is ready to consume real compliance results in later phases.

---

## ✅ What is Production-Ready Now

* S3-based ingestion
* Incremental RAG pipeline
* Vector search backend
* Audit-friendly metadata
* Extensible UI foundation

---

## 🚀 What Comes Next (Phase-2)

* IBM Granite LLM integration
* Structured compliance verdicts (JSON)
* Real-time transaction evaluation
* Human-in-the-loop approvals
* End-to-end compliance workflows

---

## 🟢 Final Note

This Phase-1 pipeline follows **industry-standard RAG ingestion design** and is fully extensible for enterprise compliance systems.


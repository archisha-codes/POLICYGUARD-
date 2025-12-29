
<<<<<<< HEAD
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
 Start Docker Engine

Open *Docker Desktop*
Wait until it shows *“Engine running”*

---

### 2️⃣ Check OpenSearch container

bash
docker ps


If you see:


policyguard-opensearch


➡️ Continue

---

### 3️⃣ If container exists but stopped

bash
docker start policyguard-opensearch


---

## ▶️ Run Project Pipeline

### 📄 Chunk PDFs (Local / S3)

bash
python run_chunking_on_data.py



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

=======
Regulatory PDF Ingestion
Automated ingestion of multiple regulatory and compliance PDFs from a shared data/ directory, enabling scalable rule intake for downstream analysis.

Heading-Aware Chunking (RAG Preparation)
Implemented structured chunking of regulatory documents based on legal and policy headings (RBI circulars, KYC/AML guidelines, statutory Acts).
Preserved document hierarchy and attached metadata such as document name and section for traceability.

Semantic Embedding Generation
Generated high-quality semantic embeddings for all regulatory chunks using Sentence-Transformers (MPNet), producing 768-dimensional vectors suitable for accurate retrieval in compliance use cases.

Proof Artifacts & Validation
Persisted chunked text and embeddings as structured JSON artifacts.
Validated chunk counts, embedding dimensions, and vector consistency across all documents.

Semantic Similarity Search (Pre-FAISS)
Implemented semantic retrieval of relevant regulatory clauses using cosine similarity.
Successfully demonstrated accurate ranking of KYC and AML regulatory sections for natural-language compliance queries.

IBM Granite Prompt Engineering (Compliance Evaluation)
Designed a strict, audit-grade prompt for IBM Granite enforcing deterministic JSON output, evidence-grounded reasoning, confidence scoring, risk scoring, and policy coverage estimation.
Ensured zero hallucination by restricting responses strictly to retrieved regulatory text.

Compliance Dashboard UI (Frontend)
Built a responsive compliance dashboard using React + Tailwind CSS featuring:

Sidebar navigation and KPI summary cards

Risk meter and real-time compliance status badge

Dynamic aggregation of compliance metrics derived from AI outputs

UI fully driven by real semantic search and AI evaluation results (no hard-coded values)
>>>>>>> 9df8a203b745378bcbd55f6700c44ed65098f767

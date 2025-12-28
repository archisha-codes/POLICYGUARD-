Completed Tasks (Phase-1)

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


# POLICYGUARD

> **Tagline**: Real-Time, Explainable & Privacy-First Financial Compliance

POLICYGUARD is an AI-driven, real-time financial compliance co-pilot for banks, fintechs, payment gateways, and regulated institutions. It combines **Deterministic Rules**, **Self-Hosted Local RAG**, **AI Compliance Intelligence**, **PII Masking & Tokenization**, **Explainable Risk Decomposition**, **Human-in-the-Loop Governance**, **Cryptographic Audit Trails**, and **Regulatory Drift Detection**.

> [!IMPORTANT]
> **PolicyGuard Philosophy**: *"AI assists compliance officers; AI does not replace them."*
> PolicyGuard is a compliance co-pilot and does not replace qualified compliance professionals or legal advice.

---

## 🚀 Key Differentiators & Principles

1. **Deterministic Rules + RAG Evidence + AI Reasoning**: No hallucinated compliance rules. AI decisions are strictly grounded in retrieved RBI/PMLA Master Circular evidence.
2. **Zero-Cost / Self-Hosted Deployability**: Runs 100% locally and on free-tier Render (backend) and Vercel (frontend) without requiring paid API keys or cloud vector databases.
3. **PII-First Architecture**: Direct identifiers (PAN, Aadhaar, Account Numbers, Names) are tokenized via Fernet encryption & SHA-256 hashes *before* hitting AI models or log files.
4. **Human-in-the-Loop & Cryptographic Ledger**: Compliance officers can Approve, Reject, or Override AI verdicts. Every officer decision is cryptographically signed into an append-only ledger using SHA-256 hash chaining.
5. **No OnDemand Dependencies**: PolicyGuard is 100% clean of OnDemand APIs, SDKs, or cloud lock-in.

---

## 🏗️ Architecture Overview

```
                  POLICYGUARD FINANCIAL COMPLIANCE
                                 │
      ┌──────────────────────────┼──────────────────────────┐
      │                          │                          │
      ▼                          ▼                          ▼
 Transaction Ingestion      Security Layer            Regulatory Knowledge
(REST API / Manual / CSV) (PII Masking & Fernet)    (RBI Master Circulars)
      │                          │                          │
      ▼                          ▼                          ▼
Validation & Normalization  Tokenization Vault       Self-Hosted Local Vector RAG
      │                          │                          │
      └──────────────────────────┼──────────────────────────┘
                                 ▼
                     Compliance Intelligence
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
            Deterministic Rules      AI Compliance Co-Pilot
            (KYC/AML/OFAC/PMLA)      (Grounded Engine / Gemini)
                    │                         │
                    └────────────┬────────────┘
                                 ▼
                         Decision Engine
                                 │
                   ┌─────────────┴─────────────┐
                   ▼                           ▼
            Human Review                Auto Approval
       (Approve/Reject/Override)       (Low-Risk Pass)
                   │                           │
                   └─────────────┬─────────────┘
                                 ▼
                     Cryptographic Audit Trail
                      (SHA-256 Hash Chain)
                                 │
                   ┌─────────────┼─────────────┐
                   ▼             ▼             ▼
                Alerts        Reports       Dashboard
```

---

## 🛠️ Core Features

- **Transaction Ingestion & Validation**: Ingests transactions with schema validation and synthetic demo datasets.
- **PII Masking & Security**: Detects and tokenizes Indian PAN (`XXXXX1234X`), Aadhaar (`XXXX XXXX 9012`), and Bank Account Numbers (`XXXXXXXXX3456`).
- **Deterministic Rule Engine**: High-value transactions without KYC (>₹1,00,000), OFAC entity match, high-risk country check, duplicate transaction detection, and smurfing/structuring patterns (₹9,000-11,000 range).
- **Self-Hosted Local RAG**: Loads pre-chunked RBI Master Circular KYC/AML circulars (`rag_prep/chunked_output.json`) and pre-computed vector embeddings (`rag_prep/chunk_embeddings.json`) locally. No paid vector DB required.
- **Rule-Grounded AI Fallback**: Operates 100% offline using local evidence-grounded inference if external AI keys are absent.
- **Human-in-the-Loop Governance**: Offers Approve, Reject, and Override actions. Stores officer notes and records original vs human decision.
- **Cryptographic Audit Ledger**: Immutable append-only audit trail with SHA-256 hash chaining.
- **Policy Drift & Regulatory Updates**: Tracks regulatory circular amendments and affected transaction logs.
- **Regulatory Knowledge Assistant**: RAG-powered chatbot answering regulatory queries with cited RBI circular sections.

---

## 📂 Repository Layout

```
POLICYGUARD/
 ├── backend/
 │    ├── app.py                   # FastAPI REST API & endpoints
 │    ├── database.py              # SQLAlchemy DB setup (SQLite / PostgreSQL)
 │    ├── models.py                # Database entities (Transaction, ComplianceLog, FeedbackLoop)
 │    ├── rag_pipeline.py          # Self-hosted Local Vector RAG Engine
 │    ├── render.yaml              # Render deployment configuration
 │    ├── Procfile                 # Render start command
 │    ├── requirements.txt         # Python dependencies
 │    ├── agents/
 │    │    ├── compliance_agent.py # AI Co-Pilot & Rule-Grounded Fallback Engine
 │    │    ├── rule_engine.py      # Fast-path Deterministic Rule Engine
 │    │    ├── pii_masking_agent.py # PII Detection & Tokenization Agent
 │    │    └── rag_bridge.py       # RAG Context & Citation Retriever
 │    └── services/
 │         ├── audit_logger.py     # Cryptographic SHA-256 Hash Chain Audit Logger
 │         ├── zero_trust_auth.py  # JWT & Role-Based Access Control (RBAC)
 │         └── gemini_client.py    # Optional Gemini client
 ├── frontend/
 │    ├── vercel.json              # Vercel deployment configuration
 │    ├── package.json             # React dependencies & scripts
 │    └── src/
 │         ├── App.tsx             # Main routing
 │         ├── pages/              # Dashboard, Transactions, Decision View, Policy Drift, Audit Logs
 │         ├── components/         # Glassmorphism UI cards, badges, Knowledge Assistant Modal
 │         └── services/api.ts     # Backend API integration
 ├── rag_prep/
 │    ├── chunked_output.json      # Pre-chunked RBI Master Circular guidelines
 │    └── chunk_embeddings.json    # Pre-computed 768-dim vector embeddings
 ├── .env.example                  # Environment variable template
 └── README.md                     # Project documentation
```

---

## 💻 Local Setup Instructions

### 1. Backend Setup (FastAPI + Python)

```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -c "from database import init_db; init_db()"
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

Backend will start at `http://localhost:8000`. Health endpoint: `http://localhost:8000/api/health`.

### 2. Frontend Setup (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Frontend will start at `http://localhost:5173`.

---

## 🌐 Deployment Configuration

### Deploying Backend to Render
1. Connect repository to **Render**.
2. Select **Web Service** with directory `backend`.
3. Set build command: `pip install -r requirements.txt`.
4. Set start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`.
5. Set environment variable `ENVIRONMENT=production` and optional `DATABASE_URL`.

### Deploying Frontend to Vercel
1. Connect repository to **Vercel**.
2. Set Root Directory to `frontend`.
3. Framework Preset: **Vite**.
4. Set Environment Variable: `VITE_API_BASE_URL=https://your-backend.onrender.com`.

---

## ⚠️ Limitations & Legal Disclaimer

*PolicyGuard is a financial compliance co-pilot designed to assist compliance officers. PolicyGuard does not provide legal advice, guaranteed regulatory immunity, or legal certification. Compliance officers remain accountable for all final institutional compliance decisions.*


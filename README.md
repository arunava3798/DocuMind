# 🧠 DocuMind — Full-Stack RAG Platform

**🔗 Live demo: [documindchat.netlify.app](https://documindchat.netlify.app)**

A production-style **Retrieval-Augmented Generation** platform: upload documents, then ask
questions answered **only from their content**, with cited sources, hybrid retrieval,
re-ranking, conversational memory, evaluation metrics, and full observability.

Built as a monorepo with an **Angular** frontend and a **FastAPI** backend, backed by
**Postgres + pgvector**, and fully containerized with CI.

> **Stack:** Angular 22 · FastAPI · Postgres/pgvector · LangChain · HuggingFace embeddings ·
> Google Gemini · Docker · GitHub Actions

---

## ✨ Features

- 📄 **Multi-format ingestion** — PDF, TXT, DOCX
- 🧠 **Free local embeddings** (`all-MiniLM-L6-v2`) or a lightweight embedding **API** — switchable
- 🔎 **Hybrid retrieval** — dense (pgvector) + sparse (Postgres full-text), fused with **Reciprocal Rank Fusion**
- 🎯 **Cross-encoder re-ranking** for precision
- ♻️ **Multi-query rewriting** to improve recall
- 💬 **Conversational memory** — follow-up questions resolve against chat history
- 🔗 **Grounded answers with sources** — every reply cites the chunks it used
- 🗂️ **Document management** — list, inspect, and delete documents (vectors + metadata)
- 📊 **Evaluation harness** — RAGAS-style metrics (faithfulness, answer relevancy, context precision/recall)
- 🔭 **Observability** — structured JSON logs + per-request latency, token usage, and estimated cost
- 🔄 **Swappable LLM** — Google Gemini (default) or local Ollama, via env var
- 🐳 **Dockerized** with `docker-compose` and **GitHub Actions CI**

---

## 🏗️ Architecture

```mermaid
flowchart LR
    U[User] --> FE[Angular SPA<br/>nginx]
    FE -->|REST| API[FastAPI backend]

    subgraph Ingestion
      API --> L[Load & chunk<br/>PDF/TXT/DOCX]
      L --> E1[Embed chunks]
      E1 --> VS[(Postgres + pgvector)]
      API --> M[(documents table)]
    end

    subgraph Query
      API --> QR[Multi-query rewrite]
      QR --> DR[Dense search<br/>pgvector]
      QR --> SR[Sparse search<br/>Postgres FTS]
      DR --> RRF[Reciprocal Rank Fusion]
      SR --> RRF
      RRF --> RR[Cross-encoder re-rank]
      RR --> P[Prompt + context + history]
      P --> LLM[Gemini / Ollama]
      LLM --> ANS[Answer + sources]
    end
```

| Layer | Technology |
| ----- | ---------- |
| Frontend | Angular 22 (standalone, signals), nginx |
| Backend | FastAPI, Pydantic, Uvicorn |
| Vector DB + metadata | Postgres + pgvector (Neon free tier) |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` (local) or Gemini embedding API |
| Retrieval | Hybrid (dense + BM25-style FTS) + RRF + cross-encoder re-ranking |
| LLM | Google Gemini `gemini-flash-lite-latest` (REST) · optional Ollama |
| Infra | Docker, docker-compose, GitHub Actions |

---

## 📁 Monorepo structure

```
.
├── backend/                     # FastAPI service
│   ├── app/
│   │   ├── main.py              # app, CORS, observability middleware, lifespan
│   │   ├── config.py           # env-driven settings (provider switches)
│   │   ├── api/                # chat (JSON + SSE), documents (ingest/list/delete)
│   │   ├── core/               # loader, chunker, embeddings, vectorstore, retriever, reranker, query_rewrite, llm
│   │   ├── db/                 # SQLAlchemy engine/session + Document model
│   │   ├── schemas/            # Pydantic request/response models
│   │   ├── services/           # ingest + chat orchestration
│   │   └── observability/      # structured logging + per-request metrics
│   ├── evaluation/             # RAGAS-style metrics + golden dataset + runner
│   ├── tests/                  # pytest (unit + integration)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                    # Angular app (chat UI, upload, doc manager)
│   ├── src/app/                # components, services, models
│   ├── Dockerfile              # multi-stage build -> nginx
│   └── nginx.conf              # serves SPA + proxies /api to backend
├── docker-compose.yml
└── .github/workflows/ci.yml     # backend tests + frontend build
```

---

## 🚀 Quickstart

> **You bring your own credentials.** This repo never ships anyone's keys or database —
> `backend/.env` is gitignored. Each person runs DocuMind with **their own** LLM (a free
> Gemini key *or* local Ollama) and **their own** database (the bundled local Postgres,
> *or* a free Neon/Supabase URL). You start from `backend/.env.example`, which has blank
> placeholders.

### Option A — Docker (whole stack, incl. database)

Runs the frontend, backend, **and a local Postgres + pgvector database** — no cloud DB needed.

```bash
cp backend/.env.example backend/.env    # then set GOOGLE_API_KEY (or use Ollama)
docker compose up --build
```

- Frontend → http://localhost:4200
- Backend API docs → http://localhost:8000/docs

The compose file provisions a `pgvector` database automatically and points the backend at it,
so the only thing you must supply is an **LLM**: a free `GOOGLE_API_KEY`, or set
`LLM_BACKEND=ollama` for a fully offline setup. (To use Neon/Supabase instead of the bundled
database, comment out the `DATABASE_URL` override in `docker-compose.yml`.)

### Option B — Local dev

**1. Backend**

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows (use source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
copy .env.example .env             # then fill in GOOGLE_API_KEY and DATABASE_URL
uvicorn app.main:app --reload --port 8000
```

**2. Frontend** (in a second terminal)

```bash
cd frontend
npm install
npm start                          # http://localhost:4200
```

---

## ⚙️ Configuration (`backend/.env`)

Everything is env-driven, so the same code runs locally, in Docker, and in the cloud.

| Variable | Purpose | Default |
| -------- | ------- | ------- |
| `GOOGLE_API_KEY` | Gemini API key ([free](https://aistudio.google.com/app/apikey)) | — |
| `DATABASE_URL` | Postgres/pgvector URL ([Neon free](https://neon.tech)) | — |
| `LLM_BACKEND` | `gemini` or `ollama` | `gemini` |
| `EMBEDDING_BACKEND` | `local` (sentence-transformers) or `api` (Gemini) | `local` |
| `RETRIEVAL_MODE` | `hybrid` or `dense` | `hybrid` |
| `RERANK_ENABLED` | cross-encoder re-ranking | `true` |
| `MULTI_QUERY_ENABLED` | multi-query rewriting | `true` |
| `TOP_K` | chunks passed to the LLM | `4` |

---

## 📊 Evaluation

A small golden dataset + a RAGAS-style metrics harness lets you measure retrieval and answer quality.

```bash
cd backend
python -m evaluation.evaluate
```

Sample run (6 questions):

| Metric | Avg |
| ------ | --- |
| context_recall | 1.000 |
| context_precision | 0.583 |
| faithfulness | 1.000 |
| answer_relevancy | 0.842 |
| answer_correctness | 0.958 |

---

## 🧪 Testing

```bash
cd backend
pytest
```

- **Unit tests** (offline): chunking, Reciprocal Rank Fusion
- **Integration tests**: ingest → chat → delete (auto-skipped if `DATABASE_URL`/`GOOGLE_API_KEY` are unset)

CI runs the backend tests + lint and the frontend build on every push via GitHub Actions.

---

## 🔭 Observability

Every request emits a structured JSON log and response headers:

```json
{"level":"INFO","message":"request","path":"/api/chat","status":200,
 "total_ms":1850.4,"llm_calls":2,"total_tokens":772,"est_cost_usd":0.000085,
 "timings_ms":{"retrieval_ms":900.1,"llm_ms":950.3}}
```

Headers: `X-Process-Time-Ms`, `X-LLM-Total-Tokens`, `X-Est-Cost-USD` (shown live in the UI per message).

---

## ☁️ Deployment (free tier)

- **Frontend** → Vercel / Netlify / Cloudflare Pages (static Angular build)
- **Backend** → Hugging Face Spaces (Docker) or Render — the backend `Dockerfile` honors `PORT`
- **Database** → Neon / Supabase (free managed Postgres with pgvector)
- **LLM** → Gemini free tier (no compute needed)

For hosted deployments set `apiBase` in `frontend/src/environments/environment.production.ts`
to the backend URL, or serve the frontend behind nginx which proxies `/api` to the backend.

---

## 🔄 Run fully offline (Ollama)

```bash
ollama pull llama3.2
```

Set `LLM_BACKEND=ollama` (and optionally `EMBEDDING_BACKEND=local`) in `backend/.env`. No API key needed.

---

## 🧠 What this project demonstrates

- End-to-end **RAG system design**: ingest → chunk → embed → hybrid retrieve → re-rank → generate
- **Information retrieval** depth: dense + sparse fusion (RRF), cross-encoder re-ranking, multi-query
- **Backend engineering**: typed FastAPI, service layer, SQLAlchemy + pgvector, SSE streaming
- **Frontend engineering**: Angular standalone components, signals, typed HTTP service
- **Quality engineering**: RAGAS-style evaluation + pytest (unit & integration)
- **Production concerns**: structured logging, cost/latency observability, provider abstraction
- **DevOps**: Docker, docker-compose, GitHub Actions CI, free-tier cloud deployment

---

## 📜 License

MIT — free to use and adapt.

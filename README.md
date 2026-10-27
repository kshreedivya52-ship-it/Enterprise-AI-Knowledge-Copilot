Enterprise AI Knowledge Copilot
High-Performance, Zero-Hallucination Enterprise RAG Platform
An enterprise-ready Retrieval-Augmented Generation (RAG) system built for zero-hallucination document intelligence, strict citation attribution, and department-level Role-Based Access Control (RBAC).

⚡ What This System Does
Vision-Aware Document Parsing: Ingests complex enterprise documents (PDF, DOCX, TXT) via LlamaParse, accurately extracting tables, headers, and hierarchical layout elements.
Hybrid Search (Dense + Sparse): Dual-vector representation in Qdrant combining dense semantic embeddings (BAAI/bge-small-en-v1.5) and sparse lexical representations (SPLADE) fused via Reciprocal Rank Fusion (RRF).
Two-Stage Precision Reranking: Filters top candidate passages using a Cross-Encoder (BGE-Reranker) down to the top 5 most relevant context chunks.
Grounded Generation & Verbatim Citations: Constrains OpenAI GPT-4o using strict Pydantic structured schemas, mandating verbatim quotation and source attribution, with an automatic fallback refusal if evidence is insufficient.
Enterprise RBAC & Department Isolation: Cryptographic JWT-based access control enforcing pre-filtering across department collections (Finance, Engineering, Legal, HR).
Multi-Turn Chat Persistence: Stateful chat session management and history tracking backed by PostgreSQL (asyncpg & SQLAlchemy).
Production Observability: Complete execution tracing, latency profiling, and token monitoring via LangSmith.
Modern Web Dashboard: Dark-mode Streamlit user interface paired with an asynchronous FastAPI REST backend.
🏗️ System Architecture
text
 ┌─────────────────┐       ┌─────────────────┐
 │ Enterprise Docs │ ───►  │   LlamaParse    │ ───► Recursive Semantic Chunking
 └─────────────────┘       └─────────────────┘
                                                       │
                                                       ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ QDRANT HYBRID STORAGE & RETRIEVAL                                                      │
 │  ├─ Dense Vector: BAAI/bge-small-en-v1.5 (Semantic Search)                             │
 │  ├─ Sparse Vector: SPLADE / FastEmbed (Keyword Match)                                  │
 │  └─ Fusion: Reciprocal Rank Fusion (RRF) + RBAC Department Pre-Filtering               │
 └────────────────────────────────────────────────────────────────────────────────────────┘
                                                       │
                                                       ▼
                                          ┌────────────────────────┐
                                          │  BGE Cross-Encoder     │ (Top-5 Re-Ranking)
                                          └────────────────────────┘
                                                       │
                                                       ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ GROUNDED LLM ENGINE (OpenAI GPT-4o)                                                    │
 │  ├─ Injects past conversation window (PostgreSQL session history)                      │
 │  ├─ Strict Pydantic Schema: { answer, citations: [source, quote], is_grounded }        │
 │  └─ Zero-Hallucination Gate: Refuses to guess if context is missing                     │
 └────────────────────────────────────────────────────────────────────────────────────────┘
                                                       │
                                                       ▼
 ┌──────────────────────┐                     ┌──────────────────────┐
 │   FastAPI Backend    │ ◄─────────────────► │ Streamlit Analyst UI │
 └──────────────────────┘                     └──────────────────────┘
            │                                            │
            ▼                                            ▼
   [ LangSmith Tracing ]                        [ PostgreSQL Storage ]
🚀 Quick Start
1. Prerequisites
Python 3.11+
Docker & Docker Compose
API Keys:
OpenAI API Key (OPENAI_API_KEY)
Llama Cloud API Key (LLAMA_CLOUD_API_KEY)
LangSmith API Key (Optional for tracing)
2. Clone & Setup Environment
bash
# Clone the repository
git clone https://github.com/<your-username>/Enterprise-AI-Knowledge-Copilot.git
cd Enterprise-AI-Knowledge-Copilot
# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
# Install dependencies
pip install -r requirements.txt
3. Configure Environment Variables
Create a .env file in the project root:

env
# LLM & Parsing Keys
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
LLAMA_CLOUD_API_KEY=your_llama_cloud_api_key
# Databases & Vector Store (Local Docker)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5433/copilot_db
# Security & RBAC
JWT_SECRET=copilot-local-secret-key-2026
DEV_MODE=true
# Observability (LangSmith)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=Enterprise-AI-Knowledge-Copilot
4. Start Infrastructure (Docker)
Start the local Qdrant vector database and PostgreSQL instances:

bash
docker compose up -d
5. Run Database Migrations
bash
alembic upgrade head
6. Launch Application
In two separate terminals:

Terminal 1: FastAPI Backend

bash
uvicorn app.main:app --reload --port 8000
Terminal 2: Streamlit Dashboard

bash
streamlit run streamlit_app.py --server.port 8501
🌐 Service Access
Service	URL	Purpose
FastAPI Interactive Docs	http://localhost:8000/docs	Swagger UI for API testing
Streamlit Web UI	http://localhost:8501	Multi-turn analyst copilot interface
Qdrant Web Console	http://localhost:6333/dashboard	Visual inspection of vectors & collections
PostgreSQL Database	localhost:5433	User sessions and conversation storage
LangSmith Tracing	https://smith.langchain.com	RAG execution tracing, latency, & tokens
🔌 API Endpoints Overview
Method	Endpoint	Description	Auth Required
POST	/auth/login	Authenticate and obtain JWT bearer token	No
POST	/auth/register	Register new user with departmental role	No
POST	/ingest/upload	Ingest, parse (LlamaParse), chunk, and index document	Yes (editor/admin)
GET	/search	Stateful hybrid search + grounded answer with citations	Yes
GET	/conversations	List conversation threads for current user	Yes
GET	/conversations/{id}/messages	Retrieve past messages in a conversation	Yes
DELETE	/conversations/{id}	Delete a conversation thread	Yes
⚙️ Configuration Reference
Variable	Required	Default	Purpose
OPENAI_API_KEY	✅	—	Used by GPT-4o for grounded answer generation
LLAMA_CLOUD_API_KEY	✅	—	Powers LlamaParse multimodal document parsing
QDRANT_URL	✅	http://localhost:6333	Vector database HTTP API
DATABASE_URL	✅	—	PostgreSQL async connection string (asyncpg)
JWT_SECRET	✅	—	Secret key used for signing RBAC tokens
DEV_MODE	❌	false	Bypasses external Auth0 in favor of local JWTs
LANGCHAIN_TRACING_V2	❌	false	Enables full request tracing to LangSmith
🔧 Technology Stack
API & Core: FastAPI, Uvicorn, Python 3.11+, Pydantic v2
LLM & Orchestration: OpenAI GPT-4o, LangChain, LangChain-OpenAI
Vector Store & Retrieval: Qdrant, FastEmbed (Sparse SPLADE + Dense BGE-small), Reciprocal Rank Fusion (RRF)
Re-ranking: BAAI Cross-Encoder (bge-reranker-base)
Document Parsing: LlamaParse (LlamaIndex Cloud)
Persistence: PostgreSQL, SQLAlchemy (Async), asyncpg, Alembic
Security: Python-Jose (JWT), Cryptography, Role-Based Access Control (RBAC)
Observability: LangSmith
Frontend UI: Streamlit
📁 Project Structure
text
Enterprise-AI-Knowledge-Copilot/
├── app/
│   ├── core/                  # Core modules
│   │   ├── auth.py            # JWT verification & RBAC decorators
│   │   ├── chunker.py         # Recursive character text splitting
│   │   ├── database.py        # Async SQLAlchemy engine & session factory
│   │   ├── llm.py             # Grounded prompt construction & Pydantic output
│   │   ├── parser.py          # LlamaParse document extraction
│   │   ├── reranker.py        # BGE Cross-Encoder reranker
│   │   └── vector_db.py       # Qdrant hybrid index setup & RRF search
│   ├── crud/                  # Database CRUD queries
│   ├── models/                # SQLAlchemy database schemas
│   ├── routes/                # FastAPI endpoint routers
│   │   ├── auth.py            # Login & registration endpoints
│   │   ├── conversations.py   # Multi-turn chat session management
│   │   ├── ingest.py          # Document upload & ingestion pipeline
│   │   └── search.py          # Hybrid retrieval & RAG query execution
│   └── main.py                # FastAPI initialization & lifespan management
├── alembic/                   # Database migration scripts
├── docker-compose.yml         # Container configuration (Qdrant, PostgreSQL)
├── requirements.txt           # Python package dependencies
├── streamlit_app.py           # Streamlit web copilot interface
└── README.md
🛠️ Essential Commands & Troubleshooting
bash
# Start container dependencies
docker compose up -d
# Check running container health
docker ps
# Restart backend services
uvicorn app.main:app --reload
# View container logs
docker compose logs -f qdrant
docker compose logs -f postgres
# Reset database & vector cache (destructive)
docker compose down -v && docker compose up -d
alembic upgrade head
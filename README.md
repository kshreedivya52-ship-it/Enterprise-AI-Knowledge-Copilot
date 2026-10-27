Enterprise AI Knowledge Copilot
High-Performance, Grounded Enterprise RAG Platform
An enterprise-ready Retrieval-Augmented Generation (RAG) system designed for grounded document intelligence, strict citation attribution, and department-level Role-Based Access Control (RBAC).
⚡ What This System Does
- Vision-aware document parsing: Ingests enterprise documents (PDF, DOCX, TXT) through LlamaParse, extracting tables, headers, and hierarchical layout elements.
- Hybrid search (dense + sparse): Uses dual-vector representations in Qdrant, combining dense semantic embeddings (BAAI/bge-small-en-v1.5) and sparse lexical representations (SPLADE), fused with Reciprocal Rank Fusion (RRF).
- Two-stage precision reranking: Uses a BGE Cross-Encoder to rerank candidate passages and select the five most relevant context chunks.
- Grounded generation and verbatim citations: Uses OpenAI GPT-4o with Pydantic structured schemas for answers, quotations, and source attribution. If evidence is insufficient, the system can refuse to guess.
- Enterprise RBAC and department isolation: JWT-based access control applies department-level restrictions across Finance, Engineering, Legal, and HR collections.
- Multi-turn chat persistence: Stores chat sessions and conversation history in PostgreSQL using SQLAlchemy and asyncpg.
- Production observability: Supports execution tracing, latency profiling, and token monitoring through LangSmith.
- Modern web dashboard: Provides a dark-mode Streamlit interface backed by an asynchronous FastAPI REST API.
🏗️ System Architecture
┌──────────────────┐       ┌──────────────────┐
│ Enterprise Docs  │ ───►  │    LlamaParse    │ ───► Recursive Semantic Chunking
└──────────────────┘       └──────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ QDRANT HYBRID STORAGE & RETRIEVAL                                             │
│  • Dense vector: BAAI/bge-small-en-v1.5 (semantic search)                    │
│  • Sparse vector: SPLADE / FastEmbed (keyword matching)                     │
│  • Fusion: Reciprocal Rank Fusion (RRF) + RBAC department pre-filtering      │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │ BGE Cross-Encoder       │
                         │ Top-5 reranking         │
                         └─────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ GROUNDED LLM ENGINE (OpenAI GPT-4o)                                          │
│  • Injects the conversation window from PostgreSQL session history           │
│  • Pydantic schema: answer, citations [source, quote], is_grounded            │
│  • Grounding gate: refuses to guess when supporting context is missing        │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────┐                 ┌──────────────────────────┐
│ FastAPI Backend          │ ◄──────────────► │ Streamlit Analyst UI     │
└──────────────────────────┘                 └──────────────────────────┘
             │                                             │
             ▼                                             ▼
    [ LangSmith Tracing ]                        [ PostgreSQL Storage ]
🚀 Quick Start
1. Prerequisites
Install the following:
- Python 3.11+
- Docker and Docker Compose
API keys:
- OpenAI API key (OPENAI_API_KEY)
- Llama Cloud API key (LLAMA_CLOUD_API_KEY)
- LangSmith API key (optional; used for tracing)
2. Clone the Repository and Set Up the Environment
Replace <your-username> with the appropriate GitHub username or repository URL.
git clone https://github.com/<your-username>/Enterprise-AI-Knowledge-Copilot.git
cd Enterprise-AI-Knowledge-Copilot

# Create a virtual environment
python -m venv .venv

# Activate on Windows PowerShell
.venv\Scripts\Activate.ps1

# Activate on Windows Command Prompt
.venv\Scripts\activate.bat

# Activate on Linux/macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
3. Configure Environment Variables
Create a .env file in the project root:
# LLM and document parsing
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
LLAMA_CLOUD_API_KEY=your_llama_cloud_api_key

# Databases and vector store (local Docker)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5433/copilot_db

# Security and RBAC
JWT_SECRET=replace_with_a_long_random_secret
DEV_MODE=true

# Observability (LangSmith)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=Enterprise-AI-Knowledge-Copilot
Security note: Keep .env out of version control. Replace example credentials and the development JWT secret with secure values before deploying. Do not commit API keys or production secrets.

4. Start Infrastructure with Docker
Start the local Qdrant vector database and PostgreSQL services:
docker compose up -d
5. Run Database Migrations
alembic upgrade head
6. Launch the Application
Run each service in a separate terminal, with the virtual environment activated.

Terminal 1 — FastAPI backend
uvicorn app.main:app --reload --port 8000
Terminal 2 — Streamlit dashboard
streamlit run streamlit_app.py --server.port 8501
🌐 Service Access
Service	URL / Address	Purpose
FastAPI interactive docs	http://localhost:8000/docs	Swagger UI for API testing
Streamlit web UI	http://localhost:8501	Multi-turn analyst copilot interface
Qdrant web console	http://localhost:6333/dashboard	Inspect vectors and collections
PostgreSQL database	localhost:5433	User sessions and conversation storage
LangSmith tracing	https://smith.langchain.com	RAG execution tracing, latency, and token monitoring


🔌 API Endpoints Overview
Method	Endpoint	Description	Authentication
POST	/auth/login	Authenticate and obtain a JWT bearer token	No
POST	/auth/register	Register a user with a departmental role	No
POST	/ingest/upload	Parse, chunk, and index an uploaded document	Yes — editor/admin
GET	/search	Stateful hybrid search and grounded answer with citations	Yes
GET	/conversations	List conversation threads for the current user	Yes
GET	/conversations/{id}/messages	Retrieve messages from a conversation	Yes
DELETE	/conversations/{id}	Delete a conversation thread	Yes


⚙️ Configuration Reference
Variable	Required	Purpose
OPENAI_API_KEY	Yes	Used by GPT-4o for grounded answer generation
LLAMA_CLOUD_API_KEY	Yes	Powers LlamaParse document parsing
QDRANT_URL	Yes	Qdrant vector database HTTP API; default: http://localhost:6333
DATABASE_URL	Yes	PostgreSQL async connection string using asyncpg
JWT_SECRET	Yes	Secret key used to sign JWTs for RBAC
DEV_MODE	No	Enables local development authentication instead of external Auth0; default: false
LANGCHAIN_TRACING_V2	No	Enables LangSmith request tracing; default: false
LANGCHAIN_API_KEY	No, if tracing disabled	LangSmith API key
LANGCHAIN_PROJECT	No	LangSmith project name


🔧 Technology Stack
- API and core: FastAPI, Uvicorn, Python 3.11+, Pydantic v2
- LLM and orchestration: OpenAI GPT-4o, LangChain, LangChain-OpenAI
- Vector store and retrieval: Qdrant, FastEmbed, dense BGE-small embeddings, sparse SPLADE, Reciprocal Rank Fusion (RRF)
- Reranking: BAAI Cross-Encoder (bge-reranker-base)
- Document parsing: LlamaParse (LlamaIndex Cloud)
- Persistence: PostgreSQL, SQLAlchemy Async, asyncpg, Alembic
- Security: Python-Jose (JWT), Cryptography, Role-Based Access Control (RBAC)
- Observability: LangSmith
- Frontend: Streamlit
📁 Project Structure
Enterprise-AI-Knowledge-Copilot/
├── app/
│   ├── core/
│   │   ├── auth.py            # JWT verification and RBAC helpers
│   │   ├── chunker.py         # Recursive character text splitting
│   │   ├── database.py        # Async SQLAlchemy engine and session factory
│   │   ├── llm.py             # Grounded prompt construction and Pydantic output
│   │   ├── parser.py          # LlamaParse document extraction
│   │   ├── reranker.py        # BGE Cross-Encoder reranker
│   │   └── vector_db.py       # Qdrant hybrid index setup and RRF search
│   ├── crud/                  # Database CRUD queries
│   ├── models/                # SQLAlchemy database schemas
│   ├── routes/
│   │   ├── auth.py            # Login and registration endpoints
│   │   ├── conversations.py   # Multi-turn chat session management
│   │   ├── ingest.py          # Document upload and ingestion pipeline
│   │   └── search.py          # Hybrid retrieval and RAG query execution
│   └── main.py                # FastAPI initialization and lifespan management
├── alembic/                   # Database migration scripts
├── docker-compose.yml         # Qdrant and PostgreSQL container configuration
├── requirements.txt           # Python dependencies
├── streamlit_app.py           # Streamlit copilot interface
└── README.md
🛠️ Essential Commands and Troubleshooting
Essential commands
# Start container dependencies
docker compose up -d

# Check running containers
docker ps

# Start/restart the backend
uvicorn app.main:app --reload

# View service logs
docker compose logs -f qdrant
docker compose logs -f postgres

# WARNING: This removes Docker volumes and may delete local database/vector data.
docker compose down -v
docker compose up -d

# Reapply database migrations
alembic upgrade head
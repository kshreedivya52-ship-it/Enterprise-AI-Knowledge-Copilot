# Enterprise-AI-Knowledge-Copilot

A high-performance, enterprise-ready **Retrieval-Augmented Generation (RAG)** pipeline designed for zero-hallucination document intelligence with verified source citations.
### ✨ Key Architecture & Features:
- 📄 **Smart Parsing**: Document ingestion via **LlamaParse** with recursive text chunking.
- 🔍 **Hybrid Retrieval**: Dense Semantic Search (BGE) + Sparse Keyword Search (SPLADE) via **Qdrant** with Reciprocal Rank Fusion (RRF).
- 🎯 **2-Stage Precision**: Cross-Encoder **BGE Reranking** for top-5 candidate filtering.
- 🧠 **Grounded LLM Generation**: **Google Gemini** with strict citation prompting, type-safe Pydantic output, and verbatim quote attribution.
- 📊 **End-to-End Observability**: Full execution tracing and latency monitoring via **LangSmith**.


uvicorn app.main:app --reload

When you sit down to continue your project:

1. Open VS Code
       ↓
2. Open project folder
       ↓
3. Open terminal
       ↓
4. Activate venv
       ↓
5. Start Docker Desktop
       ↓
6. docker compose up -d
       ↓
7. Check .env
       ↓
8. Start Uvicorn
       ↓
9. Open /docs
       ↓
10. Test your API
       ↓
11. Check LangSmith traces
       ↓
12. Start coding 🚀
Commands you'll probably use most
cd your-project
venv\Scripts\activate
docker compose up -d
docker ps
uvicorn app.main:app --reload

Then:

http://127.0.0.1:8000/docs


🏷️ Recommended GitHub Topics / Tags:
rag • fastapi • qdrant • hybrid-search • splade • gemini • langsmith • reranking • enterprise-ai • python
import logging
from dotenv import load_dotenv

# Load environment variables from .env file before anything else
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes.api import router as items_router
from app.routes.ingest import router as ingest_router
from app.routes.search import router as search_router
from app.core.vector_db import init_qdrant
from app.core.reranker import get_reranker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fastapi_app")

# In-memory mock resource for lifespan demonstration
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Initializing application resources (startup)...")
    app_state["database_connection"] = "Connected to Mock DB"
    app_state["cache_client"] = "Connected to Mock Cache"
    
    # Initialize Qdrant Collection (Dense + Sparse config)
    logger.info("Checking Qdrant collection schema...")
    try:
        init_qdrant()
        logger.info("Qdrant collection initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant collection: {e}")
        
    logger.info(f"Resources initialized: {list(app_state.keys())}")
    
    yield
    
    # Shutdown logic
    logger.info("Cleaning up application resources (shutdown)...")
    app_state.clear()
    logger.info("Application resources cleaned up successfully.")

# Initialize FastAPI app with lifespan context manager
app = FastAPI(
    title="Enterprise AI Knowledge Copilot",
    version="1.0.0",
    lifespan=lifespan
)

# Register routers
app.include_router(items_router)
app.include_router(ingest_router)
app.include_router(search_router)

@app.get("/")
async def root():
    """Root endpoint verifying API is running and lifespan state is active."""
    db_status = "Active" if "database_connection" in app_state else "Inactive"
    return {
        "message": "Welcome to the Enterprise AI Knowledge Copilot API!",
        "database_status": db_status,
        "active_services": list(app_state.keys())
    }


# Inside lifespan(app: FastAPI):
logger.info("Pre-loading BGE Reranker model...")
get_reranker()
logger.info("BGE Reranker ready.")

    


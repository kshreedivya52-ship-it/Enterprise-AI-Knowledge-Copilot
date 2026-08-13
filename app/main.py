import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes.api import router as items_router

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

@app.get("/")
async def root():
    """Root endpoint verifying API is running and lifespan state is active."""
    db_status = "Active" if "database_connection" in app_state else "Inactive"
    return {
        "message": "Welcome to the Enterprise AI Knowledge Copilot API!",
        "database_status": db_status,
        "active_services": list(app_state.keys())
    }

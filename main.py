from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.database import db_client
from app.routers import AI_Chat_threads
from app.services.rag_service import rag_service
from config import settings
import logging

# Configure logging (console only for production)
console_handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
console_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing RAG service...")
    try:
        await rag_service.initialize()
        logger.info("RAG service initialized successfully")
    except Exception as e:
        logger.warning(f"RAG service initialization failed: {e}. Continuing without RAG.")
    
    yield
    # Shutdown
    logger.info("Application shutdown")

app = FastAPI(
    title=getattr(settings, "API_TITLE", "AI assistant"),
    version=getattr(settings, "API_VERSION", "0.1"),
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "CORS_ORIGINS", ["http://localhost:3000"]),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Include routers from app.routers
app.include_router(AI_Chat_threads.router)


@app.get("/")
async def root():
    return {
        "status": "AI running",
        'websocket_endpoint_example': "ws://localhost:8000/ws/chat/{thread_id}/{user_id}"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=getattr(settings, "HOST", "0.0.0.0"),
        port=getattr(settings, "PORT", 8000),
        reload=getattr(settings, "DEBUG", False)
    )
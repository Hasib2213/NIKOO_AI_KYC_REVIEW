from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.database import db_client
from app.database.KYCdatabase import MongoDB
from app.routers import kyc, webhook, AI_Chat_threads
from app.services.rag_service import rag_service
from config import settings
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

# Configure logging (rotating file + console)
log_dir = "app/logs"
os.makedirs(log_dir, exist_ok=True)

file_handler = RotatingFileHandler(
    f"{log_dir}/app.log",
    maxBytes=10485760,  # 10MB
    backupCount=5
)
console_handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Connecting to MongoDB...")
    await MongoDB.connect_db()
    logger.info("MongoDB connected successfully")
    
    # Initialize RAG service
    logger.info("Initializing RAG service...")
    try:
        await rag_service.initialize()
        logger.info("RAG service initialized successfully")
    except Exception as e:
        logger.warning(f"RAG service initialization failed: {e}. Continuing without RAG.")
    
    yield
    # Shutdown
    logger.info("Closing MongoDB connection...")
    await MongoDB.close_db()
    logger.info("MongoDB connection closed")

app = FastAPI(
    title=getattr(settings, "API_TITLE", "AI assistant"),
    version=getattr(settings, "API_VERSION", "0.1"),
    lifespan=lifespan
)

app.add_middleware(
   CORSMiddleware,
  allow_origins=["*"],  # Configure appropriately for production
  allow_credentials=True,
    allow_methods=["*"],
   allow_headers=["*"],
)


# Include routers from app.routers
app.include_router(kyc.router)
app.include_router(webhook.router)
app.include_router(AI_Chat_threads.router)


@app.get("/")
async def root():
    return {
            "status": "AI running",
            'websocket_endpoint_example': "ws://localhost:8000/ws/chat/{thread_id}/{user_id}"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from dotenv import load_dotenv

# Load .env early (in case some code needs it before pydantic)
load_dotenv()

from app.prompts.system_prompt import SYSTEM_PROMPT   # assuming this still exists


class Settings(BaseSettings):
    # ───────────────────────────────────────────────
    #               General API / App
    # ───────────────────────────────────────────────
    API_TITLE: str = "Biometric Verification API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ───────────────────────────────────────────────
    #                   LLM / Groq
    # ───────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3-flash-preview"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 1000

    # System prompt (imported or can be overridden via env if you want)
    SYSTEM_PROMPT: str = SYSTEM_PROMPT

    # ───────────────────────────────────────────────
    #                    Database
    # ───────────────────────────────────────────────
    # Two variants from your snippets — pick one or override in .env
    MONGODB_URL: str = "mongodb://localhost:27017"          # from LLM version
    # MONGODB_URL: str = "mongodb+srv://localhost:27017"    # from Sumsub version (commented)

    DATABASE_NAME: str = "nikoo_ai"                         # from LLM version
    # DATABASE_NAME: str = "biometric_db"                   # from Sumsub version (commented)

    # ───────────────────────────────────────────────
    #                   Sumsub
    # ───────────────────────────────────────────────
    SUMSUB_API_KEY: str = ""
    SUMSUB_SECRET_KEY: str = ""
    SUMSUB_APP_TOKEN: str = ""
    SUMSUB_WEBHOOK_SECRET: str = ""
    SUMSUB_LEVEL_NAME: str = "basic-kyc-level"
    SUMSUB_BASE_URL: str = "https://api.sumsub.com"

    # Kept your original endpoints (no change)
    SUMSUB_DOCUMENT_ENDPOINT: str = "/v1/document/verify"

    # ───────────────────────────────────────────────
    #                 Security / JWT
    # ───────────────────────────────────────────────
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ───────────────────────────────────────────────
    #              Verification Settings
    # ───────────────────────────────────────────────
    LIVENESS_CONFIDENCE_THRESHOLD: float = 0.85
    DOCUMENT_CONFIDENCE_THRESHOLD: float = 0.80
    MAX_FILE_SIZE: int = 10 * 1024 * 1024   # 10MB
    REQUEST_TIMEOUT: int = 30

    # ───────────────────────────────────────────────
    #                 Azure Speech
    # ───────────────────────────────────────────────
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = "southeastasia"
    AZURE_SPEECH_ENDPOINT: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,          # kept as in original
        extra="ignore",
    )


settings = Settings()
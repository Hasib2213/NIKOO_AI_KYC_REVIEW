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
    API_TITLE: str = "Chatbot API"
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



    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,          # kept as in original
        extra="ignore",
    )


settings = Settings()
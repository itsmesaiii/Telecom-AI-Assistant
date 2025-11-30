"""
Configuration - Loads environment variables from .env file.
Manages API keys and file paths for the application.
"""


import os
from dotenv import load_dotenv

# Project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Force-load .env from the project root
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

class Config:
    # LLM API key
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # Paths
    DB_PATH = os.path.join(BASE_DIR, "data", "telecom.db")
    CHROMA_PATH = os.path.join(BASE_DIR, "data", "chromadb")
    DOCUMENTS_PATH = os.path.join(BASE_DIR, "data", "documents")

config = Config()

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Gemini configurations
    gemini_api_key: str
    
    # Qdrant configurations
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "rag_collection"

    # Default RAG configurations
    default_docs_dir: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs")
    default_chunk_size: int = 1000
    default_chunk_overlap: int = 200

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

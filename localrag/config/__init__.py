from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).parent

class Settings(BaseSettings):
    app_mode: str = "desktop"
    port: int = 8080
    ollama_url: str = "http://localhost:11434"
    chat_model: str = "mistral:7b-instruct-q4_K_M"
    embed_model: str = "nomic-embed-text"
    chunk_size: int = 400
    chunk_overlap: int = 100
    top_k: int = 10
    chroma_dir: Path = BASE_DIR / "data" / "chroma_db"
    chroma_collection: str = "documentos"

    class Config:
        env_file = ".env"

settings = Settings()

def get_host() -> str:
    return "127.0.0.1" if settings.app_mode == "desktop" else "0.0.0.0"
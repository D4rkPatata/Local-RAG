from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).parent

class Settings(BaseSettings):
    app_mode: str = "desktop"
    port: int = 8080
    ollama_url: str = "http://localhost:11434"
    chat_model: str = "qwen2.5:3b"
    # Temperatura baja: en RAG factual queremos respuestas deterministas y
    # apegadas al contexto, no creatividad (Ollama usa 0.8 por defecto).
    temperature: float = 0.2
    # Tokens máximos de la respuesta. Ollama por defecto corta en ~128 → respuestas
    # incompletas. Lo subimos para que no trunque procedimientos largos.
    num_predict: int = 768
    # Ventana de contexto. Por defecto 2048 puede truncar el contexto de 10 chunks.
    num_ctx: int = 4096
    # Máximo de mensajes previos (usuario+asistente) que se conservan como memoria.
    max_history_messages: int = 6
    embed_model: str = "nomic-embed-text"
    chunk_size: int = 700
    chunk_overlap: int = 150
    top_k: int = 10
    chroma_dir: Path = BASE_DIR / "data" / "chroma_db"
    chroma_collection: str = "documentos"
    # Política de refusal cuando el usuario no tiene clearance:
    #   "opaque" → no revela que la información existe (indistinguible de "no sé").
    #   "honest" → admite que existe pero está restringida.
    refusal_mode: str = "opaque"

    class Config:
        env_file = ".env"

settings = Settings()

def get_host() -> str:
    return "127.0.0.1" if settings.app_mode == "desktop" else "0.0.0.0"
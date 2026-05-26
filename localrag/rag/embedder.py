from pathlib import Path
import httpx
from config import settings

def embed(texto: str) -> list[float]:
    response = httpx.post(
        f"{settings.ollama_url}/api/embeddings",
        json={"model": settings.embed_model, "prompt": texto},
        timeout=30
    )
    response.raise_for_status()
    return response.json()["embedding"]
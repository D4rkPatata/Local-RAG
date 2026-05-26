from fastapi import APIRouter
import httpx
from config import settings
from rag.vectorstore import list_documents

router = APIRouter()

@router.get("/status")
def status():
    try:
        httpx.get(f"{settings.ollama_url}/api/tags", timeout=3)
        ollama_ok = True
    except Exception:
        ollama_ok = False

    return {
        "ollama": ollama_ok,
        "documentos": len(list_documents()),
        "modelo_chat": settings.chat_model,
        "modelo_embed": settings.embed_model,
    }
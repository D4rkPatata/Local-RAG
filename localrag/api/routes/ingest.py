from fastapi import APIRouter, UploadFile, File, Cookie, HTTPException
from pathlib import Path
import shutil
import tempfile
from rag.ingestion import ingestar
from rag.vectorstore import list_documents, delete_document
from auth import get_session
from access import is_admin

router = APIRouter()


def _require_admin(session_token: str | None):
    """Exige sesión válida Y capacidad de admin. Lanza 401/403 si no."""
    if not session_token:
        raise HTTPException(status_code=401, detail="No autenticado.")
    user = get_session(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Sesión expirada.")
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Solo un administrador puede gestionar documentos.")
    return user


@router.post("/ingest")
async def ingest(file: UploadFile = File(...), session_token: str | None = Cookie(default=None)):
    _require_admin(session_token)
    tmp_path = Path(tempfile.gettempdir()) / file.filename
    with tmp_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    ingestar(tmp_path)
    return {"mensaje": f"{file.filename} ingestado correctamente"}


@router.get("/documents")
def documents(session_token: str | None = Cookie(default=None)):
    # Solo admin: la lista de nombres revelaría la existencia de documentos
    # confidenciales (p. ej. D16_Pricing) a usuarios sin clearance.
    _require_admin(session_token)
    return {"documentos": list_documents()}


@router.delete("/documents/{filename}")
def delete(filename: str, session_token: str | None = Cookie(default=None)):
    _require_admin(session_token)
    delete_document(filename)
    return {"mensaje": f"{filename} eliminado"}

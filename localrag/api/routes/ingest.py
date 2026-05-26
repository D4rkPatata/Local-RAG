from fastapi import APIRouter, UploadFile, File
from pathlib import Path
import shutil
import tempfile
from rag.ingestion import ingestar
from rag.vectorstore import list_documents, delete_document

router = APIRouter()

@router.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    tmp_path = Path(tempfile.gettempdir()) / file.filename
    with tmp_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    ingestar(tmp_path)
    return {"mensaje": f"{file.filename} ingestado correctamente"}

@router.get("/documents")
def documents():
    return {"documentos": list_documents()}

@router.delete("/documents/{filename}")
def delete(filename: str):
    delete_document(filename)
    return {"mensaje": f"{filename} eliminado"}
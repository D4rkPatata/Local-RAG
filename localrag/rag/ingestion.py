import warnings
from pathlib import Path
from parsers.pdf_parser import parse_pdf
from parsers.docx_parser import parse_docx
from parsers.excel_parser import parse_excel, parse_csv
from parsers.text_parser import parse_text
from rag.embedder import embed
from rag.vectorstore import add_documents
from access import DOC_TIER, DEFAULT_TIER, DEFAULT_CATEGORY
from config import settings

PARSERS = {
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".xlsx": parse_excel,
    ".csv": parse_csv,
    ".txt": parse_text,
}

def chunkear(texto: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    # Por defecto se toman los valores de settings (chunk_size=400, overlap=100)
    # para que el corpus se indexe con la granularidad documentada del proyecto.
    chunk_size = chunk_size if chunk_size is not None else settings.chunk_size
    overlap = overlap if overlap is not None else settings.chunk_overlap
    chunks = []
    inicio = 0
    while inicio < len(texto):
        fin = inicio + chunk_size
        chunks.append(texto[inicio:fin])
        inicio += chunk_size - overlap
    return chunks

def _tier_de_archivo(filename: str) -> tuple[str, int, str]:
    """(doc_id, tier, tier_category) a partir del prefijo Dxx del filename.

    Documentos no listados en DOC_TIER se asumen Tier-1/desconocido (sin romper
    la subida de PDFs arbitrarios) y se emite un warning.
    """
    doc_id = filename.split("_")[0]
    if doc_id in DOC_TIER:
        tier, categoria = DOC_TIER[doc_id]
    else:
        tier, categoria = DEFAULT_TIER, DEFAULT_CATEGORY
        warnings.warn(
            f"'{filename}' (doc_id={doc_id}) no está en DOC_TIER; "
            f"se asume Tier-{DEFAULT_TIER}/{DEFAULT_CATEGORY}."
        )
    return doc_id, tier, categoria


def ingestar(path: Path):
    extension = path.suffix.lower()
    parser = PARSERS.get(extension)
    if parser is None:
        raise ValueError(f"Formato no soportado: {extension}")

    texto = parser(path)
    if texto is None:
        raise ValueError(f"El parser devolvió None para {path}. Verifica que el archivo sea válido.")
    if not texto.strip():
        print(f"[AVISO] El archivo {path.name} está vacío o no contiene texto.")
        
    chunks = chunkear(texto)

    doc_id, tier, tier_category = _tier_de_archivo(path.name)
    embeddings = [embed(chunk) for chunk in chunks]
    metadatas = [
        {
            "source": str(path),
            "filename": path.name,
            "chunk_index": i,
            "doc_id": doc_id,
            "tier": tier,
            "tier_category": tier_category,
        }
        for i in range(len(chunks))
    ]

    add_documents(chunks, embeddings, metadatas)
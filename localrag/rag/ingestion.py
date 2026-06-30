import re
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

# Corta en límites de oración / salto de línea, no a media palabra.
_SENT_SPLIT = re.compile(r"(?<=[.!?:;])\s+|\n+")


def _partir_palabras(texto: str, chunk_size: int) -> list[str]:
    """Parte una oración demasiado larga por palabras (sin cortar a media palabra)."""
    out, cur, largo = [], [], 0
    for w in texto.split():
        if largo + len(w) + 1 > chunk_size and cur:
            out.append(" ".join(cur))
            cur, largo = [], 0
        cur.append(w)
        largo += len(w) + 1
    if cur:
        out.append(" ".join(cur))
    return out


def chunkear(texto: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    """Chunking por oraciones: agrupa oraciones hasta chunk_size, con solape.

    Evita el corte a media palabra/oración del chunking por caracteres (que dejaba
    respuestas truncadas tipo "...y notif"). El solape arrastra las últimas oraciones
    al siguiente chunk para no perder continuidad.
    """
    chunk_size = chunk_size if chunk_size is not None else settings.chunk_size
    overlap = overlap if overlap is not None else settings.chunk_overlap

    oraciones = [s.strip() for s in _SENT_SPLIT.split(texto) if s.strip()]
    chunks: list[str] = []
    actual: list[str] = []
    largo = 0

    for s in oraciones:
        if len(s) > chunk_size:  # oración enorme: partir por palabras
            if actual:
                chunks.append(" ".join(actual))
                actual, largo = [], 0
            chunks.extend(_partir_palabras(s, chunk_size))
            continue
        if largo + len(s) + 1 > chunk_size and actual:
            chunks.append(" ".join(actual))
            # solape: arrastrar las últimas oraciones hasta ~overlap caracteres
            arrastre, tot = [], 0
            for prev in reversed(actual):
                if tot + len(prev) > overlap:
                    break
                arrastre.insert(0, prev)
                tot += len(prev) + 1
            actual = arrastre
            largo = sum(len(x) + 1 for x in actual)
        actual.append(s)
        largo += len(s) + 1

    if actual:
        chunks.append(" ".join(actual))
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
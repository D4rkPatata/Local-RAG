from pathlib import Path
from parsers.pdf_parser import parse_pdf
from parsers.docx_parser import parse_docx
from parsers.excel_parser import parse_excel, parse_csv
from parsers.text_parser import parse_text
from rag.embedder import embed
from rag.vectorstore import add_documents

PARSERS = {
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".xlsx": parse_excel,
    ".csv": parse_csv,
    ".txt": parse_text,
}

def chunkear(texto: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    chunks = []
    inicio = 0
    while inicio < len(texto):
        fin = inicio + chunk_size
        chunks.append(texto[inicio:fin])
        inicio += chunk_size - overlap
    return chunks

def ingestar(path: Path):
    extension = path.suffix.lower()
    parser = PARSERS.get(extension)
    if parser is None:
        raise ValueError(f"Formato no soportado: {extension}")

    texto = parser(path)
    chunks = chunkear(texto)

    embeddings = [embed(chunk) for chunk in chunks]
    metadatas = [
        {"source": str(path), "filename": path.name, "chunk_index": i}
        for i in range(len(chunks))
    ]

    add_documents(chunks, embeddings, metadatas)
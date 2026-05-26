from pathlib import Path
from docx import Document

def parse_docx(path: Path) -> str:
    doc = Document(path)
    texto = ""
    for parrafo in doc.paragraphs:
        if parrafo.text.strip():
            texto += parrafo.text + "\n"
    for tabla in doc.tables:
        for fila in tabla.rows:
            texto += " | ".join(celda.text.strip() for celda in fila.cells) + "\n"
    return texto
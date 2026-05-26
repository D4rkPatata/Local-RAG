from pathlib import Path
import fitz

def parse_pdf(path: Path) -> str:
    doc = fitz.open(path)
    texto = ""
    for i, pagina in enumerate(doc):
        texto += f"[Página {i + 1}]\n"
        texto += pagina.get_text()
        texto += "\n"
    return texto
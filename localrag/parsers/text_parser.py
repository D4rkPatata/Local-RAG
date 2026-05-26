from pathlib import Path
from charset_normalizer import from_path

def parse_text(path: Path) -> str:
    resultado = from_path(path).best()
    if resultado is None:
        return path.read_text(encoding="utf-8", errors="ignore")
    return str(resultado)
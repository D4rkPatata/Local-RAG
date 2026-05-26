from pathlib import Path
import pandas as pd

def parse_excel(path: Path) -> str:
    archivo = pd.ExcelFile(path)
    texto = ""
    for nombre_hoja in archivo.sheet_names:
        df = archivo.parse(nombre_hoja)
        texto += f"[Hoja: {nombre_hoja}]\n"
        texto += df.to_csv(index=False) + "\n"
    return texto

def parse_csv(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")
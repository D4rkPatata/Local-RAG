"""
reindex_nexus.py
Limpia el ChromaDB actual e indexa todos los .docx del corpus Nexus
(D01-D15 Tier-1/2 + D16-D23 Tier-3 confidencial).

Uso (desde la raíz del proyecto, con el venv activado):
    python scripts/reindex_nexus.py
"""

import sys
from pathlib import Path

# Forzamos UTF-8 en la salida para que los ✓/✗ y acentos no rompan en
# consolas Windows (cp1252) ni al redirigir la salida a un archivo.
sys.stdout.reconfigure(encoding="utf-8")

# Para que encuentre los módulos del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent / "localrag"))

import chromadb
from config import settings
from rag.ingestion import ingestar

CORPUS_DIR = Path(__file__).parent.parent / "corpus" / "synthetic_docs"

def limpiar_chromadb():
    client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    try:
        client.delete_collection(settings.chroma_collection)
        print(f"✓ Colección '{settings.chroma_collection}' eliminada.")
    except Exception:
        print(f"  Colección '{settings.chroma_collection}' no existía, continuando.")

def indexar_corpus():
    docs = sorted(CORPUS_DIR.glob("*.docx"))
    if not docs:
        print(f"✗ No se encontraron .docx en {CORPUS_DIR}")
        sys.exit(1)

    print(f"\nIndexando {len(docs)} documentos en ChromaDB...\n")
    for doc in docs:
        try:
            ingestar(doc)
            print(f"  ✓ {doc.name}")
        except Exception as e:
            print(f"  ✗ {doc.name} — ERROR: {e}")

    # Verificación
    client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    col = client.get_collection(settings.chroma_collection)
    print(f"\n✓ Indexación completa — {col.count()} chunks almacenados en ChromaDB.")

if __name__ == "__main__":
    print("=" * 55)
    print("  PrivaceCheck — Reindexación corpus Nexus")
    print("=" * 55)
    limpiar_chromadb()
    indexar_corpus()

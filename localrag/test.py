from rag.embedder import embed
from rag.vectorstore import query

embedding = embed("donde trabajo daniel")
resultados = query(embedding, top_k=5)
for r in resultados:
    print("---")
    print(r["metadata"])
    print(r["texto"][:200])
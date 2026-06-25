import airgap  # noqa: F401  — fuerza modo offline antes de cargar el modelo
from sentence_transformers import SentenceTransformer

_model = None

def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _model

def embed(texto: str) -> list[float]:
    model = _get_model()
    return model.encode(texto, convert_to_numpy=True).tolist()
import httpx
import json
from rag.embedder import embed
from rag.vectorstore import query
from config import settings

SYSTEM_PROMPT = """Eres un asistente que responde preguntas sobre documentos internos de una empresa.

Instrucciones:
- Responde siempre en español.
- Usa solo la información del contexto proporcionado para responder.
- Si encuentras la información, responde con detalle.
- Si no encuentras la información en el contexto, dilo brevemente y con naturalidad.
- No inventes información que no esté en el contexto."""

def recuperar_contexto(pregunta: str) -> list[dict]:
    embedding = embed(pregunta)
    return query(embedding, top_k=settings.top_k)

def generar_user_prompt(pregunta: str, chunks: list[dict]) -> str:
    contexto = "\n\n---\n\n".join(
        f"[Fragmento {i+1}]\n{c['texto']}"
        for i, c in enumerate(chunks)
    )
    return f"""Contexto extraído de los documentos:

{contexto}

Pregunta: {pregunta}"""

def chat_stream(pregunta: str):
    chunks = recuperar_contexto(pregunta)
    user_prompt = generar_user_prompt(pregunta, chunks)

    with httpx.stream(
        "POST",
        f"{settings.ollama_url}/api/chat",
        json={
            "model": settings.chat_model,
            "stream": True,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        },
        timeout=120
    ) as response:
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if not data.get("done"):
                    yield data.get("message", {}).get("content", "")
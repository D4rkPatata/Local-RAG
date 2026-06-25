import httpx
import json
from rag.vectorstore import retrieve
from config import settings

SYSTEM_PROMPT = """Eres un asistente que responde preguntas sobre los documentos internos de una empresa.

Reglas estrictas:
- Responde SIEMPRE en español. Nunca uses inglés.
- Usa ÚNICAMENTE la información de los fragmentos del contexto. No inventes nada.
- Cuando un fragmento tenga datos concretos (montos, porcentajes, fechas, plazos, nombres, cifras), inclúyelos TEXTUALMENTE en tu respuesta. No los resumas vagamente.
- Cita el doc_id EXACTO que aparece en el encabezado del fragmento que usaste, en formato corto entre corchetes: [D03] (no escribas "doc_id=" dentro). Ejemplo: "Las vacaciones son 30 días al año [D03]." NUNCA inventes ni adivines un doc_id.
- Solo cita cuando uses de verdad la información de ese fragmento para responder.
- Si la respuesta está en el contexto, respóndela directo y completa; no pidas más información de forma innecesaria.
- Si la información pedida NO está en ningún fragmento, responde EXACTAMENTE: "No tengo esa información en los documentos disponibles." — sin agregar ningún doc_id, corchetes ni nada más. """

# Refusals. En modo "opaque" la negativa por falta de clearance es idéntica a la
# de una pregunta sin respuesta en el corpus → no revela que la información existe.
OPAQUE_REFUSAL = "No tengo información sobre eso en los documentos disponibles."
HONEST_REFUSAL = "Esa información existe pero no tienes el nivel de acceso necesario para consultarla."


def _historial_reciente(history: list[dict] | None) -> list[dict]:
    """Normaliza y recorta el historial a los últimos N mensajes válidos."""
    if not history:
        return []
    limpio = [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]
    return limpio[-settings.max_history_messages:]


def _query_recuperacion(pregunta: str, history: list[dict]) -> str:
    """Query de recuperación enriquecida con los últimos turnos del usuario.

    Así un follow-up corto ("¿y el presupuesto?") recupera con el contexto de la
    conversación en vez de quedarse sin sentido.
    """
    prev_user = [m["content"] for m in history if m["role"] == "user"][-2:]
    return " ".join(prev_user + [pregunta]) if prev_user else pregunta


def recuperar_contexto(pregunta: str, user=None) -> list[dict]:
    return retrieve(pregunta, mode="hibrido", top_k=settings.top_k, user=user)


def _refusal(query: str, user) -> str:
    """Texto de refusal cuando no hay contexto autorizado.

    En modo honesto distingue "no existe" de "existe pero restringido" re-consultando
    sin filtro de acceso; en modo opaco siempre responde lo mismo.
    """
    if settings.refusal_mode == "honest" and user is not None:
        sin_filtro = retrieve(query, mode="hibrido", top_k=settings.top_k)
        return HONEST_REFUSAL if sin_filtro else OPAQUE_REFUSAL
    return OPAQUE_REFUSAL


def generar_user_prompt(pregunta: str, chunks: list[dict]) -> str:
    contexto = "\n\n---\n\n".join(
        f"[Fragmento {i + 1} | doc_id={c['metadata'].get('doc_id', '?')}]\n{c['texto']}"
        for i, c in enumerate(chunks)
    )
    return f"""Contexto extraído de los documentos:

{contexto}

Pregunta: {pregunta}

Recuerda citar el doc_id entre corchetes en cada afirmación."""


def chat_stream(pregunta: str, user=None, history: list[dict] | None = None):
    history = _historial_reciente(history)
    query = _query_recuperacion(pregunta, history)
    chunks = recuperar_contexto(query, user=user)

    # Sin contexto autorizado → refusal directa, NO se llama al LLM.
    if not chunks:
        yield _refusal(query, user)
        return

    mensajes = [{"role": "system", "content": SYSTEM_PROMPT}]
    mensajes += history  # memoria de la conversación
    mensajes.append({"role": "user", "content": generar_user_prompt(pregunta, chunks)})

    with httpx.stream(
        "POST",
        f"{settings.ollama_url}/api/chat",
        json={
            "model": settings.chat_model,
            "stream": True,
            "options": {"temperature": settings.temperature},
            "messages": mensajes,
        },
        timeout=120
    ) as response:
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if not data.get("done"):
                    yield data.get("message", {}).get("content", "")

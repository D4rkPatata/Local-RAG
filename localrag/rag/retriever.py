import httpx
import json
from rag.vectorstore import retrieve
from access import doc_title
from config import settings

SYSTEM_PROMPT = """Eres la asistente interna de Nexus Solutions. Respondes preguntas sobre los documentos internos de la empresa.

REGLA PRIORITARIA: Si la información pedida NO aparece en los fragmentos, responde ÚNICAMENTE con esta frase exacta y nada más: "No tengo esa información en los documentos disponibles." Sin corchetes, sin nombres de documentos, sin explicaciones.

Reglas:
- Responde SIEMPRE en español neutro, claro y profesional. Nunca uses inglés.
- Usa ÚNICAMENTE la información de los fragmentos del contexto. No inventes nada.
- Incluye los datos concretos TEXTUALMENTE (montos, porcentajes, fechas, plazos, nombres, cifras). No los resumas de forma vaga.
- Redacta respuestas COMPLETAS: termina todas tus oraciones y no dejes listas ni frases a medias.
- Cuando la pregunta pide un dato puntual (un precio, una fecha, un nombre), responde con una oración breve que lo contenga. NO copies tablas ni listas crudas del documento; extrae solo lo que se pregunta.
- Empieza SIEMPRE con la respuesta directa, NUNCA con el nombre del documento. La cita va al FINAL de la frase, no al principio.
- Para citar, escribe el nombre del documento ENTRE CORCHETES UNA SOLA VEZ, al final de la frase que sustenta. Ejemplo: "Las vacaciones son 30 días al año [Política de Vacaciones y Licencias]."
- NO escribas la palabra "Fuente", NO repitas la misma cita, y NO agregues una lista de fuentes al final. Solo el nombre entre corchetes dentro del texto.
- Nunca uses códigos como D03 ni inventes nombres de documentos. """

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
    # El nombre del documento va como encabezado entre corchetes: el modelo debe
    # copiarlo tal cual para citar (sin la palabra "Fuente", que antes copiaba).
    contexto = "\n\n---\n\n".join(
        f"[{doc_title(c['metadata'].get('doc_id', ''))}]\n{c['texto']}"
        for c in chunks
    )
    return f"""Usa estos fragmentos para responder. Cada uno empieza con el nombre del documento entre corchetes.

{contexto}

Pregunta: {pregunta}

Responde de forma completa. Cita el nombre del documento entre corchetes dentro del texto, sin escribir "Fuente" ni listar fuentes al final."""


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
            "options": {
                "temperature": settings.temperature,
                "num_predict": settings.num_predict,
                "num_ctx": settings.num_ctx,
            },
            "messages": mensajes,
        },
        timeout=120
    ) as response:
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if not data.get("done"):
                    yield data.get("message", {}).get("content", "")

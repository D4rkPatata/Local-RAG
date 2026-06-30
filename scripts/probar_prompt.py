"""
probar_prompt.py — Prueba el chat (con el LLM) sin pasar por login.

Llama directamente a chat_stream con distintos usuarios y preguntas, e imprime la
respuesta completa. Sirve para iterar el prompt y verificar respuestas sin abrir
la web. Requiere Ollama corriendo con el modelo (qwen2.5:3b).

    python scripts/probar_prompt.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent / "localrag"))

from access import User  # noqa: E402
from rag.retriever import chat_stream  # noqa: E402

# (usuario, rol, pregunta)
CASOS = [
    ("juan.perez", "colaborador_general", "¿Cómo solicito mis vacaciones?"),
    ("juan.perez", "colaborador_general", "¿Cuántos días de vacaciones tengo al año?"),
    ("carlos.vega", "comercial_senior", "¿Cuál es la tarifa hora de un Desarrollador Senior?"),
    ("carlos.vega", "comercial_senior", "¿Cuál es el cliente con mayor contrato anual?"),
    ("juan.perez", "colaborador_general", "¿Cuál es la tarifa hora de un Desarrollador Senior?"),
]


def main() -> None:
    for name, role, pregunta in CASOS:
        user = User(name, role)
        print("=" * 74)
        print(f"[{name} · {role}]  {pregunta}")
        print("-" * 74)
        respuesta = "".join(chat_stream(pregunta, user=user)).strip()
        print(respuesta or "(sin respuesta)")
        print()


if __name__ == "__main__":
    main()

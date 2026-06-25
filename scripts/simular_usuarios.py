"""
simular_usuarios.py — Simula varios usuarios conectándose al chat en paralelo.

Dispara consultas concurrentes con distintos roles contra el endpoint /chat, como
si fueran personas diferentes en distintas laptops. Sirve para demostrar el
control de acceso end-to-end (misma pregunta confidencial → respuesta para quien
tiene clearance, refusal para quien no) y para probar concurrencia.

Requisitos: la app corriendo (python localrag/main.py) y Ollama arriba.

Uso:
    python scripts/simular_usuarios.py
    python scripts/simular_usuarios.py http://192.168.1.50:8080   # contra la LAN
"""
import sys
import concurrent.futures as cf

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"

# (rol, pregunta). La pregunta de pricing es Tier-3 confidencial (D16):
# solo comercial_senior y gerencia deberían poder responderla.
ESCENARIOS = [
    ("colaborador_general", "¿Cuántos días de vacaciones tengo al año?"),
    ("colaborador_general", "¿Cuál es la tarifa hora de un Desarrollador Senior?"),
    ("mando_medio", "¿Cuál es la tarifa hora de un Desarrollador Senior?"),
    ("comercial_senior", "¿Cuál es la tarifa hora de un Desarrollador Senior?"),
    ("tecnico_senior", "¿Cuál es la tarifa hora de un Desarrollador Senior?"),
    ("gerencia", "¿Cuál es el cliente con mayor contrato anual?"),
]


def consultar(idx: int, role: str, pregunta: str) -> tuple[int, str, str, str]:
    try:
        with httpx.stream(
            "POST", f"{BASE}/chat",
            json={"pregunta": pregunta, "role": role},
            timeout=180,
        ) as r:
            if r.status_code != 200:
                return idx, role, pregunta, f"[HTTP {r.status_code}]"
            texto = "".join(part for part in r.iter_text())
        return idx, role, pregunta, texto.strip()
    except Exception as e:
        return idx, role, pregunta, f"[ERROR: {e}]"


def main() -> None:
    print(f"Simulando {len(ESCENARIOS)} usuarios concurrentes contra {BASE}\n")
    with cf.ThreadPoolExecutor(max_workers=len(ESCENARIOS)) as ex:
        futuros = [ex.submit(consultar, i, role, q) for i, (role, q) in enumerate(ESCENARIOS)]
        resultados = [f.result() for f in futuros]

    for idx, role, pregunta, resp in sorted(resultados):
        print("=" * 70)
        print(f"[Usuario {idx + 1}] rol={role}")
        print(f"  P: {pregunta}")
        print(f"  R: {resp[:400]}")
    print("=" * 70)


if __name__ == "__main__":
    main()

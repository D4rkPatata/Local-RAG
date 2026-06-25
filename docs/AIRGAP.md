# Operación air-gapped (sin egreso a red pública)

PrivaceCheck está diseñado para correr **100 % on-premise**: ningún dato de la
empresa debe salir a internet. Este documento describe las capas de control y
cómo **verificarlas**.

> ⚠️ Una VPN **no** sirve para esto: una VPN tuneliza tráfico hacia una red, no
> lo impide. El control correcto es **bloqueo de egreso (air-gap)**.

## Superficies de egreso

| Superficie | Riesgo | Control |
|---|---|---|
| Proceso Python | Descarga de modelos HuggingFace, telemetría de HF y ChromaDB | `airgap.py` (modo offline + telemetría off) |
| Proceso Ollama | `ollama pull` descarga modelos de internet | Firewall de egreso + pre-descarga |

La **inferencia** de Ollama es loopback (`127.0.0.1:11434`) y por tanto local.

## Capa 1 — Endurecimiento del proceso Python (`localrag/airgap.py`)

Se importa al inicio de `main.py`, `embedder.py` y `vectorstore.py`, **antes** de
cargar las librerías pesadas. Fija (idempotente):

- `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1` → HuggingFace/Transformers no
  intentan ninguna conexión; cargan solo desde caché local.
- `HF_HUB_DISABLE_TELEMETRY=1`, `HF_HUB_DISABLE_IMPLICIT_TOKEN=1` → sin telemetría.
- `ANONYMIZED_TELEMETRY=False` → telemetría de ChromaDB (PostHog) apagada.

Por defecto el sistema arranca **OFFLINE**. Solo para la descarga inicial de
modelos (una vez, con red) se ejecuta con `LOCALRAG_OFFLINE=0`.

## Capa 2 — Telemetría de ChromaDB explícita

`vectorstore.py` crea el cliente con `ChromaSettings(anonymized_telemetry=False)`,
de modo que la telemetría queda apagada aunque la variable de entorno no estuviera.

## Capa 3 — Control de acceso por rol y tier

Además de impedir la salida de datos, el sistema restringe **qué datos ve cada
usuario**. Cada documento tiene un tier de sensibilidad (Tier-1/2/3) y el
retriever filtra los chunks por clearance **antes** de pasarlos al LLM
(`where={"doc_id": {"$in": ...}}` en ChromaDB, y filtrado previo en BM25/LDA).

Propiedad clave: como la información restringida **nunca llega al modelo**, el
control es robusto a prompt injection. El benchmark lo confirma:

```bash
python eval/benchmark_access.py
```

> Tier Leakage Rate (retrieval-level): **0.0%** en consultas sin clearance,
> incluyendo ataques `paraphrase`, `indirect` y `jailbreak` (todos 0%).

`scripts/verify_airgap.py` incluye un check que falla si un `colaborador_general`
llega a recibir un chunk Tier-3.

## Capa 4 — Binding solo a loopback

Con `app_mode=desktop` (default), la API escucha en `127.0.0.1` (`get_host()`),
nunca en `0.0.0.0`. No se expone a la red local.

## Capa 5 — Firewall de egreso para Ollama (Windows)

La inferencia local no necesita internet; solo bloqueamos la salida del binario.
El tráfico loopback de Windows no se filtra, así que la app sigue funcionando.

```powershell
# Ajusta la ruta a tu instalación de Ollama
$ollama = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
New-NetFirewallRule -DisplayName "Block Ollama Outbound" -Direction Outbound `
    -Program $ollama -Action Block -Profile Any
```

Defensa en profundidad (opcional): bloquear también la salida de `python.exe` del
venv. Air-gap máximo: máquina físicamente desconectada o contenedor con
`--network none`.

## Setup inicial (una sola vez, con red)

```powershell
# 1. Descargar el modelo de embeddings a la caché de HuggingFace
$env:LOCALRAG_OFFLINE = "0"
python scripts/reindex_nexus.py

# 2. Descargar el modelo de chat en Ollama
ollama pull mistral:7b-instruct-q4_K_M

# 3. A partir de aquí, desconectar / aplicar firewall. El sistema ya es offline.
Remove-Item Env:LOCALRAG_OFFLINE
```

## Verificación (evidencia para el paper)

```powershell
python scripts/verify_airgap.py
```

Instala guardas sobre `socket.connect` y `socket.getaddrinfo`, ejecuta una carga
real (cargar embeddings + recuperar en los 3 modos) y reporta cada intento de
salida, clasificado en loopback vs externo. Salida esperada:

```
Modo offline forzado: True
Intentos de red totales: 0
  Externos (fugas):     —
✓ OK: cero egreso a red pública. El pipeline RAG opera air-gapped.
```

Código de salida `0` = sin fugas; `1` = se detectó egreso externo.

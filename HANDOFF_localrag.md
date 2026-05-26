# Handoff — Proyecto LocalRAG

## Qué es el proyecto

Un ejecutable de escritorio (Windows + Linux) que funciona como chatbot RAG 100% local para pequeñas empresas. El objetivo es que puedan hacer preguntas sobre sus documentos internos (contratos, manuales, listas de clientes) sin que ningún dato salga a internet. Sin llamadas a APIs externas, sin OpenAI, sin nada cloud.

## Decisiones tomadas

- **Stack backend:** Python + FastAPI + Uvicorn
- **LLM local:** Ollama (el usuario lo instala una vez; la app detecta si está y descarga el modelo automáticamente en el primer inicio)
- **Modelos recomendados por RAM:**
  - < 8 GB → `phi3:mini`
  - 8–16 GB → `mistral:7b-instruct-q4_K_M`
  - \> 16 GB → `llama3:8b-instruct`
- **Embeddings:** `nomic-embed-text` vía Ollama (también soporta `sentence-transformers` como fallback)
- **Vector DB:** ChromaDB en modo embebido (carpeta local, sin servidor separado)
- **Parsers:** PyMuPDF (PDF), python-docx (Word), pandas+openpyxl (Excel/CSV), charset-normalizer (TXT)
- **UI:** HTML/JS servido por FastAPI, se abre automáticamente en el browser
- **Empaquetado:** PyInstaller → un solo `.exe` en Windows, binario en Linux
- **Modos:** `desktop` (escucha en `127.0.0.1`) y `server` (escucha en `0.0.0.0`), controlado por env var `LOCALRAG_MODE`. Es el mismo código, un solo flag.
- **Modelo en el exe:** No se bundlea dentro del exe. Se descarga automáticamente en el primer inicio desde Ollama. Solo necesita internet una vez.

## Estructura de carpetas del proyecto

```
localrag/
├── main.py                  # Entry point: wizard de primer inicio + lanza uvicorn + abre browser
├── config.py                # Configuración central (modelos, paths, modo, puerto)
├── requirements.txt         # Dependencias Python
├── api/
│   ├── __init__.py
│   ├── app.py               # FastAPI app instance + mount de estáticos  ← PENDIENTE
│   └── routes/
│       ├── __init__.py
│       ├── chat.py          # POST /chat (streaming SSE)                 ← PENDIENTE
│       ├── ingest.py        # POST /ingest, GET /documents               ← PENDIENTE
│       └── status.py        # GET /status (health + modelos)             ← PENDIENTE
├── rag/
│   ├── __init__.py
│   ├── ingestion.py         # Orquesta parseo + chunking + embed + guardar ← PENDIENTE
│   ├── embedder.py          # Llama a Ollama /api/embeddings              ← PENDIENTE
│   ├── vectorstore.py       # Wrapper de ChromaDB                        ← PENDIENTE
│   └── retriever.py         # Busca chunks relevantes + arma prompt      ← PENDIENTE
├── parsers/
│   ├── __init__.py
│   ├── pdf_parser.py        # ✅ HECHO — PyMuPDF, devuelve str
│   ├── docx_parser.py       # ✅ HECHO — python-docx, incluye tablas
│   ├── excel_parser.py      # ✅ HECHO — pandas, todas las hojas
│   └── text_parser.py       # ✅ HECHO — charset-normalizer auto encoding
├── ui/
│   └── static/
│       ├── index.html       # UI del chat                                ← PENDIENTE
│       ├── style.css        # Estilos                                    ← PENDIENTE
│       └── app.js           # Lógica de chat + SSE streaming             ← PENDIENTE
├── data/
│   └── chroma_db/           # Base vectorial (generada en runtime, gitignored)
└── build/
    └── build.spec           # PyInstaller spec                           ← PENDIENTE
```

## Archivos ya escritos con su contenido clave

### `main.py`
- Función `run_setup_wizard()`: verifica Ollama con `GET /api/tags`, si no está lo explica y reintenta; verifica que `chat_model` y `embed_model` estén descargados, si no los descarga con `POST /api/pull` mostrando barra de progreso (stream de JSON lines).
- Función `open_browser_when_ready()`: hilo daemon que espera hasta que FastAPI responde y abre el browser.
- Al final lanza `uvicorn.run(app, host=get_host(), port=settings.port)`.

### `config.py`
- Clase `Settings` con pydantic-settings. Campos clave: `app_mode` (desktop/server), `port` (8080), `ollama_url`, `chat_model`, `embed_model`, `chunk_size` (800), `chunk_overlap` (150), `top_k` (5), `chroma_dir`, `chroma_collection`.
- Función `get_host()` → `127.0.0.1` si desktop, `0.0.0.0` si server.
- Lee vars de entorno y `.env` file.

### `parsers/pdf_parser.py`
- `parse_pdf(path: Path) -> str` usando `fitz.open()`, recorre páginas, prefija cada una con `[Página N]`.

### `parsers/docx_parser.py`
- `parse_docx(path: Path) -> str` usando `python-docx`, extrae párrafos y tablas (celdas unidas con ` | `).

### `parsers/excel_parser.py`
- `parse_excel(path: Path) -> str` — todas las hojas con `pd.ExcelFile`, prefija con `[Hoja: nombre]`.
- `parse_csv(path: Path) -> str` — pandas con fallback a texto plano.

### `parsers/text_parser.py`
- `parse_text(path: Path) -> str` — usa `charset_normalizer.from_path()` para detectar encoding automáticamente.

### `requirements.txt`
```
fastapi==0.111.0
uvicorn[standard]==0.30.1
chromadb==0.5.3
sentence-transformers==3.0.1
pymupdf==1.24.5
python-docx==1.1.2
openpyxl==3.1.4
pandas==2.2.2
charset-normalizer==3.3.2
httpx==0.27.0
pydantic==2.7.4
pydantic-settings==2.3.3
python-multipart==0.0.9
watchdog==4.0.1
tqdm==4.66.4
rich==13.7.1
```

## Qué falta construir (en orden)

1. **`rag/embedder.py`** — Llama a `POST {ollama_url}/api/embeddings` con `{"model": embed_model, "prompt": texto}`, devuelve lista de floats.

2. **`rag/vectorstore.py`** — Wrapper de ChromaDB. Métodos: `add_documents(chunks, metadatas)`, `query(embedding, top_k)`, `delete_document(doc_id)`, `list_documents()`.

3. **`rag/ingestion.py`** — Orquesta todo: recibe un `Path`, elige el parser según extensión (`.pdf`/`.docx`/`.xlsx`/`.csv`/`.txt`), chunkea el texto respetando `chunk_size` y `chunk_overlap`, llama al embedder por cada chunk, guarda en ChromaDB con metadata `{source, filename, chunk_index}`.

4. **`rag/retriever.py`** — Recibe pregunta en texto, la embede, busca top_k chunks en ChromaDB, arma el prompt con los chunks como contexto, llama a `POST {ollama_url}/api/chat` en modo streaming (SSE), devuelve el stream al cliente.

5. **`api/app.py`** — Crea la instancia FastAPI, monta las rutas, sirve los estáticos de `ui/static/` como `StaticFiles`.

6. **`api/routes/chat.py`** — `POST /chat` recibe `{question: str, history: list}`, llama al retriever, devuelve `StreamingResponse` con SSE.

7. **`api/routes/ingest.py`** — `POST /ingest` acepta archivos o rutas de carpeta, llama a ingestion. `GET /documents` lista lo que hay en ChromaDB.

8. **`api/routes/status.py`** — `GET /status` devuelve si Ollama responde, modelos cargados, cantidad de documentos indexados.

9. **`ui/static/index.html` + `app.js`** — Chat UI con dos paneles: chat a la izquierda, gestión de documentos a la derecha. El chat usa `EventSource` para consumir el streaming SSE de `/chat`.

10. **`build/build.spec`** — PyInstaller spec que incluye `ui/static/` como data files, excluye paquetes innecesarios.

## Notas importantes para el siguiente Claude

- Todos los imports dentro del proyecto usan paths relativos desde la raíz de `localrag/`.
- El proyecto NO usa LangChain a propósito — todo el pipeline está escrito a mano para que sea liviano, auditable y fácil de empaquetar.
- El chunking debe ser por caracteres (no por tokens) para no depender de tokenizadores pesados.
- La UI usa SSE (`EventSource`) para mostrar la respuesta token a token, igual que ChatGPT. El endpoint `/chat` debe devolver `text/event-stream`.
- El modo servidor necesita agregar autenticación básica (usuario/contraseña en `.env`) y historial de chat por usuario en SQLite — esto es v2, no blockeante ahora.
- PyInstaller necesita que `chromadb` y sus dependencias nativas estén en los `hiddenimports` del spec porque no las detecta automáticamente.

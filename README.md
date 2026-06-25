# LocalRAG / PrivaceCheck

Chatbot RAG **100% local** para empresas, con **control de acceso por rol** y
**egreso de red verificado en cero**. Permite preguntar sobre documentos internos
sin que ningún dato salga a internet, y garantiza que cada usuario solo reciba
información de los documentos para los que tiene autorización.

## Requisitos

- Python 3.11/3.12 (entorno gestionado con [uv](https://docs.astral.sh/uv/))
- [Ollama](https://ollama.com) para la generación (LLM local)

## Instalación

```bash
git clone https://github.com/D4rkPatata/Local-RAG.git
cd Local-RAG

# Entorno con uv (recomendado)
uv venv --python 3.12 --prompt local-rag
uv pip install -r requirements.txt

# Modelo de chat (una sola vez, con red)
ollama pull mistral:7b-instruct-q4_K_M
```

> Los **embeddings son locales** (`sentence-transformers`, sin Ollama). El sistema
> arranca en modo offline por defecto; para la primera descarga de modelos usa
> `LOCALRAG_OFFLINE=0`. Ver [docs/AIRGAP.md](docs/AIRGAP.md).

## Uso

```bash
# Indexar el corpus de demostración (23 docs de Nexus Soluciones S.A.C.)
python scripts/reindex_nexus.py

# Levantar la app
python localrag/main.py
```

Abre `http://localhost:8080`, elige tu **rol** en el selector y haz preguntas.

## Control de acceso por rol

Cada documento tiene un *tier* de sensibilidad y los roles tienen distinto
*clearance*. El retriever filtra los chunks **antes** de pasarlos al LLM, así que
la información restringida nunca llega al modelo (robusto incluso ante prompt
injection).

| Rol | Acceso |
|---|---|
| `colaborador_general` | Tier-1 (D01–D08, D15) |
| `mando_medio` | Tier-1 + Tier-2 (D09–D14) |
| `comercial_senior` | + Tier-3 comercial (D16, D17, D18, D22) |
| `tecnico_senior` | + Tier-3 técnico (D19, D20, D21, D23) |
| `gerencia` | Todos los tiers |

La API recibe el rol en cada consulta:

```bash
# colaborador_general preguntando por pricing confidencial (D16, Tier-3) → refusal
curl -N -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"pregunta":"¿Cuál es la tarifa hora de un Desarrollador Senior?","role":"colaborador_general"}'

# comercial_senior → respuesta con citación [D16]
curl -N -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"pregunta":"¿Cuál es la tarifa hora de un Desarrollador Senior?","role":"comercial_senior"}'
```

El modo de refusal se configura en `config` (`refusal_mode`): `opaque` (no revela
que la información existe) u `honest` (admite que existe pero está restringida).

## Evaluación

```bash
python eval/benchmark.py          # ablation del retriever (P@1, P@3, MRR)
python eval/benchmark_tiered.py   # ablation estratificado por tier
python eval/benchmark_access.py   # control de acceso: TLR, FRR, citación, resiliencia adversarial
python scripts/verify_airgap.py   # verifica egreso cero + filtro de acceso
python -m pytest tests/           # tests del control de acceso
```

## Stack

- **Backend:** Python + FastAPI
- **Retriever:** híbrido denso+disperso (embeddings + BM25) con RRF; LDA como ablation
- **Embeddings:** `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers, local)
- **LLM:** Mistral 7B vía Ollama (local)
- **Vector DB:** ChromaDB (con filtro de acceso por metadata)
- **UI:** HTML/CSS/JS

## Formatos soportados

PDF, Word (.docx), Excel (.xlsx), CSV, TXT

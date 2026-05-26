# LocalRAG

Chatbot RAG 100% local para empresas. Puedes hacer preguntas sobre tus documentos internos sin que ningún dato salga a internet.

## Requisitos

- Python 3.10+
- [Ollama](https://ollama.com) instalado y corriendo

## Instalación

```bash
# 1. Clonar el repo
git clone https://github.com/D4rkPatata/Local-RAG.git
cd Local-RAG

# 2. Crear entorno virtual
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate    # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Descargar modelos
ollama pull mistral:7b-instruct-q4_K_M
ollama pull nomic-embed-text
```

## Uso

```bash
python localrag/main.py
```

Abre el browser en `http://localhost:8080`, sube tus documentos y empieza a hacer preguntas.

## Formatos soportados

PDF, Word (.docx), Excel (.xlsx), CSV, TXT

## Stack

- **Backend:** Python + FastAPI
- **LLM:** Mistral 7B vía Ollama (local, sin internet)
- **Embeddings:** nomic-embed-text vía Ollama
- **Vector DB:** ChromaDB
- **UI:** HTML/CSS/JS

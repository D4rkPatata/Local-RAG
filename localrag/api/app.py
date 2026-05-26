from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from api.routes import chat, ingest, status

app = FastAPI(title="LocalRAG")

app.include_router(chat.router)
app.include_router(ingest.router)
app.include_router(status.router)

UI_DIR = Path(__file__).parent.parent / "ui" / "static"
if UI_DIR.exists():
    app.mount("/", StaticFiles(directory=UI_DIR, html=True), name="ui")
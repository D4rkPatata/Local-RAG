import airgap  # noqa: F401  — endurecimiento offline antes de cualquier otra cosa
import sys
import time
import threading
import webbrowser
import httpx
import uvicorn
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def check_ollama(ollama_url: str) -> bool:
    try:
        httpx.get(f"{ollama_url}/api/tags", timeout=3)
        return True
    except Exception:
        return False

def check_model(ollama_url: str, model: str) -> bool:
    try:
        res = httpx.get(f"{ollama_url}/api/tags", timeout=3)
        models = [m["name"] for m in res.json().get("models", [])]
        return any(model in m for m in models)
    except Exception:
        return False

def download_model(ollama_url: str, model: str):
    console.print(f"\n[yellow]Descargando modelo {model}...[/yellow]")
    with httpx.stream("POST", f"{ollama_url}/api/pull",
        json={"name": model}, timeout=600) as response:
        import json
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                status = data.get("status", "")
                if "pulling" in status or "downloading" in status:
                    completed = data.get("completed", 0)
                    total = data.get("total", 1)
                    if total > 0:
                        pct = int((completed / total) * 100)
                        console.print(f"  {status} {pct}%", end="\r")
    console.print(f"\n[green]Modelo {model} listo.[/green]")

def open_browser_when_ready(url: str):
    for _ in range(30):
        time.sleep(1)
        try:
            httpx.get(url, timeout=2)
            webbrowser.open(url)
            return
        except Exception:
            continue

def run_wizard():
    from config import settings

    console.print("\n[bold blue]LocalRAG[/bold blue] — Iniciando...\n")

    # 1. Verificar Ollama
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as progress:
        progress.add_task("Verificando Ollama...")
        time.sleep(1)

    if not check_ollama(settings.ollama_url):
        console.print("[red]✗ Ollama no está corriendo.[/red]")
        console.print("\nPor favor:")
        console.print("  1. Descarga Ollama desde [link=https://ollama.com]ollama.com[/link]")
        console.print("  2. Instálalo y ábrelo")
        console.print("  3. Vuelve a ejecutar este programa\n")
        sys.exit(1)

    console.print("[green]✓ Ollama detectado[/green]")

    # 2. Verificar modelo de chat. Los embeddings son locales (sentence-transformers),
    #    así que embed_model ya NO se descarga: era egreso innecesario.
    if check_model(settings.ollama_url, settings.chat_model):
        console.print(f"[green]✓ Modelo {settings.chat_model} disponible[/green]")
    elif airgap.OFFLINE:
        # En modo air-gap no se descarga nada: se exige el modelo pre-instalado.
        console.print(f"[red]✗ Modelo {settings.chat_model} no está instalado en Ollama.[/red]")
        console.print("\nModo offline activo (sin descargas). Pre-instálalo con red:")
        console.print(f"  ollama pull {settings.chat_model}")
        console.print("  (o ejecuta con LOCALRAG_OFFLINE=0 una sola vez)\n")
        sys.exit(1)
    else:
        download_model(settings.ollama_url, settings.chat_model)

    # 3. Abrir browser cuando el servidor esté listo
    url = f"http://127.0.0.1:{settings.port}"
    threading.Thread(target=open_browser_when_ready, args=(url,), daemon=True).start()

    console.print(f"\n[bold green]Servidor iniciado en {url}[/bold green]\n")

if __name__ == "__main__":
    run_wizard()

    from api.app import app
    from config import settings, get_host

    uvicorn.run(app, host=get_host(), port=settings.port)
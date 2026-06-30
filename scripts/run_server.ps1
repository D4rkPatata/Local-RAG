# run_server.ps1 — Lanza LocalRAG en modo servidor (accesible desde la LAN / una VM).
#
# Requiere: Ollama corriendo + el modelo (ollama pull qwen2.5:3b).
# Uso:  .\scripts\run_server.ps1
#
# main.py imprime la IP a la que se conectan los demás dispositivos.

$env:APP_MODE = "server"
Write-Host "=== LocalRAG en MODO SERVIDOR ===" -ForegroundColor Cyan
Write-Host "Recuerda abrir el puerto 8080 en el firewall (una vez, como admin):" -ForegroundColor DarkGray
Write-Host '  New-NetFirewallRule -DisplayName "LocalRAG 8080" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow' -ForegroundColor DarkGray
Write-Host ""
python localrag/main.py

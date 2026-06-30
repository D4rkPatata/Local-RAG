# Prueba de despliegue: laptop como servidor + VM como "empleado"

Objetivo: correr LocalRAG en tu laptop como si fuera el servidor de la empresa, y
conectarte desde una VM (o segunda laptop) como si fuera la computadora de un
empleado. Dos formas de conectar: por **LAN directa** o por **VPN** (lo más realista).

---

## Paso 0 — Pre-requisitos en la laptop-servidor

```powershell
# Ollama corriendo + modelo de chat (una vez)
ollama pull qwen2.5:3b

# Corpus indexado (una vez)
python scripts/reindex_nexus.py
```

## Paso 1 — Arrancar en modo servidor

```powershell
.\scripts\run_server.ps1
```
Esto escucha en `0.0.0.0:8080` (no solo localhost) e imprime algo como:

```
Modo servidor: otros pueden conectarse en http://192.168.1.45:8080
```

Anota esa IP.

## Paso 2 — Abrir el puerto en el Firewall (una vez, PowerShell como admin)

```powershell
New-NetFirewallRule -DisplayName "LocalRAG 8080" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
```
Sin esto, el firewall de Windows bloquea las conexiones entrantes.

---

## Paso 3 — Conectar la VM. Elige UNA opción.

### Opción A — LAN directa (red puente / bridged)  ·  más simple

La VM debe estar en la **misma red** que la laptop. En tu software de VM cambia el
adaptador de red a **"Adaptador puente" (Bridged)**:

- VirtualBox: Configuración → Red → "Conectado a: Adaptador puente".
- VMware: Network Adapter → "Bridged".
- Hyper-V: conectar a un "External Virtual Switch".

Con bridged, la VM obtiene su propia IP en tu WiFi (como si fuera otra laptop).
Desde el navegador de la VM:

```
http://192.168.1.45:8080      ← la IP que imprimió el servidor
```

> Si usas NAT (por defecto), la VM NO ve a la laptop por su IP de LAN. Por eso se
> recomienda **bridged** para esta prueba.

### Opción B — VPN con Tailscale  ·  más realista (recomendado)

Simula el caso real: solo dispositivos autorizados (en la VPN) pueden alcanzar el
servidor. Tailscale es una VPN tipo malla, gratis y muy fácil.

1. Crea una cuenta en tailscale.com.
2. Instala Tailscale en la **laptop-servidor** y en la **VM**; inicia sesión con la
   misma cuenta en ambos.
3. Cada dispositivo recibe una IP privada `100.x.x.x`. Mira la del servidor:
   ```powershell
   tailscale ip -4
   ```
4. Desde la VM, en el navegador:
   ```
   http://100.x.x.x:8080      ← la IP Tailscale del servidor
   ```

Ventaja: aunque la VM y la laptop estén en redes distintas, se conectan por la VPN
cifrada; y **solo los dispositivos dentro de tu tailnet** pueden entrar. Eso es
exactamente la "capa de red" de la que hablamos (control de ingreso).

---

## Paso 4 — Iniciar sesión y probar el control de acceso

En la VM verás la **pantalla de login**. Usuarios de demo (contraseña `password123`):

| Usuario | Rol | Debe ver |
|---|---|---|
| `juan.perez` | colaborador_general | Solo Tier-1 |
| `ana.gomez` | mando_medio | Tier-1/2 |
| `carlos.vega` | comercial_senior | + Tier-3 comercial |
| `lucia.rios` | tecnico_senior | + Tier-3 técnico |
| `admin` | gerencia | Todo |

Prueba la demo de acceso con la **misma** pregunta y dos cuentas distintas:

> ¿Cuál es la tarifa hora de un Desarrollador Senior?

- Login como `juan.perez` → **refusal** (no tiene clearance).
- Login como `carlos.vega` → **"S/. 110 [D16]"**.

Eso demuestra, desde otra máquina, que cada cuenta recibe solo lo suyo.

---

## Si no conecta — checklist

1. ¿El servidor dice "Modo servidor: ... http://IP:8080"? (si no, faltó `APP_MODE=server`).
2. ¿Creaste la regla de firewall para el puerto 8080?
3. ¿La VM está en **bridged** (Opción A) o ambos en **Tailscale** (Opción B)?
4. Desde la VM, prueba primero `ping <IP-del-servidor>`; si no responde, es problema de red, no de la app.
5. ¿Ollama está corriendo en la laptop? (la generación lo necesita).

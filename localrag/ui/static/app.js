const API = window.location.origin;
let history = [];

// ── Auth ──────────────────────────────────────────────────────────────────────

async function checkSession() {
    try {
        const res = await fetch(`${API}/auth/me`);
        if (res.ok) {
            const data = await res.json();
            showApp(data.name, data.rol);
        } else {
            showLogin();
        }
    } catch {
        showLogin();
    }
}

async function login() {
    const username = document.getElementById("loginUser").value.trim();
    const password = document.getElementById("loginPass").value;
    const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });
    if (res.ok) {
        const data = await res.json();
        showApp(data.name, data.rol);
    } else {
        document.getElementById("loginError").textContent = "Usuario o contraseña incorrectos.";
    }
}

async function logout() {
    await fetch(`${API}/auth/logout`, { method: "POST" });
    history = [];
    showLogin();
}

function showLogin() {
    document.getElementById("loginScreen").style.display = "flex";
    document.getElementById("appScreen").style.display = "none";
    document.getElementById("loginPass").value = "";
    document.getElementById("loginError").textContent = "";
}

function showApp(name, rol) {
    document.getElementById("loginScreen").style.display = "none";
    document.getElementById("appScreen").style.display = "flex";
    document.getElementById("rolBadge").textContent = `${name} · ${rol}`;
    checkStatus();
    loadDocuments();
}

// ── Chat ──────────────────────────────────────────────────────────────────────

async function sendMessage() {
    const input = document.getElementById("input");
    const pregunta = input.value.trim();
    if (!pregunta) return;

    input.value = "";
    document.getElementById("sendBtn").disabled = true;
    addMessage("Vos", pregunta, "user");
    const msgEl = addMessage("Asistente", "", "assistant thinking");

    try {
        const res = await fetch(`${API}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pregunta, history })  // sin 'role'
        });

        if (res.status === 401) {
            msgEl.textContent = "Sesión expirada. Volvé a iniciar sesión.";
            setTimeout(showLogin, 2000);
            return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let texto = "";
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            texto += decoder.decode(value);
            msgEl.textContent = texto;
            msgEl.classList.remove("thinking");
            scrollToBottom();
        }

        history.push({ role: "user", content: pregunta });
        history.push({ role: "assistant", content: texto });
        history = history.slice(-6);
    } catch (e) {
        msgEl.textContent = "Error al conectar con el servidor.";
    }

    document.getElementById("sendBtn").disabled = false;
}

// ── Documentos ────────────────────────────────────────────────────────────────

async function checkStatus() {
    try {
        const res = await fetch(`${API}/status`);
        const data = await res.json();
        document.getElementById("statusDot").className = "status-dot " + (data.ollama ? "online" : "offline");
    } catch {
        document.getElementById("statusDot").className = "status-dot offline";
    }
}

async function loadDocuments() {
    try {
        const res = await fetch(`${API}/documents`);
        const data = await res.json();
        const list = document.getElementById("docList");
        list.innerHTML = "";
        data.documentos.forEach(doc => {
            const item = document.createElement("div");
            item.className = "doc-item";
            item.innerHTML = `<span title="${doc}">${doc}</span><button onclick="deleteDoc('${doc}')">✕</button>`;
            list.appendChild(item);
        });
    } catch (e) {
        console.error("Error cargando documentos:", e);
    }
}

async function uploadFile(input) {
    const file = input.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    addMessage("Sistema", `Procesando ${file.name}...`, "thinking");
    try {
        const res = await fetch(`${API}/ingest`, { method: "POST", body: formData });
        const data = await res.json();
        removeLastThinking();
        addMessage("Sistema", data.mensaje, "assistant");
        loadDocuments();
    } catch {
        removeLastThinking();
        addMessage("Sistema", "Error al subir el documento.", "assistant");
    }
    input.value = "";
}

async function deleteDoc(filename) {
    await fetch(`${API}/documents/${encodeURIComponent(filename)}`, { method: "DELETE" });
    loadDocuments();
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function addMessage(quien, texto, clase) {
    const messages = document.getElementById("messages");
    const div = document.createElement("div");
    div.className = `message ${clase}`;
    div.textContent = texto;
    messages.appendChild(div);
    scrollToBottom();
    return div;
}

function removeLastThinking() {
    const thinking = document.querySelector(".message.thinking");
    if (thinking) thinking.remove();
}

function scrollToBottom() {
    const messages = document.getElementById("messages");
    messages.scrollTop = messages.scrollHeight;
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("input").addEventListener("keydown", e => {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
    // Enter en login
    document.getElementById("loginPass").addEventListener("keydown", e => {
        if (e.key === "Enter") login();
    });
    checkSession();  // punto de entrada: ¿hay sesión activa?
});

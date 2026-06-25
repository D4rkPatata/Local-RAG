// Misma origen que sirvió la página: en local es 127.0.0.1:8080; desde otra
// laptop en la LAN es http://<ip-del-servidor>:8080. Así el cliente siempre
// apunta al servidor correcto, no a sí mismo.
const API = window.location.origin;

// Memoria de conversación (se envía en cada request para dar continuidad).
let history = [];

// Verificar estado de Ollama al cargar
async function checkStatus() {
    try {
        const res = await fetch(`${API}/status`);
        const data = await res.json();
        const dot = document.getElementById("statusDot");
        dot.className = "status-dot " + (data.ollama ? "online" : "offline");
    } catch {
        document.getElementById("statusDot").className = "status-dot offline";
    }
}

// Cargar lista de documentos
async function loadDocuments() {
    try {
        const res = await fetch(`${API}/documents`);
        const data = await res.json();
        const list = document.getElementById("docList");
        list.innerHTML = "";
        data.documentos.forEach(doc => {
            const item = document.createElement("div");
            item.className = "doc-item";
            item.innerHTML = `
                <span title="${doc}">${doc}</span>
                <button onclick="deleteDoc('${doc}')">✕</button>
            `;
            list.appendChild(item);
        });
    } catch (e) {
        console.error("Error cargando documentos:", e);
    }
}

// Subir documento
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
    } catch (e) {
        removeLastThinking();
        addMessage("Sistema", "Error al subir el documento.", "assistant");
    }

    input.value = "";
}

// Eliminar documento
async function deleteDoc(filename) {
    await fetch(`${API}/documents/${encodeURIComponent(filename)}`, { method: "DELETE" });
    loadDocuments();
}

// Enviar pregunta
async function sendMessage() {
    const input = document.getElementById("input");
    const pregunta = input.value.trim();
    if (!pregunta) return;

    input.value = "";
    document.getElementById("sendBtn").disabled = true;

    addMessage("Vos", pregunta, "user");
    const msgEl = addMessage("Asistente", "", "assistant thinking");

    try {
        const role = document.getElementById("roleSelect").value;
        const res = await fetch(`${API}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pregunta, role, history })
        });

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

        // Guardar el turno en la memoria (cap a 6 mensajes = 3 turnos).
        history.push({ role: "user", content: pregunta });
        history.push({ role: "assistant", content: texto });
        history = history.slice(-6);
    } catch (e) {
        msgEl.textContent = "Error al conectar con el servidor.";
    }

    document.getElementById("sendBtn").disabled = false;
}

// Cambiar de rol reinicia la conversación (no se mezcla contexto entre roles).
document.addEventListener("DOMContentLoaded", () => {
    const sel = document.getElementById("roleSelect");
    if (sel) sel.addEventListener("change", () => { history = []; });
});

// Helpers
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

// Enter para enviar
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("input").addEventListener("keydown", e => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    checkStatus();
    loadDocuments();
});

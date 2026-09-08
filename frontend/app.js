// Cambia esto si el backend corre en otra URL (ej. Cloud Run).
const API_BASE = "http://localhost:8080";

const chatEl = document.getElementById("chat");
const form = document.getElementById("composer");
const input = document.getElementById("message-input");
const contextSelect = document.getElementById("context-select");

let sessionId = null;

function addBubble(text, kind) {
  const div = document.createElement("div");
  div.className = `bubble bubble--${kind}`;
  div.textContent = text;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
  return div;
}

async function loadContexts() {
  const res = await fetch(`${API_BASE}/api/contexts`);
  const data = await res.json();
  contextSelect.innerHTML = "";
  for (const ctx of data.contexts) {
    const opt = document.createElement("option");
    opt.value = ctx.id;
    opt.textContent = `${ctx.nombre_negocio} (${ctx.industria})`;
    contextSelect.appendChild(opt);
  }
}

// Cambiar de negocio reinicia la sesión: cada contexto es una
// conversación independiente, no queremos arrastrar historial
// de un rubro a otro.
contextSelect.addEventListener("change", () => {
  sessionId = null;
  chatEl.innerHTML = "";
  addBubble(`Contexto cambiado a: ${contextSelect.selectedOptions[0].textContent}`, "system");
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  addBubble(message, "user");
  input.value = "";
  input.disabled = true;

  const pending = addBubble("...", "assistant");

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        context_id: contextSelect.value,
        session_id: sessionId,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      pending.textContent = `Error: ${err.detail || res.statusText}`;
      return;
    }

    const data = await res.json();
    sessionId = data.session_id;
    pending.textContent = data.reply;
  } catch (err) {
    pending.textContent = "No se pudo contactar al backend. ¿Está corriendo en " + API_BASE + "?";
  } finally {
    input.disabled = false;
    input.focus();
  }
});

loadContexts().then(() => {
  addBubble("Elige un negocio arriba y escribe tu primera pregunta.", "system");
});

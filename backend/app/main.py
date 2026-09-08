"""
API del chatbot portable.

Endpoints:
  GET  /api/contexts          -> lista los negocios configurados
  POST /api/chat               -> envía un mensaje y recibe la respuesta

Nota de diseño: el historial de conversación se guarda en memoria del
proceso, indexado por session_id. Sirve para una demo y para portafolio;
en un despliegue real (Cloud Run con múltiples instancias, o restart)
esto se perdería, y la solución sería mover el historial a Redis o
Firestore. Se deja así a propósito y se documenta, en vez de fingir que
es persistente.
"""
from collections import defaultdict
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic

from .config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, MAX_TOKENS, MAX_HISTORY_TURNS, DEMO_MODE
from .context_loader import list_context_ids, load_context
from .demo_fallback import generate_demo_reply

app = FastAPI(title="Chatbot de Negocio Portable")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo/portafolio: restringir en producción real
    allow_methods=["*"],
    allow_headers=["*"],
)

client = None if DEMO_MODE else (
    anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
)

# session_id -> {"context_id": str, "history": [{role, content}, ...]}
# Se guarda el context_id junto con el historial a propósito: si llega
# un context_id distinto para el mismo session_id, es una señal de que
# el cliente cambió de negocio y el historial viejo NO debe mezclarse
# con el nuevo (evita que un negocio "vea" datos de otro).
_sessions: dict[str, dict] = {}


class ChatRequest(BaseModel):
    message: str
    context_id: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    context_id: str


@app.get("/api/contexts")
def get_contexts():
    contexts = []
    for cid in list_context_ids():
        ctx = load_context(cid)
        contexts.append({
            "id": ctx.id,
            "nombre_negocio": ctx.nombre_negocio,
            "industria": ctx.industria,
        })
    return {"contexts": contexts}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    ctx = load_context(req.context_id)
    if ctx is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe el contexto de negocio '{req.context_id}'.",
        )

    session_id = req.session_id or str(uuid4())
    session = _sessions.get(session_id)

    # Si la sesión no existe, o existe pero es de otro negocio, se
    # arranca historial limpio. El aislamiento entre negocios se
    # garantiza acá, no solo confiando en que el frontend resetee
    # el session_id al cambiar el selector.
    if session is None or session["context_id"] != req.context_id:
        history = []
    else:
        history = session["history"]

    history.append({"role": "user", "content": req.message})
    trimmed_history = history[-(MAX_HISTORY_TURNS * 2):]

    if client is None:
        # Sin API key configurada, o DEMO_MODE activo a propósito.
        reply_text = generate_demo_reply(ctx, req.message)
    else:
        try:
            response = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=MAX_TOKENS,
                system=ctx.to_system_prompt(),
                messages=trimmed_history,
            )
            reply_text = "".join(
                block.text for block in response.content if block.type == "text"
            )
        except anthropic.APIStatusError as e:
            # La API real falló en pleno uso (sin crédito, rate limit, etc).
            # Se cae al motor de respaldo en vez de romper la demo, pero
            # se avisa explícitamente que fue un fallback, no la IA real.
            reply_text = (
                generate_demo_reply(ctx, req.message)
                + f"\n\n[nota: la API de Anthropic devolvió un error ({e.status_code}), "
                  f"esta respuesta es del motor de respaldo]"
            )

    trimmed_history.append({"role": "assistant", "content": reply_text})
    _sessions[session_id] = {"context_id": req.context_id, "history": trimmed_history}

    return ChatResponse(reply=reply_text, session_id=session_id, context_id=req.context_id)


@app.get("/api/health")
def health():
    return {"status": "ok"}

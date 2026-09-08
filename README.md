# Chatbot de Negocio Portable

Backend en FastAPI + API de Anthropic, y un frontend mínimo en HTML/JS,
diseñado para responder consultas de **cualquier negocio** sin tocar
código: el comportamiento (tono, reglas, base de conocimiento) vive en
un archivo de configuración YAML, no en el código Python.

## Por qué está construido así

La alternativa obvia — un chatbot con el system prompt escrito directo
en el código — funciona para un solo cliente, pero cada negocio nuevo
implica editar y volver a desplegar el backend. Acá el backend es
genérico: lee un contexto de negocio en tiempo de ejecución y arma el
system prompt dinámicamente. Portar el bot a un negocio nuevo es
agregar un archivo `.yaml` en `backend/contexts/`, nada más.

El trade-off explícito: el historial de conversación se guarda en
memoria del proceso (`dict` en Python), indexado por `session_id`. Es
suficiente para una demo, pero no sobrevive a un reinicio ni escala a
múltiples instancias. En un despliegue real esto se movería a Redis o
Firestore — se documenta la limitación en vez de ocultarla.

## Estructura

```
backend/
  app/
    main.py            # endpoints FastAPI
    context_loader.py  # carga YAML -> arma el system prompt
    config.py           # variables de entorno
  contexts/
    arte_cuadro.yaml    # ejemplo: taller de enmarcado (B2C)
    soporte_ti.yaml      # ejemplo: helpdesk interno (B2B interno)
    generico_saas.yaml   # ejemplo: producto SaaS (B2B)
  Dockerfile
  requirements.txt
frontend/
  index.html / app.js / style.css   # UI de chat + selector de negocio
```

## Cómo correrlo local

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # y pega tu ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8080
```

Luego abre `frontend/index.html` en el navegador (o sírvelo con
`python -m http.server` desde esa carpeta). El selector superior
cambia de negocio sin reiniciar el backend.

## Cómo agregar un negocio nuevo

Crea `backend/contexts/mi_negocio.yaml` siguiendo la estructura de los
ejemplos (`nombre_negocio`, `industria`, `tono`, `descripcion`,
`reglas`, `faqs`). Aparece automáticamente en el selector del
frontend — no requiere reiniciar nada ni tocar Python.

## Deploy

El `Dockerfile` sigue el mismo patrón que uso en producción para la
integración Meraki–Freshdesk: contenedor liviano en Python, puerto
tomado de la variable `PORT` para ser compatible con Cloud Run.

```bash
gcloud run deploy chatbot-negocio \
  --source backend/ \
  --set-env-vars ANTHROPIC_API_KEY=xxx,ANTHROPIC_MODEL=claude-sonnet-5 \
  --region us-central1
```

## Limitaciones conocidas (a propósito, no por descuido)

- Sesión en memoria: no persiste entre reinicios ni escala horizontal.
- Sin autenticación: el endpoint `/api/chat` es público. Para producción
  real se necesitaría rate limiting y/o API key por cliente.
- Sin RAG: el "conocimiento" del negocio es una lista corta de FAQs en
  el propio prompt, no una base vectorial. Es la elección correcta para
  negocios con conocimiento acotado; para catálogos grandes convendría
  agregar recuperación (embeddings + vector DB) en vez de meter todo al
  system prompt.

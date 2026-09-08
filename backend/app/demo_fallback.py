"""
Modo demo: responde usando las FAQs del contexto de negocio, sin
llamar a la API de Anthropic. Sirve para dos cosas:

1. Probar la arquitectura (selector de negocio, aislamiento de sesión,
   armado de system prompt) sin gastar créditos.
2. Tener un plan B honesto para una demo en vivo si la cuenta de API
   se queda sin saldo justo antes de una entrevista.

Esto NO es un chatbot con IA — es un matching de palabras clave contra
las preguntas frecuentes cargadas en el YAML. Se declara así en la
respuesta para no hacerse pasar por algo que no es.
"""
import re
from .context_loader import BusinessContext

_STOPWORDS = {
    "el", "la", "los", "las", "de", "del", "un", "una", "y", "o", "que",
    "en", "a", "con", "para", "por", "es", "son", "se", "su", "sus",
    "tiene", "tienen", "como", "cómo", "qué", "cuál", "cuáles",
}


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-záéíóúñ]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def generate_demo_reply(ctx: BusinessContext, message: str) -> str:
    query_tokens = _tokenize(message)

    best_faq = None
    best_score = 0
    for faq in ctx.faqs:
        faq_tokens = _tokenize(faq.pregunta)
        overlap = len(query_tokens & faq_tokens)
        if overlap > best_score:
            best_score = overlap
            best_faq = faq

    prefix = f"[modo demo — {ctx.nombre_negocio}, sin llamada a la API] "

    if best_faq and best_score > 0:
        return prefix + best_faq.respuesta

    return prefix + ctx.mensaje_fuera_de_alcance

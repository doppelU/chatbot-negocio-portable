"""
Este módulo es el corazón de la "portabilidad" del bot.

La idea: el comportamiento del chatbot para un negocio específico
(su tono, sus reglas, su base de conocimiento) vive en un archivo
YAML, no en el código. Para portar el bot a un negocio nuevo, se
agrega un archivo en /contexts — no se toca ni una línea de Python.

Esto es deliberado: separa "cómo funciona el chatbot" (código) de
"qué sabe y cómo habla" (configuración), que es exactamente el tipo
de decisión de diseño que se espera poder explicar en una entrevista.
"""
from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field

from .config import CONTEXTS_DIR


class FAQ(BaseModel):
    pregunta: str
    respuesta: str


class BusinessContext(BaseModel):
    id: str
    nombre_negocio: str
    industria: str
    tono: str
    descripcion: str
    reglas: list[str] = Field(default_factory=list)
    faqs: list[FAQ] = Field(default_factory=list)
    mensaje_fuera_de_alcance: str = (
        "No tengo información sobre eso. Te recomiendo contactar "
        "directamente al equipo del negocio."
    )

    def to_system_prompt(self) -> str:
        """Arma el system prompt que se le pasa a la API de Anthropic."""
        faqs_texto = "\n".join(
            f"- P: {f.pregunta}\n  R: {f.respuesta}" for f in self.faqs
        ) or "(sin FAQs cargadas)"

        reglas_texto = "\n".join(f"- {r}" for r in self.reglas) or "(sin reglas adicionales)"

        return f"""Eres el asistente virtual de "{self.nombre_negocio}", un negocio del rubro {self.industria}.

DESCRIPCIÓN DEL NEGOCIO:
{self.descripcion}

TONO DE COMUNICACIÓN:
{self.tono}

REGLAS QUE DEBES SEGUIR:
{reglas_texto}

BASE DE CONOCIMIENTO (preguntas frecuentes del negocio):
{faqs_texto}

INSTRUCCIONES:
- Responde solo con información contenida en este contexto o de sentido común
  no comprometedor (saludos, cortesía).
- Si te preguntan algo que no está en la base de conocimiento ni se puede
  inferir razonablemente de la descripción del negocio, responde exactamente:
  "{self.mensaje_fuera_de_alcance}"
- No inventes precios, plazos, direcciones ni datos de contacto que no
  aparezcan arriba.
- Mantén el tono especificado en todo momento.
"""


def list_context_ids() -> list[str]:
    return sorted(p.stem for p in CONTEXTS_DIR.glob("*.yaml"))


def load_context(context_id: str) -> Optional[BusinessContext]:
    path = CONTEXTS_DIR / f"{context_id}.yaml"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return BusinessContext(id=context_id, **data)

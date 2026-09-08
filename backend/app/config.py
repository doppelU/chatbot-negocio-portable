"""
Configuración centralizada. Todo lo que depende del entorno vive acá,
para no tener os.environ desperdigado por el código.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CONTEXTS_DIR = BASE_DIR / "contexts"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Modelo configurable vía env. Verifica en docs.claude.com cuál está
# vigente en tu cuenta antes de usar esto en producción.
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "1024"))

# Cuántos turnos de historial se mandan de vuelta al modelo por sesión.
# Es un límite simple para no hacer crecer el costo/latencia sin control.
MAX_HISTORY_TURNS = int(os.environ.get("MAX_HISTORY_TURNS", "12"))

# Si es true, o si no hay API key, el backend responde con el motor de
# respaldo basado en FAQs (sin costo, sin llamar a Anthropic). Útil para
# desarrollar sin gastar créditos, o como plan B si la cuenta se queda
# sin saldo justo antes de una demo en vivo.
DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"

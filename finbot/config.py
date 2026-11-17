"""Settings.

GROQ_API_KEY is read ONLY from the system environment (e.g. exported in ~/.zshrc),
never from a .env file. Optional non-secret settings may come from .env.
"""
import os
from pathlib import Path

from dotenv import dotenv_values

# Secret: system environment only.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Non-secret settings: system env wins, then .env, then defaults.
_dotenv = dotenv_values(Path(__file__).resolve().parent.parent / ".env")


def _setting(name: str, default: str) -> str:
    return os.environ.get(name) or _dotenv.get(name) or default


GROQ_MODEL = _setting("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_TEMPERATURE = float(_setting("GROQ_TEMPERATURE", "0.1"))

DISCLAIMER = (
    "FinBot is for educational purposes only and is not financial advice. "
    "Do your own research or consult a registered financial adviser before investing."
)

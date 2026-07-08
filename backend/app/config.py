"""Configuration centralisée de l'application."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
AGENT_MODEL: str = os.getenv("AGENT_MODEL", "claude-haiku-4-5-20251001")
DATABASE_PATH: Path = BASE_DIR / os.getenv("DATABASE_PATH", "data/sahel.db")
CORS_ORIGINS: list[str] = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()
]

DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

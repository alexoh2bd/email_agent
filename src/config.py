"""Paths, model name, and limits for the email agent."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Repo root (parent of src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

REGION = os.getenv("REGION", "us-central1")
PROJECT_ID = os.getenv("PROJECT_ID", "")

# Vertex model id (short name or full publisher resource string)
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")

MEMORY_DIR = Path(os.getenv("MEMORY_DIR", str(PROJECT_ROOT / "memory")))
GROUNDING_DIR = Path(os.getenv("GROUNDING_DIR", str(PROJECT_ROOT / "memory" / "grounding")))
SEMANTIC_INDEX_PATH = Path(os.getenv("SEMANTIC_INDEX_PATH", str(MEMORY_DIR / "semantic_index.json")))
PERSONA_PATH = Path(os.getenv("PERSONA_PATH", str(MEMORY_DIR / "persona.md")))

MAX_ARCHITECT_TURNS = int(os.getenv("MAX_ARCHITECT_TURNS", "5"))
MAX_DRAFT_TURNS = int(os.getenv("MAX_DRAFT_TURNS", "15"))

# Truncate long grounding reads for the model context
MAX_GROUNDING_CHARS = int(os.getenv("MAX_GROUNDING_CHARS", "8000"))

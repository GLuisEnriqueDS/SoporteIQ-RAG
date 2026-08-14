import os
from pathlib import Path

from dotenv import load_dotenv

BOT_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BOT_DIR.parent

load_dotenv(PROJECT_DIR / ".env")

os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "30")

# --- Vertex AI (Gemini) ---
VERTEX_PROJECT_ID = os.environ["VERTEX_PROJECT_ID"]
VERTEX_LOCATION = os.environ["VERTEX_LOCATION"]
VERTEX_CREDENTIALS_JSON = os.environ["VERTEX_CREDENTIALS_JSON"]
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# --- Embeddings ---
EMBEDDINGS_MODEL = os.environ.get(
    "EMBEDDINGS_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
# --- Base de conocimiento ---
KNOWLEDGE_BASE_PATH = BOT_DIR / "knowledge" / "soporte_tecnico_fibra.json"
CHROMA_PERSIST_DIR = BOT_DIR / "rag" / "chroma_store"
CHROMA_COLLECTION_NAME = "soporte_tecnico_fibra"

# --- Chunking ---
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80
CHUNK_SPLIT_THRESHOLD = 800  # chars; por debajo de esto no se trocea

# --- Recuperación híbrida (vectorial + BM25) ---
RETRIEVAL_K = 4
VECTOR_WEIGHT = 0.5
BM25_WEIGHT = 0.5

MIN_RELEVANCE_SCORE = 0.35

# Turnos consecutivos sin resolver antes de escalar automáticamente.
MAX_INTENTOS_FALLIDOS = 2

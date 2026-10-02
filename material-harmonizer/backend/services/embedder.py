"""
embedder.py
===========
Singleton wrapper around SentenceTransformer(all-MiniLM-L6-v2).

The model is loaded once on first call and reused for all subsequent calls.
Embeddings are L2-normalized (normalize_embeddings=True) so cosine similarity
equals the dot product.

Input text for embedding = cleaned_description + compact spec string.
"""

import logging
from typing import Dict, Any, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── Singleton model ────────────────────────────────────────────────────────────
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        from config import EMBEDDING_MODEL
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}  (first run downloads ~90 MB)")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("Embedding model loaded.")
    return _model


# ── Public helpers ─────────────────────────────────────────────────────────────

def build_embed_text(cleaned_description: str, specs: Dict[str, Any]) -> str:
    """
    Combine cleaned description with a compact spec string for richer embeddings.
    e.g. "hexagon bolt m10 50mm grade 8.8 zinc plated | M10 50 8.8 zinc plated"
    """
    spec_parts = []
    for k, v in specs.items():
        spec_parts.append(str(v))
    spec_str = " ".join(spec_parts)
    if spec_str:
        return f"{cleaned_description} | {spec_str}"
    return cleaned_description


def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Embed a list of strings and return an (N, 384) float32 numpy array.
    Uses batch_size=64, normalize_embeddings=True.
    """
    model = _get_model()
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    embeddings = model.encode(
        texts,
        batch_size=64,
        normalize_embeddings=True,
        show_progress_bar=len(texts) > 200,
    )
    return embeddings.astype(np.float32)


def embed_single(text: str) -> np.ndarray:
    """Embed a single string and return a (384,) float32 array."""
    return embed_texts([text])[0]

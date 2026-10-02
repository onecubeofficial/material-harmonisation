"""
code_generator.py
=================
Generates standard material codes in the format:
    {CAT3}-{SUB3}-{SEQ5}   e.g.  FAS-BLT-00012

SEQ5 is a zero-padded running number per (CAT3, SUB3) derived from the max
existing std_code in the standard_materials table.

Also determines the suggested_description for a cluster: the cleaned
description of the member closest to the cluster centroid, title-cased with
units normalized.
"""

import re
import logging
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.categorizer import categorize_with_codes

logger = logging.getLogger(__name__)

# ── Unit title-case fixup ─────────────────────────────────────────────────────

_UNIT_TITLE_FIXES = [
    (re.compile(r"\bMm\b"), "mm"),
    (re.compile(r"\bKg\b"), "kg"),
    (re.compile(r"\bKv\b"), "kV"),
    (re.compile(r"\bKw\b"), "kW"),
    (re.compile(r"\bHz\b"), "Hz"),
    (re.compile(r"\bVg\b"), "VG"),
    (re.compile(r"\bSae\b"), "SAE"),
    (re.compile(r"\bIso\b"), "ISO"),
    (re.compile(r"\bPvc\b"), "PVC"),
    (re.compile(r"\bHdpe\b"), "HDPE"),
    (re.compile(r"\bPtfe\b"), "PTFE"),
    (re.compile(r"\bNbr\b"), "NBR"),
    (re.compile(r"\bDn\b"), "DN"),
    (re.compile(r"\bNb\b"), "NB"),
    (re.compile(r"\bOd\b"), "OD"),
    (re.compile(r"\bId\b"), "ID"),
    (re.compile(r"\bIs\b"), "IS"),
    (re.compile(r"\bNos\b"), "Nos"),
    (re.compile(r"\bSqMm\b"), "sq mm"),
    (re.compile(r"\bSqM\b"), "sq m"),
]


def _pretty_description(cleaned: str) -> str:
    """Title-case a cleaned description and fix common unit casing."""
    result = cleaned.title()
    for pattern, replacement in _UNIT_TITLE_FIXES:
        result = pattern.sub(replacement, result)
    return result.strip()


# ── Sequence number ────────────────────────────────────────────────────────────

def _next_seq(db: Session, cat3: str, sub3: str) -> int:
    """
    Find the current max SEQ for this (CAT3, SUB3) prefix and return next value.
    Prefix pattern: 'CAT3-SUB3-NNNNN'
    """
    prefix = f"{cat3}-{sub3}-"
    result = db.execute(
        text(
            "SELECT std_code FROM standard_materials "
            "WHERE std_code LIKE :prefix "
            "ORDER BY std_code DESC LIMIT 1"
        ),
        {"prefix": prefix + "%"},
    ).fetchone()

    if result is None:
        return 1

    last_code: str = result[0]
    try:
        seq_part = last_code.split("-")[-1]
        return int(seq_part) + 1
    except (ValueError, IndexError):
        return 1


def generate_std_code(
    category: str,
    subcategory: str,
    db: Session,
) -> str:
    """
    Generate the next standard code for a given category/subcategory.
    Looks up cat/sub codes from category_rules and builds SEQ from DB.
    """
    info = categorize_with_codes(f"{category} {subcategory}")
    cat3 = info.get("cat_code", category[:3].upper())[:3].upper()
    sub3 = info.get("sub_code", subcategory[:3].upper())[:3].upper()

    seq = _next_seq(db, cat3, sub3)
    return f"{cat3}-{sub3}-{seq:05d}"


def pick_suggested_description(
    members: List[Any],          # RawMaterial ORM objects
) -> str:
    """
    Return the cleaned description of the member whose embedding is
    closest to the cluster centroid (highest average cosine similarity).
    Falls back to the longest cleaned description if embeddings are missing.
    """
    valid = [m for m in members if m.embedding is not None and m.cleaned_description]
    if not valid:
        # Fallback: use longest description
        best = max(members, key=lambda m: len(m.cleaned_description or m.description))
        return _pretty_description(best.cleaned_description or best.description)

    embeddings = np.array([np.array(m.embedding, dtype=np.float32) for m in valid])
    centroid = embeddings.mean(axis=0)
    norm = np.linalg.norm(centroid)
    if norm > 0:
        centroid /= norm

    sims = []
    for emb in embeddings:
        n = np.linalg.norm(emb)
        e = emb / n if n > 0 else emb
        sims.append(float(np.dot(e, centroid)))

    best_idx = int(np.argmax(sims))
    best_desc = valid[best_idx].cleaned_description or valid[best_idx].description
    return _pretty_description(best_desc)

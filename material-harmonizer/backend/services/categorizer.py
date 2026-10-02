"""
categorizer.py
==============
Assigns category and subcategory to a material based on keyword matching
against data/category_rules.json.

Strategy: scan all subcategory keyword lists first (more specific), then
fall back to category-level keywords if no subcategory matched.
Falls back to "Uncategorized" / "General" if nothing matches.
"""

import json
import os
import re
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

# ── Load rules once ───────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_rules() -> List[dict]:
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    path = os.path.join(data_dir, "category_rules.json")
    with open(path, "r") as f:
        return json.load(f)["categories"]


# ── Build flat keyword → (category, subcategory) lookup once ─────────────────

@lru_cache(maxsize=1)
def _build_lookup() -> List[Tuple[re.Pattern, str, str, str, str]]:
    """
    Returns a list of (compiled_pattern, cat_name, cat_code, sub_name, sub_code)
    sorted by keyword length descending (longer/more-specific matches first).
    """
    entries = []
    for cat in _load_rules():
        cat_name = cat["name"]
        cat_code = cat["code"]
        for sub in cat.get("subcategories", []):
            sub_name = sub["name"]
            sub_code = sub["code"]
            for kw in sub.get("keywords", []):
                pattern = re.compile(r"\b" + re.escape(kw.lower()) + r"\b")
                entries.append((pattern, cat_name, cat_code, sub_name, sub_code, len(kw)))

    # Sort: longer keywords first so "ball bearing" beats "bearing"
    entries.sort(key=lambda e: e[5], reverse=True)
    return [(p, cn, cc, sn, sc) for p, cn, cc, sn, sc, _ in entries]


def categorize(cleaned_description: str) -> Tuple[str, str]:
    """
    Return (category_name, subcategory_name) for a cleaned description.
    Falls back to ("Uncategorized", "General") if no keywords match.
    """
    if not cleaned_description:
        return "Uncategorized", "General"

    text = cleaned_description.lower()
    lookup = _build_lookup()

    for pattern, cat_name, cat_code, sub_name, sub_code in lookup:
        if pattern.search(text):
            return cat_name, sub_name

    return "Uncategorized", "General"


def categorize_with_codes(cleaned_description: str) -> Dict[str, str]:
    """
    Returns a dict with category, subcategory, category_code, subcategory_code.
    """
    text = cleaned_description.lower()
    lookup = _build_lookup()

    for pattern, cat_name, cat_code, sub_name, sub_code in lookup:
        if pattern.search(text):
            return {
                "category": cat_name,
                "subcategory": sub_name,
                "cat_code": cat_code,
                "sub_code": sub_code,
            }

    return {
        "category": "Uncategorized",
        "subcategory": "General",
        "cat_code": "UNC",
        "sub_code": "GEN",
    }

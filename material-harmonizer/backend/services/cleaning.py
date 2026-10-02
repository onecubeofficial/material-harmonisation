"""
cleaning.py
===========
Normalizes raw material description strings into clean, canonical form.

Pipeline:
  1. Lowercase + trim + collapse whitespace
  2. Normalize separators/punctuation (keep 'x' between numbers for dimensions)
  3. Normalize units to canonical short forms
  4. Expand abbreviations from data/abbreviations.json
  5. Remove meaningless stopwords
"""

import json
import os
import re
from functools import lru_cache
from typing import Dict

# ── Load abbreviation map once ────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_abbreviations() -> Dict[str, str]:
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    path = os.path.join(data_dir, "abbreviations.json")
    with open(path, "r") as f:
        return json.load(f)


# ── Unit normalisation map ────────────────────────────────────────────────────
# Maps common variants → canonical form.  Applied as whole-word replacements.

UNIT_MAP = {
    # length
    r"\bmillimetre\b": "mm",
    r"\bmillimeter\b": "mm",
    r"\bmm\.\b":       "mm",
    r"\bcentimetre\b": "cm",
    r"\bcentimeter\b": "cm",
    r"\bmetre\b":      "m",
    r"\bmeter\b":      "m",
    r"\bmtr\b":        "m",
    r"\bmeters\b":     "m",
    r"\bmetres\b":     "m",
    r"\binch\b":       "inch",
    r"\binches\b":     "inch",
    r'(?<!\w)"(?!\w)': "inch",   # lone double-quote used as inch symbol
    r"\bin\b":         "inch",   # only when used as unit (handled after abbrev pass)
    # mass
    r"\bkilogram\b":   "kg",
    r"\bkilograms\b":  "kg",
    r"\bkgs\b":        "kg",
    r"\bgrams?\b":     "g",
    r"\bgm\b":         "g",
    r"\btonne\b":      "t",
    r"\btonnes\b":     "t",
    r"\bmt\b":         "t",       # metric tonne (ambiguous but most common use)
    # volume / capacity
    r"\blitre\b":      "l",
    r"\bliters?\b":    "l",
    r"\bltr\b":        "l",
    r"\blt\b":         "l",
    r"\bgallon\b":     "gal",
    # electrical
    r"\bvolts?\b":     "v",
    r"\bamperes?\b":   "a",
    r"\bamps?\b":      "a",
    r"\bwatts?\b":     "w",
    r"\bkilowatts?\b": "kw",
    r"\bkilovolt\b":   "kv",
    r"\bhertz\b":      "hz",
    r"\bkilohm\b":     "kohm",
    # area
    r"\bsqmm\b":       "sq mm",
    r"\bsq\.mm\b":     "sq mm",
    r"\bsq\.m\b":      "sq m",
    r"\bsq m\b":       "sq m",
    # pressure
    r"\bkilopascal\b": "kpa",
    r"\bmegapascal\b": "mpa",
    r"\bpound[s]? per square inch\b": "psi",
    # quantity abbreviations
    r"\bnumbers?\b":   "nos",
    r"\bpieces?\b":    "pcs",
    r"\bpairs?\b":     "pr",
    r"\brolls?\b":     "roll",
    r"\bdrums?\b":     "drum",
    r"\bsets?\b":      "set",
}

# Compile unit patterns once
_UNIT_PATTERNS = [(re.compile(pat, re.IGNORECASE), repl)
                  for pat, repl in UNIT_MAP.items()]

# Stopwords – only the truly content-free ones
_STOPWORDS = frozenset(["for", "of", "the", "and", "to", "a", "an", "is", "are",
                         "in", "as", "per", "by", "at", "on", "from", "up"])


def clean_description(raw: str) -> str:
    """
    Return the cleaned, normalised description string.
    """
    if not raw or not isinstance(raw, str):
        return ""

    text = raw.strip()

    # 1. Lowercase
    text = text.lower()

    # 2. Collapse multiple spaces / tabs / newlines
    text = re.sub(r"\s+", " ", text)

    # 3. Normalize separators EXCEPT 'x' between digits (dimension notation)
    #    Replace commas, semicolons, slashes (not in fractions), hyphens between
    #    non-numeric chars with a space.
    text = re.sub(r",|;", " ", text)
    # Replace / unless between digits or between a digit and a unit word
    text = re.sub(r"(?<!\d)/(?!\d)", " ", text)
    # Replace hyphens between non-digit chars
    text = re.sub(r"(?<![0-9])-(?![0-9])", " ", text)
    # Keep e.g. M10x50 but normalise "M10 x 50" → "M10x50"
    text = re.sub(r"(\d)\s+[xX]\s+(\d)", r"\1x\2", text)
    # Also handle "M 10" → "M10" (metric thread prefix)
    text = re.sub(r"\bm\s*-?\s*(\d)", r"m\1", text)

    # 4. Normalize units
    for pattern, replacement in _UNIT_PATTERNS:
        text = pattern.sub(replacement, text)

    # 5. Expand abbreviations (whole-word, longest match first)
    abbrevs = _load_abbreviations()
    # Sort by length descending to match longer abbreviations first
    sorted_abbrevs = sorted(abbrevs.keys(), key=len, reverse=True)
    for abbr in sorted_abbrevs:
        # Only replace if it's a whole word
        pattern = re.compile(r"\b" + re.escape(abbr) + r"\b", re.IGNORECASE)
        text = pattern.sub(abbrevs[abbr], text)

    # 6. Remove stopwords
    tokens = text.split()
    tokens = [t for t in tokens if t not in _STOPWORDS]
    text = " ".join(tokens)

    # 7. Final cleanup – collapse spaces again, strip
    text = re.sub(r"\s+", " ", text).strip()

    return text

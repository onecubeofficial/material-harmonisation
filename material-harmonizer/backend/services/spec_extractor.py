"""
spec_extractor.py
=================
Extracts structured spec attributes from a cleaned description string using
a list of (name, compiled_regex, normalizer_fn) tuples.

Extend by adding new tuples to the SPEC_RULES list at the bottom.
"""

import re
from typing import Any, Callable, Dict, List, Optional, Tuple

# ── Normalizer helpers ────────────────────────────────────────────────────────

def _upper(m: re.Match) -> str:
    return m.group(0).upper().replace(" ", "").replace("-", "")

def _float_group(group: int = 1):
    def _n(m: re.Match) -> str:
        return m.group(group).strip()
    return _n

def _identity(m: re.Match) -> str:
    return m.group(0).strip()

def _normalize_grade(m: re.Match) -> str:
    """Return grade value, removing spaces and normalizing case."""
    raw = m.group(1).strip()
    return raw.upper().replace(" ", "")

def _normalize_thread(m: re.Match) -> str:
    """M10, M-10, M 10 → M10."""
    digits = re.sub(r"[^0-9.]", "", m.group(0))
    return f"M{digits}"

def _normalize_bearing(m: re.Match) -> str:
    return m.group(0).upper().replace(" ", "")

def _normalize_viscosity(m: re.Match) -> str:
    """ISO VG 68 → ISO VG68."""
    raw = m.group(0).upper()
    raw = re.sub(r"\s+", " ", raw).strip()
    # Collapse "ISO VG 68" → "ISO VG68"
    raw = re.sub(r"(ISO\s*VG)\s*(\d+)", r"ISO VG\2", raw)
    return raw

def _normalize_pressure(m: re.Match) -> str:
    raw = m.group(0).upper().replace(" ", "")
    return raw

def _dim_3way(m: re.Match) -> str:
    return f"{m.group(1)}x{m.group(2)}x{m.group(3)}"

def _dim_length(m: re.Match) -> str:
    return m.group(1)

def _normalize_nb(m: re.Match) -> str:
    """DN50 or 2 inch NB → DN50 or NB2INCH."""
    raw = m.group(0).upper().replace(" ", "")
    return raw

def _normalize_cable(m: re.Match) -> str:
    cores = m.group(1).strip()
    area  = m.group(2).strip()
    return f"{cores}Cx{area}sqmm"

def _normalize_voltage(m: re.Match) -> str:
    val  = m.group(1).strip()
    unit = m.group(2).strip().lower()
    if unit in ("v", "volt", "volts"):
        unit = "V"
    elif unit in ("kv", "kilovolt"):
        unit = "kV"
    return f"{val}{unit}"

def _normalize_current(m: re.Match) -> str:
    return f"{m.group(1).strip()}A"

def _normalize_power(m: re.Match) -> str:
    val  = m.group(1).strip()
    unit = m.group(2).strip().lower()
    if unit in ("hp", "horsepower"):
        unit = "hp"
    elif unit in ("kw", "kilowatt"):
        unit = "kW"
    elif unit in ("w", "watt"):
        unit = "W"
    return f"{val}{unit}"

# ── Spec rule type: (name, pattern, normalizer) ──────────────────────────────

SpecRule = Tuple[str, re.Pattern, Callable[[re.Match], str]]

SPEC_RULES: List[SpecRule] = [

    # ── Thread size: M10, M-10, M 10 (must come before length_mm) ────────────
    (
        "thread_size",
        re.compile(r"\bm\s*-?\s*(\d{1,3})(?=\b|x|\s)", re.IGNORECASE),
        _normalize_thread,
    ),

    # ── Dimensions 3-way: 100x50x5 ───────────────────────────────────────────
    (
        "dimensions",
        re.compile(r"(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
        _dim_3way,
    ),

    # ── Length from MxL notation: M10x50 → 50 ────────────────────────────────
    (
        "length_mm",
        re.compile(r"\bm\d+\s*[xX]\s*(\d+(?:\.\d+)?)(?:\s*mm)?\b", re.IGNORECASE),
        _dim_length,
    ),

    # ── Length from explicit "50 mm long" or "50mm" (standalone) ─────────────
    (
        "length_mm",
        re.compile(r"\b(\d+(?:\.\d+)?)\s*mm\s*(?:long|lg|length)\b", re.IGNORECASE),
        _float_group(1),
    ),

    # ── Diameter mm: 10 mm dia, 10mm OD, Ø10 ────────────────────────────────
    (
        "diameter_mm",
        re.compile(
            r"(?:(?:(\d+(?:\.\d+)?)\s*mm\s*(?:dia(?:meter)?|od|id))"
            r"|(?:(?:dia(?:meter)?|od|id)\s*(\d+(?:\.\d+)?)\s*mm))",
            re.IGNORECASE,
        ),
        lambda m: (m.group(1) or m.group(2)).strip(),
    ),

    # ── Diameter inch: 2 inch dia, 2" dia ────────────────────────────────────
    (
        "diameter_inch",
        re.compile(
            r"(\d+(?:\.\d+)?)\s*(?:inch|in|\")\s*(?:dia(?:meter)?|od|id|nb)?",
            re.IGNORECASE,
        ),
        _float_group(1),
    ),

    # ── Nominal bore: DN50, NB50, 2 inch NB ──────────────────────────────────
    (
        "nominal_bore",
        re.compile(r"\b(?:dn|nb)\s*(\d+)\b", re.IGNORECASE),
        lambda m: f"DN{m.group(1)}",
    ),

    # ── Grade: 8.8, 10.9, A2-70, EN8, SS304, IS2062 ──────────────────────────
    (
        "grade",
        re.compile(
            r"\b(?:gr(?:ade)?|cl(?:ass)?|property class|pc)\s*[.\-]?\s*"
            r"((?:[a-z]{0,3}\d+[.\-]?\d*[a-z0-9]*))\b",
            re.IGNORECASE,
        ),
        _normalize_grade,
    ),

    # ── Material: stainless steel, mild steel, carbon steel, brass, etc. ─────
    (
        "material",
        re.compile(
            r"\b(stainless\s*steel|mild\s*steel|carbon\s*steel|cast\s*iron|"
            r"galvanized\s*iron|brass|copper|aluminium|aluminum|pvc|hdpe|ptfe|"
            r"rubber|viton|neoprene|bronze|titanium|inconel|ss\s*30[0-9]|ss\s*31[0-9])\b",
            re.IGNORECASE,
        ),
        lambda m: m.group(1).lower().replace("  ", " ").strip(),
    ),

    # ── Finish: zinc plated, galvanized, black oxide, etc. ───────────────────
    (
        "finish",
        re.compile(
            r"\b(zinc\s*plated|galvanized|galvanised|hot\s*dip\s*galv|"
            r"black\s*oxide|electroless\s*nickel|chrome\s*plated|"
            r"dacromet|mechanical\s*zinc|phosphated)\b",
            re.IGNORECASE,
        ),
        lambda m: m.group(1).lower().strip(),
    ),

    # ── Pressure rating: PN16, 150#, 10 bar ──────────────────────────────────
    (
        "pressure_rating",
        re.compile(
            r"\b(pn\s*\d+|\d+\s*#|\d+(?:\.\d+)?\s*(?:bar|mpa|psi|kpa))\b",
            re.IGNORECASE,
        ),
        _normalize_pressure,
    ),

    # ── Voltage: 415V, 11kV, 230 V ───────────────────────────────────────────
    (
        "voltage",
        re.compile(
            r"\b(\d+(?:\.\d+)?)\s*(v|kv|volt|volts|kilovolt)\b",
            re.IGNORECASE,
        ),
        _normalize_voltage,
    ),

    # ── Current: 32A, 100 A, 63amp ────────────────────────────────────────────
    (
        "current",
        re.compile(r"\b(\d+(?:\.\d+)?)\s*(?:a|amp|ampere)s?\b", re.IGNORECASE),
        _normalize_current,
    ),

    # ── Power: 5 hp, 3.7 kW, 15 W ────────────────────────────────────────────
    (
        "power",
        re.compile(
            r"\b(\d+(?:\.\d+)?)\s*(hp|horsepower|kw|kilowatt|w|watt)s?\b",
            re.IGNORECASE,
        ),
        _normalize_power,
    ),

    # ── Bearing code: 6205, 6205-2RS, NU310, 22210C ──────────────────────────
    (
        "bearing_code",
        re.compile(
            r"\b((?:nu|nj|nb|nn|na|nk|nup|nf|rnu|sl|lm|nnk|"
            r"22|23|24|30|31|32|33)\d{2,3}[a-z0-9\-]*"
            r"|\d{4}[a-z0-9\-]{0,6})\b",
            re.IGNORECASE,
        ),
        _normalize_bearing,
    ),

    # ── Viscosity grade: ISO VG 68, SAE 40 ───────────────────────────────────
    (
        "viscosity_grade",
        re.compile(
            r"\b(iso\s*vg\s*\d+|sae\s*\d+(?:w[\-\s]?\d+)?)\b",
            re.IGNORECASE,
        ),
        _normalize_viscosity,
    ),

    # ── Cable cores x area: 3 core 2.5 sqmm, 3Cx2.5sqmm ─────────────────────
    (
        "cable_cores_area",
        re.compile(
            r"\b(\d+(?:\.\d+)?)\s*[cC](?:ore|ores?)?\s*[xX]?\s*(\d+(?:\.\d+)?)\s*sq\s*mm\b",
            re.IGNORECASE,
        ),
        _normalize_cable,
    ),
]


def extract_specs(cleaned_description: str) -> Dict[str, Any]:
    """
    Run all spec rules against cleaned_description and return a dict of found attributes.
    Only the first match per spec key is kept (unless the rule can appear multiple times,
    in which case the first is most specific for most rules).
    """
    specs: Dict[str, str] = {}
    if not cleaned_description:
        return specs

    for name, pattern, normalizer in SPEC_RULES:
        if name in specs:
            # Already captured this spec key from a higher-priority rule
            continue
        m = pattern.search(cleaned_description)
        if m:
            try:
                value = normalizer(m)
                if value:
                    specs[name] = value
            except (IndexError, AttributeError):
                pass

    return specs

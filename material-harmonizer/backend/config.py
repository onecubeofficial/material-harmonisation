"""
config.py – loads environment variables and exposes typed settings.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Always load .env from the same directory as this file,
# regardless of where uvicorn is launched from.
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

DATABASE_URL: str = os.environ["DATABASE_URL"]

EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Minimum composite score to declare two items a match
MATCH_THRESHOLD: float = float(os.getenv("MATCH_THRESHOLD", "0.80"))

# Confidence band thresholds for cluster review flags
REVIEW_BAND_LOW: float = float(os.getenv("REVIEW_BAND_LOW", "0.80"))
REVIEW_BAND_HIGH: float = float(os.getenv("REVIEW_BAND_HIGH", "0.92"))

# Assumed bulk-purchase discount rate used for savings estimates
BULK_DISCOUNT_ASSUMPTION: float = float(os.getenv("BULK_DISCOUNT_ASSUMPTION", "0.08"))

# Spec keys that trigger the hard-veto rule (values must match or pair is not a match)
HARD_VETO_KEYS = [
    "thread_size",
    "length_mm",
    "diameter_mm",
    "nominal_bore",
    "grade",
    "pressure_rating",
    "bearing_code",
    "voltage",
    "viscosity_grade",
]

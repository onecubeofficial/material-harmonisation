"""
upload.py
=========
POST /api/upload
Accepts multipart: cpse_name (text) + file (.xlsx or .csv).
Required columns: material_code, description
Optional columns:  uom, unit_price, annual_qty, true_group
Upserts the CPSE row and bulk-inserts raw material rows (ON CONFLICT DO NOTHING).
"""

import io
import logging
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from db import get_db
from models import CPSE, RawMaterial, AuditLog
from schemas import UploadResponse

router = APIRouter(prefix="/api", tags=["upload"])
logger = logging.getLogger(__name__)

REQUIRED_COLS = {"material_code", "description"}
OPTIONAL_COLS = {"uom", "unit_price", "annual_qty", "true_group"}


def _read_file(file: UploadFile) -> pd.DataFrame:
    """Read .xlsx or .csv upload into a DataFrame."""
    content = file.file.read()
    filename = (file.filename or "").lower()
    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        df = pd.read_excel(io.BytesIO(content))
    elif filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(content))
    else:
        try:
            df = pd.read_excel(io.BytesIO(content))
        except Exception:
            df = pd.read_csv(io.BytesIO(content))
    return df


@router.post("/upload", response_model=UploadResponse)
def upload_file(
    cpse_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # ── Read file ──────────────────────────────────────────────────────────────
    try:
        df = _read_file(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot read file: {e}")

    # Normalize column names: lowercase + strip
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required columns: {missing}. Found: {list(df.columns)}",
        )

    total_rows = len(df)

    # ── Upsert CPSE ────────────────────────────────────────────────────────────
    cpse = db.query(CPSE).filter(CPSE.name == cpse_name).first()
    if cpse is None:
        cpse = CPSE(name=cpse_name)
        db.add(cpse)
        db.flush()  # get the id

    cpse_id = cpse.id

    # ── Build list of valid rows ───────────────────────────────────────────────
    records = []
    skipped = 0

    for _, row in df.iterrows():
        source_code = str(row["material_code"]).strip()
        description = str(row["description"]).strip()

        if not source_code or not description or source_code == "nan" or description == "nan":
            skipped += 1
            continue

        records.append({
            "cpse_id": cpse_id,
            "source_code": source_code,
            "description": description,
            "uom": _opt_str(row, "uom"),
            "unit_price": _opt_float(row, "unit_price"),
            "annual_qty": _opt_float(row, "annual_qty"),
            "true_group": _opt_str(row, "true_group"),
        })

    # ── Bulk insert with ON CONFLICT DO NOTHING ────────────────────────────────
    # One round-trip for all rows instead of N×2 round-trips.
    inserted = 0
    if records:
        stmt = pg_insert(RawMaterial).values(records)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["cpse_id", "source_code"]  # matches uq_cpse_source
        )
        result = db.execute(stmt)
        inserted = result.rowcount if result.rowcount >= 0 else len(records)
        skipped += (len(records) - inserted)

    # ── Audit log ──────────────────────────────────────────────────────────────
    db.add(AuditLog(
        action="upload",
        entity="cpse",
        entity_id=cpse_id,
        details={
            "cpse_name": cpse_name,
            "file": file.filename,
            "total_rows": total_rows,
            "inserted": inserted,
            "skipped": skipped,
        },
    ))

    db.commit()

    return UploadResponse(
        cpse_name=cpse_name,
        inserted=inserted,
        skipped=skipped,
        total_rows=total_rows,
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _opt_str(row, col: str):
    if col not in row or pd.isna(row[col]):
        return None
    v = str(row[col]).strip()
    return v if v and v != "nan" else None


def _opt_float(row, col: str):
    if col not in row or pd.isna(row[col]):
        return None
    try:
        return float(row[col])
    except (ValueError, TypeError):
        return None

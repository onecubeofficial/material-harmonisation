"""
erp.py
======
GET /api/erp/lookup?cpse=CPSE_A&code=A-000001

Mock ERP integration endpoint.
Given a CPSE name and source code, returns:
  - the standard code and description
  - all equivalent source codes from other CPSEs
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from db import get_db
from models import RawMaterial, CPSE, CodeMapping, StandardMaterial
from schemas import ERPLookupOut, ERPEquivalent

router = APIRouter(prefix="/api", tags=["erp"])
logger = logging.getLogger(__name__)


@router.get("/erp/lookup", response_model=ERPLookupOut)
def erp_lookup(
    cpse: str = Query(..., description="CPSE name, e.g. CPSE_A"),
    code: str = Query(..., description="Source material code, e.g. A-000001"),
    db: Session = Depends(get_db),
):
    # Find the raw material
    raw = (
        db.query(RawMaterial)
        .join(CPSE, CPSE.id == RawMaterial.cpse_id)
        .filter(CPSE.name == cpse, RawMaterial.source_code == code)
        .first()
    )
    if raw is None:
        raise HTTPException(
            status_code=404,
            detail=f"Material code '{code}' not found for CPSE '{cpse}'",
        )

    # Check if it has a standard code mapping
    mapping = (
        db.query(CodeMapping)
        .filter(CodeMapping.raw_material_id == raw.id)
        .first()
    )
    if mapping is None:
        raise HTTPException(
            status_code=404,
            detail=f"No standard code mapped for '{code}' in '{cpse}'. "
                   "Approve the cluster first.",
        )

    std_mat = (
        db.query(StandardMaterial)
        .filter(StandardMaterial.std_code == mapping.std_code)
        .first()
    )
    if std_mat is None:
        raise HTTPException(status_code=404, detail="Standard material record missing")

    # Fetch all other source codes mapped to the same standard code
    all_mappings = (
        db.query(CodeMapping)
        .options(joinedload(CodeMapping.raw_material).joinedload(RawMaterial.cpse))
        .filter(CodeMapping.std_code == mapping.std_code)
        .all()
    )

    equivalents = [
        ERPEquivalent(
            cpse_name=m.raw_material.cpse.name if m.raw_material and m.raw_material.cpse else "Unknown",
            source_code=m.raw_material.source_code if m.raw_material else "",
            description=m.raw_material.description if m.raw_material else "",
        )
        for m in all_mappings
        if m.raw_material_id != raw.id  # exclude the queried item itself
    ]

    return ERPLookupOut(
        std_code=std_mat.std_code,
        standard_description=std_mat.standard_description,
        category=std_mat.category,
        equivalents=equivalents,
    )

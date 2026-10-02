"""
master.py
=========
GET /api/master         – paginated standard materials with mapped CPSE codes
GET /api/master/export  – CSV download of full unified master
"""

import csv
import io
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from db import get_db
from models import StandardMaterial, CodeMapping, RawMaterial, CPSE
from schemas import StandardMaterialOut, MappedCode, PaginatedResponse

router = APIRouter(prefix="/api", tags=["master"])
logger = logging.getLogger(__name__)


def _build_std_out(std: StandardMaterial, db: Session) -> StandardMaterialOut:
    """Fetch mapped codes for one standard material."""
    mappings = (
        db.query(CodeMapping)
        .options(joinedload(CodeMapping.raw_material).joinedload(RawMaterial.cpse))
        .filter(CodeMapping.std_code == std.std_code)
        .all()
    )
    mapped_codes = [
        MappedCode(
            cpse_name=m.raw_material.cpse.name if m.raw_material and m.raw_material.cpse else "Unknown",
            source_code=m.raw_material.source_code if m.raw_material else "",
            description=m.raw_material.description if m.raw_material else "",
        )
        for m in mappings
        if m.raw_material
    ]
    return StandardMaterialOut(
        id=std.id,
        std_code=std.std_code,
        standard_description=std.standard_description,
        category=std.category,
        subcategory=std.subcategory,
        uom=std.uom,
        specs=std.specs or {},
        approved_by=std.approved_by,
        approved_at=std.approved_at,
        mapped_codes=mapped_codes,
    )


@router.get("/master", response_model=PaginatedResponse)
def list_master(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(StandardMaterial)

    if category:
        q = q.filter(StandardMaterial.category == category)
    if search:
        like = f"%{search.lower()}%"
        q = q.filter(
            func.lower(StandardMaterial.standard_description).like(like)
            | func.lower(StandardMaterial.std_code).like(like)
            | func.lower(StandardMaterial.category).like(like)
        )

    total = q.count()
    items = (
        q.order_by(StandardMaterial.approved_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    results = [_build_std_out(s, db).model_dump() for s in items]

    return PaginatedResponse(
        items=results,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get("/master/export")
def export_master(db: Session = Depends(get_db)):
    """Stream a CSV file of the full unified master."""
    all_std = db.query(StandardMaterial).order_by(StandardMaterial.std_code).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "std_code", "standard_description", "category", "subcategory",
        "uom", "approved_by", "approved_at",
        "cpse_name", "source_code", "source_description",
    ])

    for std in all_std:
        mappings = (
            db.query(CodeMapping)
            .options(joinedload(CodeMapping.raw_material).joinedload(RawMaterial.cpse))
            .filter(CodeMapping.std_code == std.std_code)
            .all()
        )
        if not mappings:
            writer.writerow([
                std.std_code, std.standard_description, std.category or "",
                std.subcategory or "", std.uom or "", std.approved_by or "",
                str(std.approved_at) if std.approved_at else "",
                "", "", "",
            ])
        else:
            for m in mappings:
                rm = m.raw_material
                writer.writerow([
                    std.std_code, std.standard_description, std.category or "",
                    std.subcategory or "", std.uom or "", std.approved_by or "",
                    str(std.approved_at) if std.approved_at else "",
                    rm.cpse.name if rm and rm.cpse else "",
                    rm.source_code if rm else "",
                    rm.description if rm else "",
                ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=unified_master.csv"},
    )

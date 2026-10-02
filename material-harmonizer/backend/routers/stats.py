"""
stats.py
========
GET /api/stats – dashboard numbers
"""

import logging
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from db import get_db
from models import RawMaterial, Cluster, StandardMaterial, CodeMapping, CPSE
from schemas import StatsOut, ClustersByStatus, CategoryDuplicates, CPSEMaterials
from config import BULK_DISCOUNT_ASSUMPTION

router = APIRouter(prefix="/api", tags=["stats"])
logger = logging.getLogger(__name__)


@router.get("/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    # ── Totals ────────────────────────────────────────────────────────────────
    total_materials = db.query(func.count(RawMaterial.id)).scalar() or 0
    total_cpses = db.query(func.count(CPSE.id)).scalar() or 0

    # ── Cluster counts by status ──────────────────────────────────────────────
    status_rows = (
        db.query(Cluster.status, func.count(Cluster.id))
        .group_by(Cluster.status)
        .all()
    )
    status_map = {row[0]: row[1] for row in status_rows}
    pending  = status_map.get("pending", 0)
    approved = status_map.get("approved", 0)
    rejected = status_map.get("rejected", 0)

    duplicate_clusters_found = pending + approved  # pending + approved

    # ── Materials in duplicate clusters ───────────────────────────────────────
    materials_in_duplicates = (
        db.query(func.count(RawMaterial.id))
        .filter(RawMaterial.cluster_id != None)
        .scalar()
    ) or 0

    duplicate_percentage = (
        round(materials_in_duplicates / total_materials * 100, 2)
        if total_materials > 0 else 0.0
    )

    # ── Top categories by duplicate count ────────────────────────────────────
    top_cat_rows = (
        db.query(Cluster.category, func.count(Cluster.id).label("cnt"))
        .filter(Cluster.status.in_(["pending", "approved"]))
        .group_by(Cluster.category)
        .order_by(func.count(Cluster.id).desc())
        .limit(10)
        .all()
    )
    top_categories = [
        CategoryDuplicates(category=r[0] or "Uncategorized", count=r[1])
        for r in top_cat_rows
    ]

    # ── Materials per CPSE ────────────────────────────────────────────────────
    cpse_rows = (
        db.query(CPSE.name, func.count(RawMaterial.id).label("cnt"))
        .join(RawMaterial, RawMaterial.cpse_id == CPSE.id)
        .group_by(CPSE.name)
        .order_by(func.count(RawMaterial.id).desc())
        .all()
    )
    materials_per_cpse = [
        CPSEMaterials(cpse_name=r[0], count=r[1]) for r in cpse_rows
    ]

    # ── Estimated savings (approved clusters only) ────────────────────────────
    # Sum of (annual_qty * unit_price) for all members of approved clusters
    savings_result = db.execute(
        text(
            """
            SELECT COALESCE(SUM(rm.annual_qty * rm.unit_price), 0)
            FROM raw_materials rm
            JOIN clusters c ON c.id = rm.cluster_id
            WHERE c.status = 'approved'
              AND rm.annual_qty IS NOT NULL
              AND rm.unit_price IS NOT NULL
            """
        )
    ).scalar()
    base_spend = float(savings_result or 0)
    estimated_savings = round(base_spend * BULK_DISCOUNT_ASSUMPTION, 2)

    # ── Code reduction ────────────────────────────────────────────────────────
    # Raw codes involved in approved clusters
    code_reduction_raw = (
        db.query(func.count(RawMaterial.id))
        .join(Cluster, Cluster.id == RawMaterial.cluster_id)
        .filter(Cluster.status == "approved")
        .scalar()
    ) or 0

    code_reduction_standard = (
        db.query(func.count(StandardMaterial.id)).scalar()
    ) or 0

    return StatsOut(
        total_materials=total_materials,
        total_cpses=total_cpses,
        duplicate_clusters_found=duplicate_clusters_found,
        materials_in_duplicates=materials_in_duplicates,
        duplicate_percentage=duplicate_percentage,
        clusters_by_status=ClustersByStatus(
            pending=pending, approved=approved, rejected=rejected
        ),
        top_categories_by_duplicates=top_categories,
        materials_per_cpse=materials_per_cpse,
        estimated_savings=estimated_savings,
        code_reduction_raw=code_reduction_raw,
        code_reduction_standard=code_reduction_standard,
    )

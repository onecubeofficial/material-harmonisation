"""
clusters.py
===========
GET  /api/clusters          – paginated cluster list with filters
GET  /api/clusters/{id}     – cluster detail with member explanations
POST /api/clusters/{id}/approve
POST /api/clusters/{id}/reject
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from db import get_db
from models import Cluster, RawMaterial, CPSE, StandardMaterial, CodeMapping, AuditLog
from schemas import (
    ClusterSummary, ClusterDetail, ClusterMember, MemberExplanation,
    ApproveRequest, ActionResponse, PaginatedResponse,
)
from services.matcher import compute_centroid_similarities, build_match_explanation
from services.code_generator import generate_std_code, pick_suggested_description

router = APIRouter(prefix="/api", tags=["clusters"])
logger = logging.getLogger(__name__)


# ── List clusters ──────────────────────────────────────────────────────────────

@router.get("/clusters", response_model=PaginatedResponse)
def list_clusters(
    status: Optional[str] = Query(None, description="pending|approved|rejected"),
    category: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(Cluster)

    if status:
        q = q.filter(Cluster.status == status)
    if category:
        q = q.filter(Cluster.category == category)
    if min_confidence is not None:
        q = q.filter(Cluster.confidence >= min_confidence)
    if search:
        like = f"%{search.lower()}%"
        q = q.filter(
            func.lower(Cluster.suggested_description).like(like)
            | func.lower(Cluster.suggested_std_code).like(like)
            | func.lower(Cluster.category).like(like)
        )

    total = q.count()
    items = (
        q.order_by(Cluster.confidence.desc().nullslast(), Cluster.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    summaries = [
        ClusterSummary(
            id=c.id,
            status=c.status,
            category=c.category,
            subcategory=c.subcategory,
            suggested_std_code=c.suggested_std_code,
            suggested_description=c.suggested_description,
            confidence=float(c.confidence) if c.confidence is not None else None,
            member_count=c.member_count,
            cpse_count=c.cpse_count,
            created_at=c.created_at,
        )
        for c in items
    ]

    return PaginatedResponse(
        items=[s.model_dump() for s in summaries],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


# ── Cluster detail ─────────────────────────────────────────────────────────────

@router.get("/clusters/{cluster_id}", response_model=ClusterDetail)
def get_cluster_detail(cluster_id: int, db: Session = Depends(get_db)):
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    # Load members with their CPSE
    members: List[RawMaterial] = (
        db.query(RawMaterial)
        .options(joinedload(RawMaterial.cpse))
        .filter(RawMaterial.cluster_id == cluster_id)
        .all()
    )

    if not members:
        return ClusterDetail(
            id=cluster.id, status=cluster.status,
            category=cluster.category, subcategory=cluster.subcategory,
            suggested_std_code=cluster.suggested_std_code,
            suggested_description=cluster.suggested_description,
            confidence=float(cluster.confidence) if cluster.confidence else None,
            member_count=0, cpse_count=0, members=[],
        )

    # Compute centroid similarities
    valid_emb = [
        (i, np.array(m.embedding, dtype=np.float32))
        for i, m in enumerate(members)
        if m.embedding is not None
    ]
    sims = [0.0] * len(members)
    if valid_emb:
        emb_mat = np.array([e for _, e in valid_emb])
        centroid = emb_mat.mean(axis=0)
        n = np.linalg.norm(centroid)
        if n > 0:
            centroid /= n
        for orig_idx, emb in valid_emb:
            nn = np.linalg.norm(emb)
            e = emb / nn if nn > 0 else emb
            sims[orig_idx] = float(np.dot(e, centroid))

    # Best centroid member
    best_idx = int(np.argmax(sims))
    best_member = members[best_idx]
    best_emb = (
        np.array(best_member.embedding, dtype=np.float32)
        if best_member.embedding is not None else np.zeros(384, dtype=np.float32)
    )

    result_members = []
    for i, mat in enumerate(members):
        mat_emb = (
            np.array(mat.embedding, dtype=np.float32)
            if mat.embedding is not None else np.zeros(384, dtype=np.float32)
        )
        explanation_dict = build_match_explanation(
            best_emb, mat_emb,
            best_member.cleaned_description or best_member.description,
            mat.cleaned_description or mat.description,
            best_member.specs or {},
            mat.specs or {},
        )
        result_members.append(
            ClusterMember(
                id=mat.id,
                cpse_name=mat.cpse.name if mat.cpse else "Unknown",
                source_code=mat.source_code,
                description=mat.description,
                cleaned_description=mat.cleaned_description,
                uom=mat.uom,
                unit_price=float(mat.unit_price) if mat.unit_price is not None else None,
                annual_qty=float(mat.annual_qty) if mat.annual_qty is not None else None,
                specs=mat.specs or {},
                category=mat.category,
                centroid_similarity=round(sims[i], 4),
                explanation=MemberExplanation(**explanation_dict),
            )
        )

    return ClusterDetail(
        id=cluster.id,
        status=cluster.status,
        category=cluster.category,
        subcategory=cluster.subcategory,
        suggested_std_code=cluster.suggested_std_code,
        suggested_description=cluster.suggested_description,
        confidence=float(cluster.confidence) if cluster.confidence else None,
        member_count=cluster.member_count,
        cpse_count=cluster.cpse_count,
        members=result_members,
    )


# ── Approve ────────────────────────────────────────────────────────────────────

@router.post("/clusters/{cluster_id}/approve", response_model=ActionResponse)
def approve_cluster(
    cluster_id: int,
    body: ApproveRequest,
    db: Session = Depends(get_db),
):
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    if cluster.status == "approved":
        raise HTTPException(status_code=400, detail="Cluster already approved")

    # Remove excluded members from this cluster
    if body.remove_member_ids:
        db.query(RawMaterial).filter(
            RawMaterial.id.in_(body.remove_member_ids),
            RawMaterial.cluster_id == cluster_id,
        ).update({RawMaterial.cluster_id: None}, synchronize_session=False)

    # Fetch remaining members
    remaining = (
        db.query(RawMaterial)
        .options(joinedload(RawMaterial.cpse))
        .filter(RawMaterial.cluster_id == cluster_id)
        .all()
    )
    if not remaining:
        raise HTTPException(status_code=400, detail="No members left in cluster after removal")

    # Generate or use provided std_code
    std_code = generate_std_code(
        cluster.category or "Uncategorized",
        cluster.subcategory or "General",
        db,
    )

    std_description = body.standard_description or cluster.suggested_description or ""

    # Pick best UoM from members
    uom_counts: dict = {}
    for m in remaining:
        if m.uom:
            uom_counts[m.uom] = uom_counts.get(m.uom, 0) + 1
    best_uom = max(uom_counts, key=uom_counts.get) if uom_counts else None

    # Merge specs: keep keys shared by majority
    from collections import Counter
    spec_counter: Counter = Counter()
    spec_values: dict = {}
    for m in remaining:
        for k, v in (m.specs or {}).items():
            spec_counter[k] += 1
            spec_values.setdefault(k, v)
    majority = len(remaining) // 2 + 1
    merged_specs = {k: spec_values[k] for k, cnt in spec_counter.items() if cnt >= majority}

    # Create standard material
    std_mat = StandardMaterial(
        std_code=std_code,
        standard_description=std_description,
        category=cluster.category,
        subcategory=cluster.subcategory,
        uom=best_uom,
        specs=merged_specs,
        cluster_id=cluster_id,
        approved_by=body.approved_by or "expert",
    )
    db.add(std_mat)
    db.flush()

    # Create code mappings
    for mat in remaining:
        existing = db.query(CodeMapping).filter(CodeMapping.raw_material_id == mat.id).first()
        if existing:
            existing.std_code = std_code
        else:
            db.add(CodeMapping(std_code=std_code, raw_material_id=mat.id))

    # Update cluster
    cluster.status = "approved"
    cluster.suggested_std_code = std_code
    cluster.suggested_description = std_description
    cluster.member_count = len(remaining)
    cluster.cpse_count = len({m.cpse_id for m in remaining})
    cluster.reviewed_at = datetime.now(timezone.utc)

    # Audit log
    db.add(AuditLog(
        action="approve",
        entity="cluster",
        entity_id=cluster_id,
        details={
            "std_code": std_code,
            "approved_by": body.approved_by or "expert",
            "members": len(remaining),
            "removed": body.remove_member_ids,
        },
    ))

    db.commit()
    return ActionResponse(ok=True, message=f"Cluster approved as {std_code}", std_code=std_code)


# ── Reject ─────────────────────────────────────────────────────────────────────

@router.post("/clusters/{cluster_id}/reject", response_model=ActionResponse)
def reject_cluster(cluster_id: int, db: Session = Depends(get_db)):
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    cluster.status = "rejected"
    cluster.reviewed_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        action="reject",
        entity="cluster",
        entity_id=cluster_id,
        details={"cluster_id": cluster_id},
    ))
    db.commit()
    return ActionResponse(ok=True, message="Cluster rejected")

"""
audit.py
========
GET /api/audit – paginated audit log (read-only)
"""

import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db import get_db
from models import AuditLog
from schemas import AuditLogOut, PaginatedResponse

router = APIRouter(prefix="/api", tags=["audit"])
logger = logging.getLogger(__name__)


@router.get("/audit", response_model=PaginatedResponse)
def list_audit(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedResponse(
        items=[
            AuditLogOut(
                id=log.id,
                action=log.action,
                entity=log.entity,
                entity_id=log.entity_id,
                details=log.details or {},
                created_at=log.created_at,
            ).model_dump()
            for log in items
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )

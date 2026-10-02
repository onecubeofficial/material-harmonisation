"""
schemas.py – Pydantic v2 request/response models for all API endpoints.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


# ── CPSE ──────────────────────────────────────────────────────────────────────

class CPSEOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


# ── Upload ────────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    cpse_name: str
    inserted: int
    skipped: int
    total_rows: int


# ── Process status ────────────────────────────────────────────────────────────

class ProcessStatus(BaseModel):
    state: str          # idle | running | done | error
    step: str = ""
    progress_percent: int = 0
    message: str = ""


# ── Clusters ──────────────────────────────────────────────────────────────────

class ClusterSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    category: Optional[str]
    subcategory: Optional[str]
    suggested_std_code: Optional[str]
    suggested_description: Optional[str]
    confidence: Optional[float]
    member_count: int
    cpse_count: int
    created_at: Optional[datetime]


class SpecChip(BaseModel):
    key: str
    value: str


class MemberExplanation(BaseModel):
    embedding_sim: float
    fuzzy_sim: float
    matching_specs: List[str]
    differing_specs: List[str]
    reason: str


class ClusterMember(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    cpse_name: str
    source_code: str
    description: str
    cleaned_description: Optional[str]
    uom: Optional[str]
    unit_price: Optional[float]
    annual_qty: Optional[float]
    specs: Dict[str, Any]
    category: Optional[str]
    centroid_similarity: float
    explanation: MemberExplanation


class ClusterDetail(BaseModel):
    id: int
    status: str
    category: Optional[str]
    subcategory: Optional[str]
    suggested_std_code: Optional[str]
    suggested_description: Optional[str]
    confidence: Optional[float]
    member_count: int
    cpse_count: int
    members: List[ClusterMember]


# ── Approve / Reject ──────────────────────────────────────────────────────────

class ApproveRequest(BaseModel):
    standard_description: Optional[str] = None
    remove_member_ids: List[int] = []
    approved_by: Optional[str] = "expert"


class ActionResponse(BaseModel):
    ok: bool
    message: str
    std_code: Optional[str] = None


# ── Master database ───────────────────────────────────────────────────────────

class MappedCode(BaseModel):
    cpse_name: str
    source_code: str
    description: str


class StandardMaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    std_code: str
    standard_description: str
    category: Optional[str]
    subcategory: Optional[str]
    uom: Optional[str]
    specs: Dict[str, Any]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    mapped_codes: List[MappedCode] = []


# ── Stats ─────────────────────────────────────────────────────────────────────

class CategoryDuplicates(BaseModel):
    category: str
    count: int


class CPSEMaterials(BaseModel):
    cpse_name: str
    count: int


class ClustersByStatus(BaseModel):
    pending: int
    approved: int
    rejected: int


class StatsOut(BaseModel):
    total_materials: int
    total_cpses: int
    duplicate_clusters_found: int
    materials_in_duplicates: int
    duplicate_percentage: float
    clusters_by_status: ClustersByStatus
    top_categories_by_duplicates: List[CategoryDuplicates]
    materials_per_cpse: List[CPSEMaterials]
    estimated_savings: float
    code_reduction_raw: int
    code_reduction_standard: int


# ── ERP lookup ────────────────────────────────────────────────────────────────

class ERPEquivalent(BaseModel):
    cpse_name: str
    source_code: str
    description: str


class ERPLookupOut(BaseModel):
    std_code: str
    standard_description: str
    category: Optional[str]
    equivalents: List[ERPEquivalent]


# ── Audit log ─────────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    action: str
    entity: Optional[str]
    entity_id: Optional[int]
    details: Dict[str, Any]
    created_at: Optional[datetime]


# ── Generic pagination wrapper ────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

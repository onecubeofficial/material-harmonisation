"""
models.py – SQLAlchemy ORM models that mirror backend/sql/schema.sql.
The pgvector column uses pgvector.sqlalchemy.Vector(384).
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Numeric, DateTime,
    ForeignKey, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from db import Base


class CPSE(Base):
    __tablename__ = "cpses"

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    materials = relationship("RawMaterial", back_populates="cpse")


class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True)
    # status: pending | approved | rejected
    status = Column(Text, nullable=False, default="pending")
    category = Column(Text)
    subcategory = Column(Text)
    suggested_description = Column(Text)
    suggested_std_code = Column(Text)
    confidence = Column(Numeric(5, 4))
    member_count = Column(Integer, default=0)
    cpse_count = Column(Integer, default=0)
    reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    members = relationship("RawMaterial", back_populates="cluster")
    standard_material = relationship("StandardMaterial", back_populates="cluster", uselist=False)


class RawMaterial(Base):
    __tablename__ = "raw_materials"

    id = Column(Integer, primary_key=True)
    cpse_id = Column(Integer, ForeignKey("cpses.id", ondelete="CASCADE"))
    source_code = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    uom = Column(Text)
    unit_price = Column(Numeric(14, 2))
    annual_qty = Column(Numeric(14, 2))
    cleaned_description = Column(Text)
    specs = Column(JSONB, default=dict)
    category = Column(Text)
    subcategory = Column(Text)
    embedding = Column(Vector(384))
    cluster_id = Column(Integer, ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True)
    # true_group is only for evaluation; never exposed in API
    true_group = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("cpse_id", "source_code", name="uq_cpse_source"),)

    cpse = relationship("CPSE", back_populates="materials")
    cluster = relationship("Cluster", back_populates="members")
    code_mapping = relationship("CodeMapping", back_populates="raw_material", uselist=False)


class StandardMaterial(Base):
    __tablename__ = "standard_materials"

    id = Column(Integer, primary_key=True)
    std_code = Column(Text, unique=True, nullable=False)
    standard_description = Column(Text, nullable=False)
    category = Column(Text)
    subcategory = Column(Text)
    uom = Column(Text)
    specs = Column(JSONB, default=dict)
    cluster_id = Column(Integer, ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(Text, default="expert")
    approved_at = Column(DateTime(timezone=True), server_default=func.now())

    cluster = relationship("Cluster", back_populates="standard_material")
    code_mappings = relationship("CodeMapping", back_populates="standard_material")


class CodeMapping(Base):
    __tablename__ = "code_mappings"

    id = Column(Integer, primary_key=True)
    std_code = Column(Text, ForeignKey("standard_materials.std_code", ondelete="CASCADE"))
    raw_material_id = Column(Integer, ForeignKey("raw_materials.id", ondelete="CASCADE"))

    __table_args__ = (UniqueConstraint("raw_material_id", name="uq_raw_material_mapping"),)

    standard_material = relationship("StandardMaterial", back_populates="code_mappings")
    raw_material = relationship("RawMaterial", back_populates="code_mapping")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    # action: upload | process | approve | reject | edit
    action = Column(Text, nullable=False)
    entity = Column(Text)
    entity_id = Column(Integer)
    details = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

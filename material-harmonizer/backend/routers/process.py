"""
process.py
==========
POST /api/process   – start the ML pipeline in a BackgroundTask
GET  /api/process/status – return current pipeline status for UI polling

Pipeline steps (per spec §7.7):
  1. Select raw materials with no embedding yet
  2. Clean → extract specs → categorize → embed → save
  3. Run matching → create/replace pending clusters
  4. Update global status object
  5. Write audit_log entry
"""

import logging
import traceback
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from db import get_db, SessionLocal
from models import RawMaterial, Cluster, AuditLog, CPSE
from schemas import ProcessStatus
from services.cleaning import clean_description
from services.spec_extractor import extract_specs
from services.categorizer import categorize
from services.embedder import embed_texts, build_embed_text
from services.matcher import build_clusters
from services.code_generator import pick_suggested_description, generate_std_code
from config import MATCH_THRESHOLD, REVIEW_BAND_HIGH

router = APIRouter(prefix="/api", tags=["process"])
logger = logging.getLogger(__name__)

# ── Global in-memory status ────────────────────────────────────────────────────
_status: Dict[str, Any] = {
    "state": "idle",
    "step": "",
    "progress_percent": 0,
    "message": "",
}


def _set_status(state: str, step: str = "", pct: int = 0, msg: str = ""):
    _status.update(state=state, step=step, progress_percent=pct, message=msg)


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/process", status_code=202)
def start_process(background_tasks: BackgroundTasks):
    if _status["state"] == "running":
        return {"detail": "Pipeline already running"}
    background_tasks.add_task(_run_pipeline)
    return {"detail": "Pipeline started"}


@router.get("/process/status", response_model=ProcessStatus)
def get_status():
    return ProcessStatus(**_status)


# ── Pipeline ───────────────────────────────────────────────────────────────────

def _run_pipeline():
    """Full ML pipeline executed in a background thread."""
    _set_status("running", "Initializing", 0, "Starting pipeline...")
    db: Session = SessionLocal()
    try:
        # ── Step 1: fetch unprocessed materials (no embedding) ────────────────
        _set_status("running", "Fetching data", 5, "Loading unprocessed materials...")
        unprocessed: List[RawMaterial] = (
            db.query(RawMaterial)
            .filter(RawMaterial.embedding == None)
            .all()
        )
        logger.info(f"[process] {len(unprocessed)} materials to process")

        if unprocessed:
            # ── Step 2a: Clean + spec extract + categorize ────────────────────
            _set_status("running", "Cleaning", 10, f"Cleaning {len(unprocessed)} descriptions...")
            for mat in unprocessed:
                mat.cleaned_description = clean_description(mat.description)
                mat.specs = extract_specs(mat.cleaned_description)
                cat, sub = categorize(mat.cleaned_description)
                mat.category = cat
                mat.subcategory = sub
            db.flush()

            # ── Step 2b: Embed ────────────────────────────────────────────────
            _set_status("running", "Embedding", 30, f"Embedding {len(unprocessed)} materials...")
            texts = [
                build_embed_text(m.cleaned_description or "", m.specs or {})
                for m in unprocessed
            ]
            embeddings = embed_texts(texts)
            for mat, emb in zip(unprocessed, embeddings):
                mat.embedding = emb.tolist()
            db.flush()
            logger.info("[process] Embeddings computed and saved")

        # ── Step 3: Matching – run over ALL materials by category ─────────────
        _set_status("running", "Matching", 55, "Running AI matching across categories...")

        # Delete all pending clusters (never touch approved/rejected)
        db.query(Cluster).filter(Cluster.status == "pending").delete()
        # Unlink raw materials from deleted pending clusters
        db.execute(
            text("UPDATE raw_materials SET cluster_id = NULL WHERE cluster_id NOT IN "
                 "(SELECT id FROM clusters)")
        )
        db.flush()

        # Get all categories that have at least 2 materials with embeddings
        cat_rows = (
            db.execute(
                text(
                    "SELECT category, COUNT(*) as cnt "
                    "FROM raw_materials "
                    "WHERE embedding IS NOT NULL "
                    "GROUP BY category HAVING COUNT(*) >= 2"
                )
            ).fetchall()
        )
        categories = [r[0] for r in cat_rows if r[0]]

        _set_status("running", "Matching", 60, f"Matching across {len(categories)} categories...")

        total_clusters_created = 0
        for idx, cat in enumerate(categories):
            pct = 60 + int((idx / max(len(categories), 1)) * 35)
            _set_status("running", f"Matching: {cat}", pct, f"Clustering {cat}...")

            materials = (
                db.query(RawMaterial)
                .filter(
                    RawMaterial.category == cat,
                    RawMaterial.embedding != None,
                )
                .all()
            )

            clusters = build_clusters(materials, threshold=MATCH_THRESHOLD)

            for cl_data in clusters:
                member_ids = cl_data["member_ids"]
                confidence = cl_data["confidence"]
                members = [m for m in materials if m.id in set(member_ids)]

                # Determine most common category/subcategory
                sub_counts: Dict[str, int] = defaultdict(int)
                for m in members:
                    sub_counts[m.subcategory or "General"] += 1
                best_sub = max(sub_counts, key=sub_counts.get)

                # Suggested description = member closest to centroid
                suggested_desc = pick_suggested_description(members)

                # CPSE count
                cpse_ids = {m.cpse_id for m in members}

                cluster = Cluster(
                    status="pending",
                    category=cat,
                    subcategory=best_sub,
                    suggested_description=suggested_desc,
                    confidence=confidence,
                    member_count=len(member_ids),
                    cpse_count=len(cpse_ids),
                )
                db.add(cluster)
                db.flush()  # get cluster.id

                # Link members
                for m in members:
                    m.cluster_id = cluster.id

                total_clusters_created += 1

        db.flush()

        # ── Step 4: Update cluster std code suggestions ───────────────────────
        _set_status("running", "Generating codes", 97, "Generating suggested standard codes...")
        pending_clusters = db.query(Cluster).filter(Cluster.status == "pending").all()
        for cl in pending_clusters:
            try:
                cl.suggested_std_code = generate_std_code(
                    cl.category or "Uncategorized",
                    cl.subcategory or "General",
                    db,
                )
            except Exception:
                cl.suggested_std_code = "UNC-GEN-00001"

        # ── Step 5: Audit log ─────────────────────────────────────────────────
        db.add(AuditLog(
            action="process",
            entity="pipeline",
            details={
                "processed_materials": len(unprocessed),
                "categories_matched": len(categories),
                "clusters_created": total_clusters_created,
            },
        ))

        db.commit()
        _set_status("done", "Complete", 100,
                    f"Done. {total_clusters_created} clusters created.")
        logger.info(f"[process] Pipeline complete. {total_clusters_created} clusters.")

    except Exception as exc:
        db.rollback()
        logger.error(f"[process] Pipeline error: {exc}")
        logger.error(traceback.format_exc())
        _set_status("error", "Error", 0, str(exc))
    finally:
        db.close()

"""
evaluate.py
===========
Evaluates predicted clusters against the true_group ground-truth column.

Metric: pairwise precision, recall, F1
  - A "positive pair" is any (i, j) where both items share the same true_group.
  - True Positive  : same true_group AND same predicted cluster
  - False Positive : different true_group but same predicted cluster
  - False Negative : same true_group but different (or no) predicted cluster

Usage:
    cd material-harmonizer/backend
    python scripts/evaluate.py

Optional: tune the threshold over 0.70..0.95 and print F1 per value.
Set TUNE_THRESHOLD=1 env var to enable.
"""

import os
import sys
import logging

# Allow imports from backend root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


# ── DB access ──────────────────────────────────────────────────────────────────

def _fetch_data(db) -> Tuple[List[int], List[Optional[int]], List[Optional[str]]]:
    """
    Returns three aligned lists:
      ids         : RawMaterial.id
      cluster_ids : RawMaterial.cluster_id  (None = no cluster)
      true_groups : RawMaterial.true_group  (None = no ground truth)
    """
    from models import RawMaterial
    rows = (
        db.query(RawMaterial.id, RawMaterial.cluster_id, RawMaterial.true_group)
        .filter(RawMaterial.true_group != None)
        .all()
    )
    ids, cluster_ids, true_groups = zip(*rows) if rows else ([], [], [])
    return list(ids), list(cluster_ids), list(true_groups)


# ── Pairwise metrics ──────────────────────────────────────────────────────────

def pairwise_metrics(
    cluster_ids: List[Optional[int]],
    true_groups: List[Optional[str]],
) -> Tuple[float, float, float]:
    """
    Compute pairwise precision, recall, F1.

    We iterate over all pairs (i < j) and classify them as TP / FP / FN.
    Items with no true_group or no cluster_id are handled gracefully.
    """
    n = len(cluster_ids)
    tp = fp = fn = 0

    # Group indices by cluster and by true_group for efficiency (O(n) grouping)
    cluster_map: Dict[int, List[int]] = defaultdict(list)
    truth_map: Dict[str, List[int]] = defaultdict(list)

    for idx, (cid, tg) in enumerate(zip(cluster_ids, true_groups)):
        if cid is not None:
            cluster_map[cid].append(idx)
        if tg is not None:
            truth_map[tg].append(idx)

    # Count predicted positive pairs (same cluster)
    predicted_pos = sum(len(v) * (len(v) - 1) // 2 for v in cluster_map.values())
    # Count true positive pairs (same true_group)
    true_pos_total = sum(len(v) * (len(v) - 1) // 2 for v in truth_map.values())

    # TP: same cluster AND same true_group
    # Build set of (i,j) pairs in same cluster
    cluster_pair_set: set = set()
    for indices in cluster_map.values():
        for a in range(len(indices)):
            for b in range(a + 1, len(indices)):
                i, j = sorted((indices[a], indices[b]))
                cluster_pair_set.add((i, j))

    # For each truth-group pair, check if they're in the same cluster
    tp = 0
    for indices in truth_map.values():
        for a in range(len(indices)):
            for b in range(a + 1, len(indices)):
                i, j = sorted((indices[a], indices[b]))
                if (i, j) in cluster_pair_set:
                    tp += 1

    fp = predicted_pos - tp
    fn = true_pos_total - tp

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) > 0 else 0.0)

    return round(precision, 4), round(recall, 4), round(f1, 4)


# ── Per-category breakdown ────────────────────────────────────────────────────

def category_breakdown(db) -> None:
    from models import RawMaterial
    rows = (
        db.query(
            RawMaterial.category,
            RawMaterial.id,
            RawMaterial.cluster_id,
            RawMaterial.true_group,
        )
        .filter(RawMaterial.true_group != None)
        .all()
    )

    cat_data: Dict[str, Tuple[List, List]] = defaultdict(lambda: ([], []))
    for cat, _, cid, tg in rows:
        cat_data[cat][0].append(cid)
        cat_data[cat][1].append(tg)

    logger.info("\n── Per-category breakdown ──────────────────────────────")
    logger.info(f"{'Category':<30} {'P':>6} {'R':>6} {'F1':>6} {'Items':>6}")
    logger.info("─" * 58)
    for cat in sorted(cat_data):
        cids, tgs = cat_data[cat]
        p, r, f1 = pairwise_metrics(cids, tgs)
        logger.info(f"{cat:<30} {p:>6.3f} {r:>6.3f} {f1:>6.3f} {len(cids):>6}")


# ── Threshold tuning ──────────────────────────────────────────────────────────

def tune_threshold(db) -> None:
    """
    Re-run in-memory matching at multiple thresholds using the already-computed
    embeddings. Prints F1 for each threshold value.
    Note: this uses the full in-memory matcher, not the DB cluster state.
    """
    import numpy as np
    from models import RawMaterial
    from services.matcher import build_clusters

    logger.info("\n── Threshold Tuning ────────────────────────────────────")
    logger.info(f"{'Threshold':>10} {'P':>8} {'R':>8} {'F1':>8}")
    logger.info("─" * 40)

    # Fetch all materials with embeddings and true_groups
    materials = (
        db.query(RawMaterial)
        .filter(
            RawMaterial.embedding != None,
            RawMaterial.true_group != None,
            RawMaterial.category != None,
        )
        .all()
    )
    if not materials:
        logger.info("No processed materials found. Run the pipeline first.")
        return

    # Group by category
    by_cat: Dict[str, list] = defaultdict(list)
    for m in materials:
        by_cat[m.category].append(m)

    for threshold in [0.70, 0.72, 0.74, 0.76, 0.78, 0.80, 0.82, 0.84,
                       0.86, 0.88, 0.90, 0.92, 0.95]:
        # Build temporary clusters in memory
        id_to_cluster: Dict[int, int] = {}
        cluster_id_counter = 0

        for cat, mats in by_cat.items():
            clusters = build_clusters(mats, threshold=threshold)
            for cl in clusters:
                for mid in cl["member_ids"]:
                    id_to_cluster[mid] = cluster_id_counter
                cluster_id_counter += 1

        # Build aligned lists
        cids = [id_to_cluster.get(m.id) for m in materials]
        tgs  = [m.true_group for m in materials]

        p, r, f1 = pairwise_metrics(cids, tgs)
        logger.info(f"{threshold:>10.2f} {p:>8.4f} {r:>8.4f} {f1:>8.4f}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    from db import SessionLocal
    db = SessionLocal()
    try:
        ids, cluster_ids, true_groups = _fetch_data(db)

        if not ids:
            logger.info("No materials with true_group found.")
            logger.info("Upload the dummy data files and run the pipeline first.")
            return

        total = len(ids)
        clustered = sum(1 for c in cluster_ids if c is not None)
        unique_groups = len(set(tg for tg in true_groups if tg))

        logger.info("=" * 60)
        logger.info("  AI Material Harmonizer – Evaluation Report")
        logger.info("=" * 60)
        logger.info(f"  Total materials evaluated : {total}")
        logger.info(f"  Materials in clusters     : {clustered}")
        logger.info(f"  Unique true groups        : {unique_groups}")

        p, r, f1 = pairwise_metrics(cluster_ids, true_groups)

        logger.info("")
        logger.info("── Overall Pairwise Metrics ────────────────────────────")
        logger.info(f"  Precision : {p:.4f}  ({p*100:.1f}%)")
        logger.info(f"  Recall    : {r:.4f}  ({r*100:.1f}%)")
        logger.info(f"  F1 Score  : {f1:.4f}  ({f1*100:.1f}%)")
        logger.info("")
        logger.info("  Interpretation:")
        logger.info("    Precision = of matched pairs, how many are truly duplicates")
        logger.info("    Recall    = of all true duplicate pairs, how many were found")
        logger.info("    F1        = harmonic mean of precision and recall")

        category_breakdown(db)

        # Optional threshold tuning
        if os.getenv("TUNE_THRESHOLD", "0") == "1":
            tune_threshold(db)

        logger.info("\n" + "=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()

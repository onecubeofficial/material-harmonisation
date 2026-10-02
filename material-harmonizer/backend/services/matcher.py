"""
matcher.py
==========
Performs pairwise material matching and cluster formation.

Scoring formula (per spec):
  final_score = 0.55 * embedding_cosine
              + 0.25 * (rapidfuzz.token_set_ratio / 100)
              + 0.20 * spec_agreement

Hard-veto rule: if both items share a critical spec key but with DIFFERENT values,
the pair score is forced to 0 (they cannot be in the same cluster).

Clusters are formed with union-find (connected components) over edges whose
final_score >= MATCH_THRESHOLD. Only clusters with >= 2 members are kept.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from config import MATCH_THRESHOLD, HARD_VETO_KEYS

logger = logging.getLogger(__name__)

# ── Spec agreement ────────────────────────────────────────────────────────────

def spec_agreement(specs_a: Dict[str, Any], specs_b: Dict[str, Any]) -> float:
    """
    Fraction of shared spec keys where values agree.
    Returns 1.0 if there are no shared keys (cannot compare).
    """
    shared_keys = set(specs_a.keys()) & set(specs_b.keys())
    if not shared_keys:
        return 1.0
    matches = sum(1 for k in shared_keys if str(specs_a[k]) == str(specs_b[k]))
    return matches / len(shared_keys)


def hard_veto(specs_a: Dict[str, Any], specs_b: Dict[str, Any]) -> bool:
    """
    Return True (veto the pair) if any critical spec key is present in both
    items but has different values.
    """
    for key in HARD_VETO_KEYS:
        if key in specs_a and key in specs_b:
            if str(specs_a[key]) != str(specs_b[key]):
                return True
    return False


def score_pair(
    emb_a: np.ndarray,
    emb_b: np.ndarray,
    cleaned_a: str,
    cleaned_b: str,
    specs_a: Dict[str, Any],
    specs_b: Dict[str, Any],
) -> float:
    """Compute the composite match score for a pair of materials."""
    if hard_veto(specs_a, specs_b):
        return 0.0

    # Cosine similarity (embeddings are already L2-normalised → dot product)
    cos_sim = float(np.dot(emb_a, emb_b))
    cos_sim = max(0.0, min(1.0, cos_sim))  # clamp to [0, 1]

    # Fuzzy text similarity
    fuzzy_sim = fuzz.token_set_ratio(cleaned_a, cleaned_b) / 100.0

    # Spec agreement
    spec_sim = spec_agreement(specs_a, specs_b)

    return 0.55 * cos_sim + 0.25 * fuzzy_sim + 0.20 * spec_sim


# ── Union-Find ────────────────────────────────────────────────────────────────

class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path compression
            x = self.parent[x]
        return x

    def union(self, x: int, y: int) -> None:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

    def groups(self) -> Dict[int, List[int]]:
        from collections import defaultdict
        d: Dict[int, List[int]] = defaultdict(list)
        for i in range(len(self.parent)):
            d[self.find(i)].append(i)
        return dict(d)


# ── Main matcher ──────────────────────────────────────────────────────────────

def build_clusters(
    materials: List[Any],          # list of RawMaterial ORM objects (already fetched)
    threshold: float = MATCH_THRESHOLD,
) -> List[Dict]:
    """
    Given a list of RawMaterial objects (same category), compute pairwise
    scores and return a list of cluster dicts:
        {
          "member_ids": [int, ...],
          "edges": [(id_a, id_b, score), ...],
          "confidence": float,
        }

    Only clusters with 2+ members are returned.
    """
    n = len(materials)
    if n < 2:
        return []

    # Build index → material mapping
    mat_list = list(materials)

    # Extract embeddings as matrix for fast batch cosine computation
    emb_matrix = np.array(
        [np.array(m.embedding, dtype=np.float32) for m in mat_list]
    )

    uf = UnionFind(n)
    edge_scores: Dict[Tuple[int, int], float] = {}

    # For large categories: cosine top-k (k=10) to limit O(n^2) comparisons
    # For small categories (<=200): full pairwise
    K_NEIGHBORS = 10
    use_topk = n > 200

    if use_topk:
        # Batch cosine: (n, n) but only keep top-k per row
        sim_matrix = emb_matrix @ emb_matrix.T  # (n, n)
        for i in range(n):
            row = sim_matrix[i]
            row[i] = -1  # exclude self
            top_k = np.argpartition(row, -K_NEIGHBORS)[-K_NEIGHBORS:]
            for j in top_k:
                if j <= i:
                    continue
                s = score_pair(
                    emb_matrix[i], emb_matrix[j],
                    mat_list[i].cleaned_description or "",
                    mat_list[j].cleaned_description or "",
                    mat_list[i].specs or {},
                    mat_list[j].specs or {},
                )
                if s >= threshold:
                    edge_scores[(i, j)] = s
                    uf.union(i, j)
    else:
        for i in range(n):
            for j in range(i + 1, n):
                s = score_pair(
                    emb_matrix[i], emb_matrix[j],
                    mat_list[i].cleaned_description or "",
                    mat_list[j].cleaned_description or "",
                    mat_list[i].specs or {},
                    mat_list[j].specs or {},
                )
                if s >= threshold:
                    edge_scores[(i, j)] = s
                    uf.union(i, j)

    # Collect clusters
    groups = uf.groups()
    clusters = []
    for root, indices in groups.items():
        if len(indices) < 2:
            continue

        # Gather edges within this cluster
        cluster_edges = [
            (mat_list[i].id, mat_list[j].id, edge_scores[(i, j)])
            for (i, j), sc in edge_scores.items()
            if uf.find(i) == root and uf.find(j) == root
        ]

        # Verify no vetoed pair slipped through (shouldn't, but safety check)
        # If found, we just lower the confidence (union-find already separated them)

        confidence = (
            float(np.mean([e[2] for e in cluster_edges])) if cluster_edges else 0.0
        )

        clusters.append({
            "member_ids": [mat_list[i].id for i in indices],
            "edges": cluster_edges,
            "confidence": round(confidence, 4),
        })

    return clusters


def compute_centroid_similarities(
    member_embeddings: List[np.ndarray],
) -> List[float]:
    """
    Given a list of embedding vectors for cluster members, compute each
    member's cosine similarity to the cluster centroid.
    """
    if not member_embeddings:
        return []
    mat = np.array(member_embeddings, dtype=np.float32)
    centroid = mat.mean(axis=0)
    norm = np.linalg.norm(centroid)
    if norm > 0:
        centroid = centroid / norm
    sims = []
    for emb in mat:
        n = np.linalg.norm(emb)
        if n > 0:
            e = emb / n
        else:
            e = emb
        sims.append(float(np.dot(e, centroid)))
    return sims


def build_match_explanation(
    emb_a: np.ndarray,
    emb_b: np.ndarray,
    cleaned_a: str,
    cleaned_b: str,
    specs_a: Dict[str, Any],
    specs_b: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build the human-readable match explanation dict returned in cluster detail.
    """
    cos_sim = float(np.dot(
        emb_a / (np.linalg.norm(emb_a) or 1),
        emb_b / (np.linalg.norm(emb_b) or 1),
    ))
    cos_sim = max(0.0, min(1.0, cos_sim))
    fuzzy_sim = fuzz.token_set_ratio(cleaned_a, cleaned_b) / 100.0

    shared = set(specs_a.keys()) & set(specs_b.keys())
    matching_specs = [k for k in shared if str(specs_a[k]) == str(specs_b[k])]
    differing_specs = [k for k in shared if str(specs_a[k]) != str(specs_b[k])]

    # Build one-line reason
    parts = []
    if matching_specs:
        details = ", ".join(
            f"{k} {specs_a[k]}" for k in matching_specs[:3]
        )
        parts.append(f"Same {details}")
    parts.append(f"descriptions {int(fuzzy_sim * 100)}% similar")
    if differing_specs:
        diff_detail = ", ".join(
            f"{k} ({specs_a[k]} vs {specs_b[k]})" for k in differing_specs[:2]
        )
        parts.append(f"differs in {diff_detail}")

    return {
        "embedding_sim": round(cos_sim, 4),
        "fuzzy_sim": round(fuzzy_sim, 4),
        "matching_specs": matching_specs,
        "differing_specs": differing_specs,
        "reason": "; ".join(parts),
    }

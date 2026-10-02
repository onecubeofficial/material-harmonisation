"""
main.py
=======
FastAPI application entry point.

Start with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Interactive docs available at:
    http://localhost:8000/docs
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import upload, process, clusters, master, stats, erp, audit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)

app = FastAPI(
    title="AI Material Harmonizer",
    description=(
        "AI-driven standardization and harmonization of material codes "
        "across Central Public Sector Enterprises (CPSEs)."
    ),
    version="1.0.0",
)

# ── CORS: allow all origins (no auth, open endpoints per spec) ─────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ───────────────────────────────────────────────────────────
app.include_router(upload.router)
app.include_router(process.router)
app.include_router(clusters.router)
app.include_router(master.router)
app.include_router(stats.router)
app.include_router(erp.router)
app.include_router(audit.router)


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}


# ── Root redirect to docs ──────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

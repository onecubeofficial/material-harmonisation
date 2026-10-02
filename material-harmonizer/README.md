# AI-Driven Standardization & Harmonization of Material Codes Across CPSEs

A full-stack web application that ingests material data from multiple Central Public Sector Enterprises (CPSEs), detects duplicate items across organisations using NLP, groups them into clusters, and lets domain experts approve a single standard code per group — creating a Unified Material Master.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Browser (React 18 + Vite)                   │
│  Dashboard │ Upload │ AI Matching │ Cluster Detail │ Master │ Audit  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP / REST (Axios)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (Python 3.10+)                  │
│                                                                      │
│  POST /api/upload          →  ingest Excel / CSV                     │
│  POST /api/process         →  trigger ML pipeline (BackgroundTask)   │
│  GET  /api/process/status  →  poll pipeline progress                 │
│  GET  /api/clusters        →  paginated cluster list                 │
│  GET  /api/clusters/{id}   →  detail + match explanations            │
│  POST /api/clusters/{id}/approve|reject                              │
│  GET  /api/master          →  unified standard materials             │
│  GET  /api/master/export   →  CSV download                           │
│  GET  /api/stats           →  dashboard metrics                      │
│  GET  /api/erp/lookup      →  mock ERP code lookup                   │
│  GET  /api/audit           →  audit trail                            │
└──────────┬────────────────────────────────┬────────────────────────┘
           │ SQLAlchemy 2.x / psycopg2       │ sentence-transformers
           ▼                                 ▼
┌────────────────────────┐       ┌───────────────────────────────────┐
│  Supabase (Postgres)   │       │  Local CPU  (all-MiniLM-L6-v2)   │
│  + pgvector extension  │       │  384-dim embeddings               │
└────────────────────────┘       └───────────────────────────────────┘

ML Pipeline
───────────
CPSE Data
  → Clean & Normalise (cleaning.py)
  → Extract Specs    (spec_extractor.py)   regex rules
  → Categorise       (categorizer.py)      keyword lookup
  → Embed            (embedder.py)         sentence-transformers
  → Match            (matcher.py)          cosine + fuzzy + spec agreement
  → Cluster          (matcher.py)          union-find connected components
  → Generate Code    (code_generator.py)   FAS-BLT-00012 format
  → Human Review     (ClusterDetail page)
  → Unified Master   (standard_materials table)
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| Node.js | 18+ |
| Supabase account | free tier at supabase.com |

No Docker, no paid APIs, no authentication required.

---

## 1 · Supabase Setup

1. Create a free project at [supabase.com](https://supabase.com).
2. Open **SQL Editor** and paste the contents of `backend/sql/schema.sql`, then click **Run**.  
   This creates all tables, indexes and enables the `pgvector` extension.
3. Go to **Project Settings → Database → Connection string** and copy the  
   **Session pooler** URI (recommended — the direct host may be IPv6-only on the free tier).  
   It looks like:  
   `postgresql://postgres.xxxx:PASSWORD@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres`
4. Keep this URI handy for the next step.

> **Note:** Free-tier projects pause after ~1 week of inactivity. Resume them from the Supabase dashboard. The free storage limit is 500 MB.

---

## 2 · Backend Setup

```bash
# From the project root
cd material-harmonizer/backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Edit `.env` and fill in your Supabase connection string:

```env
DATABASE_URL=postgresql+psycopg2://postgres.xxxx:PASSWORD@HOST:5432/postgres
EMBEDDING_MODEL=all-MiniLM-L6-v2
MATCH_THRESHOLD=0.80
REVIEW_BAND_LOW=0.80
REVIEW_BAND_HIGH=0.92
BULK_DISCOUNT_ASSUMPTION=0.08
```

> **First run note:** The embedding model (`all-MiniLM-L6-v2`, ~90 MB) downloads automatically from Hugging Face on the first call to the pipeline. Subsequent runs use the cached model.

Start the backend:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 3 · Frontend Setup

```bash
# From the project root
cd material-harmonizer/frontend

npm install
npm run dev
```

The UI opens at [http://localhost:5173](http://localhost:5173).

To point the frontend at a different backend URL, create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

---

## 4 · Generate Dummy Data

```bash
cd material-harmonizer/backend
python data/generate_dummy_data.py
```

This creates in `backend/data/`:
- `cpse_a.xlsx` — CPSE A (~700 rows, code format `A-000123`)
- `cpse_b.xlsx` — CPSE B (~700 rows, code format `MC/FAS/4521`)
- `cpse_c.xlsx` — CPSE C (~700 rows, code format `10045678`)
- `ground_truth.csv` — combined file with `true_group` labels for evaluation

Properties:
- ~40% of true groups appear in 2 or 3 CPSEs with descriptions phrased differently
- Hard negatives included (e.g. M10×50 vs M10×60, SS304 vs SS316, bearing 6205 vs 6206)
- Fixed random seed (42) for reproducibility
- `true_group` is never exposed in the UI — only used by `evaluate.py`

---

## 5 · Demo Walkthrough

### Step 1 — Upload data
1. Open the **Upload** page.
2. Enter `CPSE_A` as the CPSE name, select `cpse_a.xlsx`, click **Upload File**.
3. Repeat for `CPSE_B` (`cpse_b.xlsx`) and `CPSE_C` (`cpse_c.xlsx`).

### Step 2 — Run the AI pipeline
1. Go to **Dashboard** and click **Run Processing**.
2. Watch the progress bar poll every 1.5 s. The pipeline:
   - Cleans and normalises all descriptions
   - Extracts spec attributes (thread size, grade, bore, etc.)
   - Categorises items by keyword rules
   - Embeds descriptions with `all-MiniLM-L6-v2`
   - Runs composite matching (55% embedding + 25% fuzzy + 20% spec agreement)
   - Builds clusters with union-find
   - Applies hard-veto rules (different size/grade → never clustered)
3. Status updates to **Done** when complete.

### Step 3 — Review clusters
1. Go to **AI Matching**.
2. Filter by status `pending` to see new clusters.
3. Click a cluster row to open **Cluster Detail**.
4. Review the suggested standard code and description (editable).
5. Expand each member row to see the match explanation (embedding %, fuzzy %, matching/differing specs).
6. Optionally toggle **Remove from cluster** on irrelevant members.
7. Click **Approve** to create a standard code in the Unified Master, or **Reject** to discard.

### Step 4 — View Unified Master
1. Go to **Master Database**.
2. Each row shows the standard code, description, specs, and all mapped CPSE source codes (expandable).
3. Click **Export CSV** to download the full master.

### Step 5 — ERP lookup
Test the mock ERP endpoint directly:

```
GET http://localhost:8000/api/erp/lookup?cpse=CPSE_A&code=A-000001
```

Returns the standard code, standard description, and all equivalent source codes from other CPSEs.

### Step 6 — Run evaluation
```bash
cd material-harmonizer/backend
python scripts/evaluate.py
```

Prints pairwise precision, recall and F1 vs `true_group` ground truth, plus a per-category breakdown.

To also run threshold tuning (tests thresholds 0.70 to 0.95):
```bash
TUNE_THRESHOLD=1 python scripts/evaluate.py
```

---

## 6 · Scoring Formula

```
final_score = 0.55 × embedding_cosine_similarity
            + 0.25 × (token_set_ratio / 100)       # rapidfuzz
            + 0.20 × spec_agreement
```

**Hard-veto rule:** if two items share a critical spec key (thread_size, length_mm, diameter_mm, nominal_bore, grade, pressure_rating, bearing_code, voltage, viscosity_grade) but with *different* values, the pair is forced to score 0 regardless of textual similarity. This prevents M10×50 from matching M10×60.

---

## 7 · Standard Code Format

```
{CAT3}-{SUB3}-{SEQ5}

Examples:
  FAS-BLT-00012   →  Fasteners / Bolts, sequence 12
  BRG-BAL-00003   →  Bearings / Ball Bearings, sequence 3
  VLV-GTV-00007   →  Valves / Gate Valves, sequence 7
  ELC-PWR-00021   →  Electrical Cables / Power Cables, sequence 21
```

CAT3 and SUB3 come from `data/category_rules.json`. SEQ5 is a running counter per prefix stored in the `standard_materials` table.

---

## 8 · Project Structure

```
material-harmonizer/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── main.py                   FastAPI app, CORS, router registration
│   ├── config.py                 env vars and thresholds
│   ├── db.py                     SQLAlchemy engine / session
│   ├── models.py                 ORM models (pgvector embedding column)
│   ├── schemas.py                Pydantic v2 request/response models
│   ├── sql/
│   │   └── schema.sql            Run this in Supabase SQL Editor
│   ├── routers/
│   │   ├── upload.py             POST /api/upload
│   │   ├── process.py            POST /api/process, GET /api/process/status
│   │   ├── clusters.py           GET/POST /api/clusters
│   │   ├── master.py             GET /api/master, /api/master/export
│   │   ├── stats.py              GET /api/stats
│   │   ├── erp.py                GET /api/erp/lookup
│   │   └── audit.py              GET /api/audit
│   ├── services/
│   │   ├── cleaning.py           text normalisation + abbreviation expansion
│   │   ├── spec_extractor.py     regex spec extraction (15+ attribute types)
│   │   ├── categorizer.py        keyword → category/subcategory
│   │   ├── embedder.py           sentence-transformers singleton
│   │   ├── matcher.py            scoring, hard-veto, union-find clustering
│   │   └── code_generator.py     CAT3-SUB3-SEQ5 code generation
│   ├── data/
│   │   ├── abbreviations.json    ~150 abbreviation expansions
│   │   ├── category_rules.json   15 categories, 60+ subcategories, 200+ keywords
│   │   └── generate_dummy_data.py
│   └── scripts/
│       └── evaluate.py           pairwise P/R/F1 + threshold tuning
└── frontend/
    ├── package.json              React 18, Vite, Tailwind, TanStack Table, Recharts
    ├── vite.config.js
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx               React Router with 6 routes
        ├── api.js                Axios instance (VITE_API_URL)
        ├── index.css             Tailwind + utility component classes
        ├── components/
        │   ├── Layout.jsx        Sidebar + header shell
        │   ├── StatCard.jsx      dashboard metric tile
        │   ├── ScoreBadge.jsx    colour-coded confidence badge
        │   ├── SpecChips.jsx     spec attribute chips
        │   └── DataTable.jsx     TanStack Table v8 with server-side pagination
        └── pages/
            ├── Dashboard.jsx     stat cards + 3 Recharts charts + pipeline control
            ├── Upload.jsx        drag-and-drop + file preview + upload
            ├── Matching.jsx      filterable cluster list
            ├── ClusterDetail.jsx member review + approve/reject + explanations
            ├── MasterDatabase.jsx expandable standard material rows + CSV export
            └── AuditLog.jsx      read-only paginated audit trail
```

---

## 9 · Assumptions & Known Limitations

- **No authentication.** All endpoints are open. This is intentional per spec (hackathon/internal demo only).
- **CPU-only embeddings.** The `all-MiniLM-L6-v2` model runs on CPU. Processing 2 100 items takes roughly 30–90 seconds depending on hardware.
- **Supabase free tier.** Projects pause after ~1 week of inactivity. The pgvector HNSW index requires Supabase's hosted Postgres (not SQLite or plain local Postgres without the extension).
- **Matching is run on all pending data.** Re-running the pipeline deletes all `pending` clusters and recreates them. `approved` and `rejected` clusters are never touched.
- **Category as blocking key.** Two materials from different categories will never be matched, even if their descriptions are identical. This is a deliberate design choice to reduce false positives and computation time.
- **Hard-veto keys** cover the most safety-critical spec dimensions. Other differing specs contribute to a lower score but do not veto outright.
- **Estimated savings** uses a flat 8% bulk-discount assumption applied to the total annual spend of approved cluster members. Clearly labelled "estimate" in the UI.
- **`true_group` column** in the uploaded files is purely for evaluation via `evaluate.py`. It is stored in the database but never returned by any API endpoint.
- **File preview in Upload page** uses the `xlsx` npm package. Very large files (>10 MB) may be slow to parse in the browser.
- **No WebSocket.** Pipeline progress is polled every 1.5 seconds via `/api/process/status`.

---

## 10 · Tech Stack Summary

| Layer | Technology | Reason |
|-------|-----------|--------|
| Frontend | React 18 + Vite | Fast dev experience, modern ecosystem |
| Styling | Tailwind CSS | Utility-first, no custom CSS needed |
| Tables | TanStack Table v8 | Headless, flexible, server-side pagination |
| Charts | Recharts | Simple React-native charting |
| HTTP client | Axios | Consistent error handling |
| Icons | lucide-react | Clean, consistent icon set |
| Backend | FastAPI + Uvicorn | Fast, async, auto-docs, type-safe |
| ORM | SQLAlchemy 2.x | Mature, supports pgvector |
| Database | Supabase Postgres + pgvector | Free tier, hosted, vector search |
| Embeddings | sentence-transformers | Free, runs locally on CPU |
| Fuzzy match | rapidfuzz | Fast token_set_ratio |
| ML utils | scikit-learn, numpy | Cosine similarity, array ops |
| Spec extract | Python re | No LLM needed, fully rule-based |

# Project Spec: AI-Driven Standardization & Harmonization of Material Codes Across CPSEs

> Instruction to the AI coding assistant (Amazon Q): Build this entire project exactly as described below. Create all files, folders, code, SQL, sample data and README. Follow the "Hard Constraints" strictly. Where a choice is not specified, pick the simplest free option. Do not ask clarifying questions; make reasonable assumptions and note them in the README.

---

## 1. Problem Summary

Different Central Public Sector Enterprises (CPSEs) code the same material differently (different code formats, spellings, abbreviations, units). This causes duplicate stock, poor procurement visibility and lost bulk-purchase savings.

We are building a web application that:

1. Ingests material data from multiple CPSEs (Excel/CSV upload).
2. Cleans and normalizes descriptions and extracts specifications.
3. Uses NLP (embeddings + fuzzy matching + spec comparison) to detect duplicate or similar materials across CPSEs.
4. Groups matches into clusters and suggests one standard code per cluster.
5. Lets an expert review, edit, approve or reject each cluster (human-in-the-loop).
6. Stores approved results in a Unified Material Master and exposes it through APIs (including a mock ERP lookup endpoint).
7. Shows a dashboard with duplicates found, approval status and estimated savings.

Pipeline: `CPSE Data -> Clean & Preprocess -> AI Analysis (NLP) -> Smart Matching -> Standard Code Generation -> Validation & Dashboard -> Unified Material Master`

---

## 2. Hard Constraints

- **Everything must be free.** Only free and open-source libraries and the Supabase free tier. No paid APIs (no OpenAI, no Anthropic API, no paid cloud services).
- **No authentication, no login, no roles, no security hardening.** Open endpoints. Do not add JWT, OAuth or API keys. CORS may allow all origins.
- **No deployment work.** No Docker, CI/CD, cloud config, Nginx or hosting setup. Local run only (`uvicorn` and `npm run dev`).
- **No Celery, no Redis.** Use FastAPI `BackgroundTasks` for long jobs.
- **Embeddings must run locally** using `sentence-transformers` (CPU only).
- **Database: Supabase (hosted Postgres) with the `pgvector` extension.**
- Keep the code simple, readable and commented. A hackathon team must be able to understand and demo it.

---

## 3. Tech Stack (all free)

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite, Tailwind CSS, React Router |
| Frontend libs | TanStack Table (data tables), Recharts (charts), Axios (HTTP), lucide-react (icons) |
| Backend | Python 3.10+, FastAPI, Uvicorn |
| Data handling | pandas, openpyxl |
| NLP / ML | sentence-transformers (model: `all-MiniLM-L6-v2`, 384 dimensions), rapidfuzz, scikit-learn, numpy |
| Spec extraction | Python `re` (regex) with a rule dictionary (no paid LLM) |
| Database | Supabase Postgres + `pgvector` |
| DB access | SQLAlchemy 2.x + `psycopg2-binary` + `pgvector` Python package, using the Supabase connection string |
| Config | `python-dotenv` (`.env` file) |

---

## 4. Project Structure

```
material-harmonizer/
├── README.md
├── PROJECT_SPEC.md
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── main.py                  # FastAPI app, CORS, router registration
│   ├── config.py                # loads env vars, thresholds
│   ├── db.py                    # SQLAlchemy engine/session
│   ├── models.py                # SQLAlchemy models
│   ├── schemas.py               # Pydantic schemas
│   ├── sql/
│   │   └── schema.sql           # full Supabase SQL (run in SQL editor)
│   ├── routers/
│   │   ├── upload.py
│   │   ├── process.py
│   │   ├── clusters.py
│   │   ├── master.py
│   │   ├── stats.py
│   │   └── erp.py               # mock ERP lookup
│   ├── services/
│   │   ├── cleaning.py          # normalization + abbreviation expansion
│   │   ├── spec_extractor.py    # regex spec extraction
│   │   ├── embedder.py          # sentence-transformers wrapper (singleton)
│   │   ├── matcher.py           # scoring + clustering
│   │   ├── categorizer.py       # keyword-based category/subcategory
│   │   └── code_generator.py    # standard code generation
│   ├── data/
│   │   ├── abbreviations.json
│   │   ├── category_rules.json
│   │   └── generate_dummy_data.py
│   └── scripts/
│       └── evaluate.py          # precision/recall vs ground truth
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── api.js               # axios instance (base URL http://localhost:8000)
        ├── components/          # Layout, Sidebar, StatCard, ScoreBadge, SpecChips, DataTable
        └── pages/
            ├── Dashboard.jsx
            ├── Upload.jsx
            ├── Matching.jsx          # cluster list
            ├── ClusterDetail.jsx     # review/approve/reject
            ├── MasterDatabase.jsx
            └── AuditLog.jsx
```

---

## 5. Supabase Setup (document in README)

1. Create a free project at supabase.com.
2. Open **SQL Editor** and run `backend/sql/schema.sql`.
3. Go to **Project Settings -> Database -> Connection string** and copy the **Session pooler** URI (use this if the direct connection fails, because the direct host can be IPv6-only on the free tier).
4. Put it in `backend/.env` as `DATABASE_URL=postgresql+psycopg2://...`.
5. Note in the README: free-tier projects pause after about 1 week of inactivity and can be resumed from the dashboard; the free database limit is 500 MB.

`.env.example`:

```
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/postgres
EMBEDDING_MODEL=all-MiniLM-L6-v2
MATCH_THRESHOLD=0.80
REVIEW_BAND_LOW=0.80
REVIEW_BAND_HIGH=0.92
BULK_DISCOUNT_ASSUMPTION=0.08
```

---

## 6. Database Schema (`backend/sql/schema.sql`)

```sql
create extension if not exists vector;

create table if not exists cpses (
  id serial primary key,
  name text unique not null,
  created_at timestamptz default now()
);

create table if not exists clusters (
  id serial primary key,
  status text not null default 'pending',        -- pending | approved | rejected
  category text,
  subcategory text,
  suggested_description text,
  suggested_std_code text,
  confidence numeric(5,4),                        -- average pairwise score in cluster
  member_count int default 0,
  cpse_count int default 0,
  reviewed_at timestamptz,
  created_at timestamptz default now()
);

create table if not exists raw_materials (
  id serial primary key,
  cpse_id int references cpses(id) on delete cascade,
  source_code text not null,
  description text not null,
  uom text,
  unit_price numeric(14,2),
  annual_qty numeric(14,2),
  cleaned_description text,
  specs jsonb default '{}'::jsonb,                -- extracted spec attributes
  category text,
  subcategory text,
  embedding vector(384),
  cluster_id int references clusters(id) on delete set null,
  true_group text,                                -- ground-truth label (dummy data only, never shown in UI)
  created_at timestamptz default now(),
  unique (cpse_id, source_code)
);

create table if not exists standard_materials (
  id serial primary key,
  std_code text unique not null,
  standard_description text not null,
  category text,
  subcategory text,
  uom text,
  specs jsonb default '{}'::jsonb,
  cluster_id int references clusters(id) on delete set null,
  approved_by text default 'expert',
  approved_at timestamptz default now()
);

create table if not exists code_mappings (
  id serial primary key,
  std_code text references standard_materials(std_code) on delete cascade,
  raw_material_id int references raw_materials(id) on delete cascade,
  unique (raw_material_id)
);

create table if not exists audit_log (
  id serial primary key,
  action text not null,                           -- upload | process | approve | reject | edit
  entity text,
  entity_id int,
  details jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create index if not exists idx_raw_cluster on raw_materials(cluster_id);
create index if not exists idx_raw_category on raw_materials(category);
create index if not exists idx_raw_embedding on raw_materials using hnsw (embedding vector_cosine_ops);
```

Define matching SQLAlchemy models in `models.py` (use `pgvector.sqlalchemy.Vector(384)` for the embedding column).

---

## 7. Backend Services (core logic)

### 7.1 `cleaning.py`
Input: raw description string. Output: `cleaned_description`.

Steps:
1. Lowercase, trim, collapse whitespace.
2. Normalize separators and punctuation (`,` `;` `-` `/` to spaces, but keep `x` between numbers, e.g. `10x50`).
3. Normalize units: `millimetre/millimeter/mm.` -> `mm`, `inch/in/"` -> `inch`, `kilogram/kgs` -> `kg`, `volt/volts/v` -> `v`, etc.
4. Expand abbreviations using `data/abbreviations.json`, for example:
   `hex -> hexagon`, `hd -> head`, `ss -> stainless steel`, `ms -> mild steel`, `cs -> carbon steel`, `gi -> galvanized iron`, `dia -> diameter`, `nb -> nominal bore`, `galv -> galvanized`, `zn -> zinc`, `brg -> bearing`, `gr -> grade`, `cl -> class`, `lub -> lubricant`, `pvc`, `hdpe` kept as-is.
5. Remove stopwords that carry no meaning (`for`, `of`, `the`, `and`, `with`) but keep words like `with` only if the abbreviation file marks them as meaningful.
6. Sort nothing; keep word order.

### 7.2 `spec_extractor.py`
Extract a dict of normalized attributes using regex. Support at least:

- `thread_size` (e.g. `M10`, `M-10`, `10mm` on fasteners -> `M10`)
- `length_mm` (from `10x50`, `M10x50`, `50 mm long`)
- `dimensions` (e.g. `100x50x5`)
- `diameter_mm` and `diameter_inch`
- `nominal_bore` (e.g. `DN50`, `2 inch NB`)
- `grade` (e.g. `8.8`, `10.9`, `A2-70`, `EN8`, `304`, `316`)
- `material` (stainless steel, mild steel, carbon steel, brass, cast iron, copper, PVC, rubber, etc.)
- `finish` (zinc plated, galvanized, black oxide, etc.)
- `pressure_rating` (e.g. `PN16`, `150#`, `10 bar`)
- `voltage`, `current`, `power` (e.g. `415v`, `32a`, `5 hp`, `3.7 kw`)
- `bearing_code` (e.g. `6205`, `6205-2RS`, `NU310`)
- `viscosity_grade` (e.g. `ISO VG 68`, `SAE 40`)
- `cable_cores_area` (e.g. `3 core 2.5 sqmm`)

Return only the attributes found. Make the extractor easy to extend (list of `(name, compiled_regex, normalizer)` tuples).

### 7.3 `categorizer.py`
Use `data/category_rules.json` (keyword -> category/subcategory). Provide at least 12 categories such as:
Fasteners (bolt, nut, washer, screw), Bearings, Valves, Pipes & Fittings, Electrical Cables, Electrical Switchgear, Pumps & Spares, Gaskets & Seals, Lubricants & Oils, Safety Items, Hand Tools, Abrasives & Cutting, Paints & Coatings, Instrumentation, Packing & Stationery. Fall back to `Uncategorized`.

### 7.4 `embedder.py`
- Load `SentenceTransformer(EMBEDDING_MODEL)` once (singleton).
- Function `embed_texts(list[str]) -> np.ndarray` with batch size 64 and `normalize_embeddings=True`.
- Input text for embedding = `cleaned_description` plus a compact string of key specs.

### 7.5 `matcher.py`
For every pair of materials in the **same category** (use category as a blocking key to limit comparisons; within a category use pgvector or in-memory numpy cosine top-k, k=10):

```
final_score = 0.55 * embedding_cosine
            + 0.25 * (rapidfuzz.token_set_ratio(cleaned_a, cleaned_b) / 100)
            + 0.20 * spec_agreement(specs_a, specs_b)
```

- `spec_agreement` = fraction of shared spec keys with equal values (return 1.0 if no shared keys).
- **Hard veto rule:** if both items have the same spec key among `thread_size, length_mm, diameter_mm, nominal_bore, grade, pressure_rating, bearing_code, voltage, viscosity_grade` and the values differ, then the pair is NOT a match (set score to 0). Example: `M10x50` must never match `M10x60`.
- Pairs with `final_score >= MATCH_THRESHOLD` become edges.
- Build clusters with **union-find** (connected components) over edges. Before finalizing, verify no cluster contains a vetoed pair; if it does, split it by removing the lowest-scoring edges.
- Cluster `confidence` = mean score of its edges.
- Only keep clusters with 2 or more members.
- Flag clusters: confidence >= `REVIEW_BAND_HIGH` = "High confidence", between low and high = "Needs review".

### 7.6 `code_generator.py`
Standard code format: `{CAT3}-{SUB3}-{SEQ5}`, for example `FAS-BLT-00012`.
- `CAT3` and `SUB3` = first 3 letters (uppercase) from category and subcategory (use a mapping in `category_rules.json` if provided).
- `SEQ5` = zero-padded running number per `(CAT3, SUB3)`, taken from the max existing `standard_materials.std_code` in the database.
- `suggested_description` = the cleaned description of the member closest to the cluster centroid (highest average similarity), title-cased, with units normalized.

### 7.7 Processing job
`POST /api/process` runs in a `BackgroundTask` and performs:
1. Select raw materials with no embedding yet.
2. Clean -> extract specs -> categorize -> embed -> save.
3. Run matching over all materials -> create/replace `pending` clusters (never touch `approved` clusters).
4. Update a global in-memory status object: `{state: idle|running|done|error, step, progress_percent, message}`.
5. Write an `audit_log` entry.

---

## 8. REST API (FastAPI, base path `/api`)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/upload` | multipart: `cpse_name` (text) + `file` (.xlsx or .csv). Required columns: `material_code`, `description`; optional: `uom`, `unit_price`, `annual_qty`, `true_group`. Upsert CPSE and insert rows. Return counts. |
| POST | `/api/process` | start the pipeline in the background |
| GET | `/api/process/status` | return current pipeline status for UI polling |
| GET | `/api/clusters` | query params: `status`, `category`, `min_confidence`, `search`, `page`, `page_size`. Return cluster summaries. |
| GET | `/api/clusters/{id}` | members (with CPSE, source code, description, specs, uom), similarity score of each to the centroid, suggested std code and description, and an **explanation** (see below) |
| POST | `/api/clusters/{id}/approve` | body: `{standard_description?, remove_member_ids?: [], approved_by?}`. Creates `standard_materials`, `code_mappings`, sets status `approved`, writes audit log. |
| POST | `/api/clusters/{id}/reject` | sets status `rejected`, writes audit log |
| GET | `/api/master` | query params: `search`, `category`, `page`, `page_size`. Returns standard materials with mapped CPSE codes. |
| GET | `/api/master/export` | CSV download of the unified master with all mapped CPSE codes |
| GET | `/api/stats` | dashboard numbers (see section 9) |
| GET | `/api/erp/lookup` | query: `cpse` and `code`. Returns the standard code, description and all equivalent codes in other CPSEs. This is the mock ERP integration endpoint. |
| GET | `/api/audit` | paginated audit log |
| GET | `/api/health` | health check |

**Explanation for each match (important for demo):** in cluster detail, for each member compared to the suggested standard item, return: embedding similarity, fuzzy similarity, list of matching specs, list of differing specs (if any), and a one-line human-readable reason, e.g. `"Same thread size M10, length 50mm, grade 8.8; descriptions 91% similar"`.

---

## 9. Dashboard Stats (`/api/stats`)

Return:
- `total_materials`, `total_cpses`
- `duplicate_clusters_found` (pending + approved)
- `materials_in_duplicates`
- `duplicate_percentage`
- `clusters_by_status` (pending, approved, rejected)
- `top_categories_by_duplicates` (list of `{category, count}`)
- `materials_per_cpse`
- `estimated_savings` = for approved clusters: sum of `(sum of annual_qty x unit_price over members) x BULK_DISCOUNT_ASSUMPTION`. Label it clearly as an **estimate** in the UI.
- `code_reduction` = raw codes before vs standard codes after (approved only)

---

## 10. Frontend Requirements

Use a clean, modern look with Tailwind: left sidebar, top header, card-based layout, blue primary color (government/enterprise feel). Make it responsive.

### Pages

1. **Dashboard**
   - Stat cards: total materials, CPSEs, duplicate clusters, duplicate %, estimated savings (INR formatted, with "estimate" label).
   - Charts (Recharts): bar chart of duplicates by category, pie/donut of cluster status, bar chart of materials per CPSE.
   - A "Run Processing" button with a progress bar polling `/api/process/status` every 1.5 seconds.

2. **Upload**
   - Drag-and-drop zone, CPSE name input, accepts `.xlsx` and `.csv`.
   - Preview of the first 10 rows before submit.
   - Success message with inserted/skipped counts.
   - A "Download sample template" link (served by the backend or generated on the client).

3. **Matching (cluster list)**
   - Table with: cluster id, category, suggested std code, member count, CPSE count, confidence badge (green >= 0.92, amber 0.80-0.92), status.
   - Filters: status, category, confidence range, search. Pagination.
   - Click a row to open Cluster Detail.

4. **Cluster Detail**
   - Header with suggested standard code and editable description.
   - Table of member items: CPSE, source code, description, UoM, spec chips, similarity bar, match explanation.
   - Per-row "Remove from cluster" toggle.
   - Buttons: **Approve**, **Reject**. After action, go back to the list and show a toast.

5. **Master Database**
   - Searchable, filterable table of standard materials with the mapped CPSE codes shown as expandable rows.
   - "Export CSV" button.

6. **Audit Log**
   - Simple read-only table of actions with timestamps.

### Also
- Global loading and error states; use toast notifications.
- Axios base URL from `VITE_API_URL` (default `http://localhost:8000`).

---

## 11. Dummy Data Generator (`backend/data/generate_dummy_data.py`)

Generate three Excel files (`cpse_a.xlsx`, `cpse_b.xlsx`, `cpse_c.xlsx`) and also a combined `ground_truth.csv`, with these properties:

- About **700 items per CPSE (about 2,100 total)** across at least 12 categories.
- Columns: `material_code`, `description`, `uom`, `unit_price`, `annual_qty`, `true_group`.
- Each CPSE uses a **different code format** (e.g. `A-000123`, `MC/FAS/4521`, `10045678`).
- About **40% of true groups appear in 2 or 3 CPSEs** with the **same item described differently**. Use different abbreviations, word order, units, casing and spelling. Example for one true group:
  - CPSE A: `BOLT HEX M10X50 GR 8.8 ZINC PLATED`
  - CPSE B: `Hexagon Head Bolt, 10 mm dia x 50 mm long, Grade 8.8, Zn plated`
  - CPSE C: `HEX HD BOLT M-10 X 50MM CL.8.8 GALV`
- Include **hard negatives** (items that look similar but are different, e.g. M10x50 vs M10x60, SS304 vs SS316, 6205 vs 6206 bearing, 2 inch vs 3 inch valve). These must have different `true_group` values.
- Include some **within-CPSE duplicates** as well.
- Use a fixed random seed for reproducibility.
- Base item templates on realistic industrial categories (fasteners, bearings, valves, pipes, cables, gaskets, lubricants, safety items, pumps, tools, paints, switchgear).

The `true_group` column is for evaluation only. The UI must never display it.

---

## 12. Evaluation Script (`backend/scripts/evaluate.py`)

After processing, compare predicted clusters with `true_group`, computing pairwise **precision, recall and F1**, and print a small report. This gives the team a measurable accuracy number for the hackathon presentation. Include a helper to tune `MATCH_THRESHOLD` by trying values 0.70 to 0.95 and printing the F1 for each.

---

## 13. README Requirements

Include:
1. Project overview and architecture diagram (ASCII or Mermaid).
2. Prerequisites: Python 3.10+, Node 18+, a free Supabase account.
3. Step-by-step setup: Supabase, backend (venv, `pip install -r requirements.txt`, `.env`), frontend (`npm install`, `npm run dev`).
4. Demo walkthrough: generate dummy data -> upload three files -> click Run Processing -> review clusters -> approve -> view Master Database -> test the ERP lookup endpoint.
5. Note that the first run downloads the embedding model (about 90 MB) once.
6. Assumptions and known limitations.

---

## 14. Acceptance Criteria

The project is complete when:

1. `schema.sql` runs cleanly on a fresh Supabase project.
2. Backend starts with `uvicorn main:app --reload` and `/docs` lists all endpoints.
3. Frontend starts with `npm run dev` and all six pages load and work against the backend.
4. Uploading the three dummy files and running processing creates clusters with no crashes.
5. A cluster can be reviewed, edited, approved and rejected, and approved clusters appear in the Master Database with all mapped CPSE codes.
6. The ERP lookup returns the correct standard code for a known CPSE code.
7. Hard-negative pairs (different size, grade or model) are not clustered together.
8. `evaluate.py` runs and prints precision, recall and F1.
9. No authentication, no Docker/deployment files, and no paid service or API key anywhere in the project.

---

## 15. Build Order for the Assistant

1. Scaffold folders and `requirements.txt` / `package.json`.
2. Write `schema.sql`, `models.py`, `db.py`, `config.py`.
3. Write the data files (`abbreviations.json`, `category_rules.json`) and `generate_dummy_data.py`; generate sample data.
4. Implement services: cleaning -> spec extractor -> categorizer -> embedder -> matcher -> code generator.
5. Implement routers and `main.py`.
6. Write `evaluate.py` and verify metrics on the dummy data.
7. Build the frontend pages and components.
8. Write the README.

-- schema.sql – Run this in Supabase SQL Editor before starting the backend.
-- It is idempotent (IF NOT EXISTS) so it can be re-run safely.

create extension if not exists vector;

-- ── CPSEs ────────────────────────────────────────────────────────────────────
create table if not exists cpses (
  id         serial primary key,
  name       text unique not null,
  created_at timestamptz default now()
);

-- ── Clusters ─────────────────────────────────────────────────────────────────
create table if not exists clusters (
  id                   serial primary key,
  status               text not null default 'pending',   -- pending | approved | rejected
  category             text,
  subcategory          text,
  suggested_description text,
  suggested_std_code   text,
  confidence           numeric(5,4),                       -- mean pairwise score
  member_count         int default 0,
  cpse_count           int default 0,
  reviewed_at          timestamptz,
  created_at           timestamptz default now()
);

-- ── Raw Materials ─────────────────────────────────────────────────────────────
create table if not exists raw_materials (
  id                  serial primary key,
  cpse_id             int references cpses(id) on delete cascade,
  source_code         text not null,
  description         text not null,
  uom                 text,
  unit_price          numeric(14,2),
  annual_qty          numeric(14,2),
  cleaned_description text,
  specs               jsonb default '{}'::jsonb,
  category            text,
  subcategory         text,
  embedding           vector(384),
  cluster_id          int references clusters(id) on delete set null,
  true_group          text,                                -- evaluation only, never shown in UI
  created_at          timestamptz default now(),
  unique (cpse_id, source_code)
);

-- ── Standard Materials ────────────────────────────────────────────────────────
create table if not exists standard_materials (
  id                   serial primary key,
  std_code             text unique not null,
  standard_description text not null,
  category             text,
  subcategory          text,
  uom                  text,
  specs                jsonb default '{}'::jsonb,
  cluster_id           int references clusters(id) on delete set null,
  approved_by          text default 'expert',
  approved_at          timestamptz default now()
);

-- ── Code Mappings ─────────────────────────────────────────────────────────────
create table if not exists code_mappings (
  id              serial primary key,
  std_code        text references standard_materials(std_code) on delete cascade,
  raw_material_id int references raw_materials(id) on delete cascade,
  unique (raw_material_id)
);

-- ── Audit Log ─────────────────────────────────────────────────────────────────
create table if not exists audit_log (
  id         serial primary key,
  action     text not null,                               -- upload | process | approve | reject | edit
  entity     text,
  entity_id  int,
  details    jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

-- ── Indexes ───────────────────────────────────────────────────────────────────
create index if not exists idx_raw_cluster   on raw_materials(cluster_id);
create index if not exists idx_raw_category  on raw_materials(category);
create index if not exists idx_raw_embedding on raw_materials using hnsw (embedding vector_cosine_ops);

# Test Data – Material Harmonizer

All files here are used to manually test the `/api/upload` endpoint and the downstream
processing pipeline.  Re-generate them any time by running:

```bash
cd material-harmonizer/backend
.venv/bin/python3 test/generate_test_data.py
```

---

## Files

### Happy-path CPSE files

| File | CPSE name to use | Rows | Code format | Purpose |
|---|---|---|---|---|
| `cpse_a.xlsx` | `NTPC` | 30 | `A-000001` | NTPC-style codes |
| `cpse_b.xlsx` | `BHEL` | 30 | `MC/FAS/1001` | BHEL-style codes |
| `cpse_c.xlsx` | `IOCL` | 30 | `10000001` | IOCL-style numeric codes |

**What's inside each file:**

- **10 cross-CPSE duplicates** — the same physical item appears in all three files
  with completely different wording (e.g. `BOLT HEX M12X50 GR 8.8 ZINC PLATED` vs
  `Hexagon Head Bolt, 12 mm dia x 50 mm long, Grade 8.8, Zn plated` vs
  `HEX HD BOLT M12-X50MM CL.8.8 GALV`). Their `true_group` starts with `X_`.
  After processing these should cluster together.

- **2–3 within-CPSE duplicates** — same item, different description wording, within
  one CPSE. Exercises the intra-CPSE deduplication path.

- **~18 CPSE-unique items** — items that appear in only one CPSE (no expected cluster
  partner). Useful for checking false-positive rate.

**Columns:** `material_code`, `description`, `uom`, `unit_price`, `annual_qty`, `true_group`

> `true_group` is for evaluation only and is never displayed in the UI.

---

### Upload them in order

```bash
# Start the backend first
cd material-harmonizer/backend
.venv/bin/uvicorn main:app --reload --port 8000

# Then upload (in a second terminal)
curl -X POST http://localhost:8000/api/upload \
  -F "cpse_name=NTPC" \
  -F "file=@backend/test/cpse_a.xlsx"

curl -X POST http://localhost:8000/api/upload \
  -F "cpse_name=BHEL" \
  -F "file=@backend/test/cpse_b.xlsx"

curl -X POST http://localhost:8000/api/upload \
  -F "cpse_name=IOCL" \
  -F "file=@backend/test/cpse_c.xlsx"
```

Expected response for each:
```json
{ "cpse_name": "NTPC", "inserted": 30, "skipped": 0, "total_rows": 30 }
```

---

### Edge-case files

| File | Upload as cpse_name | Expected result |
|---|---|---|
| `single_row.csv` | `TEST_SINGLE` | `inserted=1, skipped=0` |
| `empty_body.csv` | `TEST_EMPTY` | `inserted=0, skipped=0, total_rows=0` |
| `missing_columns.csv` | `TEST_BAD` | **HTTP 422** – missing `description` column |
| `duplicate_codes.xlsx` | `TEST_DUPS` | `inserted=3, skipped=2` (rows with repeated `material_code` are skipped) |

#### Test missing columns
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "cpse_name=TEST_BAD" \
  -F "file=@backend/test/missing_columns.csv"
# → 422 Unprocessable Entity
```

#### Test duplicate codes within one CPSE
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "cpse_name=TEST_DUPS" \
  -F "file=@backend/test/duplicate_codes.xlsx"
# → inserted=3, skipped=2
```

---

## Categories covered

| Code | Category | Example items |
|---|---|---|
| `FAS` | Fasteners | Bolts, nuts, washers |
| `BRG` | Bearings | Deep groove ball, cylindrical roller |
| `VLV` | Valves | Ball, gate, globe |
| `PPF` | Pipes & Fittings | MS seamless pipe |
| `ELC` | Electrical Cables | XLPE armoured |
| `LUB` | Lubricants | Hydraulic oil, engine oil, grease |
| `GSK` | Gaskets | Spiral wound |
| `SAF` | Safety | Helmet, goggles, harness, extinguisher |
| `INS` | Instrumentation | Pressure gauge, thermocouple |
| `ELS` | Electrical Switchgear | MCB |
| `HNT` | Hand Tools | Spanners, hacksaw |
| `ABR` | Abrasives | Grinding discs |
| `PNT` | Paints | Epoxy primer |
| `PMP` | Pump Spares | Mechanical seals |

---

## After uploading – run the pipeline

```bash
curl -X POST http://localhost:8000/api/process
```

Then check clusters:
```bash
curl http://localhost:8000/api/clusters?page=1&page_size=20
```

You should see clusters containing items from multiple CPSEs for all 10 `X_*` true groups.

"""
generate_dummy_data.py
======================
Generates three Excel files (cpse_a.xlsx, cpse_b.xlsx, cpse_c.xlsx) and a
combined ground_truth.csv with ~700 items per CPSE (~2 100 total).

Properties
----------
* Each CPSE uses a different code format.
* ~40 % of true_groups appear in 2 or 3 CPSEs with different descriptions.
* Hard negatives have the SAME category but different spec values (size/grade/model).
* Some within-CPSE duplicates are included.
* Fixed random seed (42) for reproducibility.
* true_group column is for evaluation only; never shown in the UI.

Run:
    python backend/data/generate_dummy_data.py
Output files are written to backend/data/.
"""

import random
import os
import pandas as pd
import numpy as np

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ──────────────────────────────────────────────────────────────────────────────
# Code format helpers
# ──────────────────────────────────────────────────────────────────────────────

def code_a(seq: int) -> str:
    """CPSE A format: A-000123"""
    return f"A-{seq:06d}"

def code_b(category_abbr: str, seq: int) -> str:
    """CPSE B format: MC/FAS/4521"""
    return f"MC/{category_abbr}/{seq:04d}"

def code_c(seq: int) -> str:
    """CPSE C format: 10045678"""
    return f"{10000000 + seq:08d}"

# ──────────────────────────────────────────────────────────────────────────────
# Item templates: (true_group, category, uom, unit_price, annual_qty,
#                  desc_a, desc_b, desc_c)
# Each template produces one true_group.  Approx 40 % will be cross-CPSE.
# ──────────────────────────────────────────────────────────────────────────────

TEMPLATES = []

# ── Fasteners – Bolts ─────────────────────────────────────────────────────────
for grade in ["8.8", "10.9", "4.6", "4.8", "12.9"]:
    for size, length in [("M8", "30"), ("M10", "50"), ("M10", "60"), ("M12", "40"),
                          ("M12", "60"), ("M16", "60"), ("M16", "80"), ("M20", "80"),
                          ("M20", "100"), ("M24", "100"), ("M24", "120"), ("M6", "20"),
                          ("M8", "40"), ("M30", "150")]:
        tg = f"BOLT_HEX_{size}x{length}_GR{grade.replace('.','')}_ZNPL"
        da = f"BOLT HEX {size}X{length} GR {grade} ZINC PLATED"
        db = f"Hexagon Head Bolt, {size[1:]} mm dia x {length} mm long, Grade {grade}, Zn plated"
        dc = f"HEX HD BOLT {size}-X{length}MM CL.{grade} GALV"
        TEMPLATES.append((tg, "FAS", "NOS", round(random.uniform(2, 80), 2),
                          round(random.uniform(100, 5000), 0), da, db, dc))

# ── Fasteners – Nuts ─────────────────────────────────────────────────────────
for grade in ["8", "10", "4"]:
    for size in ["M8", "M10", "M12", "M16", "M20", "M24"]:
        tg = f"NUT_HEX_{size}_GR{grade}"
        da = f"NUT HEX {size} GR {grade} ZINC PLATED"
        db = f"Hexagon Nut {size}, Property Class {grade}, Zinc plated"
        dc = f"HEX NUT {size} CL.{grade} ZN PLATED"
        TEMPLATES.append((tg, "FAS", "NOS", round(random.uniform(1, 20), 2),
                          round(random.uniform(200, 8000), 0), da, db, dc))

# ── Fasteners – Washers ───────────────────────────────────────────────────────
for size in ["M8", "M10", "M12", "M16", "M20"]:
    for wtype in ["PLAIN", "SPRING"]:
        tg = f"WASHER_{wtype}_{size}_ZN"
        da = f"WASHER {wtype} {size} ZINC PLATED"
        db = f"{wtype.title()} Washer {size}, Zinc plated"
        dc = f"{wtype[:3]} WSHR {size} ZN PL"
        TEMPLATES.append((tg, "FAS", "NOS", round(random.uniform(0.5, 5), 2),
                          round(random.uniform(500, 20000), 0), da, db, dc))

# ── Bearings ──────────────────────────────────────────────────────────────────
for bearing_code, b_type in [
    ("6205", "DEEP GROOVE BALL"), ("6206", "DEEP GROOVE BALL"), ("6207", "DEEP GROOVE BALL"),
    ("6305", "DEEP GROOVE BALL"), ("6306", "DEEP GROOVE BALL"), ("6308", "DEEP GROOVE BALL"),
    ("6205-2RS", "DEEP GROOVE BALL SEALED"), ("6206-2RS", "DEEP GROOVE BALL SEALED"),
    ("6208-2RS", "DEEP GROOVE BALL SEALED"), ("6207-2Z", "DEEP GROOVE BALL SHIELDED"),
    ("NU205", "CYLINDRICAL ROLLER"), ("NU206", "CYLINDRICAL ROLLER"),
    ("NU308", "CYLINDRICAL ROLLER"), ("NU310", "CYLINDRICAL ROLLER"),
    ("NU311", "CYLINDRICAL ROLLER"), ("22205", "SPHERICAL ROLLER"),
    ("22210", "SPHERICAL ROLLER"), ("22310", "SPHERICAL ROLLER"),
    ("30205", "TAPER ROLLER"), ("30208", "TAPER ROLLER"), ("30310", "TAPER ROLLER"),
    ("51105", "THRUST BALL"), ("51205", "THRUST BALL"),
]:
    tg = f"BRG_{bearing_code}"
    da = f"BEARING {bearing_code} {b_type}"
    db = f"{b_type.title()} Bearing {bearing_code} to ISO 355"
    dc = f"BRG-{bearing_code} {b_type[:4]}"
    TEMPLATES.append((tg, "BRG", "NOS", round(random.uniform(50, 5000), 2),
                      round(random.uniform(5, 200), 0), da, db, dc))

# ── Valves ────────────────────────────────────────────────────────────────────
for vtype, vcode in [("BALL VALVE", "BV"), ("GATE VALVE", "GV"), ("GLOBE VALVE", "GL"),
                      ("BUTTERFLY VALVE", "BFV"), ("CHECK VALVE", "CHK")]:
    for size_nb in ["15", "25", "40", "50", "80", "100", "150", "200"]:
        for rating in ["PN16", "PN25", "150#"]:
            for mat in [("CS", "CARBON STEEL"), ("SS", "STAINLESS STEEL")]:
                tg = f"{vcode}_{size_nb}NB_{rating}_{mat[0]}"
                da = f"{vtype} DN{size_nb} {rating} {mat[1]}"
                db = f"{vtype.title()}, NB {size_nb}mm, {rating}, {mat[1].title()}"
                dc = f"{vcode} {size_nb}NB {mat[0]} {rating} FLANGED"
                TEMPLATES.append((tg, "VLV", "NOS", round(random.uniform(500, 50000), 2),
                                  round(random.uniform(1, 50), 0), da, db, dc))
                if len(TEMPLATES) > 700:  # keep template count manageable
                    break
            if len(TEMPLATES) > 700:
                break
        if len(TEMPLATES) > 700:
            break

# ── Pipes ─────────────────────────────────────────────────────────────────────
for mat, mcode in [("MS", "MILD STEEL"), ("SS304", "SS 304"), ("GI", "GALVANIZED IRON")]:
    for nb in ["15", "25", "40", "50", "80", "100"]:
        for sch in ["SCH40", "SCH80", "SCH20"]:
            tg = f"PIPE_{mat}_{nb}NB_{sch}_IS1239"
            da = f"{mcode} PIPE DN{nb} {sch} SEAMLESS IS 1239"
            db = f"Seamless Pipe {nb} NB, {sch}, {mcode.title()}, IS:1239"
            dc = f"SMLS PIPE {nb}NB {sch} {mat} IS1239"
            TEMPLATES.append((tg, "PPF", "MTR", round(random.uniform(200, 5000), 2),
                              round(random.uniform(10, 500), 0), da, db, dc))

# ── Electrical Cables ─────────────────────────────────────────────────────────
for cores, area in [("2", "1.5"), ("3", "2.5"), ("3", "4"), ("4", "6"),
                     ("4", "10"), ("3.5", "16"), ("3.5", "25"), ("3.5", "35"),
                     ("3.5", "50"), ("3.5", "70"), ("3.5", "95"), ("3.5", "120")]:
    tg = f"CABLE_XLPE_PVC_{cores}Cx{area}sqmm_1100V_ARMRD"
    da = f"CABLE XLPE PVC {cores} CORE {area} SQMM 1.1KV ARMOURED"
    db = f"Armoured Cable, {cores}C x {area} sq.mm, XLPE/PVC, 1100V"
    dc = f"{cores}C x {area}SQMM XLPE/PVC/SWA/PVC 1.1KV ARMD"
    TEMPLATES.append((tg, "ELC", "MTR", round(random.uniform(100, 8000), 2),
                      round(random.uniform(50, 2000), 0), da, db, dc))

# ── Lubricants ────────────────────────────────────────────────────────────────
for grade in ["VG32", "VG46", "VG68", "VG100", "VG150", "VG220", "VG320", "VG460"]:
    tg = f"HYDRAULIC_OIL_ISO_{grade}"
    da = f"HYDRAULIC OIL ISO {grade.replace('VG','VG ')} IS 11656"
    db = f"Hydraulic Oil, ISO {grade.replace('VG','VG ')}, Mineral based"
    dc = f"HYD OIL ISO-{grade} AW TYPE IS11656"
    TEMPLATES.append((tg, "LUB", "LTR", round(random.uniform(80, 300), 2),
                      round(random.uniform(50, 1000), 0), da, db, dc))

for grade_sae in ["SAE 20W-50", "SAE 15W-40", "SAE 40", "SAE 30"]:
    tg = f"ENGINE_OIL_{grade_sae.replace(' ','_')}"
    da = f"ENGINE OIL {grade_sae} CI-4 IS 13656"
    db = f"Engine Oil {grade_sae}, API CI-4, Diesel"
    dc = f"ENG OIL {grade_sae} CI-4 GRADE"
    TEMPLATES.append((tg, "LUB", "LTR", round(random.uniform(90, 350), 2),
                      round(random.uniform(100, 2000), 0), da, db, dc))

for nlgi in ["2", "3", "00"]:
    for base in [("LI", "LITHIUM"), ("CA", "CALCIUM"), ("EP", "EP LITHIUM")]:
        tg = f"GREASE_{base[0]}_NLGI{nlgi}"
        da = f"GREASE {base[1]} NLGI {nlgi} EP IS 7623"
        db = f"{base[1].title()} Grease, NLGI Grade {nlgi}, EP"
        dc = f"{base[0]} GREASE NLGI-{nlgi} EP TYPE"
        TEMPLATES.append((tg, "LUB", "KG", round(random.uniform(120, 500), 2),
                          round(random.uniform(20, 500), 0), da, db, dc))

# ── Gaskets ───────────────────────────────────────────────────────────────────
for mat in [("SS304", "SS 304"), ("CS", "SOFT IRON"), ("GRPH", "GRAPHITE")]:
    for size in ["50", "80", "100", "150", "200"]:
        tg = f"GASKET_SWG_{size}NB_{mat[0]}_PN16"
        da = f"GASKET SPIRAL WOUND DN{size} {mat[1]} PN16"
        db = f"Spiral Wound Gasket {size}NB, {mat[1].title()}, PN16"
        dc = f"SWG {size}NB {mat[0]} PN16 RF"
        TEMPLATES.append((tg, "GSK", "NOS", round(random.uniform(200, 2000), 2),
                          round(random.uniform(5, 100), 0), da, db, dc))

# ── Safety Items ──────────────────────────────────────────────────────────────
safety_items = [
    ("HELMET_SAFETY_HDPE", "SAFETY HELMET HDPE IS 2925", "Safety Helmet, HDPE, IS:2925", "SFTY HLMT HDPE IS2925", "SAF", "NOS", 150, 500, 10, 200),
    ("GLOVES_NITRILE_MED", "NITRILE GLOVES MEDIUM DISPOSABLE", "Nitrile Gloves Medium, Disposable, 100pcs/box", "NTRLE GLVS MEDIUM DISP 100/BX", "SAF", "BOX", 350, 800, 20, 500),
    ("SHOES_SAFETY_SS_8", "SAFETY SHOES STEEL TOE SIZE 8 IS15298", "Safety Shoes Size 8, Steel Toe, IS:15298", "SFTY SHOE SIZE-8 STEEL TOE IS15298", "SAF", "PAIR", 800, 2500, 5, 100),
    ("GOGGLES_CLEAR_ANSI", "SAFETY GOGGLES CLEAR LENS ANSI Z87.1", "Safety Goggles, Clear Lens, Anti-Fog, ANSI Z87.1", "SFTY GGLS CLR LENS ANTI-FOG", "SAF", "NOS", 200, 600, 10, 300),
    ("HARNESS_FULL_BODY", "SAFETY HARNESS FULL BODY IS 3521", "Full Body Safety Harness, IS:3521, SWL 140kg", "FULL BODY HARNS IS3521 SWL140KG", "SAF", "NOS", 1200, 4000, 2, 50),
    ("EXTINGUISHER_CO2_4.5KG", "FIRE EXTINGUISHER CO2 4.5 KG IS 15683", "CO2 Fire Extinguisher 4.5kg, IS:15683", "CO2 FIRE EXTN 4.5KG IS15683", "SAF", "NOS", 2500, 8000, 1, 30),
]
for item in safety_items:
    tg, da, db, dc, cat, uom, pmin, pmax, qmin, qmax = item
    TEMPLATES.append((tg, cat, uom, round(random.uniform(pmin, pmax), 2),
                      round(random.uniform(qmin, qmax), 0), da, db, dc))

# ── Instrumentation ───────────────────────────────────────────────────────────
for prange, cls in [("0-10 BAR", "CL1.0"), ("0-25 BAR", "CL0.5"), ("0-60 BAR", "CL1.0"), ("0-100 BAR", "CL0.5")]:
    tg = f"PG_{prange.replace(' ','_').replace('-','_')}_{cls}"
    da = f"PRESSURE GAUGE {prange} SS316 BOURDON {cls}"
    db = f"Bourdon Pressure Gauge, Range {prange}, SS316 Wetted, {cls}"
    dc = f"PG {prange} SS316 TUBE {cls} BS1780"
    TEMPLATES.append((tg, "INS", "NOS", round(random.uniform(800, 5000), 2),
                      round(random.uniform(1, 30), 0), da, db, dc))

for trange, sensor in [("0-100C", "PT100"), ("0-200C", "K TYPE"), ("0-400C", "J TYPE")]:
    tg = f"TEMP_{trange.replace(' ','_').replace('-','_')}_{sensor.replace(' ','_')}"
    da = f"THERMOCOUPLE {sensor} {trange} SS316 PROTECTION TUBE"
    db = f"{sensor} Thermocouple, Range {trange}, SS316, 6mm Dia"
    dc = f"T/C {sensor} {trange} SS316 TUBE 6MM"
    TEMPLATES.append((tg, "INS", "NOS", round(random.uniform(600, 3000), 2),
                      round(random.uniform(1, 20), 0), da, db, dc))

# ── Electrical Switchgear ─────────────────────────────────────────────────────
for amps, poles in [("6A", "1P"), ("10A", "1P"), ("16A", "2P"), ("20A", "3P"),
                     ("32A", "3P"), ("63A", "3P"), ("100A", "3P")]:
    tg = f"MCB_{amps}_{poles}_10KA_CRV_C"
    da = f"MCB {poles} {amps} 10KA CURVE C IS 8828"
    db = f"Miniature Circuit Breaker {amps} {poles}, 10kA, Type C, IS:8828"
    dc = f"MCB {poles} POLE {amps} 10KA C-CURVE IS8828"
    TEMPLATES.append((tg, "ELS", "NOS", round(random.uniform(200, 2000), 2),
                      round(random.uniform(2, 100), 0), da, db, dc))

# ── Hand Tools ────────────────────────────────────────────────────────────────
hand_tools = [
    ("SPANNER_COMBINATION_13MM", "COMBINATION SPANNER 13 MM CR-V STEEL", "Combination Spanner 13mm, Cr-V Steel", "COMBO SPNR 13MM CRV STL", "HNT", "NOS", 120, 400, 5, 50),
    ("SPANNER_COMBINATION_17MM", "COMBINATION SPANNER 17 MM CR-V STEEL", "Combination Spanner 17mm, Cr-V Steel", "COMBO SPNR 17MM CRV STL", "HNT", "NOS", 140, 450, 5, 50),
    ("HAMMER_BALL_PEEN_500G", "BALL PEEN HAMMER 500 GM WOOD HANDLE", "Ball Peen Hammer 500g, Wood Handle, IS:841", "BALL PEEN HAMMER 500GM WD HNDL", "HNT", "NOS", 200, 600, 3, 30),
    ("TAPE_MEASURE_5M", "MEASURING TAPE 5 METER STEEL BLADE IS 1270", "Steel Tape Measure 5m, IS:1270", "MESR TAPE 5MTR STL IS1270", "HNT", "NOS", 150, 500, 2, 30),
    ("FILE_BASTARD_250MM", "BASTARD FILE 250 MM FLAT SECOND CUT", "Flat Bastard File 250mm, Second Cut", "FLAT FILE BASTARD 250MM 2ND CUT", "HNT", "NOS", 80, 250, 5, 100),
    ("HACKSAW_FRAME_300MM_ADJ", "HACKSAW FRAME 300 MM ADJUSTABLE", "Adjustable Hacksaw Frame 300mm, Tubular", "HACKSAW FRAME 300MM ADJ TUBULAR", "HNT", "NOS", 150, 450, 2, 50),
]
for item in hand_tools:
    tg, da, db, dc, cat, uom, pmin, pmax, qmin, qmax = item
    TEMPLATES.append((tg, cat, uom, round(random.uniform(pmin, pmax), 2),
                      round(random.uniform(qmin, qmax), 0), da, db, dc))

# ── Abrasives ─────────────────────────────────────────────────────────────────
for size_dia, thick, grit in [("115", "6", "A36"), ("125", "6", "A36"), ("180", "6", "A24"),
                                ("230", "6", "A24"), ("100", "6", "A60")]:
    tg = f"GRINDING_DISC_{size_dia}x{thick}x22_{grit}"
    da = f"GRINDING DISC {size_dia}X{thick}X22 MM {grit} DEPRESSED CENTRE"
    db = f"Depressed Centre Grinding Disc {size_dia}x{thick}x22mm, {grit} Grit"
    dc = f"GRD DISC {size_dia}X{thick}X22 {grit} DC WHEEL"
    TEMPLATES.append((tg, "ABR", "NOS", round(random.uniform(40, 200), 2),
                      round(random.uniform(50, 1000), 0), da, db, dc))

# ── Paints ────────────────────────────────────────────────────────────────────
for colour in ["RED OXIDE", "GREY", "YELLOW"]:
    tg = f"PRIMER_EPOXY_2PACK_{colour.replace(' ','_')}"
    da = f"EPOXY PRIMER 2 PACK {colour} IS 13213 20L"
    db = f"Two Pack Epoxy Primer, {colour.title()}, IS:13213, 20 Litre"
    dc = f"EPXY PRIMER 2K {colour} 20LT IS13213"
    TEMPLATES.append((tg, "PNT", "DRUM", round(random.uniform(1500, 6000), 2),
                      round(random.uniform(5, 100), 0), da, db, dc))

# ── Pump Spares ───────────────────────────────────────────────────────────────
for seal_type, size in [("MECHANICAL SEAL", "25MM"), ("MECHANICAL SEAL", "40MM"),
                          ("GLAND PACKING", "12MM"), ("GLAND PACKING", "16MM")]:
    tg = f"{seal_type.replace(' ','_')}_{size}"
    da = f"{seal_type} {size} SS316/CARBON/NBR PUMP SEAL"
    db = f"{seal_type.title()} {size}, SS316/Carbon/NBR, Single Spring"
    dc = f"{seal_type[:4]} SEAL {size} SS316 CARB NBR SNGL SPR"
    TEMPLATES.append((tg, "PMP", "NOS", round(random.uniform(500, 8000), 2),
                      round(random.uniform(2, 50), 0), da, db, dc))

print(f"[gen] Total base templates: {len(TEMPLATES)}")

# ──────────────────────────────────────────────────────────────────────────────
# Hard negatives: items that look alike but are genuinely different
# ──────────────────────────────────────────────────────────────────────────────

HARD_NEGATIVES = []

# Two very similar valve descriptions but different bore → different true_group
for nb_a, nb_b in [("50", "65"), ("80", "100"), ("100", "150")]:
    for mat in ["CS", "SS"]:
        tg_a = f"GV_{nb_a}NB_PN16_{mat}_HN"
        tg_b = f"GV_{nb_b}NB_PN16_{mat}_HN"
        da_a = f"GATE VALVE DN{nb_a} PN16 {mat} FLANGED RF"
        da_b = f"GATE VALVE DN{nb_b} PN16 {mat} FLANGED RF"
        HARD_NEGATIVES.append((tg_a, "VLV", "NOS", 1200.0, 5.0, da_a,
                               f"Gate Valve {nb_a}NB PN16 {mat}", da_a))
        HARD_NEGATIVES.append((tg_b, "VLV", "NOS", 1800.0, 5.0, da_b,
                               f"Gate Valve {nb_b}NB PN16 {mat}", da_b))

# Bearings that differ only in bore (6205 vs 6206 etc.) – already in TEMPLATES above
# Adding extra ones here to make sure all 3 CPSEs see the hard negative
for code_p, code_q in [("6205", "6305"), ("6206", "6306"), ("NU205", "NU305")]:
    for which_pair in [(code_p, code_q)]:
        for bc in which_pair:
            tg = f"BRG_{bc}_HN"
            da = f"BEARING {bc} DEEP GROOVE BALL BEARING"
            db = f"Deep Groove Ball Bearing {bc}, ISO 355"
            dc = f"BRG-{bc} DGBB"
            HARD_NEGATIVES.append((tg, "BRG", "NOS",
                                   round(random.uniform(50, 500), 2),
                                   round(random.uniform(5, 200), 0),
                                   da, db, dc))

# Bolts same size different grade
for size_len in [("M12", "50"), ("M16", "60"), ("M20", "80")]:
    for g_a, g_b in [("8.8", "10.9"), ("4.6", "8.8")]:
        for g in [g_a, g_b]:
            tg = f"BOLT_HEX_{size_len[0]}x{size_len[1]}_GR{g.replace('.','')}_HN_STSSL"
            da = f"BOLT HEX {size_len[0]}X{size_len[1]} GR {g} SS304"
            db = f"Hex Bolt {size_len[0]} x {size_len[1]}mm Grade {g} SS304"
            dc = f"HEX BOLT {size_len[0]}-X{size_len[1]}MM GR{g} SS304"
            HARD_NEGATIVES.append((tg, "FAS", "NOS",
                                   round(random.uniform(5, 120), 2),
                                   round(random.uniform(100, 3000), 0),
                                   da, db, dc))

print(f"[gen] Hard negatives generated: {len(HARD_NEGATIVES)}")

ALL_TEMPLATES = TEMPLATES + HARD_NEGATIVES

# ──────────────────────────────────────────────────────────────────────────────
# Category abbreviation lookup for CPSE B codes
# ──────────────────────────────────────────────────────────────────────────────
CAT_ABBR = {
    "FAS": "FAS", "BRG": "BRG", "VLV": "VLV", "PPF": "PPF",
    "ELC": "ELC", "LUB": "LUB", "GSK": "GSK", "SAF": "SAF",
    "INS": "INS", "ELS": "ELS", "HNT": "HNT", "ABR": "ABR",
    "PNT": "PNT", "PMP": "PMP", "PKS": "PKS",
}

# ──────────────────────────────────────────────────────────────────────────────
# Assign templates to CPSEs
# ──────────────────────────────────────────────────────────────────────────────
# Strategy:
# - ~40 % of true_groups appear in all 3 CPSEs (cross_cpse = 3)
# - ~20 % appear in exactly 2 CPSEs
# - ~40 % appear in only 1 CPSE (per-cpse unique)
# Hard negatives always appear in all 3 CPSEs.

TARGET_PER_CPSE = 700

rows_a, rows_b, rows_c = [], [], []

seq_a = seq_c = 1
seq_b: dict = {}  # per category

def next_seq_b(cat: str) -> int:
    seq_b.setdefault(cat, 1000)
    v = seq_b[cat]
    seq_b[cat] += 1
    return v

def add_row(rows, code_fn, desc, tg, cat, uom, price, qty, seq=None, cat_abbr=None):
    if code_fn == "a":
        global seq_a
        code = code_a(seq_a)
        seq_a += 1
    elif code_fn == "b":
        code = code_b(cat_abbr or cat, next_seq_b(cat))
    else:
        global seq_c
        code = code_c(seq_c)
        seq_c += 1
    rows.append({
        "material_code": code,
        "description": desc,
        "uom": uom,
        "unit_price": price,
        "annual_qty": qty,
        "true_group": tg,
        "category_hint": cat,
    })

# shuffle templates for randomness
shuffled = ALL_TEMPLATES.copy()
random.shuffle(shuffled)

# Separate hard negatives (always cross-CPSE)
hard_neg_tgs = {t[0] for t in HARD_NEGATIVES}

cross3_pool = []
cross2_pool = []
single_pool_a = []
single_pool_b = []
single_pool_c = []

roll_idx = 0
for tpl in shuffled:
    tg = tpl[0]
    if tg in hard_neg_tgs:
        cross3_pool.append(tpl)
        continue
    roll = random.random()
    if roll < 0.40:
        cross3_pool.append(tpl)
    elif roll < 0.60:
        cross2_pool.append(tpl)
    elif roll < 0.73:
        single_pool_a.append(tpl)
    elif roll < 0.86:
        single_pool_b.append(tpl)
    else:
        single_pool_c.append(tpl)

# Add cross-3 templates
for tpl in cross3_pool:
    tg, cat, uom, price, qty, da, db, dc = tpl
    price_noise = lambda p: round(p * random.uniform(0.90, 1.10), 2)
    qty_noise   = lambda q: round(q * random.uniform(0.80, 1.20), 0)
    add_row(rows_a, "a", da, tg, cat, uom, price_noise(price), qty_noise(qty))
    add_row(rows_b, "b", db, tg, cat, uom, price_noise(price), qty_noise(qty), cat_abbr=CAT_ABBR.get(cat, cat))
    add_row(rows_c, "c", dc, tg, cat, uom, price_noise(price), qty_noise(qty))

# Add cross-2 templates (to A+B or B+C or A+C randomly)
for tpl in cross2_pool:
    tg, cat, uom, price, qty, da, db, dc = tpl
    price_noise = lambda p: round(p * random.uniform(0.90, 1.10), 2)
    qty_noise   = lambda q: round(q * random.uniform(0.80, 1.20), 0)
    pair = random.choice(["AB", "BC", "AC"])
    if pair == "AB":
        add_row(rows_a, "a", da, tg, cat, uom, price_noise(price), qty_noise(qty))
        add_row(rows_b, "b", db, tg, cat, uom, price_noise(price), qty_noise(qty), cat_abbr=CAT_ABBR.get(cat, cat))
    elif pair == "BC":
        add_row(rows_b, "b", db, tg, cat, uom, price_noise(price), qty_noise(qty), cat_abbr=CAT_ABBR.get(cat, cat))
        add_row(rows_c, "c", dc, tg, cat, uom, price_noise(price), qty_noise(qty))
    else:
        add_row(rows_a, "a", da, tg, cat, uom, price_noise(price), qty_noise(qty))
        add_row(rows_c, "c", dc, tg, cat, uom, price_noise(price), qty_noise(qty))

# Fill singles
for tpl in single_pool_a:
    tg, cat, uom, price, qty, da, db, dc = tpl
    add_row(rows_a, "a", da, tg, cat, uom, price, qty)

for tpl in single_pool_b:
    tg, cat, uom, price, qty, da, db, dc = tpl
    add_row(rows_b, "b", db, tg, cat, uom, price, qty, cat_abbr=CAT_ABBR.get(cat, cat))

for tpl in single_pool_c:
    tg, cat, uom, price, qty, da, db, dc = tpl
    add_row(rows_c, "c", dc, tg, cat, uom, price, qty)

# ──────────────────────────────────────────────────────────────────────────────
# Pad to reach ~700 per CPSE by repeating random single-CPSE items with noise
# ──────────────────────────────────────────────────────────────────────────────

def pad_rows(rows, target, code_fn, cat_abbr_map):
    random.shuffle(rows)
    base = rows.copy()
    while len(rows) < target:
        tpl = random.choice(base)
        # Create a variant within-CPSE duplicate
        tg_dup = tpl["true_group"] + "_DUP"
        desc_variants = [
            tpl["description"].lower(),
            tpl["description"].upper(),
            tpl["description"].replace(",", " ").replace("  ", " "),
            "DUPLICATE ENTRY - " + tpl["description"],
        ]
        new_desc = random.choice(desc_variants)
        cat = tpl["category_hint"]
        if code_fn == "a":
            global seq_a
            code = code_a(seq_a); seq_a += 1
        elif code_fn == "b":
            code = code_b(cat_abbr_map.get(cat, cat), next_seq_b(cat))
        else:
            global seq_c
            code = code_c(seq_c); seq_c += 1
        rows.append({
            "material_code": code,
            "description": new_desc,
            "uom": tpl["uom"],
            "unit_price": round(tpl["unit_price"] * random.uniform(0.95, 1.05), 2),
            "annual_qty": tpl["annual_qty"],
            "true_group": tg_dup,
            "category_hint": cat,
        })

pad_rows(rows_a, TARGET_PER_CPSE, "a", CAT_ABBR)
pad_rows(rows_b, TARGET_PER_CPSE, "b", CAT_ABBR)
pad_rows(rows_c, TARGET_PER_CPSE, "c", CAT_ABBR)

print(f"[gen] CPSE A: {len(rows_a)} rows")
print(f"[gen] CPSE B: {len(rows_b)} rows")
print(f"[gen] CPSE C: {len(rows_c)} rows")

# ──────────────────────────────────────────────────────────────────────────────
# Build DataFrames with only the required columns (true_group included)
# ──────────────────────────────────────────────────────────────────────────────

COLS = ["material_code", "description", "uom", "unit_price", "annual_qty", "true_group"]

def to_df(rows):
    df = pd.DataFrame(rows)[COLS]
    return df

df_a = to_df(rows_a)
df_b = to_df(rows_b)
df_c = to_df(rows_c)

# ──────────────────────────────────────────────────────────────────────────────
# Save files
# ──────────────────────────────────────────────────────────────────────────────

path_a = os.path.join(OUT_DIR, "cpse_a.xlsx")
path_b = os.path.join(OUT_DIR, "cpse_b.xlsx")
path_c = os.path.join(OUT_DIR, "cpse_c.xlsx")

df_a.to_excel(path_a, index=False)
df_b.to_excel(path_b, index=False)
df_c.to_excel(path_c, index=False)
print(f"[gen] Written: {path_a}")
print(f"[gen] Written: {path_b}")
print(f"[gen] Written: {path_c}")

# Combined ground truth
df_a["cpse"] = "CPSE_A"
df_b["cpse"] = "CPSE_B"
df_c["cpse"] = "CPSE_C"
combined = pd.concat([df_a, df_b, df_c], ignore_index=True)
gt_path = os.path.join(OUT_DIR, "ground_truth.csv")
combined.to_csv(gt_path, index=False)
print(f"[gen] Written: {gt_path}")
print("[gen] Done.")

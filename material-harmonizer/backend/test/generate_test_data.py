"""
generate_test_data.py
=====================
Generates focused test files for the material-harmonizer upload API.

Files produced (all in the same directory as this script):
  cpse_a.xlsx  – NTPC-style codes  (A-000001),  30 rows
  cpse_b.xlsx  – BHEL-style codes  (MC/FAS/1001), 30 rows
  cpse_c.xlsx  – IOCL-style codes  (10000001),    30 rows
  single_row.csv       – minimal 1-row happy-path CSV
  missing_columns.csv  – missing 'description' column  (should 422)
  empty_body.csv       – header-only file  (0 data rows, inserts=0)
  duplicate_codes.xlsx – 5 rows where 3 codes repeat across sheets

Cross-CPSE duplicates
---------------------
  true_group starting with X_ appears in all 3 CPSE files with different
  wording so the processing pipeline can find them as clusters.

Run:
    python backend/test/generate_test_data.py
"""

import os
import pandas as pd

OUT = os.path.dirname(os.path.abspath(__file__))

# ── Helper ─────────────────────────────────────────────────────────────────────

def xlsx(df: pd.DataFrame, name: str):
    path = os.path.join(OUT, name)
    df.to_excel(path, index=False)
    print(f"  written: {path}  ({len(df)} rows)")

def csv_(df: pd.DataFrame, name: str):
    path = os.path.join(OUT, name)
    df.to_csv(path, index=False)
    print(f"  written: {path}  ({len(df)} rows)")


# ══════════════════════════════════════════════════════════════════════════════
# CPSE A  –  NTPC  (code format  A-NNNNNN)
# ══════════════════════════════════════════════════════════════════════════════
rows_a = [
    # ── Cross-CPSE duplicates (true_group starts with X_) ──────────────────
    ("A-000001", "BOLT HEX M12X50 GR 8.8 ZINC PLATED",                    "NOS", 18.50,  2000, "X_BOLT_HEX_M12x50_GR88_ZNPL"),
    ("A-000002", "NUT HEX M12 GR 8 ZINC PLATED",                          "NOS",  5.20,  4000, "X_NUT_HEX_M12_GR8"),
    ("A-000003", "BEARING 6205 DEEP GROOVE BALL BEARING",                  "NOS", 220.00,   50, "X_BRG_6205"),
    ("A-000004", "BALL VALVE DN50 PN16 CARBON STEEL FLANGED",              "NOS", 3800.00,  10, "X_BV_50NB_PN16_CS"),
    ("A-000005", "HYDRAULIC OIL ISO VG 46 IS 11656",                       "LTR", 145.00,  500, "X_HYD_OIL_VG46"),
    ("A-000006", "SAFETY HELMET HDPE IS 2925",                             "NOS", 210.00,  100, "X_HELMET_SAFETY_HDPE"),
    ("A-000007", "CABLE XLPE PVC 3 CORE 2.5 SQMM 1.1KV ARMOURED",        "MTR", 185.00,  300, "X_CABLE_3Cx2p5sqmm"),
    ("A-000008", "GASKET SPIRAL WOUND DN50 SS 304 PN16",                   "NOS", 650.00,   20, "X_GSK_SWG_50NB_SS304_PN16"),
    ("A-000009", "PRESSURE GAUGE 0-10 BAR SS316 BOURDON CL1.0",           "NOS", 1200.00,  15, "X_PG_0_10BAR_CL1p0"),
    ("A-000010", "MCB 3P 32A 10KA CURVE C IS 8828",                       "NOS", 680.00,   25, "X_MCB_32A_3P_10KA_CRV_C"),
    # ── Within-CPSE duplicates (same true_group, different wording) ─────────
    ("A-000011", "bolt hex m12 x 50mm grade 8.8 zn plated",               "NOS", 18.20,  1800, "X_BOLT_HEX_M12x50_GR88_ZNPL"),  # dup of A-000001
    ("A-000012", "HEX HEAD BOLT M12X50 GR8.8 GALVANISED",                 "NOS", 19.00,  2100, "X_BOLT_HEX_M12x50_GR88_ZNPL"),  # dup of A-000001
    # ── CPSE-A unique items ─────────────────────────────────────────────────
    ("A-000013", "WASHER PLAIN M12 ZINC PLATED",                           "NOS",  1.80, 10000, "WASHER_PLAIN_M12_ZN"),
    ("A-000014", "WASHER SPRING M10 ZINC PLATED",                          "NOS",  1.20,  8000, "WASHER_SPRING_M10_ZN"),
    ("A-000015", "GATE VALVE DN80 PN16 CARBON STEEL FLANGED RF",          "NOS", 5200.00,   5, "GV_80NB_PN16_CS"),
    ("A-000016", "MS PIPE DN25 SCH40 SEAMLESS IS 1239",                   "MTR", 420.00,  200, "PIPE_MS_25NB_SCH40_IS1239"),
    ("A-000017", "BEARING NU205 CYLINDRICAL ROLLER",                       "NOS", 850.00,   20, "BRG_NU205"),
    ("A-000018", "GREASE LITHIUM NLGI 2 EP IS 7623",                      "KG",  280.00,  100, "GREASE_LI_NLGI2"),
    ("A-000019", "THERMOCOUPLE K TYPE 0-200C SS316 PROTECTION TUBE",      "NOS", 1800.00,   8, "TEMP_0_200C_K_TYPE"),
    ("A-000020", "COMBINATION SPANNER 13 MM CR-V STEEL",                  "NOS", 250.00,   20, "SPANNER_COMBINATION_13MM"),
    ("A-000021", "GRINDING DISC 115X6X22 MM A36 DEPRESSED CENTRE",       "NOS",   65.00, 500, "GRINDING_DISC_115x6x22_A36"),
    ("A-000022", "EPOXY PRIMER 2 PACK RED OXIDE IS 13213 20L",            "DRUM", 3200.00, 20, "PRIMER_EPOXY_2PACK_RED_OXIDE"),
    ("A-000023", "MECHANICAL SEAL 25MM SS316/CARBON/NBR PUMP SEAL",       "NOS", 2800.00,  10, "MECHANICAL_SEAL_25MM"),
    ("A-000024", "BOLT HEX M16X60 GR 8.8 ZINC PLATED",                   "NOS",  42.00,  800, "BOLT_HEX_M16x60_GR88_ZNPL"),
    ("A-000025", "BOLT HEX M10X50 GR 4.6 ZINC PLATED",                   "NOS",  12.00, 3000, "BOLT_HEX_M10x50_GR46_ZNPL"),
    ("A-000026", "GLOBE VALVE DN25 PN16 STAINLESS STEEL FLANGED",        "NOS", 4100.00,   4, "GL_25NB_PN16_SS"),
    ("A-000027", "SAFETY GOGGLES CLEAR LENS ANSI Z87.1",                  "NOS", 380.00,   50, "GOGGLES_CLEAR_ANSI"),
    ("A-000028", "FIRE EXTINGUISHER CO2 4.5 KG IS 15683",                "NOS", 5500.00,  10, "EXTINGUISHER_CO2_4p5KG"),
    ("A-000029", "ENGINE OIL SAE 15W-40 API CI-4 IS 13656",              "LTR", 210.00,  400, "ENGINE_OIL_SAE_15W_40"),
    ("A-000030", "HACKSAW FRAME 300 MM ADJUSTABLE",                       "NOS", 320.00,   15, "HACKSAW_FRAME_300MM_ADJ"),
]

# ══════════════════════════════════════════════════════════════════════════════
# CPSE B  –  BHEL  (code format  MC/CAT/NNNN)
# ══════════════════════════════════════════════════════════════════════════════
rows_b = [
    # ── Cross-CPSE duplicates ───────────────────────────────────────────────
    ("MC/FAS/1001", "Hexagon Head Bolt, 12 mm dia x 50 mm long, Grade 8.8, Zn plated",  "NOS", 17.80,  1950, "X_BOLT_HEX_M12x50_GR88_ZNPL"),
    ("MC/FAS/1002", "Hexagon Nut M12, Property Class 8, Zinc plated",                   "NOS",  5.00,  3800, "X_NUT_HEX_M12_GR8"),
    ("MC/BRG/1003", "Deep Groove Ball Bearing 6205 to ISO 355",                         "NOS", 215.00,   45, "X_BRG_6205"),
    ("MC/VLV/1004", "Ball Valve, NB 50mm, PN16, Carbon Steel, Flanged",                "NOS", 3750.00,   8, "X_BV_50NB_PN16_CS"),
    ("MC/LUB/1005", "Hydraulic Oil, ISO VG 46, Mineral based",                         "LTR", 138.00,  480, "X_HYD_OIL_VG46"),
    ("MC/SAF/1006", "Safety Helmet, HDPE, IS:2925",                                     "NOS", 195.00,   90, "X_HELMET_SAFETY_HDPE"),
    ("MC/ELC/1007", "Armoured Cable, 3C x 2.5 sq.mm, XLPE/PVC, 1100V",               "MTR", 180.00,  280, "X_CABLE_3Cx2p5sqmm"),
    ("MC/GSK/1008", "Spiral Wound Gasket 50NB, SS 304, PN16",                          "NOS", 620.00,   18, "X_GSK_SWG_50NB_SS304_PN16"),
    ("MC/INS/1009", "Bourdon Pressure Gauge, Range 0-10 Bar, SS316 Wetted, CL1.0",    "NOS", 1150.00,  12, "X_PG_0_10BAR_CL1p0"),
    ("MC/ELS/1010", "Miniature Circuit Breaker 32A 3P, 10kA, Type C, IS:8828",        "NOS", 660.00,   22, "X_MCB_32A_3P_10KA_CRV_C"),
    # ── Within-CPSE duplicates ──────────────────────────────────────────────
    ("MC/BRG/1011", "Ball Bearing 6205, Single Row Deep Groove",                       "NOS", 218.00,   40, "X_BRG_6205"),  # dup of BRG/1003
    # ── CPSE-B unique items ─────────────────────────────────────────────────
    ("MC/FAS/1012", "Plain Washer M12, Zinc plated",                                   "NOS",  1.75,  9500, "WASHER_PLAIN_M12_ZN"),
    ("MC/FAS/1013", "Spring Washer M10, Zinc plated",                                  "NOS",  1.15,  7500, "WASHER_SPRING_M10_ZN"),
    ("MC/VLV/1014", "Gate Valve, NB 80mm, PN16, Carbon Steel, Flanged RF",            "NOS", 5100.00,   4, "GV_80NB_PN16_CS"),
    ("MC/PPF/1015", "Seamless Pipe 25 NB, SCH40, Mild Steel, IS:1239",               "MTR", 405.00,  180, "PIPE_MS_25NB_SCH40_IS1239"),
    ("MC/BRG/1016", "Cylindrical Roller Bearing NU205, ISO 355",                      "NOS", 830.00,   18, "BRG_NU205"),
    ("MC/LUB/1017", "Lithium Grease, NLGI Grade 2, EP",                               "KG",  270.00,   90, "GREASE_LI_NLGI2"),
    ("MC/INS/1018", "K TYPE Thermocouple, Range 0-200C, SS316, 6mm Dia",              "NOS", 1750.00,   6, "TEMP_0_200C_K_TYPE"),
    ("MC/HNT/1019", "Combination Spanner 13mm, Cr-V Steel",                           "NOS", 240.00,   18, "SPANNER_COMBINATION_13MM"),
    ("MC/ABR/1020", "Depressed Centre Grinding Disc 115x6x22mm, A36 Grit",           "NOS",   60.00, 450, "GRINDING_DISC_115x6x22_A36"),
    ("MC/PNT/1021", "Two Pack Epoxy Primer, Red Oxide, IS:13213, 20 Litre",           "DRUM", 3100.00, 18, "PRIMER_EPOXY_2PACK_RED_OXIDE"),
    ("MC/PMP/1022", "Mechanical Seal 25mm, SS316/Carbon/NBR, Single Spring",          "NOS", 2750.00,   8, "MECHANICAL_SEAL_25MM"),
    ("MC/FAS/1023", "Hexagon Head Bolt M16 x 60mm, Grade 8.8, Zinc Plated",          "NOS",  40.00,  750, "BOLT_HEX_M16x60_GR88_ZNPL"),
    ("MC/FAS/1024", "Hexagon Head Bolt M10 x 50mm, Grade 4.6, Zinc Plated",          "NOS",  11.50, 2800, "BOLT_HEX_M10x50_GR46_ZNPL"),
    ("MC/VLV/1025", "Globe Valve, NB 25mm, PN16, Stainless Steel, Flanged",          "NOS", 4050.00,   3, "GL_25NB_PN16_SS"),
    ("MC/SAF/1026", "Safety Goggles, Clear Lens, Anti-Fog, ANSI Z87.1",              "NOS", 370.00,   45, "GOGGLES_CLEAR_ANSI"),
    ("MC/SAF/1027", "CO2 Fire Extinguisher 4.5kg, IS:15683",                         "NOS", 5400.00,   8, "EXTINGUISHER_CO2_4p5KG"),
    ("MC/LUB/1028", "Engine Oil SAE 15W-40, API CI-4, Diesel",                       "LTR", 205.00,  380, "ENGINE_OIL_SAE_15W_40"),
    ("MC/HNT/1029", "Adjustable Hacksaw Frame 300mm, Tubular",                        "NOS", 310.00,   12, "HACKSAW_FRAME_300MM_ADJ"),
    ("MC/SAF/1030", "Full Body Safety Harness, IS:3521, SWL 140kg",                  "NOS", 2600.00,   6, "HARNESS_FULL_BODY"),
]

# ══════════════════════════════════════════════════════════════════════════════
# CPSE C  –  IOCL  (code format  NNNNNNNN numeric)
# ══════════════════════════════════════════════════════════════════════════════
rows_c = [
    # ── Cross-CPSE duplicates ───────────────────────────────────────────────
    ("10000001", "HEX HD BOLT M12-X50MM CL.8.8 GALV",                    "NOS", 19.00,  2100, "X_BOLT_HEX_M12x50_GR88_ZNPL"),
    ("10000002", "HEX NUT M12 CL.8 ZN PLATED",                           "NOS",  5.50,  4200, "X_NUT_HEX_M12_GR8"),
    ("10000003", "BRG-6205 DGBB",                                         "NOS", 225.00,   55, "X_BRG_6205"),
    ("10000004", "BV 50NB CS PN16 FLANGED",                               "NOS", 3900.00,  12, "X_BV_50NB_PN16_CS"),
    ("10000005", "HYD OIL ISO-VG46 AW TYPE IS11656",                     "LTR", 150.00,  520, "X_HYD_OIL_VG46"),
    ("10000006", "SFTY HLMT HDPE IS2925",                                 "NOS", 220.00,  110, "X_HELMET_SAFETY_HDPE"),
    ("10000007", "3C x 2.5SQMM XLPE/PVC/SWA/PVC 1.1KV ARMD",           "MTR", 188.00,  320, "X_CABLE_3Cx2p5sqmm"),
    ("10000008", "SWG 50NB SS304 PN16 RF",                               "NOS", 670.00,   22, "X_GSK_SWG_50NB_SS304_PN16"),
    ("10000009", "PG 0-10 BAR SS316 TUBE CL1.0 BS1780",                 "NOS", 1250.00,  18, "X_PG_0_10BAR_CL1p0"),
    ("10000010", "MCB 3 POLE 32A 10KA C-CURVE IS8828",                  "NOS", 700.00,   28, "X_MCB_32A_3P_10KA_CRV_C"),
    # ── Within-CPSE duplicates ──────────────────────────────────────────────
    ("10000011", "BALL VALVE 50NB CARBON STEEL PN16 FLGD",              "NOS", 3850.00,   9, "X_BV_50NB_PN16_CS"),   # dup of 10000004
    # ── CPSE-C unique items ─────────────────────────────────────────────────
    ("10000012", "PLN WSHR M12 ZN PL",                                   "NOS",  1.90, 11000, "WASHER_PLAIN_M12_ZN"),
    ("10000013", "SPR WSHR M10 ZN PL",                                   "NOS",  1.30,  8500, "WASHER_SPRING_M10_ZN"),
    ("10000014", "GV 80NB CS PN16 FLANGED RF",                          "NOS", 5300.00,   6, "GV_80NB_PN16_CS"),
    ("10000015", "SMLS PIPE 25NB SCH40 MS IS1239",                      "MTR", 430.00,  220, "PIPE_MS_25NB_SCH40_IS1239"),
    ("10000016", "BRG-NU205 CYL ROLLER",                                 "NOS", 870.00,   22, "BRG_NU205"),
    ("10000017", "LI GREASE NLGI-2 EP TYPE",                             "KG",  290.00,  110, "GREASE_LI_NLGI2"),
    ("10000018", "T/C K TYPE 0-200C SS316 TUBE 6MM",                    "NOS", 1850.00,  10, "TEMP_0_200C_K_TYPE"),
    ("10000019", "COMBO SPNR 13MM CRV STL",                              "NOS", 260.00,   22, "SPANNER_COMBINATION_13MM"),
    ("10000020", "GRD DISC 115X6X22 A36 DC WHEEL",                      "NOS",   70.00, 550, "GRINDING_DISC_115x6x22_A36"),
    ("10000021", "EPXY PRIMER 2K RED OXIDE 20LT IS13213",               "DRUM", 3300.00, 22, "PRIMER_EPOXY_2PACK_RED_OXIDE"),
    ("10000022", "MECH SEAL 25MM SS316 CARB NBR SNGL SPR",              "NOS", 2900.00,  12, "MECHANICAL_SEAL_25MM"),
    ("10000023", "HEX BOLT M16-X60MM GR8.8 GALV",                      "NOS",  44.00,  850, "BOLT_HEX_M16x60_GR88_ZNPL"),
    ("10000024", "HEX BOLT M10-X50MM GR4.6 GALV",                      "NOS",  12.50, 3200, "BOLT_HEX_M10x50_GR46_ZNPL"),
    ("10000025", "GLOBE VLV 25NB SS PN16 FLGD",                         "NOS", 4200.00,   5, "GL_25NB_PN16_SS"),
    ("10000026", "SFTY GGLS CLR LENS ANTI-FOG",                         "NOS", 390.00,   55, "GOGGLES_CLEAR_ANSI"),
    ("10000027", "CO2 FIRE EXTN 4.5KG IS15683",                         "NOS", 5600.00,  12, "EXTINGUISHER_CO2_4p5KG"),
    ("10000028", "ENG OIL SAE 15W-40 CI-4 GRADE",                      "LTR", 215.00,  420, "ENGINE_OIL_SAE_15W_40"),
    ("10000029", "HACKSAW FRAME 300MM ADJ TUBULAR",                     "NOS", 330.00,   18, "HACKSAW_FRAME_300MM_ADJ"),
    ("10000030", "FULL BODY HARNS IS3521 SWL140KG",                     "NOS", 2700.00,   7, "HARNESS_FULL_BODY"),
]

COLS = ["material_code", "description", "uom", "unit_price", "annual_qty", "true_group"]

def make_df(rows):
    return pd.DataFrame(rows, columns=COLS)

print("Generating test data…")

xlsx(make_df(rows_a), "cpse_a.xlsx")
xlsx(make_df(rows_b), "cpse_b.xlsx")
xlsx(make_df(rows_c), "cpse_c.xlsx")


# ══════════════════════════════════════════════════════════════════════════════
# single_row.csv  –  minimal happy-path CSV (only required columns)
# ══════════════════════════════════════════════════════════════════════════════
single = pd.DataFrame([{
    "material_code": "TEST-001",
    "description":   "BOLT HEX M10X40 GR 8.8 ZINC PLATED",
    "uom":           "NOS",
    "unit_price":    14.50,
    "annual_qty":    1000,
}])
csv_(single, "single_row.csv")


# ══════════════════════════════════════════════════════════════════════════════
# missing_columns.csv  –  no 'description' column  → expect HTTP 422
# ══════════════════════════════════════════════════════════════════════════════
bad_cols = pd.DataFrame([{
    "material_code": "BAD-001",
    "item_name":     "This column is wrong",   # 'description' is absent
    "uom":           "NOS",
}])
csv_(bad_cols, "missing_columns.csv")


# ══════════════════════════════════════════════════════════════════════════════
# empty_body.csv  –  correct headers but zero data rows  → inserted=0, skipped=0
# ══════════════════════════════════════════════════════════════════════════════
empty = pd.DataFrame(columns=COLS)
csv_(empty, "empty_body.csv")


# ══════════════════════════════════════════════════════════════════════════════
# duplicate_codes.xlsx  –  same material_code repeated within one CPSE
# ══════════════════════════════════════════════════════════════════════════════
dup_rows = [
    ("DUP-001", "BOLT HEX M8X30 GR 8.8 ZINC PLATED",         "NOS", 8.50,  500, "DUP_BOLT"),
    ("DUP-002", "NUT HEX M8 GR 8 ZINC PLATED",               "NOS", 3.20, 1000, "DUP_NUT"),
    ("DUP-001", "BOLT HEX M8X30 GR8.8 ZN PL (DUPLICATE)",   "NOS", 8.50,  500, "DUP_BOLT"),  # same code as first row
    ("DUP-003", "WASHER PLAIN M8 ZINC PLATED",                "NOS", 0.90, 2000, "DUP_WSHR"),
    ("DUP-002", "HEX NUT M8 GRADE 8 ZN (DUPLICATE)",        "NOS", 3.20, 1000, "DUP_NUT"),   # same code as second row
]
xlsx(pd.DataFrame(dup_rows, columns=COLS), "duplicate_codes.xlsx")

print("\nDone. Test files in:", OUT)

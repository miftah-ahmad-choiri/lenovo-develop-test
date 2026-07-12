"""
Input / output path configuration for the WO Onsite pipeline.

All paths are resolved relative to this file so they work on any machine
without hardcoding an absolute path.
"""
import os

# Root of the repository (3 levels up: wo_onsite/ → services/ → app/ → root)
_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# ── Input files (uploaded to files/upload/excel/) ────────────────────────────
EXCEL_DIR = os.path.join(_ROOT, "files", "upload", "excel")

DEVI1_PATH  = os.path.join(EXCEL_DIR, "new_WO_Header_Status_-_Labor_Vendor_Updated_Open_WO_ONLY_7-7-2026_4-47-39_PM.xlsx")
DEVI2_PATH  = os.path.join(EXCEL_DIR, "Masterfile_-_Cut_Jan_2026_-_Copy.xlsx")
DEVI3_PATH  = os.path.join(EXCEL_DIR, "Active_Work_Orders_7-7-2026_4-46-51_PM.xlsx")
DEVI4_PATH  = os.path.join(EXCEL_DIR, "Work_Order_Product_Advanced_Find_View_7-7-2026_4-49-03_PM.xlsx")
DEVI12_PATH = os.path.join(EXCEL_DIR, "Vendor-mapping.xlsx")

# ── Output files ──────────────────────────────────────────────────────────────
EXCELS_DIR  = os.path.join(_ROOT, "files", "download", "excel")
OUTPUT_PATH = os.path.join(EXCELS_DIR, "df_combined_final_report.xlsx")

# ── Final column order for the exported report ────────────────────────────────
FINAL_COLUMNS_ORDER = [
    "Creation Date", "WO#", "SN", "Product", "Status",
    "Service Order Description", "Part Description",
    "Actual ASP", "Origin Vendor ID", "Information",
    "Customer Address", "Customer Name", "Customer Phone No ",
    "Status Part", "WH Ship      (LAPS)", "process",
]

"""
Pipeline configuration — input/output paths, column ordering, and
file-category detection configs for the WO Onsite pipeline.

All paths are resolved relative to the repository root so they work
on any machine without hardcoding an absolute path.
"""
import os

# Repository root — two levels up from this file (app/config/ → app/ → root)
_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))

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

# ── File category configs — required columns per source-file type ─────────────
# Detection is done by column-matching (not filename), matching the
# detect_and_validate_dataframe logic.  Each key is the category identifier.
FILE_CATEGORY_CONFIGS = {
    "WOID": {
        "file_category": "Work Order Advance Find View",
        "source_file": "MSD",
        "required_columns": [
            " Contact Name (Contact) (Contact)", "Address 1 (Contact) (Contact)", "Created On",
            "Company Name", "Release Date", "Serial Number", "Service Delivery Instructions",
            "Owner", "Customer (Labor Vendor Related) (Partner Function)",
            "Labor Vendor Related", "Mobile Phone (Contact) (Contact)",
            "Primary Email (Contact) (Contact)", "Product Description",
            "Serial Number (Case) (Case)", "Work Order ID", "Work Order Status",
        ],
        "date_column": "Created On",
    },
    "SOID": {
        "file_category": "Work Order Product Advance Find View",
        "source_file": "MSD",
        "required_columns": [
            "Created On", "Release Date", "(Do Not Modify) Work Order Product",
            "Delivery Date", "Description", "Product", "Shipment Date", "Work Order",
            "Work Order Product Status", "Work Order Status (Work Order) (Work Order)",
        ],
        "date_column": "Created On",
    },
    "OPENORDER": {
        "file_category": "ID-IBM ID Open Order",
        "source_file": "Lenovo",
        "required_columns": [
            "Company Name", "Customer Name", "ETA WO can Close", "Is Customer Willing to Wait?",
            "Serial Number", "Service Delivery Instructions", "STATUS",
            "Status Update with Explanation", "Category", "Work Order ID", "Work Order Status",
            "WO Release Date",
        ],
        "date_column": "WO Release Date",
    },
    "SHIPMENT": {
        "file_category": "Lenovo Shipment Daily Report",
        "source_file": "YCH Logistics",
        "required_columns": [
            "Company Name", "Contact", "Service Provider ID", "Order Date", "SOID",
            "Service Delivery Type", "Ship PN", "Ship PN Desc", "Ship POU POD Time",
            "Ship To Address", "Ship To City", "SO", "Target",
        ],
        "date_column": "Order Date",
    },
    "PARTONHOLD": {
        "file_category": "Backlog Report File",
        "source_file": "Lenovo",
        "required_columns": [
            "ETA", "Machine SN", "Model", "Owner", "Part Number", "PN Desc",
            "Service Order ID", "SO ETA", "Status Date", "Service Order Creation Date",
        ],
        "date_column": "Service Order Creation Date",
    },
    "UNRETURN": {
        "file_category": "ID-IBM ID POU Unreturn",
        "source_file": "Lenovo",
        "required_columns": [
            "Ship PN", "Delivery Date", "WO Type", "AWB Number", "Labor Status",
            "Vendor Name", "Aging Days", "Vendor ID", "Note", "Return Status",
            "SO Completion Date", "DC/Collection Form", "Aging Range",
        ],
        "date_column": "SO Completion Date",
    },
    "GTAAP": {
        "file_category": "GTAAP Report",
        "source_file": "Resolv",
        "required_columns": [
            "Aging days", "DC#", "Deskripsi Suku Cadang", "Jenis Layanan", "Kota",
            "Labor Fix Date/time", "Nama Penyedia Layanan", "Nomor Suku Cadang",
            "Part Return Date", "Service Provider ID", "SOID", "Status",
            "Status Tenaga Kerja", "Tanggal Pengiriman Suku Cadang", "WO#",
        ],
        "date_column": "Tanggal Pengiriman Suku Cadang",
    },
}

"""
Central configuration for the Flask application.

All paths are resolved relative to the repository root so they work
on any machine without hardcoding absolute paths.
"""
import os

# Repository root — two levels up from this file (app/config/settings.py → root)
_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


class Config:
    # ── Flask core ─────────────────────────────────────────────────────────────
    SECRET_KEY = "lenovo-asp-secret-key"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # ── Upload folders ─────────────────────────────────────────────────────────
    # Evidence files (images / PDFs submitted with tickets)
    UPLOAD_FOLDER = os.path.join(_ROOT, "files", "upload")

    # Source Excel files uploaded before running the pipeline
    EXCEL_UPLOAD_FOLDER = os.path.join(_ROOT, "files", "upload", "excel")

    # ── Excel output ───────────────────────────────────────────────────────────
    EXCELS_DIR  = os.path.join(_ROOT, "files", "download", "excel")
    EXCEL_PATH  = os.path.join(_ROOT, "files", "download", "excel", "df_combined_final_report.xlsx")

import os


class Config:
    SECRET_KEY = "lenovo-asp-secret-key"
    UPLOAD_FOLDER = "uploads"
    EXCEL_UPLOAD_FOLDER = os.path.join("uploads", "excel")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "excels", "df_combined_final_report.xlsx")
    EXCELS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "excels"))

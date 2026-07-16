"""
Backward-compatibility shim.

All configuration has moved to app.config.pipeline_config.
This module re-exports everything so existing imports keep working.
"""
from app.config.pipeline_config import (  # noqa: F401
    EXCEL_DIR,
    DEVI1_PATH,
    DEVI2_PATH,
    DEVI3_PATH,
    DEVI4_PATH,
    DEVI12_PATH,
    EXCELS_DIR,
    OUTPUT_PATH,
    FINAL_COLUMNS_ORDER,
    FILE_CATEGORY_CONFIGS,
)

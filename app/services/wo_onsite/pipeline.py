"""
WO Onsite pipeline entry point.

Run this file directly to regenerate excels/df_combined_final_report.xlsx:

    python -m app.services.wo_onsite.pipeline
    # or
    python app/services/wo_onsite/pipeline.py
"""
import io
import os
from datetime import datetime
import pandas as pd

from app.services.wo_onsite.config import (
    DEVI1_PATH, DEVI2_PATH, DEVI3_PATH, DEVI4_PATH, DEVI12_PATH,
    OUTPUT_PATH, EXCELS_DIR, FINAL_COLUMNS_ORDER,
)
from app.services.wo_onsite.transforms import (
    new_wo_filter_detection,
    process_new_work_orders,
    process_customer_info,
    update_actual_asp_from_devi1,
    combine_wo_and_customer_info,
    process_devi4_data,
    combine_devi2_new_wo_with_consolidation,
    filter_devi2_not_in_devi4,
    merge_and_reorder_dfs,
    update_actual_vendor_id,
    update_asp_information,
    format_columns_for_export,
)


def load_inputs() -> dict:
    """Load all source Excel files and return them as a dict of DataFrames."""
    print("Loading source files...")
    return {
        "devi1":  pd.read_excel(DEVI1_PATH,  sheet_name=0),
        "devi2":  pd.read_excel(DEVI2_PATH,  sheet_name=0),
        "devi3":  pd.read_excel(DEVI3_PATH,  sheet_name=0),
        "devi4":  pd.read_excel(DEVI4_PATH,  sheet_name=0),
        "devi12": pd.read_excel(DEVI12_PATH, sheet_name=1),
    }


def run_pipeline() -> pd.DataFrame:
    """
    Execute the full WO Onsite pipeline and return the final DataFrame.
    Also exports the result to OUTPUT_PATH.
    """
    src = load_inputs()

    # Step 1 — detect new WOs
    df_new_wo = new_wo_filter_detection(src["devi3"], src["devi2"])

    # Step 2 — build new-WO detail rows
    df_new_wo_proc1 = process_new_work_orders(src["devi3"], df_new_wo)

    # Step 3 — enrich with customer info
    df_devi1_processed        = process_customer_info(src["devi1"])
    df_new_wo_proc1_updated   = update_actual_asp_from_devi1(df_new_wo_proc1, src["devi1"])
    df_new_wo_only            = combine_wo_and_customer_info(df_new_wo_proc1_updated, df_devi1_processed)

    # Step 4 — process devi4 (parts / products)
    df_devi4_merged = process_devi4_data(src["devi4"], src["devi2"], df_new_wo_only)

    # Step 5 — merge devi2 open rows with new-WO rows
    df_combined_open = combine_devi2_new_wo_with_consolidation(src["devi2"], df_new_wo_only)

    # Step 6 — devi2 rows not covered by devi4
    df_devi2_remainder = filter_devi2_not_in_devi4(src["devi2"], df_devi4_merged)

    # Step 7 — merge devi4 + combined open, apply final column order
    df_consolidated = merge_and_reorder_dfs(df_devi4_merged, df_combined_open, FINAL_COLUMNS_ORDER)

    # Step 8 — concatenate remainder + consolidated
    df_report = pd.concat([df_devi2_remainder, df_consolidated], ignore_index=True)

    # Step 9 — fill in Actual Vendor ID + Origin ASP from devi2
    df_report = update_actual_vendor_id(df_report, src["devi2"])

    # Step 10 — resolve official ASP names via vendor-mapping
    df_report = update_asp_information(df_report, src["devi12"])

    # Step 11 — format columns for clean export
    df_report = format_columns_for_export(df_report)

    # Export — fixed name (used by Flask / dashboard)
    df_report.to_excel(OUTPUT_PATH, index=False)

    # Also write a timestamped copy: Masterfile_YYYYMMDD_HHMMSS.xlsx
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stamped_name = f"Masterfile_{ts}.xlsx"
    stamped_path = os.path.join(EXCELS_DIR, stamped_name)
    df_report.to_excel(stamped_path, index=False)

    print(f"Exported {len(df_report)} rows. Done. Stamped: {stamped_name}")
    return df_report


def run_pipeline_to_buffer() -> tuple[io.BytesIO, str]:
    """
    Execute the full pipeline and return the result as an in-memory Excel buffer.
    Nothing is written to disk — safe for ephemeral filesystems (e.g. Render free tier).

    Returns:
        (buffer, download_filename)
    """
    df_report = run_pipeline()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Masterfile_{ts}.xlsx"

    buf = io.BytesIO()
    df_report.to_excel(buf, index=False)
    buf.seek(0)
    return buf, filename


if __name__ == "__main__":
    run_pipeline()

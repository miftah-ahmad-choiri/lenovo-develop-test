import os
import pandas as pd
from flask import current_app


def _fmt(val):
    """Return a clean string from any cell value (handles NaN, NaT, datetime)."""
    if val is None:
        return ""
    if isinstance(val, float) and val != val:  # float NaN
        return ""
    try:
        if pd.isnull(val):
            return ""
    except (TypeError, ValueError):
        pass
    if hasattr(val, "strftime"):
        return val.strftime("%Y-%m-%d %H:%M")
    return str(val).strip()


def load_wo_data() -> list[dict]:
    """Load work-order rows from df_combined_final_report.xlsx."""
    excel_path = current_app.config["EXCEL_PATH"]
    df = pd.read_excel(excel_path, sheet_name=0)

    data = []
    for _, row in df.iterrows():
        data.append({
            # keys used by both templates — mapped to new column names
            "wo":             _fmt(row.get("WO#")),
            "contact":        _fmt(row.get("Actual ASP")),
            "pic":            _fmt(row.get("CE Name")),
            "created_on":     _fmt(row.get("Creation Date")),
            "order_date":     _fmt(row.get("Creation Date")),
            "courier_pickup": _fmt(row.get("WH Ship      (LAPS)")),
            "month":          "",
            "parts_eta":      _fmt(row.get("Part ETA Date")),
            "asp_received":   _fmt(row.get("Technician assign Date")),
            "wo_closed":      _fmt(row.get("Fixed Date")),
            "status":         _fmt(row.get("Status")),
            "failed_reason":  _fmt(row.get("Reason")),
            "remark":         _fmt(row.get("Remarks")),
            "city":           _fmt(row.get("Customer Address")),
            "product":        _fmt(row.get("Product")),
            # extra fields available in new file
            "sn":             _fmt(row.get("SN")),
            "actual_asp":     _fmt(row.get("Actual ASP")),
            "origin_asp":     _fmt(row.get("Origin ASP")),
            "origin_vendor":  _fmt(row.get("Origin Vendor ID")),
            "actual_vendor":  _fmt(row.get("Actual Vendor ID")),
            "part_desc":      _fmt(row.get("Part Description")),
            "status_part":    _fmt(row.get("Status Part")),
            "cust_name":      _fmt(row.get("Customer Name")),
            "cust_phone":     _fmt(row.get("Customer Phone No ")),
            "aging":          _fmt(row.get("Aging")),
            "aging_category": _fmt(row.get("Aging Category")),
            "kpi":            _fmt(row.get("KPI\n(Pass / Failed)")),
            "svc_desc":       _fmt(row.get("Service Order Description")),
            "information":    _fmt(row.get("Information")),
        })
    return data

import os
import pandas as pd
from datetime import datetime
from flask import current_app


def _fmt(val):
    """Return a clean string from any cell value (handles NaN, NaT, datetime)."""
    if val is None:
        return ""
    if isinstance(val, float) and val != val:  # float NaN
        return ""
    # pandas NaT or any object that claims to be NaT
    try:
        import pandas as _pd
        if _pd.isnull(val):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M")
    if hasattr(val, 'isoformat'):  # pandas Timestamp
        return str(val)[:16]
    return str(val).strip()


def load_onsite_data() -> list[dict]:
    """
    Load df_combined_final_report.xlsx and return a list of row dicts
    ready for JSON serialisation in the dashboard.
    Returns an empty list if the file does not exist yet.
    """
    path = current_app.config["ONSITE_REPORT_PATH"]
    if not os.path.isfile(path):
        return []

    df = pd.read_excel(path, sheet_name=0)

    records = []
    for _, row in df.iterrows():
        records.append({
            "creation_date":   _fmt(row.get("Creation Date")),
            "wo":              _fmt(row.get("WO#")),
            "sn":              _fmt(row.get("SN")),
            "product":         _fmt(row.get("Product")),
            "status":          _fmt(row.get("Status")),
            "svc_desc":        _fmt(row.get("Service Order Description")),
            "part_desc":       _fmt(row.get("Part Description")),
            "qty":             _fmt(row.get("QTY")),
            "origin_asp":      _fmt(row.get("Origin ASP")),
            "actual_asp":      _fmt(row.get("Actual ASP")),
            "ce_name":         _fmt(row.get("CE Name")),
            "cust_address":    _fmt(row.get("Customer Address")),
            "cust_name":       _fmt(row.get("Customer Name")),
            "cust_phone":      _fmt(row.get("Customer Phone No ")),
            "add_pic":         _fmt(row.get("Additional PIC")),
            "status_part":     _fmt(row.get("Status Part")),
            "part_eta":        _fmt(row.get("Part ETA Date")),
            "wh_ship":         _fmt(row.get("WH Ship      (LAPS)")),
            "aging":           _fmt(row.get("Aging")),
            "aging_category":  _fmt(row.get("Aging Category")),
            "courier_pod":     _fmt(row.get("Courier POD")),
            "tech_assign":     _fmt(row.get("Technician assign Date")),
            "fixed_date":      _fmt(row.get("Fixed Date")),
            "remarks":         _fmt(row.get("Remarks")),
            "achievement":     _fmt(row.get("Achievement")),
            "information":     _fmt(row.get("Information")),
            "kpi":             _fmt(row.get("KPI\n(Pass / Failed)")),
            "reason":          _fmt(row.get("Reason")),
            "email_subject":   _fmt(row.get("Email Subject")),
            "distance_km":     _fmt(row.get("Distance (KM)")),
            "origin_vendor":   _fmt(row.get("Origin Vendor ID")),
            "actual_vendor":   _fmt(row.get("Actual Vendor ID")),
            "process":         _fmt(row.get("process")),
        })
    return records

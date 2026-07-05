from flask import Blueprint, render_template
import openpyxl
import os
import json
from datetime import datetime

dashboard_bp = Blueprint("dashboard", __name__)

EXCEL_PATH = os.path.join(os.path.dirname(__file__), "excels", "test-dashboard-file.xlsx")


def fmt_date(val):
    """Return ISO date string or empty string from an openpyxl cell value."""
    if val is None:
        return ""
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M")
    return str(val)


def load_wo_data():
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    headers = rows[0]
    data = []
    for r in rows[1:]:
        if not any(r):
            continue
        row = dict(zip(headers, r))
        data.append({
            "wo":           str(row.get("Lenovo WO") or ""),
            "contact":      str(row.get("Contact") or ""),
            "pic":          str(row.get("PIC") or ""),
            "created_on":   fmt_date(row.get("Created On")),
            "order_date":   fmt_date(row.get("Order Date")),
            "courier_pickup": fmt_date(row.get("Courier Pick Up")),
            "month":        str(row.get("Month") or ""),
            "parts_eta":    fmt_date(row.get("Parts ETA Date")),
            "asp_received": fmt_date(row.get("ASP Received Date & Time")),
            "wo_closed":    fmt_date(row.get("Date & Time WO# Closed")),
            "status":       str(row.get("Status") or ""),
            "failed_reason": str(row.get("Failed Reason") or ""),
            "remark":       str(row.get("Remark") or ""),
            "city":         str(row.get("City") or ""),
            "product":      str(row.get("Product Category") or ""),
        })
    return data


@dashboard_bp.route("/dashboard")
def dashboard():
    wo_data = load_wo_data()
    # Part in Transit = CCI only: no ASP received date yet (simulate: treat "Need Additional Part" as still waiting for 2nd part / in-transit)
    # Per business logic: "CCI Only" = WOs where part has been ordered but ASP has not confirmed receipt (asp_received is empty)
    transit = [w for w in wo_data if not w["asp_received"]]
    # If all have received dates in test data, fall back to open/pending rows to show something meaningful
    if not transit:
        transit = [w for w in wo_data if w["status"] in ("Need Additional Part", "ASP Issue")]
    # Part Return candidates = Closed WOs (part was used / needs to be returned)
    closed = [w for w in wo_data if w["status"] == "Closed"]
    return render_template(
        "dashboard.html",
        wo_data_json=json.dumps(wo_data),
        transit_json=json.dumps(transit),
        closed_json=json.dumps(closed),
        total=len(wo_data),
        total_closed=len([w for w in wo_data if w["status"] == "Closed"]),
        total_open=len([w for w in wo_data if w["status"] != "Closed"]),
        total_transit=len(transit),
    )

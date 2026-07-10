import os
import openpyxl
from datetime import datetime
from flask import current_app


def fmt_date(val):
    """Return formatted date string or empty string from an openpyxl cell value."""
    if val is None:
        return ""
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M")
    return str(val)


def load_wo_data():
    """Load work-order rows from the configured Excel file."""
    excel_path = current_app.config["EXCEL_PATH"]
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    headers = rows[0]
    data = []
    for r in rows[1:]:
        if not any(r):
            continue
        row = dict(zip(headers, r))
        data.append({
            "wo":             str(row.get("Lenovo WO") or ""),
            "contact":        str(row.get("Contact") or ""),
            "pic":            str(row.get("PIC") or ""),
            "created_on":     fmt_date(row.get("Created On")),
            "order_date":     fmt_date(row.get("Order Date")),
            "courier_pickup": fmt_date(row.get("Courier Pick Up")),
            "month":          str(row.get("Month") or ""),
            "parts_eta":      fmt_date(row.get("Parts ETA Date")),
            "asp_received":   fmt_date(row.get("ASP Received Date & Time")),
            "wo_closed":      fmt_date(row.get("Date & Time WO# Closed")),
            "status":         str(row.get("Status") or ""),
            "failed_reason":  str(row.get("Failed Reason") or ""),
            "remark":         str(row.get("Remark") or ""),
            "city":           str(row.get("City") or ""),
            "product":        str(row.get("Product Category") or ""),
        })
    return data

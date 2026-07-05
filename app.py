from flask import Flask, render_template, request, redirect, url_for, flash
import os
import json
import openpyxl
from datetime import datetime

app = Flask(__name__)
app.secret_key = "lenovo-asp-secret-key"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB limit

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "pdf"}
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "excels", "test-dashboard-file.xlsx")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def fmt_date(val):
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
            "wo":            str(row.get("Lenovo WO") or ""),
            "contact":       str(row.get("Contact") or ""),
            "pic":           str(row.get("PIC") or ""),
            "created_on":    fmt_date(row.get("Created On")),
            "order_date":    fmt_date(row.get("Order Date")),
            "courier_pickup": fmt_date(row.get("Courier Pick Up")),
            "month":         str(row.get("Month") or ""),
            "parts_eta":     fmt_date(row.get("Parts ETA Date")),
            "asp_received":  fmt_date(row.get("ASP Received Date & Time")),
            "wo_closed":     fmt_date(row.get("Date & Time WO# Closed")),
            "status":        str(row.get("Status") or ""),
            "failed_reason": str(row.get("Failed Reason") or ""),
            "remark":        str(row.get("Remark") or ""),
            "city":          str(row.get("City") or ""),
            "product":       str(row.get("Product Category") or ""),
        })
    return data


@app.route("/", methods=["GET", "POST"])
def index():
    wo_data = load_wo_data()
    open_wo   = [w for w in wo_data if w["status"] != "Closed"]
    transit   = [w for w in wo_data if w["status"] in ("Need Additional Part", "ASP Issue")]
    closed_wo = [w for w in wo_data if w["status"] == "Closed"]

    stats = {
        "total":         len(wo_data),
        "total_closed":  len(closed_wo),
        "total_open":    len(open_wo),
        "total_transit": len(transit),
    }

    if request.method == "POST":
        errors = []
        wo_number    = request.form.get("wo_number", "").strip()
        tanggal_part = request.form.get("tanggal_part", "").strip()
        ticket_status = request.form.get("ticket_status", "").strip()

        if not wo_number:
            errors.append("WO Number is required.")
        if not tanggal_part:
            errors.append("Tanggal part diterima oleh ASP is required.")
        if not ticket_status:
            errors.append("Ticket Status is required.")

        if ticket_status in ("Completed", "Completed but Not Solved"):
            if not request.form.get("wo_close_reason"):
                errors.append("If WO Close reason is required.")
        if ticket_status == "Completed but Not Solved":
            if not request.form.get("not_solved_reason"):
                errors.append("If WO close but not solved reason is required.")
        if ticket_status == "Reschedule":
            if not request.form.get("reschedule_by"):
                errors.append("Reschedule by Customer or ASP is required.")
            if not request.form.get("reschedule_date"):
                errors.append("Reschedule Date is required.")
            reschedule_by = request.form.get("reschedule_by", "")
            if reschedule_by == "ASP Defer" and not request.form.get("reschedule_reason_asp"):
                errors.append("Reschedule Reason by ASP Defer is required.")
            if reschedule_by == "Customer Defer" and not request.form.get("reschedule_reason_customer"):
                errors.append("Reschedule Reason by Customer Defer is required.")
        if ticket_status == "WO Canceled":
            if not request.form.get("canceled_reason", "").strip():
                errors.append("WO Canceled Reason is required.")

        uploaded_file = request.files.get("evidence")
        file_saved = None
        if uploaded_file and uploaded_file.filename:
            if allowed_file(uploaded_file.filename):
                from werkzeug.utils import secure_filename
                filename = secure_filename(uploaded_file.filename)
                uploaded_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                file_saved = filename
            else:
                errors.append("Invalid file type. Allowed: PNG, JPG, JPEG, GIF, BMP, WEBP, PDF.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("index.html",
                form_data=request.form,
                active_tab="tab-ticket",
                wo_data_json=json.dumps(wo_data),
                open_wo_json=json.dumps(open_wo),
                transit_json=json.dumps(transit),
                closed_json=json.dumps(closed_wo),
                **stats)

        flash(
            f"Ticket submitted! WO: {wo_number}" + (f" | File: {file_saved}" if file_saved else ""),
            "success"
        )
        return redirect(url_for("index"))

    return render_template("index.html",
        form_data={},
        active_tab="tab-ticket",
        wo_data_json=json.dumps(wo_data),
        open_wo_json=json.dumps(open_wo),
        transit_json=json.dumps(transit),
        closed_json=json.dumps(closed_wo),
        **stats)


if __name__ == "__main__":
    app.run(debug=True)

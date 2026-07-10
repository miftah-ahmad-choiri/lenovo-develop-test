import os
import subprocess
import sys
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app, send_file,
)
from app.services.excel_upload_service import allowed_excel, save_excel_upload, list_excel_uploads

excel_upload_bp = Blueprint("excel_upload", __name__)


def _report_info() -> dict:
    """Return metadata about the compiled report file (if it exists)."""
    excels_dir = current_app.config["EXCELS_DIR"]
    fixed_path = os.path.join(excels_dir, "df_combined_final_report.xlsx")
    if os.path.isfile(fixed_path):
        mtime = os.path.getmtime(fixed_path)
        compiled_at = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        # Find the most-recent timestamped copy (Masterfile_*.xlsx)
        stamped = sorted(
            [f for f in os.listdir(excels_dir) if f.startswith("Masterfile_") and f.endswith(".xlsx")],
            reverse=True,
        )
        latest_stamped = stamped[0] if stamped else None
        return {"exists": True, "compiled_at": compiled_at, "latest_stamped": latest_stamped}
    return {"exists": False, "compiled_at": None, "latest_stamped": None}


@excel_upload_bp.route("/upload-excel", methods=["GET", "POST"])
def upload_excel():
    if request.method == "POST":
        file = request.files.get("excel_file")

        if not file or not file.filename:
            flash("Please choose an Excel file to upload.", "danger")
            return redirect(url_for("excel_upload.upload_excel"))

        if not allowed_excel(file.filename):
            flash("Invalid file type. Allowed: .xlsx, .xls, .csv", "danger")
            return redirect(url_for("excel_upload.upload_excel"))

        saved, error = save_excel_upload(file)
        if error:
            flash(error, "danger")
        else:
            flash(f'File "{saved}" uploaded successfully.', "success")

        return redirect(url_for("excel_upload.upload_excel"))

    files = list_excel_uploads()
    for f in files:
        f["modified_fmt"] = datetime.fromtimestamp(f["modified"]).strftime("%Y-%m-%d %H:%M")

    return render_template("excel_upload.html", files=files, report=_report_info())


@excel_upload_bp.route("/upload-excel/delete/<filename>", methods=["POST"])
def delete_excel(filename):
    from werkzeug.utils import secure_filename
    safe = secure_filename(filename)
    path = os.path.join(current_app.config["EXCEL_UPLOAD_FOLDER"], safe)
    if os.path.isfile(path):
        os.remove(path)
        flash(f'File "{safe}" deleted.', "success")
    else:
        flash("File not found.", "danger")
    return redirect(url_for("excel_upload.upload_excel"))


@excel_upload_bp.route("/upload-excel/reset", methods=["POST"])
def reset_excel():
    """Delete ALL files in the excel upload folder."""
    folder = current_app.config["EXCEL_UPLOAD_FOLDER"]
    deleted = 0
    for fname in os.listdir(folder):
        fpath = os.path.join(folder, fname)
        if os.path.isfile(fpath):
            os.remove(fpath)
            deleted += 1
    flash(f"Reset complete — {deleted} file{'s' if deleted != 1 else ''} deleted.", "success")
    return redirect(url_for("excel_upload.upload_excel"))


@excel_upload_bp.route("/upload-excel/compile", methods=["POST"])
def compile_report():
    """Run the WO Onsite pipeline to regenerate df_combined_final_report.xlsx."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "app.services.wo_onsite.pipeline"],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            flash("Report compiled successfully. Dashboard data has been refreshed.", "success")
        else:
            err = (result.stderr or result.stdout or "Unknown error").strip().splitlines()[-1]
            flash(f"Compile failed: {err}", "danger")
    except subprocess.TimeoutExpired:
        flash("Compile timed out (> 5 min). Please try again.", "danger")
    except Exception as e:
        flash(f"Compile error: {e}", "danger")
    return redirect(url_for("excel_upload.upload_excel"))


@excel_upload_bp.route("/upload-excel/download")
def download_report():
    """Serve the latest timestamped Masterfile export as a download."""
    excels_dir = current_app.config["EXCELS_DIR"]

    # Prefer the latest Masterfile_*.xlsx; fall back to the fixed report
    stamped = sorted(
        [f for f in os.listdir(excels_dir) if f.startswith("Masterfile_") and f.endswith(".xlsx")],
        reverse=True,
    )
    if stamped:
        filepath = os.path.join(excels_dir, stamped[0])
        download_name = stamped[0]
    else:
        filepath = os.path.join(excels_dir, "df_combined_final_report.xlsx")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_name = f"Masterfile_{ts}.xlsx"

    if not os.path.isfile(filepath):
        flash("No compiled report found. Please run Compile Report first.", "danger")
        return redirect(url_for("excel_upload.upload_excel"))

    return send_file(
        filepath,
        as_attachment=True,
        download_name=download_name,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

import os
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app, send_file,
)
from app.services.upload.excel import allowed_excel, save_excel_upload, list_excel_uploads
from app.services.wo_onsite.pipeline import run_pipeline_to_buffer

admin_bp = Blueprint("admin", __name__)


def _report_info() -> dict:
    excels_dir = current_app.config["EXCELS_DIR"]
    fixed_path = os.path.join(excels_dir, "df_combined_final_report.xlsx")
    if os.path.isfile(fixed_path):
        mtime = os.path.getmtime(fixed_path)
        compiled_at = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        stamped = sorted(
            [f for f in os.listdir(excels_dir) if f.startswith("Masterfile_") and f.endswith(".xlsx")],
            reverse=True,
        )
        return {"exists": True, "compiled_at": compiled_at, "latest_stamped": stamped[0] if stamped else None}
    return {"exists": False, "compiled_at": None, "latest_stamped": None}


def _list_masterfiles() -> list:
    excels_dir = current_app.config["EXCELS_DIR"]
    result = []
    for fname in sorted(os.listdir(excels_dir), reverse=True):
        if fname.startswith("Masterfile_") and fname.endswith(".xlsx"):
            fpath = os.path.join(excels_dir, fname)
            stat  = os.stat(fpath)
            result.append({
                "name":         fname,
                "size_kb":      round(stat.st_size / 1024, 1),
                "modified_fmt": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            })
    return result


# ── Dashboard ────────────────────────────────────────────────────────────────

@admin_bp.route("/admin/dashboard", methods=["GET"])
def dashboard():
    return render_template("admin/dashboard.html",
                           portal="admin", active_page="admin_dashboard")


# ── Ticket Management ────────────────────────────────────────────────────────

@admin_bp.route("/admin/tickets", methods=["GET"])
def tickets():
    return render_template("admin/ticket_management.html",
                           portal="admin", active_page="admin_tickets")


# ── Data Import / Export ─────────────────────────────────────────────────────

@admin_bp.route("/admin/data-import", methods=["GET"])
def data_import():
    files = list_excel_uploads()
    for f in files:
        f["modified_fmt"] = datetime.fromtimestamp(f["modified"]).strftime("%Y-%m-%d %H:%M")
    return render_template("admin/data_import.html",
                           files=files, report=_report_info(),
                           portal="admin", active_page="data_import")


@admin_bp.route("/admin/data-import/upload", methods=["POST"])
def data_import_upload():
    file = request.files.get("excel_file")
    if not file or not file.filename:
        flash("Please choose an Excel file to upload.", "danger")
        return redirect(url_for("admin.data_import"))
    if not allowed_excel(file.filename):
        flash("Invalid file type. Allowed: .xlsx, .xls, .csv", "danger")
        return redirect(url_for("admin.data_import"))
    saved, error = save_excel_upload(file)
    if error:
        flash(error, "danger")
    else:
        flash(f'File "{saved}" uploaded successfully.', "success")
    return redirect(url_for("admin.data_import"))


@admin_bp.route("/admin/data-import/delete/<filename>", methods=["POST"])
def data_import_delete(filename):
    from werkzeug.utils import secure_filename
    safe = secure_filename(filename)
    path = os.path.join(current_app.config["EXCEL_UPLOAD_FOLDER"], safe)
    if os.path.isfile(path):
        os.remove(path)
        flash(f'File "{safe}" deleted.', "success")
    else:
        flash("File not found.", "danger")
    return redirect(url_for("admin.data_import"))


@admin_bp.route("/admin/data-import/reset", methods=["POST"])
def data_import_reset():
    folder = current_app.config["EXCEL_UPLOAD_FOLDER"]
    deleted = 0
    for fname in os.listdir(folder):
        fpath = os.path.join(folder, fname)
        if os.path.isfile(fpath):
            os.remove(fpath)
            deleted += 1
    flash(f"Reset complete — {deleted} file{'s' if deleted != 1 else ''} deleted.", "success")
    return redirect(url_for("admin.data_import"))


@admin_bp.route("/admin/data-import/compile", methods=["POST"])
def data_import_compile():
    try:
        buf, filename = run_pipeline_to_buffer()
        return send_file(buf, as_attachment=True, download_name=filename,
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        flash(f"Compile error: {e}", "danger")
        return redirect(url_for("admin.data_import"))


@admin_bp.route("/admin/data-import/download", methods=["GET"])
def data_import_download():
    excels_dir = current_app.config["EXCELS_DIR"]
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
        return redirect(url_for("admin.data_import"))
    return send_file(filepath, as_attachment=True, download_name=download_name,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ── Validation Center ────────────────────────────────────────────────────────

@admin_bp.route("/admin/validation", methods=["GET"])
def validation():
    return render_template("admin/validation_center.html",
                           portal="admin", active_page="validation")


# ── User & ASP Management ────────────────────────────────────────────────────

@admin_bp.route("/admin/users", methods=["GET"])
def users():
    return render_template("admin/user_management.html",
                           portal="admin", active_page="user_mgmt")


# ── System Archive ───────────────────────────────────────────────────────────

@admin_bp.route("/admin/archive", methods=["GET"])
def archive():
    files = list_excel_uploads()
    for f in files:
        f["modified_fmt"] = datetime.fromtimestamp(f["modified"]).strftime("%Y-%m-%d %H:%M")
    return render_template("admin/system_archive.html",
                           masterfiles=_list_masterfiles(),
                           uploaded_files=files,
                           portal="admin", active_page="archive")


@admin_bp.route("/admin/archive/download/masterfile/<filename>", methods=["GET"])
def archive_download(filename):
    from werkzeug.utils import secure_filename
    safe     = secure_filename(filename)
    filepath = os.path.join(current_app.config["EXCELS_DIR"], safe)
    if not os.path.isfile(filepath):
        flash("File not found.", "danger")
        return redirect(url_for("admin.archive"))
    return send_file(filepath, as_attachment=True, download_name=safe,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

import os
import tempfile
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app, send_file, jsonify,
)
from werkzeug.utils import secure_filename
from app.services.upload.excel import allowed_excel, save_excel_upload, list_excel_uploads
from app.services.upload.upload_verification import verify_uploaded_file
from app.services.upload.excel_to_df import (
    load_single_dataframe, DF_LABELS, _KEY_TO_DF,
)
from app.services.wo_onsite.pipeline import run_pipeline_to_buffer
from app.config.pipeline_config import FILE_CATEGORY_CONFIGS

admin_bp = Blueprint("admin", __name__)


def _report_info() -> dict:
    excels_dir = current_app.config["EXCELS_DIR"]
    fixed_path = os.path.join(excels_dir, "df_combined_final_report.xlsx")
    if os.path.isfile(fixed_path):
        mtime = os.path.getmtime(fixed_path)
        compiled_at = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        if os.path.isdir(excels_dir):
            stamped = sorted(
                [f for f in os.listdir(excels_dir) if f.startswith("Masterfile_") and f.endswith(".xlsx")],
                reverse=True,
            )
        else:
            stamped = []
        return {"exists": True, "compiled_at": compiled_at, "latest_stamped": stamped[0] if stamped else None}
    return {"exists": False, "compiled_at": None, "latest_stamped": None}


def _list_masterfiles() -> list:
    excels_dir = current_app.config["EXCELS_DIR"]
    if not os.path.isdir(excels_dir):
        return []
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
    import traceback as _tb
    files = list_excel_uploads()
    upload_folder = current_app.config["EXCEL_UPLOAD_FOLDER"]
    for f in files:
        f["modified_fmt"] = datetime.fromtimestamp(f["modified"]).strftime("%Y-%m-%d %H:%M")
        # Run column-based verification on the already-saved file
        try:
            filepath = os.path.join(upload_folder, f["name"])
            v = verify_uploaded_file(filepath)
            f["file_category"]     = v.get("file_category") or ""
            f["source_file"]       = v.get("source_file") or ""
            f["latest_date"]       = v.get("latest_date") or ""
            f["days_range"]        = v.get("days_range") or ""
            f["validation_status"] = v.get("validation_status") or ""
        except Exception:
            current_app.logger.warning(
                "verify_uploaded_file failed for %s:\n%s", f["name"], _tb.format_exc()
            )
            f["file_category"]     = ""
            f["source_file"]       = ""
            f["latest_date"]       = ""
            f["days_range"]        = ""
            f["validation_status"] = ""

    # Build a lookup: file_category → uploaded file dict (last one wins per category)
    uploaded_by_category = {}
    for f in files:
        if f["file_category"]:
            uploaded_by_category[f["file_category"]] = f

    # One row per known category — merged with uploaded file data if present
    category_rows = []
    for key, cfg in FILE_CATEGORY_CONFIGS.items():
        cat_name = cfg["file_category"]
        uploaded = uploaded_by_category.get(cat_name)
        category_rows.append({
            "category_key":  key,
            "file_category": cat_name,
            "source_file":   cfg["source_file"],
            # from uploaded file (empty strings when nothing uploaded yet)
            "filename":      uploaded["name"]         if uploaded else "",
            "size_kb":       uploaded["size_kb"]      if uploaded else "",
            "modified_fmt":  uploaded["modified_fmt"] if uploaded else "",
            "latest_date":   uploaded["latest_date"]  if uploaded else "",
            "days_range":    uploaded["days_range"]   if uploaded else "",
        })

    try:
        report = _report_info()
    except Exception:
        current_app.logger.error("_report_info ERROR:\n" + _tb.format_exc())
        report = {"exists": False, "compiled_at": None, "latest_stamped": None}
    return render_template("admin/data_import.html",
                           files=files, report=report,
                           category_rows=category_rows,
                           portal="admin", active_page="data_import")


@admin_bp.route("/admin/data-import/verify", methods=["POST"])
def data_import_verify():
    """
    Accepts a multipart file, saves it to a temp location, runs
    verify_uploaded_file(), and returns JSON — no permanent save is done here.
    """
    file = request.files.get("excel_file")
    if not file or not file.filename:
        return jsonify({"ok": False, "error": "No file selected."})
    if not allowed_excel(file.filename):
        return jsonify({"ok": False, "error": "Invalid file type. Allowed: .xlsx, .xls, .csv"})

    safe_name = secure_filename(file.filename)
    # Write to a temp file for inspection
    suffix = "." + safe_name.rsplit(".", 1)[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        file.save(tmp_path)

    try:
        result = verify_uploaded_file(tmp_path)
        result["filename"] = safe_name          # use the user-visible name
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    return jsonify(result)


@admin_bp.route("/admin/data-import/upload", methods=["POST"])
def data_import_upload():
    import shutil, traceback as _tb
    file = request.files.get("excel_file")
    if not file or not file.filename:
        flash("Please choose an Excel file to upload.", "danger")
        return redirect(url_for("admin.data_import"))
    if not allowed_excel(file.filename):
        flash("Invalid file type. Allowed: .xlsx, .xls, .csv", "danger")
        return redirect(url_for("admin.data_import"))

    safe_name = secure_filename(file.filename)
    upload_folder = current_app.config["EXCEL_UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    # ── Step 1: save to a temp file and verify category ──────────────────────
    suffix = "." + safe_name.rsplit(".", 1)[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        file.save(tmp_path)

    try:
        new_result = verify_uploaded_file(tmp_path)
        new_category = new_result.get("file_category") or ""

        # ── Step 2: if category matches an existing file, compare dates ──────
        replaced_name = None
        if new_category:
            for existing_fname in list(os.listdir(upload_folder)):
                if not allowed_excel(existing_fname):
                    continue
                existing_path = os.path.join(upload_folder, existing_fname)
                try:
                    ex_result = verify_uploaded_file(existing_path)
                except Exception:
                    continue
                if ex_result.get("file_category") != new_category:
                    continue

                # Same category found — compare latest_date (format dd-mm-yyyy)
                def _parse_date(d):
                    try:
                        from datetime import datetime as _dt
                        return _dt.strptime(d, "%d-%m-%Y")
                    except Exception:
                        return None

                new_date = _parse_date(new_result.get("latest_date") or "")
                ex_date  = _parse_date(ex_result.get("latest_date") or "")

                if new_date and ex_date and new_date >= ex_date:
                    # New file is newer or equal — delete the old one
                    os.remove(existing_path)
                    replaced_name = existing_fname
                elif new_date and ex_date and new_date < ex_date:
                    # Existing file is newer — reject the upload
                    flash(
                        f'Upload rejected: "{existing_fname}" already covers a '
                        f'later date ({ex_result["latest_date"]}) for category '
                        f'"{new_category}". Delete it first if you want to replace it.',
                        "warning",
                    )
                    return redirect(url_for("admin.data_import"))
                else:
                    # Can't compare dates — keep new, delete old
                    os.remove(existing_path)
                    replaced_name = existing_fname
                break  # only one file per category allowed

        # ── Step 3: move temp file to upload folder ───────────────────────────
        dest_path = os.path.join(upload_folder, safe_name)
        shutil.move(tmp_path, dest_path)
        tmp_path = None  # prevent finally from deleting it again

        if replaced_name:
            flash(
                f'"{safe_name}" uploaded and replaced "{replaced_name}" '
                f'(same category: {new_category}).',
                "success",
            )
        else:
            flash(f'File "{safe_name}" uploaded successfully.', "success")

    except Exception:
        current_app.logger.error("data_import_upload ERROR:\n" + _tb.format_exc())
        flash("Upload failed due to an internal error.", "danger")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    return redirect(url_for("admin.data_import"))


@admin_bp.route("/admin/data-import/delete/<filename>", methods=["POST"])
def data_import_delete(filename):
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
    import traceback as _tb, sys
    try:
        folder = current_app.config["EXCEL_UPLOAD_FOLDER"]
        deleted = 0
        if os.path.isdir(folder):
            for fname in list(os.listdir(folder)):
                if not allowed_excel(fname):
                    continue
                fpath = os.path.join(folder, fname)
                if os.path.isfile(fpath):
                    os.remove(fpath)
                    deleted += 1
        flash(f"Reset complete — {deleted} file{'s' if deleted != 1 else ''} deleted.", "success")
    except Exception:
        tb = _tb.format_exc()
        print("=== data_import_reset ERROR ===", file=sys.stderr)
        print(tb, file=sys.stderr)
        flash(f"Reset failed: {tb.splitlines()[-1]}", "danger")
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


# ── DataFrame Viewer ─────────────────────────────────────────────────────────

@admin_bp.route("/admin/data-import/view/<category_key>", methods=["GET"])
def data_import_view(category_key: str):
    """Render a full-table view for the uploaded file matching *category_key*.
    All rows are sent to the template; pagination and search are handled client-side.
    """
    category_key = category_key.upper()
    if category_key not in FILE_CATEGORY_CONFIGS:
        flash(f'Unknown category "{category_key}".', "danger")
        return redirect(url_for("admin.data_import"))

    df = load_single_dataframe(category_key)
    df_name = _KEY_TO_DF.get(category_key, "")
    label   = DF_LABELS.get(df_name, category_key)
    cfg     = FILE_CATEGORY_CONFIGS[category_key]

    if df is None:
        flash(f'No uploaded file found for category "{label}".', "warning")
        return redirect(url_for("admin.data_import"))

    headers = df.columns.tolist()
    rows    = df.values.tolist()

    return render_template(
        "admin/df_viewer.html",
        df_name=df_name,
        label=label,
        source_file=cfg.get("source_file", ""),
        headers=headers,
        rows=rows,
        total_rows=len(df),
        total_cols=len(headers),
        portal="admin",
        active_page="data_import",
    )


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

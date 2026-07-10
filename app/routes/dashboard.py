import json
from flask import Blueprint, render_template
from app.services.excel_service import load_wo_data

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():
    wo_data = load_wo_data()

    closed   = [w for w in wo_data if w["status"].lower() in ("completed", "closed")]
    open_wo  = [w for w in wo_data if w["status"].lower() not in ("completed", "closed", "cancelled", "canceled")]
    transit  = [w for w in wo_data if w["status_part"] and w["status_part"].lower() == "waiting part"]
    if not transit:
        transit = [w for w in wo_data if "part hold" in w["status"].lower()]

    return render_template(
        "dashboard.html",
        wo_data_json=json.dumps(wo_data),
        transit_json=json.dumps(transit),
        closed_json=json.dumps(closed),
        total=len(wo_data),
        total_closed=len(closed),
        total_open=len(open_wo),
        total_transit=len(transit),
        # onsite stat row reuses same data
        onsite_total=len(wo_data),
        onsite_open=len(open_wo),
        onsite_part_hold=len([w for w in wo_data if "part hold" in w["status"].lower()]),
        onsite_closed=len(closed),
        onsite_json=json.dumps(wo_data),
    )

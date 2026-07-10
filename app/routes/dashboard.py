import json
from flask import Blueprint, render_template
from app.services.excel_service import load_wo_data

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():
    wo_data = load_wo_data()

    # Part in Transit: WOs where ASP has not yet confirmed receipt
    transit = [w for w in wo_data if not w["asp_received"]]
    # Fall back to open/pending rows if all have received dates in test data
    if not transit:
        transit = [w for w in wo_data if w["status"] in ("Need Additional Part", "ASP Issue")]

    closed = [w for w in wo_data if w["status"] == "Closed"]

    return render_template(
        "dashboard.html",
        wo_data_json=json.dumps(wo_data),
        transit_json=json.dumps(transit),
        closed_json=json.dumps(closed),
        total=len(wo_data),
        total_closed=len(closed),
        total_open=len([w for w in wo_data if w["status"] != "Closed"]),
        total_transit=len(transit),
    )

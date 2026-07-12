import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services.excel_report.reader import load_wo_data

asp_bp = Blueprint("asp", __name__)


def _build_wo_context():
    wo_data   = load_wo_data()
    closed_wo = [w for w in wo_data if w["status"].lower() in ("completed", "closed")]
    open_wo   = [w for w in wo_data if w["status"].lower() not in ("completed", "closed", "cancelled", "canceled")]
    transit   = [w for w in wo_data if w.get("status_part") and w["status_part"].lower() == "waiting part"]
    if not transit:
        transit = [w for w in wo_data if "part hold" in w["status"].lower()]
    part_hold = [w for w in wo_data if "part hold" in w["status"].lower()]

    return dict(
        wo_data=wo_data,
        open_wo=open_wo,
        transit=transit,
        closed_wo=closed_wo,
        wo_data_json=json.dumps(wo_data),
        open_wo_json=json.dumps(open_wo),
        transit_json=json.dumps(transit),
        closed_json=json.dumps(closed_wo),
        total=len(wo_data),
        total_closed=len(closed_wo),
        total_open=len(open_wo),
        total_transit=len(transit),
        total_part_hold=len(part_hold),
        onsite_total=len(wo_data),
        onsite_open=len(open_wo),
        onsite_part_hold=len(part_hold),
        onsite_closed=len(closed_wo),
        portal="asp",
    )


@asp_bp.route("/asp/dashboard", methods=["GET"])
def dashboard():
    ctx = _build_wo_context()
    ctx["active_page"] = "asp_dashboard"
    return render_template("asp/dashboard.html", **ctx)


@asp_bp.route("/asp/work-orders", methods=["GET"])
def work_orders():
    ctx = _build_wo_context()
    ctx["active_page"] = "wo_active"
    ctx["active_group"] = "work_orders"
    tab = request.args.get("tab", "active")
    tab_map = {"active": "wo_active", "closed": "wo_closed", "escalated": "wo_escalated", "pending": "wo_pending"}
    ctx["active_page"] = tab_map.get(tab, "wo_active")
    return render_template("asp/work_orders.html", **ctx)


@asp_bp.route("/asp/parts", methods=["GET"])
def parts_management():
    ctx = _build_wo_context()
    ctx["active_group"] = "parts"
    tab = request.args.get("tab", "awaiting")
    tab_map = {"awaiting": "parts_awaiting", "received": "parts_received", "return": "parts_return"}
    ctx["active_page"] = tab_map.get(tab, "parts_awaiting")
    return render_template("asp/parts_management.html", **ctx)


@asp_bp.route("/asp/reschedule", methods=["GET"])
def reschedule():
    ctx = _build_wo_context()
    ctx["active_page"] = "reschedule"
    return render_template("asp/reschedule.html", **ctx)


@asp_bp.route("/asp/escalation", methods=["GET"])
def escalation():
    ctx = _build_wo_context()
    ctx["active_page"] = "escalation"
    return render_template("asp/escalation.html", **ctx)

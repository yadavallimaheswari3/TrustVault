
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.models import AuditLog, User


admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/audit-logs", methods=["GET"])
@login_required
def view_audit_logs():
    if current_user.role != User.ADMIN:
        return jsonify({
            "error": "Admin access required"
        }), 403

    action = request.args.get("action", "").strip()
    outcome = request.args.get("outcome", "").strip()

    query = AuditLog.query

    if action:
        query = query.filter_by(action=action)

    if outcome:
        if outcome not in ("allowed", "denied"):
            return jsonify({
                "error": "Invalid outcome"
            }), 400

        query = query.filter_by(outcome=outcome)

    logs = query.order_by(
        AuditLog.created_at.desc()
    ).limit(100).all()

    results = []

    for log in logs:
        actor = (
            User.query.get(log.actor_id)
            if log.actor_id is not None
            else None
        )

        results.append({
            "id": log.id,
            "actor": actor.email if actor else None,
            "document_id": log.document_id,
            "action": log.action,
            "outcome": log.outcome,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        })

    return jsonify({
        "count": len(results),
        "audit_logs": results,
    }), 200


from flask import (
    Blueprint,
    jsonify,
    request,
    render_template,
    redirect,
    url_for,
    flash,
)
from flask_login import login_required, current_user

from app.models import AuditLog, User, Document
from app.extensions import db
from app.audit import record_audit_event

admin_bp = Blueprint("admin", __name__)


def admin_required():
    return (
        current_user.is_authenticated
        and current_user.role == User.ADMIN
    )


@admin_bp.route("/admin/dashboard", methods=["GET"])
@login_required
def admin_dashboard():

    if not admin_required():
        record_audit_event(
            action="admin_access",
            outcome="denied",
            details="Unauthorized attempt to access Admin dashboard",
        )
        return jsonify({"error": "Admin access required"}), 403

    total_users = User.query.count()
    total_documents = Document.query.count()

    admin_count = User.query.filter_by(role=User.ADMIN).count()
    owner_count = User.query.filter_by(role=User.OWNER).count()
    viewer_count = User.query.filter_by(role=User.VIEWER).count()

    recent_activities = AuditLog.query.order_by(
        AuditLog.created_at.desc()
    ).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_documents=total_documents,
        admin_count=admin_count,
        owner_count=owner_count,
        viewer_count=viewer_count,
        recent_activities=recent_activities,
    )


@admin_bp.route("/admin/users", methods=["GET"])
@login_required
def manage_users():

    if not admin_required():
        record_audit_event(
            action="admin_access",
            outcome="denied",
            details="Unauthorized attempt to access user management",
        )
        return jsonify({"error": "Admin access required"}), 403

    users = User.query.order_by(User.created_at.desc()).all()

    return render_template("admin/users.html", users=users)


@admin_bp.route("/admin/users/<int:user_id>/role", methods=["POST"])
@login_required
def change_user_role(user_id):

    if not admin_required():
        record_audit_event(
            action="role_change",
            outcome="denied",
            details="Non-admin attempted to change a user role",
        )
        return jsonify({"error": "Admin access required"}), 403

    user = db.session.get(User, user_id)

    if user is None:
        record_audit_event(
            action="role_change",
            outcome="denied",
            details=f"Attempt to change role of missing user ID {user_id}",
        )
        flash("User not found.", "error")
        return redirect(url_for("admin.manage_users"))

    new_role = request.form.get("role", "").strip().lower()

    allowed_roles = (
        User.ADMIN,
        User.OWNER,
        User.VIEWER,
    )

    if new_role not in allowed_roles:
        record_audit_event(
            action="role_change",
            outcome="denied",
            details=f"Invalid role selected for user {user.email}",
        )
        flash("Invalid role selected.", "error")
        return redirect(url_for("admin.manage_users"))

    if user.id == current_user.id:
        record_audit_event(
            action="role_change",
            outcome="denied",
            details="Admin attempted to change their own role",
        )
        flash("You cannot change your own role.", "error")
        return redirect(url_for("admin.manage_users"))

    if user.role == User.ADMIN and new_role != User.ADMIN:
        admin_count = User.query.filter_by(role=User.ADMIN).count()

        if admin_count <= 1:
            record_audit_event(
                action="role_change",
                outcome="denied",
                details="Attempt to demote the last Admin account",
            )
            flash("You cannot remove the last Admin account.", "error")
            return redirect(url_for("admin.manage_users"))

    old_role = user.role

    if old_role == new_role:
        flash("User already has this role.", "info")
        return redirect(url_for("admin.manage_users"))

    try:
        user.role = new_role

        audit = AuditLog(
            actor_id=current_user.id,
            action="role_change",
            outcome="success",
            details=(
                f"Admin changed {user.email} role "
                f"from {old_role} to {new_role}."
            ),
            ip_address=request.remote_addr,
        )

        db.session.add(audit)
        db.session.commit()

        flash("User role updated successfully.", "success")

    except Exception:
        db.session.rollback()
        flash("Could not update user role.", "error")

    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/admin/audit-logs", methods=["GET"])
@login_required
def view_audit_logs():

    if not admin_required():
        record_audit_event(
            action="admin_access",
            outcome="denied",
            details="Unauthorized attempt to access audit logs",
        )
        return jsonify({"error": "Admin access required"}), 403

    action = request.args.get("action", "").strip()
    outcome = request.args.get("outcome", "").strip()

    query = AuditLog.query

    if action:
        query = query.filter_by(action=action)

    if outcome:
        if outcome not in ("allowed", "denied", "success"):
            return jsonify({"error": "Invalid outcome"}), 400

        query = query.filter_by(outcome=outcome)

    logs = query.order_by(
        AuditLog.created_at.desc()
    ).limit(100).all()

    results = []

    for log in logs:
        actor = (
            db.session.get(User, log.actor_id)
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


@admin_bp.route("/admin/audit-logs/page", methods=["GET"])
@login_required
def audit_logs_page():

    if not admin_required():
        record_audit_event(
            action="admin_access",
            outcome="denied",
            details="Unauthorized attempt to access audit log page",
        )
        return jsonify({"error": "Admin access required"}), 403

    action = request.args.get("action", "").strip()
    outcome = request.args.get("outcome", "").strip()

    query = AuditLog.query

    if action:
        query = query.filter_by(action=action)

    if outcome in ("allowed", "denied", "success"):
        query = query.filter_by(outcome=outcome)
    elif outcome:
        outcome = ""

    audit_logs = query.order_by(
        AuditLog.created_at.desc()
    ).limit(100).all()

    results = []

    for log in audit_logs:
        actor = (
            db.session.get(User, log.actor_id)
            if log.actor_id is not None
            else None
        )

        results.append({
            "action": log.action,
            "actor": actor.email if actor else None,
            "outcome": log.outcome,
            "document_id": log.document_id,
            "details": log.details,
            "created_at": log.created_at,
        })

    return render_template(
        "admin/audit_logs.html",
        audit_logs=results,
        selected_action=action,
        selected_outcome=outcome,
    )

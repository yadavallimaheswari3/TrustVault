
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, Document, DocumentPermission
from app.audit import record_audit_event

permissions_bp = Blueprint("permissions", __name__)


@permissions_bp.route(
    "/documents/<int:document_id>/permissions",
    methods=["POST"],
)
@login_required
def grant_permission(document_id):
    document = db.session.get(Document, document_id)

    if document is None:
        record_audit_event(
            action="permission_grant",
            outcome="denied",
            document_id=document_id,
            details="Document not found",
        )
        return jsonify({"error": "Document not found"}), 404

    if document.owner_id != current_user.id:
        record_audit_event(
            action="permission_grant",
            outcome="denied",
            document_id=document.id,
            details="Only the document owner can grant permission",
        )
        return jsonify({"error": "Only the owner can grant permission"}), 403

    data = request.get_json(silent=True) or request.form

    email = data.get("email", "").strip().lower()
    permission_type = data.get("permission", "").strip().lower()

    if not email or permission_type not in ("read", "edit"):
        return jsonify({"error": "Valid email and permission are required"}), 400

    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"error": "User not found"}), 404

    if user.id == current_user.id:
        return jsonify({"error": "Owner already has access"}), 400

    existing_permission = DocumentPermission.query.filter_by(
        document_id=document.id,
        user_id=user.id,
    ).first()

    if existing_permission:
        existing_permission.permission = permission_type
        existing_permission.granted_by_id = current_user.id
    else:
        new_permission = DocumentPermission(
            document_id=document.id,
            user_id=user.id,
            permission=permission_type,
            granted_by_id=current_user.id,
        )
        db.session.add(new_permission)

    db.session.commit()

    record_audit_event(
        action="permission_grant",
        outcome="allowed",
        document_id=document.id,
        details=f"{permission_type} permission granted to {email}",
    )

    return jsonify({"message": "Permission granted successfully"}), 200


@permissions_bp.route(
    "/documents/<int:document_id>/permissions/<int:user_id>",
    methods=["DELETE"],
)
@login_required
def revoke_permission(document_id, user_id):
    document = db.session.get(Document, document_id)

    if document is None:
        record_audit_event(
            action="permission_revoke",
            outcome="denied",
            document_id=document_id,
            details="Document not found",
        )
        return jsonify({"error": "Document not found"}), 404

    if document.owner_id != current_user.id:
        record_audit_event(
            action="permission_revoke",
            outcome="denied",
            document_id=document.id,
            details="Only the document owner can revoke permission",
        )
        return jsonify({"error": "Only the owner can revoke permission"}), 403

    permission = DocumentPermission.query.filter_by(
        document_id=document.id,
        user_id=user_id,
    ).first()

    if permission is None:
        return jsonify({"error": "Permission not found"}), 404

    db.session.delete(permission)
    db.session.commit()

    record_audit_event(
        action="permission_revoke",
        outcome="allowed",
        document_id=document.id,
        details=f"Permission revoked from user {user_id}",
    )

    return jsonify({"message": "Permission revoked successfully"}), 200

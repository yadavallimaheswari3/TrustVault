
from flask import request
from flask_login import current_user

from app.extensions import db
from app.models import AuditLog


def record_audit_event(
    action,
    outcome,
    document_id=None,
    details=None,
):
    actor_id = (
        current_user.id
        if current_user.is_authenticated
        else None
    )

    audit_entry = AuditLog(
        actor_id=actor_id,
        document_id=document_id,
        action=action,
        outcome=outcome,
        details=details,
        ip_address=request.remote_addr,
    )

    db.session.add(audit_entry)
    db.session.commit()

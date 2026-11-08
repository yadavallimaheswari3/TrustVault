
import hashlib
import hmac
import json
from datetime import datetime, timezone

from flask import current_app, request
from flask_login import current_user

from app.extensions import db
from app.models import AuditLog


def _timestamp_for_hash(value):
    """Normalize timestamps so SQLite produces consistent hashes."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)

    return value.isoformat()


def _calculate_event_hash(event, secret_key):
    event_data = {
        "id": event.id,
        "actor_id": event.actor_id,
        "document_id": event.document_id,
        "action": event.action,
        "outcome": event.outcome,
        "details": event.details,
        "ip_address": event.ip_address,
        "created_at": _timestamp_for_hash(event.created_at),
        "previous_hash": event.previous_hash,
    }

    message = json.dumps(
        event_data,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hmac.new(
        secret_key.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()


def record_audit_event(action, outcome, document_id=None, details=None):
    secret_key = current_app.config["SECRET_KEY"]

    actor_id = current_user.id if current_user.is_authenticated else None

    previous_event = (
        AuditLog.query
        .filter(AuditLog.event_hash.isnot(None))
        .order_by(AuditLog.id.desc())
        .first()
    )

    audit_entry = AuditLog(
        actor_id=actor_id,
        document_id=document_id,
        action=action,
        outcome=outcome,
        details=details,
        ip_address=request.remote_addr,
        created_at=datetime.now(timezone.utc),
        previous_hash=(
            previous_event.event_hash if previous_event else None
        ),
    )

    db.session.add(audit_entry)
    db.session.flush()

    audit_entry.event_hash = _calculate_event_hash(
        audit_entry,
        secret_key,
    )

    db.session.commit()



def verify_audit_chain():
    """Verify the signed audit history after its legacy-record boundary."""
    secret_key = current_app.config["SECRET_KEY"]

    events = AuditLog.query.order_by(AuditLog.id.asc()).all()

    # Older records before the first signed event are legacy records.
    first_signed_index = next(
        (i for i, event in enumerate(events) if event.event_hash),
        None,
    )

    if first_signed_index is None:
        return True

    signed_events = events[first_signed_index:]
    expected_previous_hash = None

    for event in signed_events:
        # Unsigned records after signing began are not accepted.
        if not event.event_hash:
            return False

        if event.previous_hash != expected_previous_hash:
            return False

        expected_hash = _calculate_event_hash(event, secret_key)

        if not hmac.compare_digest(event.event_hash, expected_hash):
            return False

        expected_previous_hash = event.event_hash

    return True

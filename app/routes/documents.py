
from flask import Blueprint, abort, current_app, send_from_directory
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Document
from app.permissions import can_view_document
from app.audit import record_audit_event

documents_bp = Blueprint("documents", __name__)


@documents_bp.route("/documents/<int:document_id>/download")
@login_required
def download_document(document_id):
    document = db.session.get(Document, document_id)

    if document is None:
        record_audit_event(
            action="download",
            outcome="denied",
            details="Document not found",
        )
        abort(404)

    if not can_view_document(current_user, document):
        record_audit_event(
            action="download",
            outcome="denied",
            document_id=document.id,
            details="User does not have permission",
        )
        abort(403)

    record_audit_event(
        action="download",
        outcome="allowed",
        document_id=document.id,
        details="User authorized to download document",
    )

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        document.storage_key,
        as_attachment=True,
        download_name=document.original_filename,
    )

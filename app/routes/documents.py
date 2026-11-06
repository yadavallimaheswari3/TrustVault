from datetime import date
from pathlib import Path
import uuid

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    request,
    send_from_directory,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Document, User
from app.permissions import can_view_document
from app.audit import record_audit_event

documents_bp = Blueprint("documents", __name__)

MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg",
}


@documents_bp.route("/documents/upload", methods=["POST"])
@login_required
def upload_document():
    if current_user.role != User.OWNER:
        record_audit_event(
            action="upload",
            outcome="denied",
            details="Only document owners can upload files",
        )
        return jsonify({"error": "Only owners can upload files"}), 403

    uploaded_file = request.files.get("file")

    if uploaded_file is None or not uploaded_file.filename:
        return jsonify({"error": "Please select a file"}), 400

    original_filename = secure_filename(uploaded_file.filename)
    extension = Path(original_filename).suffix.lower()

    if not original_filename or extension not in ALLOWED_EXTENSIONS:
        record_audit_event(
            action="upload",
            outcome="denied",
            details="Invalid file type",
        )
        return jsonify({"error": "File type not allowed"}), 400

    file_data = uploaded_file.stream.read(MAX_FILE_SIZE + 1)

    if len(file_data) > MAX_FILE_SIZE:
        record_audit_event(
            action="upload",
            outcome="denied",
            details="File exceeds 10 MB limit",
        )
        return jsonify({"error": "File size exceeds 10 MB"}), 413

    category = request.form.get("category", "").strip()

    if len(category) > 100:
        return jsonify({"error": "Category is too long"}), 400

    storage_key = uuid.uuid4().hex + extension

    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)

    file_path = upload_folder / storage_key
    file_path.write_bytes(file_data)

    document = Document(
        owner_id=current_user.id,
        original_filename=original_filename,
        storage_key=storage_key,
        category=category or None,
        file_size=len(file_data),
    )

    try:
        db.session.add(document)
        db.session.commit()
    except Exception:
        db.session.rollback()
        file_path.unlink(missing_ok=True)
        raise

    record_audit_event(
        action="upload",
        outcome="allowed",
        document_id=document.id,
        details=f"Document uploaded: {original_filename}",
    )

    return jsonify({
        "message": "Document uploaded successfully",
        "document_id": document.id,
    }), 201


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
@documents_bp.route("/documents/search", methods=["GET"])
@login_required
def search_documents():
    name = request.args.get("name", "").strip().lower()
    owner_email = request.args.get("owner", "").strip().lower()
    category = request.args.get("category", "").strip().lower()
    date_filter = request.args.get("date", "").strip()

    search_date = None

    if date_filter:
        try:
            search_date = date.fromisoformat(date_filter)
        except ValueError:
            return jsonify({"error": "Date must be YYYY-MM-DD"}), 400

    documents = Document.query.order_by(
        Document.uploaded_at.desc()
    ).all()

    results = []

    for document in documents:
        if not can_view_document(current_user, document):
            continue

        if name and name not in document.original_filename.lower():
            continue

        if owner_email and owner_email not in document.owner.email.lower():
            continue

        if category and category not in (document.category or "").lower():
            continue

        if search_date and document.uploaded_at.date() != search_date:
            continue

        results.append({
            "id": document.id,
            "name": document.original_filename,
            "owner": document.owner.email,
            "category": document.category,
            "uploaded_at": document.uploaded_at.isoformat(),
            "file_size": document.file_size,
        })

    return jsonify({
        "count": len(results),
        "documents": results,
    }), 200
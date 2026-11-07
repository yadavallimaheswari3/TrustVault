
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
from app.models import Document, DocumentPermission, User
from app.permissions import can_view_document, can_edit_document
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


@documents_bp.route(
    "/documents/<int:document_id>",
    methods=["PATCH"],
)
@login_required
def edit_document(document_id):
    document = db.session.get(Document, document_id)

    if document is None:
        record_audit_event(
            action="edit",
            outcome="denied",
            document_id=document_id,
            details="Document not found",
        )
        return jsonify({"error": "Document not found"}), 404

    if not can_edit_document(current_user, document):
        record_audit_event(
            action="edit",
            outcome="denied",
            document_id=document.id,
            details="User does not have edit permission",
        )
        return jsonify({"error": "Permission denied"}), 403

    data = request.get_json(silent=True) or {}

    new_name = data.get("name")
    new_category = data.get("category")

    if new_name is None and new_category is None:
        return jsonify({"error": "No changes provided"}), 400

    if new_name is not None:
        if not isinstance(new_name, str):
            return jsonify({"error": "Invalid document name"}), 400

        new_name = secure_filename(new_name)

        if not new_name or len(new_name) > 255:
            return jsonify({"error": "Invalid document name"}), 400

        document.original_filename = new_name

    if new_category is not None:
        if not isinstance(new_category, str):
            return jsonify({"error": "Invalid category"}), 400

        new_category = new_category.strip()

        if len(new_category) > 100:
            return jsonify({"error": "Category is too long"}), 400

        document.category = new_category or None

    db.session.commit()

    record_audit_event(
        action="edit",
        outcome="allowed",
        document_id=document.id,
        details="Document details updated",
    )

    return jsonify({"message": "Document updated successfully"}), 200


@documents_bp.route(
    "/documents/<int:document_id>",
    methods=["DELETE"],
)
@login_required
def delete_document(document_id):
    document = db.session.get(Document, document_id)

    if document is None:
        record_audit_event(
            action="delete",
            outcome="denied",
            document_id=document_id,
            details="Document not found",
        )
        return jsonify({"error": "Document not found"}), 404

    if document.owner_id != current_user.id:
        record_audit_event(
            action="delete",
            outcome="denied",
            document_id=document.id,
            details="Only the owner can delete documents",
        )
        return jsonify({
            "error": "Only the owner can delete documents"
        }), 403

    file_path = (
        Path(current_app.config["UPLOAD_FOLDER"])
        / document.storage_key
    )

    try:
        if file_path.exists():
            file_path.unlink()
            DocumentPermission.query.filter_by(
            document_id=document.id
        ).delete(synchronize_session=False)

        db.session.delete(document)
        db.session.commit()


    except Exception:
        db.session.rollback()
        raise

    record_audit_event(
        action="delete",
        outcome="allowed",
        document_id=None,
        details=f"Document {document.id} deleted by owner",
    )

    return jsonify({
        "message": "Document deleted successfully"
    }), 200


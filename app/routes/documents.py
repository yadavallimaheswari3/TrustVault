
from datetime import date
from pathlib import Path
from io import BytesIO
import uuid
import zipfile

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    request,
    send_file,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Document, DocumentPermission, User
from app.permissions import can_view_document, can_edit_document
from app.audit import record_audit_event
from app.storage import upload_file, download_file, delete_file


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


def validate_file_content(filename, file_data):
    """Check that uploaded content matches its allowed file extension."""

    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        return file_data.startswith(b"%PDF-")

    if extension == ".png":
        return file_data.startswith(b"\x89PNG\r\n\x1a\n")

    if extension in {".jpg", ".jpeg"}:
        return file_data.startswith(b"\xff\xd8\xff")

    if extension == ".doc":
        return file_data.startswith(
            bytes.fromhex("D0CF11E0A1B11AE1")
        )

    if extension == ".docx":
        try:
            with zipfile.ZipFile(BytesIO(file_data)) as archive:
                names = archive.namelist()
                return (
                    "[Content_Types].xml" in names
                    and "word/document.xml" in names
                )
        except (zipfile.BadZipFile, OSError):
            return False

    if extension == ".txt":
        try:
            file_data.decode("utf-8-sig")
            return b"\x00" not in file_data
        except UnicodeDecodeError:
            return False

    return False


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

    if not original_filename:
        return jsonify({"error": "Invalid filename"}), 400

    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        record_audit_event(
            action="upload",
            outcome="denied",
            details="Invalid file extension",
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

    if not file_data:
        return jsonify({"error": "The selected file is empty"}), 400

    if not validate_file_content(original_filename, file_data):
        record_audit_event(
            action="upload",
            outcome="denied",
            details="File content does not match its extension",
        )
        return jsonify({"error": "Invalid file content"}), 400

    category = request.form.get("category", "").strip()

    if len(category) > 100:
        return jsonify({"error": "Category is too long"}), 400

    storage_key = uuid.uuid4().hex + extension

    document = Document(
        owner_id=current_user.id,
        original_filename=original_filename,
        storage_key=storage_key,
        category=category or None,
        file_size=len(file_data),
    )

    try:
        upload_file(
            storage_key,
            file_data,
            uploaded_file.mimetype or "application/octet-stream",
        )

        db.session.add(document)
        db.session.commit()

    except Exception:
        db.session.rollback()

        try:
            delete_file(storage_key)
        except Exception:
            current_app.logger.exception(
                "Could not clean up uploaded cloud file."
            )

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

    try:
        file_data = download_file(document.storage_key)
    except Exception:
        current_app.logger.exception(
            "Could not download document from cloud storage: %s",
            document.id,
        )
        abort(404)

    record_audit_event(
        action="download",
        outcome="allowed",
        document_id=document.id,
        details="Authorized document download",
    )

    return send_file(
        BytesIO(file_data),
        as_attachment=True,
        download_name=document.original_filename,
        mimetype="application/octet-stream",
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
            return jsonify({
                "error": "Date must be YYYY-MM-DD"
            }), 400

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


@documents_bp.route("/documents/<int:document_id>", methods=["PATCH"])
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

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    record_audit_event(
        action="edit",
        outcome="success",
        document_id=document.id,
        details="Document details updated",
    )

    return jsonify({
        "message": "Document updated successfully"
    }), 200


@documents_bp.route("/documents/<int:document_id>", methods=["DELETE"])
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

    deleted_document_id = document.id
    storage_key = document.storage_key

    try:
        DocumentPermission.query.filter_by(
            document_id=deleted_document_id
        ).delete(synchronize_session=False)

        db.session.delete(document)
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    try:
        delete_file(storage_key)
    except Exception:
        current_app.logger.exception(
            "Could not remove deleted cloud document: %s",
            deleted_document_id,
        )

    record_audit_event(
        action="delete",
        outcome="allowed",
        document_id=None,
        details=f"Document {deleted_document_id} deleted by owner",
    )

    return jsonify({
        "message": "Document deleted successfully"
    }), 200

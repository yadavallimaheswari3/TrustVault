
from flask import Blueprint, jsonify, render_template
from flask_login import login_required, current_user

from app.models import Document
from app.permissions import can_view_document

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index():
    all_documents = Document.query.order_by(
        Document.uploaded_at.desc()
    ).all()

    accessible_documents = [
        document
        for document in all_documents
        if can_view_document(current_user, document)
    ]

    my_documents = [
        document
        for document in accessible_documents
        if document.owner_id == current_user.id
    ]

    shared_documents = [
        document
        for document in accessible_documents
        if document.owner_id != current_user.id
    ]

    recent_documents = accessible_documents[:5]

    return render_template(
        "index.html",
        documents=accessible_documents,
        total_documents=len(accessible_documents),
        my_documents_count=len(my_documents),
        shared_documents_count=len(shared_documents),
        recent_documents=recent_documents,
    )


@main_bp.route("/health")
def health():
    return jsonify(status="ok")

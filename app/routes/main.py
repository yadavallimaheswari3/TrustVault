from app.permissions import can_view_document
from flask import Blueprint, jsonify, render_template
from flask_login import login_required, current_user
from app.models import Document
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index():
    all_documents = Document.query.all()

    visible_documents = [
        document
        for document in all_documents
        if can_view_document(current_user, document)
    ]

    return render_template(
        "index.html",
        documents=visible_documents,
    )

@main_bp.route("/health")
def health():
    return jsonify(status="ok")
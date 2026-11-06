from app.models import DocumentPermission


def can_view_document(user, document):
    # The document owner can always view their document.
    if document.owner_id == user.id:
        return True

    # Check whether this user has read or edit permission.
    permission = DocumentPermission.query.filter_by(
        document_id=document.id,
        user_id=user.id,
    ).first()

    return permission is not None and permission.permission in (
        "read",
        "edit",
    )


def can_edit_document(user, document):
    # The document owner can always edit their document.
    if document.owner_id == user.id:
        return True

    # Check whether this user has edit permission.
    permission = DocumentPermission.query.filter_by(
        document_id=document.id,
        user_id=user.id,
        permission="edit",
    ).first()

    return permission is not None
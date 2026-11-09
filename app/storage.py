
from flask import current_app
from supabase import create_client


def get_storage_client():
    url = current_app.config.get("SUPABASE_URL")
    secret_key = current_app.config.get("SUPABASE_SECRET_KEY")

    if not url or not secret_key:
        raise RuntimeError("Supabase storage configuration is missing.")

    return create_client(url, secret_key)


def upload_file(storage_key, file_bytes, content_type):
    client = get_storage_client()
    bucket = current_app.config["SUPABASE_BUCKET"]

    return client.storage.from_(bucket).upload(
        path=storage_key,
        file=file_bytes,
        file_options={"content-type": content_type},
    )


def download_file(storage_key):
    client = get_storage_client()
    bucket = current_app.config["SUPABASE_BUCKET"]

    return client.storage.from_(bucket).download(storage_key)


def delete_file(storage_key):
    client = get_storage_client()
    bucket = current_app.config["SUPABASE_BUCKET"]

    return client.storage.from_(bucket).remove([storage_key])

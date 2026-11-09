
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def get_default_config():
    return {
        "SECRET_KEY": os.environ.get("SECRET_KEY"),
        "UPLOAD_FOLDER": os.environ.get("UPLOAD_FOLDER") or str(BASE_DIR / "storage"),
        "SQLALCHEMY_DATABASE_URI": os.environ.get(
            "DATABASE_URL",
            f"sqlite:///{BASE_DIR / 'trustvault.db'}"
        ),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "pool_pre_ping": True,
            "pool_recycle": 300,
        },
        "SUPABASE_URL": os.environ.get("SUPABASE_URL"),
        "SUPABASE_SECRET_KEY": os.environ.get("SUPABASE_SECRET_KEY"),
        "SUPABASE_BUCKET": os.environ.get(
            "SUPABASE_BUCKET", "trustvault-documents"
        ),
    }

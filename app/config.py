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
    }
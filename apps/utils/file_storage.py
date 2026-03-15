import os
import shutil
from fastapi import UploadFile
from typing import BinaryIO
from uuid import uuid4
from pathlib import Path
import logging

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")  
UPLOAD_BASE = "uploads"

logger = logging.getLogger(__name__)

UPLOAD_BASE = "uploads"


def ensure_dirs():
    for folder in ["cv", "generated", "cover", "reviews"]:
        os.makedirs(f"{UPLOAD_BASE}/{folder}", exist_ok=True)

ensure_dirs()

def save_uploaded_file(file: UploadFile, folder: str, user_id: str) -> str:
    """
    Save uploaded file to 'folder/<user_id>/' and return full path.
    """
    # Ensure user folder exists
    user_folder = os.path.join(folder, user_id)
    os.makedirs(user_folder, exist_ok=True)

    file_path = os.path.join(user_folder, file.filename)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path


def save_bytes_file(content: bytes | BinaryIO, folder: str, user_id: str, ext: str = ".pdf") -> str:
    filename = f"{uuid4()}{ext}"
    rel_path = f"{folder}/{user_id}/{filename}"
    full_path = f"{UPLOAD_BASE}/{rel_path}"

    os.makedirs(os.path.dirname(full_path),exist_ok=True)

    if isinstance(content, bytes):
        with open(full_path, "wb") as f:
            f.write(content)
    else: 
        with open(full_path, "wb") as f:
            shutil.copyfileobj(content, f)

    return rel_path




def get_file_url(rel_path: str) -> str:
    """
    Convert a relative file path to a URL that can be served publicly.
    Adjust UPLOAD_BASE according to your static folder setup.
    """
    UPLOAD_BASE = "uploads" 
    DOMAIN = os.getenv("APP_DOMAIN", "http://localhost:8000")
    return f"{DOMAIN}/{UPLOAD_BASE}/{rel_path}"




def delete_file(relative_path: str) -> bool:
    """
    DB-তে সেভ করা relative path থেকে ফাইল ডিলিট করে
    Returns: True if deleted successfully, False otherwise
    """
    if not relative_path:
        return False

    full_path = Path("uploads") / relative_path.lstrip("/")

    if full_path.exists():
        try:
            full_path.unlink()
            logger.info(f"File deleted: {relative_path}")
            return True
        except Exception as e:
            logger.warning(f"Failed to delete file {relative_path}: {str(e)}")
            return False
    else:
        logger.warning(f"File not found for deletion: {relative_path}")
        return False
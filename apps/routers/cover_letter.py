from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from uuid import UUID
import logging
from datetime import datetime

from ..database import get_db
from ..models.user import User
from ..models.cv import CV, CoverLetter
from ..schemas.cover_letter_schema import (
    CoverLetterGenerateRequest,
    CoverLetterResponse
)
from ..authentication.oauth import get_current_user
from ..utils.file_storage import save_bytes_to_file, get_file_url

# ধরে নিচ্ছি তোমার AI cover letter generator ফাংশন আছে
# যদি না থাকে তাহলে placeholder বা তোমার আসল ফাংশন ব্যবহার করো
from apps.ai.app.cover_letter_generator import generate_cover_letter_content  # তোমার AI ফাংশন

router = APIRouter(prefix="/cover-letter", tags=["Cover Letter"])

logger = logging.getLogger(__name__)
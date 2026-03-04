from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from uuid import UUID
import logging
from datetime import datetime
from ..database import get_db
from ..models.users_model import User
from ..models.cv_model import CV, CoverLetter
from ..schemas.cover_letter_schema import CoverLetterGenerateRequest, CoverLetterResponse
from ..authentication.users_oauth import get_current_user
from ..utils.file_storage import save_bytes_file, get_file_url
from apps.ai.app.cover_letter_generator import generate_cover_letter

router = APIRouter(
    prefix="/cover-letter", 
    tags=["Cover Letter"]
)

logger = logging.getLogger(__name__)

@router.post("/generate", response_model=CoverLetterResponse)
async def generate_cover_letter_endpoint(
    req: CoverLetterGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    cv = db.query(CV).filter(
        CV.id == req.cv_id,
        CV.user_id == current_user.id
    ).first()

    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found or not yours."
        )

    cv_data = {
        "personal_details": getattr(cv.user, "personal_details", {}),
        "work_experience": cv.work_experience or [],
        "education": cv.education or [],
        "it_skills": cv.it_skills or [],
        "language_skills": cv.language_skills or []
    }

    cover_text = await generate_cover_letter(
        cv_data=cv_data,
        job_description=req.job_description,
        language=req.language,
        user_name=current_user.full_name,
        tone=req.tone,
        length=req.length
    )

    cover_letter = CoverLetter(
        user_id=current_user.id,
        cv_id=req.cv_id,
        title=req.title,
        content=cover_text,
        language=req.language
    )

    db.add(cover_letter)
    db.commit()
    db.refresh(cover_letter)

    return cover_letter
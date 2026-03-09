from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from uuid import UUID
import logging
from ..database import get_db
from ..models.users_model import User
from ..models.cv_model import CV, CoverLetter, CVForm
from ..schemas.cover_letter_schema import CoverLetterGenerateRequest, CoverLetterResponse
from ..authentication.users_oauth import get_current_user
from ...apps.ai.app.cover_letter_generator import generate_cover_letter

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
    """
    Generate a personalized cover letter based on user's CV form data.
    """
    cv = db.query(CV).filter(
        CV.id == req.cv_id,
        CV.user_id == current_user.id
    ).first()

    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found or not owned by you."
        )
    
    cv_form = db.query(CVForm).filter(
        CVForm.user_id == current_user.id
    ).first()

    if not cv_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No CV form data found for this user."
        )
    
    cv_data = {
        "personal_details": cv_form.personal_details or {},
        "education": cv_form.education or [],
        "work_experience": cv_form.employment or [], 
        "language_skills": cv_form.languages or [],
        "it_skills": cv_form.skills or [],
        "activities": cv_form.activities or []
    }

    personal_details = cv_form.personal_details or {}
    full_name = (
        personal_details.get("full_name")
        or personal_details.get("name")
        or current_user.full_name
        or "Candidate"
    )

    cover_text = await generate_cover_letter(
        cv_data=cv_data,
        job_description=req.job_description,
        language=req.language,
        user_name=full_name
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

    return CoverLetterResponse(
        id=cover_letter.id,
        cv_id=cover_letter.cv_id,
        content=cover_letter.content,
        file_url=None,
        language=cover_letter.language,
        created_at=cover_letter.created_at
    )


@router.get("/{id}", response_model=CoverLetterResponse)
async def get_cover_letter(
    id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Retrieve a specific cover letter by ID (only if owned by the user).
    """
    cover = db.query(CoverLetter).filter(
        CoverLetter.id == id,
        CoverLetter.user_id == current_user.id
    ).first()

    if not cover:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cover letter not found or not owned by you."
        )

    return CoverLetterResponse.from_orm(cover)
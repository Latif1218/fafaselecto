from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Form, File
from sqlalchemy.orm import Session
from typing import Annotated
from uuid import UUID
import logging
import uuid
from ..database import get_db
from ..models.users_model import User
from ..models.cv_model import CV, CoverLetter, CVForm
from ..schemas.cover_letter_schema import CoverLetterGenerateRequest, CoverLetterResponse
from ..authentication.users_oauth import get_current_user
from apps.ai.app.cover_letter_generator import generate_cover_letter
import os

router = APIRouter(
    prefix="/cover-letter", 
    tags=["Cover Letter"]
)

logger = logging.getLogger(__name__)


UPLOAD_DIR = "uploads/cv"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/generate", response_model=CoverLetterResponse)
async def generate_cover_letter_endpoint(
    job_description: str = Form(...),
    job_link: str | None = Form(None),
    language: str = Form("en"),
    title: str = Form("Cover Letter"),
    cv_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    """
    Generate cover letter from uploaded CV
    """

    file_ext = cv_file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    with open(file_path, "wb") as buffer:
        buffer.write(await cv_file.read())

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
        job_description=job_description,
        job_link=job_link,
        language=language,
        user_name=full_name
    )

    cover_letter = CoverLetter(
        user_id=current_user.id,
        title=title,
        job_description=job_description,
        job_link=job_link,
        content=cover_text,
        language=language,
        file_path=file_path
    )

    db.add(cover_letter)
    db.commit()
    db.refresh(cover_letter)

    return CoverLetterResponse(
        id=cover_letter.id,
        cv_id=None,
        title=cover_letter.title,
        job_description=cover_letter.job_description,
        job_link=cover_letter.job_link,
        content=cover_letter.content,
        file_url=cover_letter.file_path,
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
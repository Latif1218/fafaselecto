from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, Optional
from datetime import datetime
import logging

from ..database import get_db
from ..models.users_model import User
from ..models.cv_model import CVForm
from ..schemas.cv_schema import CVGenerateResponse
from ..schemas.cv_form_schema import CVFormPartial, CVFormFull, CVFormResponse, PersonalDetails, EducationEntry, EmploymentEntry, LanguageEntry, SkillEntry, ActivityEntry
from ..authentication.users_oauth import get_current_user
from ..routers.cv_router import generate_optimized_cv

router = APIRouter(prefix="/cv/form", tags=["CV Form (Multi-step)"])

logger = logging.getLogger(__name__)



@router.post("/save", response_model=CVFormResponse, status_code=status.HTTP_200_OK)
def save_cv_form_step(
    step_data: CVFormPartial,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    form = db.query(CVForm).filter(CVForm.user_id == current_user.id).first()

    if not form:
        form = CVForm(user_id=current_user.id)
        db.add(form)

    updated_step = None

    if step_data.personal_details:
        form.personal_details = step_data.personal_details.dict()
        updated_step = "personal_details"

    if step_data.education:
        form.education = [edu.dict() for edu in step_data.education]
        updated_step = "education"

    if step_data.employment:
        form.employment = [emp.dict() for emp in step_data.employment]
        updated_step = "employment"

    if step_data.language:
        form.languages = [lang.dict() for lang in step_data.language]
        updated_step = "languages"

    if step_data.skills:
        form.skills = [skill.dict() for skill in step_data.skills]
        updated_step = "skills"

    if step_data.activities:
        form.activities = [act.dict() for act in step_data.activities]
        updated_step = "activities"

    if not updated_step:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid step data provided to save"
        )

    form.last_updated_step = updated_step
    form.is_completed = False
    form.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(form)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save form step")

  
    return CVFormResponse.from_orm(form)
    



@router.get("/current", response_model=CVFormResponse, status_code=status.HTTP_201_CREATED)
def gat_current_cv_form(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    form = db.query(CVForm).filter(CVForm.user_id == current_user.id).first()

    if not form:
        return None
    return CVFormResponse.from_orm(form)





@router.post("/submit", response_model=CVGenerateResponse)
async def submit_cv_form_and_generate(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    form = db.query(CVForm).filter(CVForm.user_id == current_user.id).first()

    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No form data found. Please save form steps first."
        )
    
    if not all([
        form.personal_details,
        form.education,
        form.employment,
        form.languages,
        form.skills,
        form.activities
    ]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Form is incomplete. Please fill all steps befoure submitting."
        )
    
    form_full = CVFormFull(
        personal_details=PersonalDetails(**form.personal_details),
        education=[EducationEntry(**edu) for edu in form.education],
        employment=[EmploymentEntry(**emp) for emp in form.employment],
        language=[LanguageEntry(**lang) for lang in form.languages],
        skills=[SkillEntry(**skill) for skill in form.skills],
        activities=[ActivityEntry(**act) for act in form.activities]
    )
    try:
        generated_cv = await generate_optimized_cv(
            form_data=form_full,
            current_user=current_user,
            db=db
        )
        form.is_completed = True
        form.last_updated_step = "submitted"
        form.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"Form submitted & CV generated for user {current_user.id}")

        return generated_cv

    except Exception as e:
        db.rollback()
        logger.error(f"Form submit & CV generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit form and generate CV: {str(e)}"
        )

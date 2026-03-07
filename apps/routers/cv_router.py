from uuid import UUID
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Query
from typing import Dict, Any, Annotated, List
from sqlalchemy.orm import Session
from datetime import datetime
from apps.ai.app.llm_client import extract_text_from_pdf_bytes
from apps.ai.app.models import CVContent, CVGenerationResult
from apps.schemas.cv_form_schema import CVFormFull
from ..ai.app.cv_grader import grade_cv, format_client_output, analyze_cv_metadata, GradingResult
from ..ai.app.generator import generate_cv_from_data
from ..authentication.users_oauth import get_current_user
from ..database import get_db
from ..models.users_model import User, UserPlan
from ..models.cv_model import CV, CVForm
from ..schemas.cv_schema import CVListItem, CVDetail, CVEvaluationResponse, CVGenerateResponse
from ..schemas.cv_form_schema import CVFormFull
from ..utils.file_storage import save_uploaded_file, save_bytes_file, get_file_url, delete_file
import logging
import os


router = APIRouter(
    prefix="/cv",
    tags=["CV Management"])



logger = logging.getLogger(__name__)



@router.post("/upload_and_evaluate", response_model=CVEvaluationResponse)
async def upload_and_evaluate_cv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.plan != UserPlan.ESSENTIAL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature is only available for Essential plan users."
        )
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    file_path = save_uploaded_file(file, folder="cv", user_id=str(current_user.id))


    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Uploaded file could not be saved."
        )

    try:
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()

        raw_text = extract_text_from_pdf_bytes(pdf_bytes)
        metadata = analyze_cv_metadata(raw_text, page_count=1)

        cv_data: Dict[str, Any] = {"raw_text": raw_text}

        result: GradingResult = grade_cv(cv_data, metadata)
        formatted = format_client_output(result)

        db_cv = CV(
            user_id=current_user.id,
            title=file.filename or "Uploaded CV",
            file_path=file_path,
            file_type="pdf",
            score=result.score,
            tips=result.tips,
            is_favorite=False
        )
        db.add(db_cv)
        db.commit()
        db.refresh(db_cv)

        formatted["message"] = formatted.get(
            "message",
            "CV evaluated successfully."
        )

        if formatted.get("tips"):
            formatted["tips"] = [
                {
                    "category": "Improvement",
                    "message": tip,
                    "priority": 2  
                } 
                if isinstance(tip, str)
                else tip
                for tip in formatted["tips"]
            ]

        return CVEvaluationResponse(**formatted)
    

    except Exception as e:
        import traceback
        print("=== CV Evaluation Error ===")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the CV: {str(e)}"
        )
    


@router.post("/generate", response_model=CVGenerateResponse)
async def generate_optimized_cv(
    form_data: CVFormFull,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    
    allowed_plans = {UserPlan.STARTER, UserPlan.PREMIUM, UserPlan.ULTIMATE}
    if current_user.plan not in allowed_plans:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"CV generation requires one of these plans: {', '.join(allowed_plans)}. Please upgrade."
        )
    
    try:
        form = db.query(CVForm).filter(CVForm.user_id == current_user.id).first()

        form_payload = {
            "personal_details" : form_data.personal_details.dict(),
            "education": [edu.dict() for edu in form_data.education],
            "employment": [emp.dict() for emp in form_data.employment],
            "languages": [lang.dict() for lang in form_data.language],
            "skills": [skill.dict() for skill in form_data.skills],
            "activities": [act.dict() for act in form_data.activities],
            "last_updated_step": "full_submit",
            "is_completed": True
        }

        if form:
            for key, value in form_payload.items():
                setattr(form, key, value)
        else:
            form = CVForm(
                user_id = current_user.id,
                **form_payload
            )
            db.add(form)
        db.commit()
        db.refresh(form)


        cv_content = CVContent(
            contact_information=[
                {
                    "name": form_payload["personal_details"]["full_name"],
                    "email": form_payload["personal_details"]["email"],
                    "phone": form_payload["personal_details"]["phone_number"],
                    "address": form_payload["personal_details"].get("address"),
                    "linkedin": form_payload["personal_details"].get("linkedin"),
                    "portfolio": form_payload["personal_details"].get("portfolio")
                }
            ],

            education=form_payload["education"],
            
            work_experience=[
                {
                    "position": emp["position"],
                    "company": emp["company"],
                    "location": emp.get("location"),
                    "date": f"{emp['start_date']} - {emp.get('end_date', 'Present')}",
                    "description": emp["description"]
                }
                for emp in form_payload["employment"]
            ],

            language_skills=[
                f"{lang['language']} ({lang.get('level','')})"
                for lang in form_payload["languages"]
            ],

            it_skills=[
                f"{skill['activity_name']} ({skill.get('level','')})"
                for skill in form_payload["skills"]
            ],

            activities_interests=[
                act["title"]
                for act in form_payload["activities"]
            ],

            domain="finance"
        )
        

        results: Dict[str, CVGenerationResult] = generate_cv_from_data(
            cv_content=cv_content,
            languages=["fr", "en"]
        )

        saved_files = {}
        for lang, result in results.items():
            pdf_path = save_bytes_file(
                result.pdf_bytes,
                folder="generated",
                user_id=str(current_user.id),
                ext=".pdf"
            )
            saved_files[lang] = {"pdf_path": pdf_path, "pdf_url": get_file_url(pdf_path)}

            if result.docx_bytes:
                docx_path = save_bytes_file(
                    result.docx_bytes,
                    folder="generated",
                    user_id=str(current_user.id),
                    ext=".docx"
                )
                saved_files[lang]["docx_url"] = get_file_url(docx_path)

        primary_cv = CV(
            user_id=current_user.id,
            title=f"AI Generated CV - {datetime.utcnow().strftime('%Y-%m')}",
            file_path=saved_files["fr"]["pdf_path"],
            file_type="pdf",
            score=95,
            tips=[],
            is_favorite=False
        )
        db.add(primary_cv)
        db.commit()
        db.refresh(primary_cv)

        return CVGenerateResponse(
            cv_id=primary_cv.id,
            pdf_url=saved_files["fr"]["pdf_url"],
            docx_url=saved_files["fr"].get("docx_url"),
            language="FR + EN",
            message="CV successfully generated in French and English! Form data saved."
        )

    except Exception as ve:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CV generation failed: {str(e)}"
        )
    


@router.get("/list", response_model=List[CVListItem], status_code=status.HTTP_200_OK)
def list_my_cvs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|score|title)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$")
):
    query = db.query(CV).filter(CV.user_id == current_user.id)

    order_column = {
        "created_at": CV.created_at,
        "score": CV.score,
        "title": CV.title
    }.get(sort_by, CV.created_at)

    query = query.order_by(order_column.desc() if sort_order == "desc" else order_column.asc())

    cvs = query.offset(skip).limit(limit).all()

    cvs_response = [
        CVListItem(
            id=cv.id,
            title=cv.title,
            score=cv.score,
            file_url=get_file_url(cv.file_path),
            file_type=cv.file_type,
            is_favorite=cv.is_favorite,
            created_at=cv.created_at
        )
        for cv in cvs
    ]

    return cvs_response



@router.get("/{cv_id}", response_model=CVDetail, status_code=status.HTTP_200_OK)
def get_cv_detail(
    cv_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found or does not belong to you"
        )
    return CVDetail(
        id=cv.id,
        title=cv.title,
        score=cv.score,
        file_url=get_file_url(cv.file_path),  
        file_type=cv.file_type,
        is_favorite=cv.is_favorite,
        created_at=cv.created_at,
        tips=cv.tips if hasattr(cv, "tips") else None,
        raw_metadata=cv.raw_metadata if hasattr(cv, "raw_metadata") else None
    )





@router.delete("/{cv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cv(
    cv_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found or does not belong to you"
        )
    
    try:
        delete_file(cv.file_path)
        db.delete(cv)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"CV delete faield: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete CV: {str(e)}"
        )
    return None
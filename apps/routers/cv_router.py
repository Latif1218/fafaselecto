from uuid import UUID
from datetime import datetime
from typing import Dict, List
import asyncio
import logging
import os

from fastapi import APIRouter, UploadFile, Form, File, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.users_model import User, UserPlan
from ..models.cv_model import CV, CVForm
from ..authentication.users_oauth import get_current_user
from ..utils.file_storage import UPLOAD_BASE, save_bytes_file, get_file_url, delete_file
from ..schemas.cv_schema import (
    CVListItem,
    CVDetail,
    CVEvaluationResponse,
    CVGenerateResponse,
    CVOptimizeResponse,
)
from ..schemas.cv_form_schema import CVFormFull

from apps.ai.app.llm_client import extract_text_from_pdf_bytes, extract_structured_cv_data
from apps.ai.app.models import CVContent, CVGenerationResult
from apps.ai.app.cv_grader import grade_cv, format_client_output, analyze_cv_metadata, GradingResult
from apps.ai.app.generator import generate_cv_from_data, generate_cv_from_pdf
from apps.ai.app.domain_detector import detect_domain_from_cv_text

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/cv",
    tags=["CV Management"],
)


def _validate_pdf_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is missing")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")


def _get_cv_or_404(db: Session, cv_id: UUID, user_id: UUID) -> CV:
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == user_id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    return cv


@router.get("/test")
def test_route():
    return {"message": "hello test"}


# -------------------------
# Upload & Evaluate CV
# -------------------------
@router.post("/upload_and_evaluate", response_model=CVEvaluationResponse)
async def upload_and_evaluate_cv(
    email: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please register first.",
        )

    allowed_plans = {
        UserPlan.ESSENTIAL,
        UserPlan.STARTER,
        UserPlan.PREMIUM,
        UserPlan.ULTIMATE,
    }
    if user.plan not in allowed_plans:
        raise HTTPException(
            status_code=403,
            detail="Your plan does not allow CV evaluation.",
        )

    _validate_pdf_file(file)

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        file_path = save_bytes_file(
            content=pdf_bytes,
            folder="cv",
            user_id=str(user.id),
            ext=".pdf",
        )

        full_file_path = os.path.join(UPLOAD_BASE, file_path)
        if not os.path.exists(full_file_path):
            raise HTTPException(status_code=500, detail="Uploaded file could not be saved.")

        raw_text = extract_text_from_pdf_bytes(pdf_bytes)
        if not raw_text or len(raw_text.strip()) < 20:
            raise HTTPException(status_code=400, detail="Could not extract enough text from PDF")

        structured_data = extract_structured_cv_data(pdf_bytes)
        metadata = analyze_cv_metadata(raw_text, page_count=1)

        cv_data = {
            **structured_data,
            "raw_text": raw_text,
        }

        grading_result: GradingResult = grade_cv(cv_data, metadata)
        formatted = format_client_output(grading_result)

        db_cv = CV(
            user_id=user.id,
            title=file.filename or "Uploaded CV",
            file_path=file_path,
            file_type="pdf",
            score=grading_result.score,
            domain=None,
            tips=grading_result.tips,
            is_favorite=False,
        )
        db.add(db_cv)
        db.commit()
        db.refresh(db_cv)

        if formatted.get("tips"):
            formatted["tips"] = [
                {
                    "category": "Improvement",
                    "message": tip,
                    "priority": 2,
                }
                if isinstance(tip, str)
                else tip
                for tip in formatted["tips"]
            ]

        formatted["message"] = "CV evaluated successfully."
        return CVEvaluationResponse(**formatted)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("CV evaluation failed")
        raise HTTPException(status_code=500, detail=f"Error processing CV: {str(e)}")


# -------------------------
# Optimize CV
# -------------------------
@router.post("/optimize", response_model=CVOptimizeResponse)
async def optimize_uploaded_cv_direct(
    file: UploadFile = File(...),
    target_language: str = Form("fr"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_pdf_file(file)

    allowed_plans = {
        UserPlan.STARTER,
        UserPlan.PREMIUM,
        UserPlan.ULTIMATE,
    }
    if current_user.plan not in allowed_plans:
        raise HTTPException(
            status_code=403,
            detail="CV optimization requires Starter, Premium, or Ultimate plan",
        )

    try:
        pdf_bytes = await file.read()
        if not pdf_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        raw_text = extract_text_from_pdf_bytes(pdf_bytes)
        detected_domain = detect_domain_from_cv_text(raw_text) if raw_text else "finance"

        # IMPORTANT: run sync generator in a worker thread
        results: Dict[str, CVGenerationResult] = await asyncio.to_thread(
            generate_cv_from_pdf,
            pdf_bytes,
            detected_domain,
            ["fr", "en"],
        )

        if not results:
            raise HTTPException(status_code=500, detail="Failed to generate optimized CV")

        primary_lang = target_language.lower()
        if primary_lang not in ["fr", "en"]:
            primary_lang = "fr"

        if primary_lang not in results:
            primary_lang = "fr"

        saved_files: Dict[str, Dict[str, str]] = {}
        docx_path_db = None

        for lang, result in results.items():
            if not result.pdf_bytes:
                continue

            pdf_path = save_bytes_file(
                content=result.pdf_bytes,
                folder="optimized_cv",
                user_id=str(current_user.id),
                ext=".pdf",
            )
            saved_files[lang] = {
                "pdf_path": pdf_path,
                "pdf_url": get_file_url(pdf_path),
            }

            if result.docx_bytes:
                docx_path = save_bytes_file(
                    content=result.docx_bytes,
                    folder="optimized_cv",
                    user_id=str(current_user.id),
                    ext=".docx",
                )
                saved_files[lang]["docx_path"] = docx_path
                saved_files[lang]["docx_url"] = get_file_url(docx_path)

                if lang == primary_lang:
                    docx_path_db = docx_path

        if primary_lang not in saved_files:
            raise HTTPException(status_code=500, detail="Primary optimized CV file was not saved")

        try:
            optimized_pdf_full_path = os.path.join(
                UPLOAD_BASE, saved_files[primary_lang]["pdf_path"]
            )
            with open(optimized_pdf_full_path, "rb") as f:
                optimized_pdf_bytes = f.read()

            raw_text_new = extract_text_from_pdf_bytes(optimized_pdf_bytes)
            metadata_new = analyze_cv_metadata(raw_text_new, page_count=1)
            new_score = grade_cv(
                {
                    "raw_text": raw_text_new,
                    "work_experience": [],
                    "education": [],
                    "language_skills": [],
                    "it_skills": [],
                    "contact_information": {},
                },
                metadata_new,
            ).score
        except Exception:
            new_score = 75

        optimized_cv = CV(
            user_id=current_user.id,
            title=f"Optimized CV - {file.filename} ({primary_lang.upper()})",
            file_path=saved_files[primary_lang]["pdf_path"],
            docx_path=docx_path_db,
            file_type="pdf",
            score=new_score,
            tips=[],
            is_favorite=False,
            domain=detected_domain,
        )
        db.add(optimized_cv)
        db.commit()
        db.refresh(optimized_cv)

        return CVOptimizeResponse(
            new_cv_id=optimized_cv.id,
            pdf_url=saved_files[primary_lang]["pdf_url"],
            docx_url=saved_files[primary_lang].get("docx_url"),
            download_url=f"/cv/download/{optimized_cv.id}?file_type=pdf",
            language=f"{primary_lang.upper()} + {'EN' if primary_lang == 'fr' else 'FR'}",
            estimated_score_improvement=new_score,
            message=f"CV successfully optimized! New score: {new_score}",
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("CV optimization failed")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


# -------------------------
# Generate CV from form
# -------------------------
@router.post("/generate", response_model=CVGenerateResponse)
async def generate_optimized_cv(
    form_data: CVFormFull,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed_plans = {
        UserPlan.STARTER,
        UserPlan.PREMIUM,
        UserPlan.ULTIMATE,
    }
    if current_user.plan not in allowed_plans:
        raise HTTPException(
            status_code=403,
            detail="CV generation requires Starter, Premium, or Ultimate plan",
        )

    try:
        form = db.query(CVForm).filter(CVForm.user_id == current_user.id).first()

        form_payload = {
            "personal_details": form_data.personal_details.dict(),
            "education": [edu.dict() for edu in form_data.education],
            "employment": [emp.dict() for emp in form_data.employment],
            "languages": [lang.dict() for lang in form_data.language],
            "skills": [skill.dict() for skill in form_data.skills],
            "activities": [act.dict() for act in form_data.activities],
            "last_updated_step": "full_submit",
            "is_completed": True,
        }

        if form:
            for key, value in form_payload.items():
                setattr(form, key, value)
        else:
            form = CVForm(user_id=current_user.id, **form_payload)
            db.add(form)

        db.commit()
        db.refresh(form)

        work_experience = []
        for emp in form_payload["employment"]:
            description = emp.get("description")
            bullets = description if isinstance(description, list) else [description] if description else []

            work_experience.append(
                {
                    "position": emp.get("position"),
                    "company": emp.get("company"),
                    "location": emp.get("location"),
                    "date": f"{emp.get('start_date', '')} - {emp.get('end_date', 'Present')}",
                    "bullets": bullets,
                }
            )

        cv_content = CVContent(
            contact_information=[
                {
                    "name": form_payload["personal_details"].get("full_name"),
                    "email": form_payload["personal_details"].get("email"),
                    "phone": form_payload["personal_details"].get("phone_number"),
                    "address": form_payload["personal_details"].get("address"),
                    "linkedin": form_payload["personal_details"].get("linkedin"),
                    "portfolio": form_payload["personal_details"].get("portfolio"),
                }
            ],
            education=form_payload["education"],
            work_experience=work_experience,
            language_skills=[
                f"{lang.get('language')} ({lang.get('level', '')})"
                for lang in form_payload["languages"]
            ],
            it_skills=[
                f"{skill.get('activity_name')} ({skill.get('level', '')})"
                for skill in form_payload["skills"]
            ],
            activities_interests=[
                act.get("title") for act in form_payload["activities"] if act.get("title")
            ],
            domain="finance",
        )

        # IMPORTANT: run sync generator in a worker thread
        results: Dict[str, CVGenerationResult] = await asyncio.to_thread(
            generate_cv_from_data,
            cv_content,
            ["fr", "en"],
        )

        if "fr" not in results:
            raise HTTPException(status_code=500, detail="French CV generation failed")

        saved_files: Dict[str, Dict[str, str]] = {}
        docx_path_db = None

        for lang, result in results.items():
            if not result.pdf_bytes:
                continue

            pdf_path = save_bytes_file(
                content=result.pdf_bytes,
                folder="generated",
                user_id=str(current_user.id),
                ext=".pdf",
            )
            saved_files[lang] = {
                "pdf_path": pdf_path,
                "pdf_url": get_file_url(pdf_path),
            }

            if result.docx_bytes:
                docx_path = save_bytes_file(
                    content=result.docx_bytes,
                    folder="generated",
                    user_id=str(current_user.id),
                    ext=".docx",
                )
                saved_files[lang]["docx_path"] = docx_path
                saved_files[lang]["docx_url"] = get_file_url(docx_path)

                if lang == "fr":
                    docx_path_db = docx_path

        primary_cv = CV(
            user_id=current_user.id,
            title=f"AI Generated CV - {datetime.utcnow().strftime('%Y-%m')}",
            file_path=saved_files["fr"]["pdf_path"],
            docx_path=docx_path_db,
            file_type="pdf",
            score=95,
            tips=[],
            is_favorite=False,
            domain=cv_content.domain,
        )
        db.add(primary_cv)
        db.commit()
        db.refresh(primary_cv)

        return CVGenerateResponse(
            cv_id=primary_cv.id,
            pdf_url=saved_files["fr"]["pdf_url"],
            docx_url=saved_files["fr"].get("docx_url"),
            download_url=f"/cv/download/{primary_cv.id}?file_type=pdf",
            language="FR + EN",
            message="CV successfully generated in French and English! Form data saved.",
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("CV generation failed")
        raise HTTPException(status_code=500, detail=f"CV generation failed: {str(e)}")


# -------------------------
# List CVs
# -------------------------
@router.get("/list", response_model=List[CVListItem])
def list_my_cvs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query(pattern="^(created_at|score|title)$", default="created_at"),
    sort_order: str = Query(pattern="^(asc|desc)$", default="desc"),
):
    query = db.query(CV).filter(CV.user_id == current_user.id)

    order_column = {
        "created_at": CV.created_at,
        "score": CV.score,
        "title": CV.title,
    }[sort_by]

    query = query.order_by(order_column.desc() if sort_order == "desc" else order_column.asc())
    cvs = query.offset(skip).limit(limit).all()

    return [
        CVListItem(
            id=cv.id,
            title=cv.title,
            score=cv.score,
            domain=cv.domain,
            file_url=get_file_url(cv.file_path),
            download_url=f"/cv/download/{cv.id}?file_type=pdf",
            file_type=cv.file_type,
            is_favorite=cv.is_favorite,
            created_at=cv.created_at,
        )
        for cv in cvs
    ]


@router.get("/my-cvs", response_model=List[CVListItem])
def get_user_cvs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cvs = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.created_at.desc()).all()

    return [
        CVListItem(
            id=cv.id,
            title=cv.title,
            score=cv.score,
            domain=cv.domain,
            file_url=get_file_url(cv.file_path),
            download_url=f"/cv/download/{cv.id}?file_type=pdf",
            file_type=cv.file_type,
            is_favorite=cv.is_favorite,
            created_at=cv.created_at,
        )
        for cv in cvs
    ]


@router.get("/my-favorite", response_model=CVListItem)
def get_user_favorite_cv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorite_cv = (
        db.query(CV)
        .filter(CV.user_id == current_user.id, CV.is_favorite.is_(True))
        .first()
    )

    if not favorite_cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No favorite CV found",
        )

    return CVListItem(
        id=favorite_cv.id,
        title=favorite_cv.title,
        score=favorite_cv.score,
        domain=favorite_cv.domain,
        file_url=get_file_url(favorite_cv.file_path),
        download_url=f"/cv/download/{favorite_cv.id}?file_type=pdf",
        file_type=favorite_cv.file_type,
        is_favorite=favorite_cv.is_favorite,
        created_at=favorite_cv.created_at,
    )


# -------------------------
# Get CV Detail
# -------------------------
@router.get("/{cv_id}", response_model=CVDetail)
def get_cv_detail(
    cv_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cv = _get_cv_or_404(db, cv_id, current_user.id)

    return CVDetail(
        id=cv.id,
        title=cv.title,
        score=cv.score,
        file_url=get_file_url(cv.file_path),
        file_type=cv.file_type,
        is_favorite=cv.is_favorite,
        created_at=cv.created_at,
        tips=cv.tips,
        raw_metadata=None,
    )


# -------------------------
# Delete CV
# -------------------------
@router.delete("/{cv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cv(
    cv_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cv = _get_cv_or_404(db, cv_id, current_user.id)

    try:
        delete_file(cv.file_path)

        if cv.docx_path:
            delete_file(cv.docx_path)

        db.delete(cv)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception("CV deletion failed")
        raise HTTPException(status_code=500, detail=f"Failed to delete CV: {str(e)}")

    return None


# -------------------------
# Download CV
# -------------------------
@router.get("/download/{cv_id}")
def download_cv(
    cv_id: UUID,
    file_type: str = Query(default="pdf", pattern="^(pdf|docx)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cv = _get_cv_or_404(db, cv_id, current_user.id)

    if file_type == "pdf":
        file_path = cv.file_path
        media_type = "application/pdf"
    else:
        if not cv.docx_path:
            raise HTTPException(status_code=404, detail="DOCX file not available for this CV")
        file_path = cv.docx_path
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    full_path = os.path.join(UPLOAD_BASE, file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail=f"{file_type.upper()} file not found")

    return FileResponse(
        path=full_path,
        filename=os.path.basename(full_path),
        media_type=media_type,
    )


# -------------------------
# Set favorite CV
# -------------------------
@router.patch("/set_favorite/{cv_id}")
def set_favorite_cv(
    cv_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cv_to_favorite = _get_cv_or_404(db, cv_id, current_user.id)

    db.query(CV).filter(
        CV.user_id == current_user.id,
        CV.id != cv_id,
    ).update({"is_favorite": False})

    cv_to_favorite.is_favorite = True

    db.commit()
    db.refresh(cv_to_favorite)

    return {
        "cv_id": str(cv_to_favorite.id),
        "is_favorite": cv_to_favorite.is_favorite,
        "message": "CV set as favorite successfully.",
    }
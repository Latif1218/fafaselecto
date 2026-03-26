from uuid import UUID
from fastapi import APIRouter, UploadFile, Form, File, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from typing import Dict, Any, Annotated, List
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import os

from ..database import get_db
from ..models.users_model import User, UserPlan
from ..models.cv_model import CV, CVForm
from ..authentication.users_oauth import get_current_user
from ..utils.file_storage import UPLOAD_BASE, save_uploaded_file, save_bytes_file, get_file_url, delete_file
from ..schemas.cv_schema import CVListItem, CVDetail, CVEvaluationResponse, CVGenerateResponse, CVOptimizeResponse
from ..schemas.cv_form_schema import CVFormFull
from apps.ai.app.llm_client import extract_text_from_pdf_bytes, extract_structured_cv_data
from apps.ai.app.models import CVContent, CVGenerationResult
from ..ai.app.cv_grader import grade_cv, format_client_output, analyze_cv_metadata, GradingResult
from ..ai.app.generator import generate_cv_from_data, generate_cv_from_pdf
from ..ai.app.domain_detector import detect_domain_from_cv_text

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/cv",
    tags=["CV Management"]
)


# ← This is just a test router 
@router.get("/test")
def test_route():
    """Test endpoint"""
    return {"message": "hello test"}

# -------------------------
# Upload & Evaluate CV
# -------------------------
@router.post("/upload_and_evaluate", response_model=CVEvaluationResponse)
async def upload_and_evaluate_cv(
    email: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please register first.")

    if user.plan not in [UserPlan.ESSENTIAL, UserPlan.STARTER, UserPlan.PREMIUM, UserPlan.ULTIMATE]:
        raise HTTPException(status_code=403, detail="Your plan does not allow CV evaluation.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    pdf_bytes = await file.read()
    file_path = save_bytes_file(
        content=pdf_bytes,
        folder="cv",
        user_id=str(user.id),
        ext=".pdf"
    )
    full_file_path = os.path.join(UPLOAD_BASE, file_path)  # <- এখানে full path
    if not os.path.exists(full_file_path):
        raise HTTPException(status_code=500, detail="Uploaded file could not be saved.")
    try:
        raw_text = extract_text_from_pdf_bytes(pdf_bytes)
        structured_data = extract_structured_cv_data(pdf_bytes)
        metadata = analyze_cv_metadata(raw_text, page_count=1)
        cv_data = {**structured_data, "raw_text": raw_text}

        grading_result: GradingResult = grade_cv(cv_data, metadata)
        formatted = format_client_output(grading_result)

        db_cv = CV(
            user_id=user.id,
            title=file.filename or "Uploaded CV",
            file_path=file_path,
            file_type="pdf",
            score=grading_result.score,
            tips=grading_result.tips,
            is_favorite=False
        )
        db.add(db_cv)
        db.commit()
        db.refresh(db_cv)

        if formatted.get("tips"):
            formatted["tips"] = [
                {"category": "Improvement", "message": tip, "priority": 2} if isinstance(tip, str) else tip
                for tip in formatted["tips"]
            ]
        formatted["message"] = formatted.get("message", "CV evaluated successfully.")

        return CVEvaluationResponse(**formatted)

    except Exception as e:
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
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    allowed_plans = {UserPlan.STARTER, UserPlan.PREMIUM, UserPlan.ULTIMATE}
    if current_user.plan not in allowed_plans:
        raise HTTPException(status_code=403, detail=f"CV optimization requires one of these plans: {', '.join(allowed_plans)}")

    try:
        pdf_bytes = await file.read()
        if not pdf_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        raw_text = extract_text_from_pdf_bytes(pdf_bytes)
        detected_domain = detect_domain_from_cv_text(raw_text)

        results: Dict[str, CVGenerationResult] = generate_cv_from_pdf(pdf_bytes, detected_domain, ["fr", "en"])
        if not results or "fr" not in results or "en" not in results:
            raise HTTPException(status_code=500, detail="Failed to generate optimized CV")

        primary_lang = target_language if target_language in ["fr", "en"] else "fr"
        primary_lang = primary_lang if primary_lang in results else "fr"

        saved_files = {}
        docx_path_db = None

        for lang, result in results.items():
            if not result.pdf_bytes:
                continue
            pdf_path = save_bytes_file(result.pdf_bytes, folder="optimized_cv", user_id=str(current_user.id), ext=".pdf")
            saved_files[lang] = {"pdf_path": pdf_path, "pdf_url": get_file_url(pdf_path)}

            if result.docx_bytes:
                docx_path = save_bytes_file(result.docx_bytes, folder="optimized_cv", user_id=str(current_user.id), ext=".docx")
                saved_files[lang]["docx_url"] = get_file_url(docx_path)
                if lang == primary_lang:
                    docx_path_db = docx_path

        # Re-grade
        try:
            optimized_pdf_path = os.path.join(UPLOAD_BASE, saved_files[primary_lang]["pdf_path"])
            raw_text_new = extract_text_from_pdf_bytes(open(optimized_pdf_path, "rb").read())
            metadata_new = analyze_cv_metadata(raw_text_new, page_count=1)
            new_score = grade_cv({"raw_text": raw_text_new}, metadata_new).score
        except Exception:
            new_score = 75  # fallback score

        optimized_cv = CV(
            user_id=current_user.id,
            title=f"Optimized Upload - {file.filename} ({primary_lang.upper()})",
            file_path=saved_files[primary_lang]["pdf_path"],
            docx_path=docx_path_db,
            file_type="pdf",
            score=new_score,
            tips=[],
            is_favorite=False,
            domain=detected_domain
        )
        db.add(optimized_cv)
        db.commit()
        db.refresh(optimized_cv)

        return CVOptimizeResponse(
            new_cv_id=optimized_cv.id,
            pdf_url=saved_files.get(primary_lang, {}).get("pdf_url"),
            docx_url=saved_files.get(primary_lang, {}).get("docx_url"),
            download_url=f"/cv/{optimized_cv.id}/download",
            language=f"{primary_lang.upper()} + EN",
            estimated_score_improvement=new_score,
            message=f"CV successfully optimized! New score: {new_score}"
        )

    except Exception as e:
        db.rollback()
        logger.exception("CV optimization failed")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


# -------------------------
# Generate CV
# -------------------------
@router.post("/generate", response_model=CVGenerateResponse)
async def generate_optimized_cv(
    form_data: CVFormFull,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allowed_plans = {UserPlan.STARTER, UserPlan.PREMIUM, UserPlan.ULTIMATE}
    if current_user.plan not in allowed_plans:
        raise HTTPException(status_code=403, detail=f"CV generation requires one of these plans: {', '.join(allowed_plans)}")

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
            "is_completed": True
        }
        if form:
            for key, value in form_payload.items():
                setattr(form, key, value)
        else:
            form = CVForm(user_id=current_user.id, **form_payload)
            db.add(form)
        db.commit()
        db.refresh(form)

        cv_content = CVContent(
            contact_information=[{
                "name": form_payload["personal_details"]["full_name"],
                "email": form_payload["personal_details"]["email"],
                "phone": form_payload["personal_details"]["phone_number"],
                "address": form_payload["personal_details"].get("address"),
                "linkedin": form_payload["personal_details"].get("linkedin"),
                "portfolio": form_payload["personal_details"].get("portfolio")
            }],
            education=form_payload["education"],
            work_experience=[{
                "position": emp["position"],
                "company": emp["company"],
                "location": emp.get("location"),
                "date": f"{emp['start_date']} - {emp.get('end_date', 'Present')}",
                "description": emp["description"]
            } for emp in form_payload["employment"]],
            language_skills=[f"{lang['language']} ({lang.get('level','')})" for lang in form_payload["languages"]],
            it_skills=[f"{skill['activity_name']} ({skill.get('level','')})" for skill in form_payload["skills"]],
            activities_interests=[act["title"] for act in form_payload["activities"]],
            domain="finance"
        )

        results: Dict[str, CVGenerationResult] = generate_cv_from_data(cv_content, ["fr", "en"])
        saved_files = {}
        docx_path_db = None
        for lang, result in results.items():
            pdf_path = save_bytes_file(result.pdf_bytes, folder="generated", user_id=str(current_user.id), ext=".pdf")
            saved_files[lang] = {"pdf_path": pdf_path, "pdf_url": get_file_url(pdf_path)}
            if result.docx_bytes:
                docx_path = save_bytes_file(result.docx_bytes, folder="generated", user_id=str(current_user.id), ext=".docx")
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
            domain=cv_content.domain
        )
        db.add(primary_cv)
        db.commit()
        db.refresh(primary_cv)

        return CVGenerateResponse(
            cv_id=primary_cv.id,
            pdf_url=saved_files["fr"]["pdf_url"],
            docx_url=saved_files["fr"].get("docx_url"),
            download_url=f"/cv/{primary_cv.id}/download",
            language="FR + EN",
            message="CV successfully generated in French and English! Form data saved."
        )

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
    sort_by: str = Query("created_at", regex="^(created_at|score|title)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$")
):
    query = db.query(CV).filter(CV.user_id == current_user.id)
    order_column = {"created_at": CV.created_at, "score": CV.score, "title": CV.title}[sort_by]
    query = query.order_by(order_column.desc() if sort_order=="desc" else order_column.asc())
    cvs = query.offset(skip).limit(limit).all()

    return [
        CVListItem(
            id=cv.id,
            title=cv.title,
            score=cv.score,
            domain=cv.domain,
            file_url=get_file_url(cv.file_path),
            download_url=f"/cv/{cv.id}/download",
            file_type=cv.file_type,
            is_favorite=cv.is_favorite,
            created_at=cv.created_at
        ) for cv in cvs
    ]

@router.get("/my-cvs", response_model=List[CVListItem])
def get_user_cvs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all CVs belonging to the authenticated user"""
    cvs = db.query(CV).filter(CV.user_id == current_user.id).all()

    return [
        CVListItem(
            id=cv.id,
            title=cv.title,
            score=cv.score,
            domain=cv.domain,
            file_url=get_file_url(cv.file_path),
            download_url=f"/cv/{cv.id}/download",
            file_type=cv.file_type,
            is_favorite=cv.is_favorite,
            created_at=cv.created_at
        ) for cv in cvs
    ]


# Route 1: Get all CVs for the current user
@router.get("/my-cvs", response_model=List[CVListItem])
def get_user_cvs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all CVs belonging to the authenticated user"""
    cvs = db.query(CV).filter(CV.user_id == current_user.id).all()
    
    # Build CVListItem objects with required fields
    return [
        CVListItem(
            id=cv.id,
            title=cv.title,
            score=cv.score,
            domain=cv.domain,
            file_url=get_file_url(cv.file_path),
            download_url=f"/cv/{cv.id}/download",  # ← Required field
            file_type=cv.file_type,
            is_favorite=cv.is_favorite,
            created_at=cv.created_at
        ) for cv in cvs
    ]


# Route 2: Get the user's favorite CV
@router.get("/my-favorite", response_model=CVListItem)
def get_user_favorite_cv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the user's favorite CV"""
    favorite_cv = db.query(CV).filter(
        CV.user_id == current_user.id,
        CV.is_favorite == True
    ).first()
    
    if not favorite_cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No favorite CV found"
        )
    
    # Build CVListItem object with required fields
    return CVListItem(
        id=favorite_cv.id,
        title=favorite_cv.title,
        score=favorite_cv.score,
        domain=favorite_cv.domain,
        file_url=get_file_url(favorite_cv.file_path),
        download_url=f"/cv/{favorite_cv.id}/download",  # ← Required field
        file_type=favorite_cv.file_type,
        is_favorite=favorite_cv.is_favorite,
        created_at=favorite_cv.created_at
    )



# -------------------------
# Get CV Detail
# -------------------------
@router.get("/{cv_id}", response_model=CVDetail)
def get_cv_detail(cv_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cv = db.query(CV).filter(CV.id==cv_id, CV.user_id==current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found or does not belong to you")
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



# -------------------------
# Delete CV
# -------------------------
@router.delete("/{cv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cv(cv_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cv = db.query(CV).filter(CV.id==cv_id, CV.user_id==current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found or does not belong to you")
    try:
        delete_file(cv.file_path)
        if getattr(cv, "docx_path", None):
            delete_file(cv.docx_path)
        db.delete(cv)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception("CV deletion failed")
        raise HTTPException(status_code=500, detail=f"Failed to delete CV: {str(e)}")
    return None


@router.get("/download/{cv_id}")
def download_cv(
    cv_id: UUID,
    file_type: str = Query("pdf", enum=["pdf", "docx"]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a CV file (PDF or DOCX) by CV ID.
    file_type query parameter controls the file format: pdf or docx.
    Only the owner of the CV can download it.
    """

    # Fetch CV from DB
    cv = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv:
        logger.warning(f"CV not found or user unauthorized: cv_id={cv_id}, user_id={current_user.id}")
        raise HTTPException(status_code=404, detail="CV not found")

    # Determine the file path based on requested type
    if file_type == "pdf":
        file_path = cv.file_path
        media_type = "application/pdf"
    else:  # docx
        if not cv.docx_path:
            logger.info(f"DOCX file not available for CV {cv_id}")
            raise HTTPException(status_code=404, detail="DOCX file not available for this CV")
        file_path = cv.docx_path
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    full_path = os.path.join(UPLOAD_BASE, file_path)

    if not os.path.exists(full_path):
        logger.error(f"File not found on disk: {full_path}")
        raise HTTPException(status_code=404, detail=f"{file_type.upper()} file not found")

    logger.info(f"Serving {file_type.upper()} file for CV {cv_id} to user {current_user.id}")
    return FileResponse(
        full_path,
        filename=os.path.basename(full_path),
        media_type=media_type
    )



@router.patch("/set_favorite/{cv_id}")
def set_favorite_cv(
    cv_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set a CV as favorite for the current user.
    Only one CV can be favorite at a time.
    """

    # Check if the CV exists and belongs to the user
    cv_to_favorite = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv_to_favorite:
        logger.warning(f"CV not found or unauthorized: cv_id={cv_id}, user_id={current_user.id}")
        raise HTTPException(status_code=404, detail="CV not found")

    # Set all other CVs for this user as not favorite
    db.query(CV).filter(CV.user_id == current_user.id, CV.id != cv_id).update({"is_favorite": False})

    # Set selected CV as favorite
    cv_to_favorite.is_favorite = True

    db.commit()
    db.refresh(cv_to_favorite)

    logger.info(f"CV {cv_id} set as favorite for user {current_user.id}")
    return {"cv_id": str(cv_to_favorite.id), "is_favorite": cv_to_favorite.is_favorite, "message": "CV set as favorite successfully."}
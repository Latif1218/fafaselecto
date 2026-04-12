from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Annotated, Optional, List
from uuid import UUID
import logging
import os
import io
import re
import pdfplumber

from ..database import get_db
from ..models.users_model import User
from ..models.cv_model import CV, CoverLetter
from ..schemas.cover_letter_schema import CoverLetterResponse, CoverLetterWarning
from ..authentication.users_oauth import get_current_user
from ..utils.file_storage import save_bytes_file, get_file_url, UPLOAD_BASE

from apps.ai.app.cover_letter_generator import generate_cover_letter
from apps.ai.app.job_offer_extractor import extract_job_offer_from_url
from apps.ai.app.cover_letter_exporter import (
    generate_cover_letter_pdf_bytes,
    generate_cover_letter_docx_bytes,
)

router = APIRouter(
    prefix="/cover-letter",
    tags=["Cover Letter"]
)

logger = logging.getLogger(__name__)


def _extract_text_from_pdf_bytes_local(pdf_bytes: bytes) -> str:
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages_text = []
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    pages_text.append(page_text)

        text = "\n".join(pages_text).strip()

        if not text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract readable text from the selected CV PDF."
            )

        return text

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text from selected CV PDF: {str(e)}"
        )


def _detect_cv_language_from_text(raw_text: str) -> str:
    text = (raw_text or "").lower()

    french_signals = [
        "expérience", "compétences", "formation", "éducation", "langues",
        "français", "téléphone", "adresse", "candidature", "stage",
        "projet académique", "profil", "objectif"
    ]

    english_signals = [
        "experience", "skills", "education", "languages",
        "phone", "address", "application", "internship",
        "academic project", "profile", "objective", "summary"
    ]

    fr_score = sum(1 for word in french_signals if word in text)
    en_score = sum(1 for word in english_signals if word in text)

    if fr_score > en_score:
        return "fr"
    return "en"


def _extract_email(text: str) -> str:
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    return match.group(0) if match else ""


def _extract_phone(text: str) -> str:
    match = re.search(r'(\+?\d[\d\s\-\(\)]{7,}\d)', text)
    return match.group(0).strip() if match else ""


def _extract_name_fallback(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "Candidate"

    for line in lines[:8]:
        if "@" in line:
            continue
        if len(line.split()) >= 2 and len(line) <= 60:
            return line

    return "Candidate"


def _extract_languages_from_text(text: str) -> List[dict]:
    text_lower = text.lower()
    found = []

    language_map = {
        "English": ["english", "anglais"],
        "French": ["french", "français", "francais"],
        "Bangla": ["bangla", "bengali"],
        "Arabic": ["arabic", "arabe"],
        "Spanish": ["spanish", "espagnol"],
        "German": ["german", "allemand"]
    }

    for normalized, variants in language_map.items():
        if any(v in text_lower for v in variants):
            found.append({"language": normalized, "level": "Not specified"})

    return found


def _extract_skills_from_text(text: str) -> List[dict]:
    known_skills = [
        "Python", "SQL", "Excel", "Power BI", "Tableau", "Java", "C++",
        "Machine Learning", "Data Analysis", "Financial Modeling", "Valuation",
        "Communication", "Leadership", "Project Management", "FastAPI",
        "Pandas", "NumPy", "Docker", "Git"
    ]

    text_lower = text.lower()
    found = []

    for skill in known_skills:
        if skill.lower() in text_lower:
            found.append({"name": skill, "level": "Not specified"})

    return found[:12]


def _extract_work_experience_from_text(raw_text: str) -> List[dict]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    date_pattern = re.compile(
        r'(?i)\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|'
        r'january|february|march|april|june|july|august|september|october|november|december|'
        r'\d{1,2}/\d{4}|\d{4})\b'
    )

    experiences: List[dict] = []
    buffer: List[str] = []

    for line in lines:
        if date_pattern.search(line):
            if buffer:
                experiences.append({
                    "role": buffer[0][:120],
                    "company": buffer[1][:120] if len(buffer) > 1 else "Company",
                    "date": line[:60],
                    "responsibilities": buffer[2:5] if len(buffer) > 2 else []
                })
                buffer = []
        else:
            buffer.append(line)

    return experiences[:4]


def _build_cv_data_from_selected_cv(selected_cv: CV, current_user: User) -> dict:
    if not selected_cv.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected CV file path not found."
        )

    full_path = os.path.join(UPLOAD_BASE, selected_cv.file_path)

    if not os.path.exists(full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected CV file is missing."
        )

    with open(full_path, "rb") as f:
        pdf_bytes = f.read()

    raw_text = _extract_text_from_pdf_bytes_local(pdf_bytes)

    contact_information = [
        {"type": "name", "value": getattr(current_user, "full_name", None) or _extract_name_fallback(raw_text)},
        {"type": "email", "value": _extract_email(raw_text)},
        {"type": "phone", "value": _extract_phone(raw_text)},
    ]

    language_skills = _extract_languages_from_text(raw_text)
    it_skills = _extract_skills_from_text(raw_text)
    work_experience = _extract_work_experience_from_text(raw_text)
    detected_language = _detect_cv_language_from_text(raw_text)

    return {
        "contact_information": contact_information,
        "education": [],
        "work_experience": work_experience,
        "language_skills": language_skills,
        "it_skills": it_skills,
        "activities": [],
        "raw_text": raw_text,
        "detected_language": detected_language
    }


def _get_selected_or_favorite_cv(db: Session, user_id: UUID, cv_id: Optional[UUID]) -> CV:
    if cv_id:
        cv = db.query(CV).filter(
            CV.id == cv_id,
            CV.user_id == user_id
        ).first()

        if not cv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected CV not found."
            )

        return cv

    favorite_cv = db.query(CV).filter(
        CV.user_id == user_id,
        CV.is_favorite == True
    ).order_by(CV.created_at.desc()).first()

    if favorite_cv:
        return favorite_cv

    latest_cv = db.query(CV).filter(
        CV.user_id == user_id
    ).order_by(CV.created_at.desc()).first()

    if latest_cv:
        return latest_cv

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No CV found for this user."
    )


@router.post("/generate", response_model=CoverLetterResponse)
async def generate_cover_letter_endpoint(
    job_description: Optional[str] = Form(None),
    job_link: Optional[str] = Form(None),
    cv_id: Optional[UUID] = Form(None),
    title: str = Form("Cover Letter"),
    additional_notes: Optional[str] = Form(None),
    generate_both_languages: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not job_description and not job_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either job_description or job_link is required."
        )

    selected_cv = _get_selected_or_favorite_cv(
        db=db,
        user_id=current_user.id,
        cv_id=cv_id
    )

    resolved_job_description = job_description
    if not resolved_job_description and job_link:
        try:
            resolved_job_description = extract_job_offer_from_url(job_link)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not extract job offer from URL: {str(e)}"
            )

    cv_data = _build_cv_data_from_selected_cv(selected_cv, current_user)
    resolved_language = cv_data.get("detected_language") or "en"

    try:
        generation_result = generate_cover_letter(
            cv_data=cv_data,
            job_offer=resolved_job_description,
            additional_notes=additional_notes,
            language=resolved_language,
            generate_both_languages=generate_both_languages
        )
    except Exception as e:
        logger.exception("Cover letter generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cover letter generation failed: {str(e)}"
        )

    job_requirements = generation_result.get("job_requirements") or {}
    warnings = []

    primary_content = (
        generation_result.get("cover_letter_fr")
        if resolved_language == "fr"
        else generation_result.get("cover_letter_en")
    )

    if not primary_content:
        primary_content = generation_result.get("cover_letter_fr") or generation_result.get("cover_letter_en")

    if not primary_content:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Generated cover letter content is empty."
        )

    try:
        pdf_bytes = generate_cover_letter_pdf_bytes(primary_content)
        docx_bytes = generate_cover_letter_docx_bytes(primary_content)
    except Exception as e:
        logger.exception("Cover letter export generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cover letter files: {str(e)}"
        )

    pdf_path = save_bytes_file(
        content=pdf_bytes,
        folder="cover_letter",
        user_id=str(current_user.id),
        ext=".pdf"
    )

    docx_path = save_bytes_file(
        content=docx_bytes,
        folder="cover_letter",
        user_id=str(current_user.id),
        ext=".docx"
    )

    cover_letter = CoverLetter(
        user_id=current_user.id,
        cv_id=selected_cv.id,
        title=title,
        job_description=resolved_job_description,
        job_link=job_link,
        company_name=job_requirements.get("company_name"),
        position_title=job_requirements.get("position"),
        content=primary_content,
        language=resolved_language,
        pdf_path=pdf_path,
        docx_path=docx_path,
        warnings=warnings
    )

    db.add(cover_letter)
    db.commit()
    db.refresh(cover_letter)

    return CoverLetterResponse(
        id=cover_letter.id,
        cv_id=cover_letter.cv_id,
        title=cover_letter.title,
        job_description=cover_letter.job_description,
        job_link=cover_letter.job_link,
        company_name=cover_letter.company_name,
        position_title=cover_letter.position_title,
        content=cover_letter.content,
        language=cover_letter.language,
        pdf_url=get_file_url(cover_letter.pdf_path) if cover_letter.pdf_path else None,
        docx_url=get_file_url(cover_letter.docx_path) if cover_letter.docx_path else None,
        preview_url=f"/cover-letter/{cover_letter.id}/preview",
        warnings=[CoverLetterWarning(**w) for w in (cover_letter.warnings or [])],
        created_at=cover_letter.created_at
    )


@router.get("/{id}", response_model=CoverLetterResponse)
async def get_cover_letter(
    id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    cover = db.query(CoverLetter).filter(
        CoverLetter.id == id,
        CoverLetter.user_id == current_user.id
    ).first()

    if not cover:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cover letter not found or not owned by you."
        )

    return CoverLetterResponse(
        id=cover.id,
        cv_id=cover.cv_id,
        title=cover.title,
        job_description=cover.job_description,
        job_link=cover.job_link,
        company_name=cover.company_name,
        position_title=cover.position_title,
        content=cover.content,
        language=cover.language,
        pdf_url=get_file_url(cover.pdf_path) if cover.pdf_path else None,
        docx_url=get_file_url(cover.docx_path) if cover.docx_path else None,
        preview_url=f"/cover-letter/{cover.id}/preview" if cover.pdf_path else None,
        warnings=[CoverLetterWarning(**w) for w in (cover.warnings or [])],
        created_at=cover.created_at
    )


@router.get("/", response_model=List[CoverLetterResponse])
async def list_cover_letter_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    covers = db.query(CoverLetter).filter(
        CoverLetter.user_id == current_user.id
    ).order_by(CoverLetter.created_at.desc()).all()

    return [
        CoverLetterResponse(
            id=cover.id,
            cv_id=cover.cv_id,
            title=cover.title,
            job_description=cover.job_description,
            job_link=cover.job_link,
            company_name=cover.company_name,
            position_title=cover.position_title,
            content=cover.content,
            language=cover.language,
            pdf_url=get_file_url(cover.pdf_path) if cover.pdf_path else None,
            docx_url=get_file_url(cover.docx_path) if cover.docx_path else None,
            preview_url=f"/cover-letter/{cover.id}/preview" if cover.pdf_path else None,
            warnings=[CoverLetterWarning(**w) for w in (cover.warnings or [])],
            created_at=cover.created_at
        )
        for cover in covers
    ]


@router.get("/{id}/preview")
async def preview_cover_letter_pdf(
    id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    cover = db.query(CoverLetter).filter(
        CoverLetter.id == id,
        CoverLetter.user_id == current_user.id
    ).first()

    if not cover or not cover.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF preview not found."
        )

    absolute_path = os.path.join(UPLOAD_BASE, cover.pdf_path)
    if not os.path.exists(absolute_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file is missing."
        )

    return FileResponse(
        absolute_path,
        media_type="application/pdf",
        filename=f"{cover.title or 'cover-letter'}.pdf"
    )


@router.get("/{id}/download/pdf")
async def download_cover_letter_pdf(
    id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    cover = db.query(CoverLetter).filter(
        CoverLetter.id == id,
        CoverLetter.user_id == current_user.id
    ).first()

    if not cover or not cover.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found."
        )

    absolute_path = os.path.join(UPLOAD_BASE, cover.pdf_path)
    if not os.path.exists(absolute_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file is missing."
        )

    return FileResponse(
        absolute_path,
        media_type="application/pdf",
        filename=f"{cover.title or 'cover-letter'}.pdf"
    )


@router.get("/{id}/download/docx")
async def download_cover_letter_docx(
    id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    cover = db.query(CoverLetter).filter(
        CoverLetter.id == id,
        CoverLetter.user_id == current_user.id
    ).first()

    if not cover or not cover.docx_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DOCX file not found."
        )

    absolute_path = os.path.join(UPLOAD_BASE, cover.docx_path)
    if not os.path.exists(absolute_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DOCX file is missing."
        )

    return FileResponse(
        absolute_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{cover.title or 'cover-letter'}.docx"
    )
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from typing import Dict, Any, Annotated
from sqlalchemy.orm import Session

from apps.ai.app.models import ContactInformation, EducationEntry, WorkExperienceEntry
from ..ai.app.cv_grader import grade_cv, analyze_cv_metadata, format_client_output, GradingResult
from ..ai.app.generator import generate_cv_from_data, CVGenerationResult, CVContent
from ..ai.app.llm_client import extract_text_from_pdf_bytes
from ..authentication.users_oauth import get_current_user
from ..database import get_db
from ..models.users_model import User, UserPlan
from ..models.cv_model import CV, CVForm, CoverLetter
from ..schemas.cv_schema import CVEvaluationResponse, CVGenerateRequest, CoverLetterRequest, CVFormData, CVGenerateResponse
from ..utils.file_storage import save_uploaded_file, save_bytes_file, get_file_url

import os


router = APIRouter(
    prefix="/cv",
    tags=["CV Management"])


@router.post("/upload_and_evaluate", response_model=CVEvaluationResponse)
async def upload_and_evaluate_cv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    if user type is free then if he uplode PDF he genarate only scode and tips .
    work only essential plan
    """

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
    form_data: CVContent,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    
    allowed_plans = [UserPlan.STARTER, UserPlan.PREMIUM, UserPlan.ULTIMATE]
    if current_user.plan not in allowed_plans:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"CV generation requires one of these plans: {', '.join(allowed_plans)}. Please upgrade."
        )

# ei porjonto complet hoice, next din akhan thake suru korte hobe 
# ===================================================================================================
# ===================================================================================================
    # -------------------------------------------------------------------------
    # 1️⃣ Save submitted form data
    # -------------------------------------------------------------------------
    db_form = CVForm(
        user_id=current_user.id,
        personal_details=request.form_data.personal_details,
        education=request.form_data.education,
        employment=request.form_data.employment,
        languages=request.form_data.languages,
        skills=request.form_data.skills,
        activities=request.form_data.activities
    )
    db.add(db_form)
    db.commit()
    db.refresh(db_form)

    try:
        # -------------------------------------------------------------------------
        # 2️⃣ Determine language
        # -------------------------------------------------------------------------
        user_language = request.form_data.personal_details.get("language", "en").lower()
        if user_language not in ["en", "fr"]:
            user_language = "en"  

        # -------------------------------------------------------------------------
        # ৩. তোমার JSON → CVContent মডেলে ম্যাপিং (এটাই মূল পরিবর্তন)
        # -------------------------------------------------------------------------
        form = request.form_data.dict()  

        # Contact Information
        contact = ContactInformation(
            name=form["personal_details"].get("full_name", ""),
            email=form["personal_details"].get("email", ""),
            phone=form["personal_details"].get("phone", ""),
            address=form["personal_details"].get("address", "")
        )

        # Education Entries
        education_entries = []
        for edu in form.get("education", []):
            education_entries.append(
                EducationEntry(
                    institution=edu.get("institution", ""),
                    degree=edu.get("degree", ""),
                    location=edu.get("location", edu.get("city", "")),
                    date=f"{edu.get('start_year', '')} - {edu.get('end_year', '')}",
                    coursework=edu.get("coursework", []),
                    major=edu.get("major", None),
                    honors=edu.get("honors", None)
                )
            )

        # Work Experience Entries
        work_experiences = []
        for emp in form.get("employment", []):
            work_experiences.append(
                WorkExperienceEntry(
                    date=f"{emp.get('start_date', '')} - {emp.get('end_date', 'Present')}",
                    company=emp.get("company", ""),
                    location=emp.get("location", ""),
                    position=emp.get("position", ""),
                    duration=emp.get("duration", ""),
                    bullets=emp.get("bullets", [])
                )
            )

        # Languages
        languages_list = [f"{l['language']} ({l['proficiency']})" for l in form.get("languages", [])]

        # Skills
        skills_list = [f"{s['skill']} ({s['level']})" for s in form.get("skills", [])]

        # Activities / Interests
        activities_list = [a.get("description", a.get("activity", "")) for a in form.get("activities", [])]

        # CVContent অবজেক্ট তৈরি
        cv_content = CVContent(
            contact_information=[contact],
            education=education_entries,
            work_experience=work_experiences,
            experience=work_experiences,  # alias
            language_skills=languages_list,
            languages=languages_list,     # alias
            it_skills=skills_list,
            activities_interests=activities_list,
            domain="finance",             # পরে ডাইনামিক করতে পারো
            summary=None,
            certifications=[]             # যদি থাকে তাহলে যোগ করো
        )

        # -------------------------------------------------------------------------
        # ৪. AI দিয়ে CV জেনারেট করা
        # -------------------------------------------------------------------------
        generation_result: Dict[str, CVGenerationResult] = generate_cv_from_data(
            cv_content,
            languages=[user_language]
        )

        # নির্বাচিত ভাষার রেজাল্ট নাও
        cv_result = generation_result[user_language]

        # -------------------------------------------------------------------------
        # ৫. ফাইল সেভ (PDF + DOCX)
        # -------------------------------------------------------------------------
        pdf_path = save_bytes_file(
            cv_result.pdf_bytes,
            "generated",
            str(current_user.id),
            ".pdf"
        )
        docx_path = save_bytes_file(
            cv_result.docx_bytes,
            "generated",
            str(current_user.id),
            ".docx"
        )

        # -------------------------------------------------------------------------
        # ৬. ডাটাবেসে CV রেকর্ড সেভ
        # -------------------------------------------------------------------------
        db_cv = CV(
            user_id=current_user.id,
            file_path=pdf_path,  # প্রাইমারি PDF
            score=100,           # AI জেনারেটেড = পারফেক্ট
            tips=[]              # টিপস লাগবে না
        )
        db.add(db_cv)
        db.commit()
        db.refresh(db_cv)

        # -------------------------------------------------------------------------
        # ৭. ক্লায়েন্টকে রেসপন্স দাও
        # -------------------------------------------------------------------------
        return {
            "pdf_url": get_file_url(pdf_path),
            "docx_url": get_file_url(docx_path),
            "cv_id": str(db_cv.id),
            "language": user_language.upper(),
            "message": f"Your optimized CV has been generated successfully in {user_language.upper()}!"
        }

    except Exception as e:
        db.rollback()
        print(f"CV Generation Error: {str(e)}")  # লগিং
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CV generation failed: {str(e)}"
        )






@router.post("/cover-letter", response_model=Dict[str, str])
async def generate_cover_letter(
    request: CoverLetterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    পেইড ফিচার: রেফারেন্স CV থেকে কভার লেটার জেনারেট
    শুধু premium/ultimate প্ল্যানে কাজ করবে
    """
    if current_user.plan not in ["premium", "ultimate"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cover letter generation requires Premium or Ultimate plan."
        )

    # রেফারেন্স CV চেক
    ref_cv = db.query(CV).filter(
        CV.id == request.reference_cv_id,
        CV.user_id == current_user.id
    ).first()

    if not ref_cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reference CV not found or does not belong to you"
        )

    # এখানে তোমার AI-এ cover letter generate ফাংশন কল করতে হবে
    # অ্যাসাম করা হচ্ছে generate_cover_letter ফাংশন আছে বা অ্যাডাপ্ট করা যাবে
    try:
        # placeholder — তোমার generator.py-এ এই ফাংশন যোগ করতে হবে
        cover_result = generate_cv_from_data({
            "type": "cover_letter",
            "reference_cv_path": ref_cv.file_path,
            "job_description": request.job_description or ""
        })

        file_path = save_bytes_file(
            cover_result.pdf_bytes,
            "cover",
            str(current_user.id),
            f".{request.format}"
        )

        db_letter = CoverLetter(
            user_id=current_user.id,
            file_path=file_path
        )
        db.add(db_letter)
        db.commit()

        return {
            "file_url": get_file_url(file_path),
            "message": "Cover letter generated successfully!"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cover letter generation failed: {str(e)}"
        )
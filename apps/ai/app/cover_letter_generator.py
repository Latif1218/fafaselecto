from typing import Dict, Optional
import logging
from .llm_client import generate_completion

logger = logging.getLogger(__name__)


async def generate_cover_letter(
    cv_data: Dict,
    job_description: str,
    language: str = "en",
    user_name: Optional[str] = None,
    model: str = "gpt-4o-mini"
) -> str:
    """
    Generate a high-quality, achievement-focused cover letter.

    Args:
        cv_data: Structured CV dictionary
        job_description: Target job description
        language: "en" or "fr"
        user_name: Candidate full name
        model: OpenAI model name

    Returns:
        Clean cover letter text
    """

    try:
        # =========================
        # Extract CV Sections Safely
        # =========================
        personal = cv_data.get("personal_details", {}) or {}
        experience = cv_data.get("work_experience", []) or []
        education = cv_data.get("education", []) or []
        skills = cv_data.get("it_skills", []) or []

        candidate_name = user_name or personal.get("full_name", "Candidate")
        email = personal.get("email", "N/A")
        phone = personal.get("phone_number", "N/A")

        # =========================
        # Format Experience Section
        # =========================
        if experience:
            experience_lines = "\n".join(
                f"- {exp.get('position', 'Role')} at {exp.get('company', 'Company')} "
                f"({exp.get('date', 'N/A')})"
                for exp in experience[:3]
            )
        else:
            experience_lines = "Not specified"

        # =========================
        # Format Education Section
        # =========================
        if education:
            education_lines = "\n".join(
                f"- {edu.get('degree', 'Degree')} from {edu.get('institution', 'Institution')} "
                f"({edu.get('date', 'N/A')})"
                for edu in education[:2]
            )
        else:
            education_lines = "Not specified"

        # =========================
        # Format Skills
        # =========================
        skills_text = ", ".join(skills[:8]) if skills else "Not specified"

        # =========================
        # Build CV Summary (SAFE)
        # =========================
        cv_summary = f"""
Name: {candidate_name}
Email: {email}
Phone: {phone}

Key Experience:
{experience_lines}

Education:
{education_lines}

Top Skills: {skills_text}
"""

        # =========================
        # Language Handling
        # =========================
        lang_full = "English" if language == "en" else "French"

        # =========================
        # Build Prompt
        # =========================
        user_prompt = f"""
You are an elite executive-level cover letter writer.

Write a highly persuasive, achievement-focused cover letter (280–380 words) in {lang_full}.

Candidate Profile:
{cv_summary}

Job Description:
{job_description}

Strict Rules:
- Start with: Dear Hiring Manager
- Opening: Strong hook (2-3 lines)
- Body: 2-3 quantified achievements aligned with job
- Show genuine interest in company
- Confident closing call-to-action
- Tone: Professional, confident, zero fluff
- Word limit: 280-380 words (never exceed 400)
- Output ONLY the letter text (no markdown, no explanation)

Generate now:
"""

        messages = [
            {
                "role": "system",
                "content": "You are a world-class executive cover letter expert."
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        # =========================
        # Call LLM
        # =========================
        cover_letter = await generate_completion(
            messages=messages,
            model=model,
            temperature=0.65,
            max_tokens=900,
            top_p=0.95
        )

        if not cover_letter:
            raise ValueError("Empty response from language model")

        logger.info(
            f"Cover letter generated | Language: {language} | "
            f"Length: {len(cover_letter)} chars"
        )

        return cover_letter.strip()

    except Exception as e:
        logger.error(f"Cover letter generation failed: {str(e)}")
        raise RuntimeError(f"Cover letter generation failed: {str(e)}")
from typing import Dict, Optional
import logging
from .llm_client import generate_completion


logger = logging.getLogger(__name__)


async def generate_cover_letter(
    cv_data: Dict,
    job_description: str,
    language: str = "en",
    user_name: Optional[str] = None,
    tone: str = "professional",
    length: int = 350,
    model: str = "gpt-4o-mini"
) -> str:
    """
    Generate a high-quality, achievement-focused cover letter.

    Args:
        cv_data: Structured CV dictionary
        job_description: Target job description
        language: "en" or "fr"
        user_name: Candidate full name
        tone: Tone style ("professional", "confident", etc.)
        length: Target word count (default 350)
        model: OpenAI model name

    Returns:
        Clean cover letter text
    """
    try:
        # Extract CV sections safely
        personal = cv_data.get("personal_details", {}) or {}
        experience = cv_data.get("work_experience", []) or []
        education = cv_data.get("education", []) or []
        skills = cv_data.get("it_skills", []) or []
        languages = cv_data.get("language_skills", []) or []

        # Resolve candidate name with fallback
        candidate_name = (
            personal.get("full_name")
            or personal.get("name")
            or user_name
            or "Candidate"
        )

        email = personal.get("email", "")
        phone = personal.get("phone_number", "")

        # Debug info
        print("PERSONAL DATA:", personal)
        print("USER NAME:", user_name)
        print("FINAL NAME:", candidate_name)

        # Format experience lines
        exp_lines = [
            f"- {exp.get('position','Role')} at {exp.get('company','Company')} ({exp.get('date','N/A')})"
            for exp in experience[:3]
        ]

        # Format education lines
        edu_lines = [
            f"- {edu.get('degree','Degree')} from {edu.get('institution','Institution')} ({edu.get('date','N/A')})"
            for edu in education[:2]
        ]

        exp_text = "\n".join(exp_lines) if exp_lines else "No experience listed"
        edu_text = "\n".join(edu_lines) if edu_lines else "No education listed"

        # Build CV summary
        cv_summary = f"""
Name: {candidate_name}
Email: {email}
Phone: {phone}

Key Experience:
{exp_text}

Education:
{edu_text}

Top Skills: {', '.join(str(s) for s in skills[:8]) or 'Not specified'}
Languages: {', '.join(str(l) for l in languages[:5]) or 'Not specified'}
"""

        lang_full = "English" if language == "en" else "French"

        # Build prompt
        user_prompt = f"""
You are an elite executive-level cover letter writer who has placed candidates at Goldman Sachs, McKinsey, Google, Jane Street, Citadel, BCG, and top startups.

Write a highly persuasive, achievement-focused cover letter ({length} words, strictly between {length-50} and {length+50} words) in {lang_full}.

Candidate Profile:
{cv_summary}

Job Description:
{job_description}

Strict Rules:
- Address: "Dear Hiring Manager"
- Opening (2-3 sentences): Powerful hook — show immediate relevance + excitement for THIS role/company
- Body (3-4 paragraphs):
  - 2-3 quantified achievements from CV that match job requirements (use numbers/metrics)
  - Show deep understanding of company/challenges + how candidate solves them
  - Highlight 1 cultural/fit element (leadership, analytical mindset, etc.)
- Closing: Confident call-to-action + thanks
- Tone: {tone} (confident but humble, professional, no arrogance, zero fluff)
- Language: Perfect {lang_full} grammar, sophisticated vocabulary
- Length: {length} words (never exceed {length+50})
- Output ONLY the cover letter text — NO intro, NO explanation, NO markdown labels

Generate the cover letter now:
"""

        messages = [
            {"role": "system", "content": "You are a world class cover letter expert"},
            {"role": "user", "content": user_prompt}
        ]

        result = await generate_completion(
            messages=messages,
            model=model,
            temperature=0.65,
            max_tokens=900
        )

        return result.strip()

    except Exception as e:
        logger.error(f"Cover letter generation failed: {str(e)}")
        raise RuntimeError(f"Cover letter generation failed: {str(e)}")
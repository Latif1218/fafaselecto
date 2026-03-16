from typing import Dict, Optional
import logging
from .llm_client import generate_completion


logger = logging.getLogger(__name__)


async def generate_cover_letter(
    cv_data: Dict,
    job_description: str,
    job_link: Optional[str] = None,
    language: str = "en",
    user_name: Optional[str] = None,
    tone: str = "professional",
    length: int = 350,
    model: str = "gpt-4o-mini"
) -> str:
    """
    Generate a high-quality, achievement-focused cover letter
    using CV data and job description.
    """

    try:

        personal = cv_data.get("personal_details") or {}
        experience = cv_data.get("work_experience") or []
        education = cv_data.get("education") or []
        skills = cv_data.get("it_skills") or []
        languages = cv_data.get("language_skills") or []

        candidate_name = (
            personal.get("full_name")
            or personal.get("name")
            or user_name
            or "Candidate"
        )

        email = personal.get("email", "")
        phone = personal.get("phone_number", "")

        logger.info(f"Generating cover letter for: {candidate_name}")

        exp_lines = []

        for exp in experience[:3]:
            position = exp.get("position", "Role")
            company = exp.get("company", "Company")
            date = exp.get("date", "N/A")

            exp_lines.append(
                f"- {position} at {company} ({date})"
            )

        exp_text = "\n".join(exp_lines) if exp_lines else "No experience listed"

        edu_lines = []

        for edu in education[:2]:
            degree = edu.get("degree", "Degree")
            institution = edu.get("institution", "Institution")
            date = edu.get("date", "N/A")

            edu_lines.append(
                f"- {degree} from {institution} ({date})"
            )

        edu_text = "\n".join(edu_lines) if edu_lines else "No education listed"

        skills_text = ", ".join(str(s) for s in skills[:8]) if skills else "Not specified"
        languages_text = ", ".join(str(l) for l in languages[:5]) if languages else "Not specified"

        cv_summary = f"""
Name: {candidate_name}
Email: {email}
Phone: {phone}

Key Experience:
{exp_text}

Education:
{edu_text}

Top Skills: {skills_text}
Languages: {languages_text}
"""

        lang_full = "English" if language == "en" else "French"

        job_link_text = job_link if job_link else "Not provided"

        user_prompt = f"""
You are an elite executive-level cover letter writer who has helped candidates get hired at Goldman Sachs, McKinsey, Google, Jane Street, Citadel, BCG, and top startups.

Write a highly persuasive, achievement-focused cover letter.

Language: {lang_full}
Target Length: {length} words (acceptable range {length-50} to {length+50})

Candidate Profile:
{cv_summary}

Job Description:
{job_description}

Job Posting Link:
{job_link_text}

STRICT INSTRUCTIONS:

Opening:
- Start with "Dear Hiring Manager"
- 2–3 sentences maximum
- Show excitement for THIS role and relevance

Body:
- 3 paragraphs
- Highlight 2–3 strong achievements from experience
- Use measurable results where possible
- Demonstrate alignment with the job requirements
- Show understanding of the company’s needs

Closing:
- Confident closing statement
- Express enthusiasm to contribute
- Thank the reader

Style Rules:
- Tone: {tone}
- Professional but natural
- No exaggeration
- No generic filler phrases
- Clear structure

Output Requirements:
- Only return the cover letter text
- Do NOT include explanations
- Do NOT include headings or markdown
"""

        messages = [
            {
                "role": "system",
                "content": "You are a world-class cover letter writer."
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        result = await generate_completion(
            messages=messages,
            model=model,
            temperature=0.65,
            max_tokens=900
        )

        if not result:
            raise ValueError("LLM returned empty response")

        return result.strip()

    except Exception as e:

        logger.error(f"Cover letter generation failed: {str(e)}")

        raise RuntimeError(
            f"Cover letter generation failed: {str(e)}"
        )
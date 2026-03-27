from typing import Dict, Optional, List, Any
import logging
import re
import json
from datetime import datetime
from .llm_client import generate_completion


logger = logging.getLogger(__name__)


def infer_language_from_cv_data(cv_data: Dict) -> str:
    detected_language = cv_data.get("detected_language")
    if detected_language in {"en", "fr"}:
        return detected_language

    language_skills = cv_data.get("language_skills") or []
    joined = " ".join(str(x).lower() for x in language_skills)

    if "french" in joined or "français" in joined or "francais" in joined:
        return "fr"

    return "en"


def build_cover_letter_warnings(
    cv_data: Dict,
    company_name: Optional[str],
    position_title: Optional[str],
    requirements: List[str],
    generated_text: str,
    used_fallback: bool = False
) -> List[Dict[str, str]]:
    warnings: List[Dict[str, str]] = []

    if not company_name:
        warnings.append({
            "code": "MISSING_COMPANY_NAME",
            "message": "Company name could not be confidently extracted from the job offer.",
            "severity": "warning"
        })

    if not position_title:
        warnings.append({
            "code": "MISSING_POSITION_TITLE",
            "message": "Position title could not be confidently extracted from the job offer.",
            "severity": "warning"
        })

    if len(requirements) < 2:
        warnings.append({
            "code": "LOW_REQUIREMENT_SIGNAL",
            "message": "Few explicit job requirements were detected. Tailoring may be less precise.",
            "severity": "warning"
        })

    experience = cv_data.get("work_experience") or []
    raw_text = cv_data.get("raw_text") or ""
    if len(experience) == 0 and not raw_text.strip():
        warnings.append({
            "code": "LOW_CV_DATA",
            "message": "The selected CV has limited readable data.",
            "severity": "warning"
        })

    word_count = len(re.findall(r"\b\w+\b", generated_text))
    if word_count < 250 or word_count > 350:
        warnings.append({
            "code": "WORD_COUNT_OUT_OF_RANGE",
            "message": "Generated letter is outside the target 250–350 word range.",
            "severity": "warning"
        })

    if used_fallback:
        warnings.append({
            "code": "FALLBACK_GENERATION_USED",
            "message": "AI generation was unavailable, so a simpler fallback cover letter was generated.",
            "severity": "warning"
        })

    return warnings


async def extract_offer_insights_with_llm(
    job_description: str,
    model: str = "gpt-4o-mini"
) -> Dict[str, Any]:
    prompt = f"""
Extract the following from this job offer and return ONLY valid JSON:

{{
  "company_name": "string or null",
  "position_title": "string or null",
  "key_requirements": ["requirement 1", "requirement 2", "requirement 3"]
}}

Rules:
- Extract only from the provided offer
- Do not invent
- Keep requirements concise
- Return only JSON

Job Offer:
{job_description}
"""

    messages = [
        {"role": "system", "content": "You extract structured hiring data accurately."},
        {"role": "user", "content": prompt}
    ]

    try:
        result = await generate_completion(
            messages=messages,
            model=model,
            temperature=0.1,
            max_tokens=400
        )
        return json.loads(result)
    except Exception:
        logger.warning("LLM extraction failed, using safe empty insights fallback")
        return {
            "company_name": None,
            "position_title": None,
            "key_requirements": []
        }


def _build_fallback_cover_letter(
    candidate_name: str,
    email: str,
    phone: str,
    address: str,
    company_name: Optional[str],
    position_title: Optional[str],
    resolved_language: str
) -> str:
    today_str = datetime.utcnow().strftime("%d/%m/%Y")
    safe_company = company_name or "Hiring Team"
    safe_position = position_title or "this role"

    if resolved_language == "fr":
        return f"""{
candidate_name}
{email}
{phone}
{address}

{safe_company}
{today_str}
Objet: Candidature au poste de {safe_position}

Madame, Monsieur,

Je vous adresse ma candidature pour le poste de {safe_position}. Mon parcours et mes compétences me permettent d'apporter une contribution sérieuse et structurée à votre équipe, dans un cadre exigeant et orienté résultats.

Mon CV met en avant des expériences, des compétences techniques et des éléments de formation qui peuvent être mobilisés pour répondre aux attentes de ce poste. J'accorde une attention particulière à la qualité du travail, à l'organisation, à l'analyse et à l'adaptation aux besoins de l'entreprise. Je souhaite mettre cette base au service de {safe_company} avec rigueur et professionnalisme.

Je suis particulièrement motivé à l'idée d'échanger avec vous afin de présenter plus concrètement la manière dont mon profil peut répondre à vos besoins. Disponible pour un entretien à votre convenance, je vous remercie pour l'attention portée à ma candidature.

Cordialement,

{candidate_name}""".strip()

    return f"""{
candidate_name}
{email}
{phone}
{address}

{safe_company}
{today_str}
Subject: Application for the position of {safe_position}

Dear Hiring Manager,

I am writing to apply for the position of {safe_position}. My background, skills, and professional approach allow me to contribute in a serious and practical way to a demanding team environment.

My CV highlights relevant experience, technical skills, and educational foundations that can support the needs of this role. I value strong execution, organization, analysis, and adaptability, and I would be glad to bring those strengths to {safe_company}. I am especially interested in contributing in a role where quality, consistency, and impact matter.

I would welcome the opportunity to discuss how my profile could support your team more specifically. I am available for an interview at your convenience, and I appreciate your time and consideration.

Sincerely,

{candidate_name}""".strip()


async def generate_cover_letter(
    cv_data: Dict,
    job_description: str,
    job_link: Optional[str] = None,
    language: Optional[str] = None,
    user_name: Optional[str] = None,
    model: str = "gpt-4o-mini"
) -> Dict[str, Any]:
    """
    Generate a structured one-page cover letter with warnings.
    Falls back gracefully if LLM quota/errors occur.
    """

    try:
        personal = cv_data.get("personal_details") or {}
        experience = cv_data.get("work_experience") or []
        education = cv_data.get("education") or []
        skills = cv_data.get("it_skills") or []
        language_skills = cv_data.get("language_skills") or []
        raw_text = cv_data.get("raw_text") or ""

        candidate_name = (
            personal.get("full_name")
            or personal.get("name")
            or user_name
            or "Candidate"
        )

        email = personal.get("email", "")
        phone = personal.get("phone_number", "")
        address = personal.get("address", "")

        resolved_language = language or infer_language_from_cv_data(cv_data)
        lang_full = "French" if resolved_language == "fr" else "English"

        insights = await extract_offer_insights_with_llm(
            job_description=job_description,
            model=model
        )

        company_name = insights.get("company_name")
        position_title = insights.get("position_title")
        requirements = insights.get("key_requirements") or []

        exp_lines = []
        for exp in experience[:5]:
            position = exp.get("position", "Role")
            company = exp.get("company", "Company")
            date = exp.get("date", "N/A")
            achievements = (
                exp.get("achievements")
                or exp.get("highlights")
                or exp.get("responsibilities")
                or exp.get("bullets")
                or []
            )

            achievement_text = ""
            if isinstance(achievements, list) and achievements:
                achievement_text = "; ".join(str(x) for x in achievements[:3])

            exp_lines.append(
                f"- Position: {position} | Company: {company} | Date: {date} | Evidence: {achievement_text}"
            )

        edu_lines = []
        for edu in education[:3]:
            degree = edu.get("degree", "Degree")
            institution = edu.get("institution", "Institution")
            date = edu.get("date", "N/A")
            edu_lines.append(f"- {degree} | {institution} | {date}")

        skills_text = ", ".join(str(s) for s in skills[:12]) if skills else "Not specified"
        languages_text = ", ".join(str(l) for l in language_skills[:8]) if language_skills else "Not specified"
        today_str = datetime.utcnow().strftime("%d/%m/%Y")

        cv_summary = f"""
Candidate Name: {candidate_name}
Email: {email}
Phone: {phone}
Address: {address}

Experience:
{chr(10).join(exp_lines) if exp_lines else "No structured experience listed"}

Education:
{chr(10).join(edu_lines) if edu_lines else "No structured education listed"}

Skills:
{skills_text}

Languages:
{languages_text}

Raw CV Text:
{raw_text[:5000] if raw_text else "Not available"}
"""

        requirement_text = "\n".join([f"- {r}" for r in requirements]) if requirements else "- No explicit requirements extracted"

        user_prompt = f"""
You are a world-class cover letter writer.

Write a one-page cover letter in {lang_full}.

The output MUST contain exactly 4 logical blocks in this order:
1) Header
2) Opening
3) Body
4) Closing

HARD RULES:
- Header must include:
  - candidate contact info
  - company name
  - date
  - subject line exactly in this format for French:
    "Objet: Candidature au poste de [POSITION]"
  - for English use:
    "Subject: Application for the position of [POSITION]"
- Opening must connect the candidate specifically to this company and role
- Body must map real CV experiences to job requirements
- Use concrete metrics only if present in CV evidence or raw CV text
- Never invent achievements, employers, dates, numbers, tools, or impact
- Zero generic filler
- Do not use clichés like "dynamic and motivated" or "dynamique et motivé"
- 250 to 350 words only
- Must feel concise enough to fit one page
- No markdown
- No headings labels like "Opening", "Body", "Closing"
- Natural business letter style
- If company name is missing, use "Hiring Team"
- If position title is missing, use "this role"

JOB OFFER STRUCTURE:
Company Name: {company_name or "Unknown"}
Position Title: {position_title or "Unknown"}
Key Requirements:
{requirement_text}

CANDIDATE CV DATA:
{cv_summary}

RAW JOB OFFER:
{job_description}

JOB LINK:
{job_link or "Not provided"}

DATE:
{today_str}

IMPORTANT MATCHING RULE:
Use ONLY evidence present in the CV data above.
If a requirement cannot be supported by the CV data, do not claim it.
"""

        messages = [
            {
                "role": "system",
                "content": "You write precise, tailored, non-generic cover letters with zero hallucination."
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        used_fallback = False

        try:
            result = await generate_completion(
                messages=messages,
                model=model,
                temperature=0.35,
                max_tokens=900
            )

            if not result:
                raise ValueError("LLM returned empty response")

            content = result.strip()

        except Exception as llm_error:
            logger.warning(f"LLM cover letter generation failed, using fallback: {str(llm_error)}")
            used_fallback = True
            content = _build_fallback_cover_letter(
                candidate_name=candidate_name,
                email=email,
                phone=phone,
                address=address,
                company_name=company_name,
                position_title=position_title,
                resolved_language=resolved_language
            )

        warnings = build_cover_letter_warnings(
            cv_data=cv_data,
            company_name=company_name,
            position_title=position_title,
            requirements=requirements,
            generated_text=content,
            used_fallback=used_fallback
        )

        return {
            "content": content,
            "language": resolved_language,
            "company_name": company_name,
            "position_title": position_title,
            "warnings": warnings
        }

    except Exception as e:
        logger.error(f"Cover letter generation failed: {str(e)}")
        raise RuntimeError(f"Cover letter generation failed: {str(e)}")
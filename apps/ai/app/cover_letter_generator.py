
from .logger import get_logger
logger = get_logger(__name__)

"""
Postulae Cover Letter Generator.

Generates premium cover letters for elite finance/consulting roles.
Optimized for Goldman Sachs, McKinsey, BCG, JP Morgan, Bain, etc.

ARCHITECTURE:
1. Extract job requirements (Claude Haiku 3) → JSON
2. Match CV achievements to job → Internal logic
3. Generate cover letter (Claude Sonnet 4.5) → Text
4. Translate if needed (Claude Haiku 3) → Text
5. Layout HTML/CSS → PDF (Playwright) + DOCX

CONSTRAINTS:
- 1 page A4 exactly
- 250-400 words (target: 300-350)
- 4-5 paragraphs
- FR + EN support
- Cost target: $0.0155/letter

PRICING (Mars 2026):
- Extract job (Haiku 3): ~$0.0002
- Generate (Sonnet 4.5): ~$0.0145
- Translate (Haiku 3): ~$0.0003
- PDF (Playwright): $0.0000
- TOTAL: ~$0.0150/letter (FR+EN)
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from anthropic import Anthropic
from dotenv import load_dotenv
from apps.config import ANTHROPIC_API_KEY

# Import density validation
import sys
sys.path.insert(0, str(Path(__file__).parent))
from .cover_letter_density import (
    validate_cover_letter_density,
    trim_cover_letter_to_target,
    OPTIMAL_MIN,
    OPTIMAL_MAX
)

load_dotenv()

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Model identifiers
MODEL_SONNET = "claude-sonnet-4-5-20250929"  # Generation (best constraints)
MODEL_HAIKU = "claude-haiku-4-5-20251001"      # Extraction + Translation (fast + cheap)

# Load prompts
PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(filename: str) -> str:
    """Load prompt from prompts/ directory."""
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def extract_job_requirements(job_offer: str) -> Dict:
    """
    Extract structured job requirements from offer text.

    Uses Claude Haiku 3 (fast + cheap).

    Args:
        job_offer: Raw job offer text (copy-pasted by user)

    Returns:
        Dictionary with structured requirements:
        {
            "company_name": str | null,
            "position": str | null,
            "division": str | null,
            "required_skills": List[str],
            "experience_years": str | null,
            "sector": str | null,
            "key_values": List[str],
            "key_responsibilities": List[str]
        }

    Raises:
        ValueError: If extraction fails
    """
    try:
        # Load extraction prompt
        system_prompt = load_prompt("extract_job_requirements.txt")

        # Call Claude Haiku 3
        response = anthropic_client.messages.create(
            model=MODEL_HAIKU,
            max_tokens=2048,
            temperature=0.1,  # Low temp for factual extraction
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Offre d'emploi à analyser:\n\n{job_offer}"
                }
            ]
        )

        # Parse JSON response
        content = response.content[0].text
        try:
            requirements = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON if wrapped in markdown
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
                requirements = json.loads(json_str)
            else:
                raise ValueError(f"Failed to parse job requirements JSON: {content[:200]}")

        # Validate required fields
        required_fields = ["company_name", "position", "required_skills", "key_responsibilities"]
        for field in required_fields:
            if field not in requirements:
                requirements[field] = None

        return requirements

    except Exception as e:
        raise ValueError(f"Job requirements extraction failed: {str(e)}")


def match_cv_to_job(cv_data: Dict, job_requirements: Dict) -> Dict:
    """
    Match CV achievements to job requirements.

    Internal logic (no LLM call).

    Args:
        cv_data: Structured CV data (from Postulae CV generator)
        job_requirements: Extracted job requirements

    Returns:
        Dictionary with matched achievements:
        {
            "matched_achievements": List[Dict],  # Top 2-3 achievements with metrics
            "matched_skills": List[str],         # Skills from CV matching job
            "cultural_fit_signals": List[str]    # Values alignment
        }
    """
    matched = {
        "matched_achievements": [],
        "matched_skills": [],
        "cultural_fit_signals": []
    }

    # Extract required skills (lowercase for matching)
    required_skills = [s.lower() for s in job_requirements.get("required_skills", [])]

    # Extract work experiences with metrics
    work_experiences = cv_data.get("work_experience", [])

    for exp in work_experiences:
        # Check if experience matches required skills
        exp_text = json.dumps(exp, ensure_ascii=False).lower()

        # Score experience based on skill matches
        skill_matches = sum(1 for skill in required_skills if skill in exp_text)

        # Look for quantified achievements (%, €, $, numbers)
        has_metrics = any(char in str(exp.get("responsibilities", [])) for char in ["%", "€", "$"])

        if skill_matches > 0 or has_metrics:
            matched["matched_achievements"].append({
                "company": exp.get("company", ""),
                "role": exp.get("role", ""),
                "responsibilities": exp.get("responsibilities", []),
                "skill_match_count": skill_matches
            })

    # Sort by relevance (skill matches + has metrics)
    matched["matched_achievements"].sort(
        key=lambda x: x["skill_match_count"],
        reverse=True
    )

    # Keep top 3 most relevant
    matched["matched_achievements"] = matched["matched_achievements"][:3]

    # Match skills
    cv_skills = []
    if "it_skills" in cv_data:
        cv_skills.extend([s.get("name", "") for s in cv_data["it_skills"]])
    if "language_skills" in cv_data:
        cv_skills.extend([s.get("language", "") for s in cv_data["language_skills"]])

    for skill in cv_skills:
        if any(req_skill in skill.lower() for req_skill in required_skills):
            matched["matched_skills"].append(skill)

    # Cultural fit signals (basic keyword matching)
    key_values = job_requirements.get("key_values", [])
    if key_values:
        # Look for collaboration, leadership, analytical mentions in CV
        cv_text = json.dumps(cv_data, ensure_ascii=False).lower()
        value_keywords = {
            "collaboration": ["team", "collaboration", "cross-functional"],
            "leadership": ["led", "leadership", "managed", "directed"],
            "analytical": ["analytical", "data", "analysis", "metrics"],
            "client": ["client", "customer", "stakeholder"]
        }

        for value in key_values:
            value_lower = value.lower()
            for keyword_category, keywords in value_keywords.items():
                if keyword_category in value_lower:
                    if any(kw in cv_text for kw in keywords):
                        matched["cultural_fit_signals"].append(value)
                        break

    return matched


def _json_to_text(cover_letter_json: Dict) -> str:
    """Convert cover letter JSON to full text string.

    Args:
        cover_letter_json: JSON with opening, paragraphs, closing

    Returns:
        Full text with all sections combined
    """
    parts = [cover_letter_json["opening"]]
    parts.extend(cover_letter_json["paragraphs"])
    parts.append(cover_letter_json["closing"])
    return "\n\n".join(parts)


def generate_cover_letter_content(
    cv_data: Dict,
    job_requirements: Dict,
    matched_data: Dict,
    additional_notes: Optional[str] = None,
    language: str = "fr"
) -> Dict:
    """
    Generate cover letter content using Claude Sonnet 4.5 (JSON structured output).

    Args:
        cv_data: Structured CV data
        job_requirements: Extracted job requirements
        matched_data: Matched achievements from match_cv_to_job()
        additional_notes: Optional user notes (motivations, networking, etc.)
        language: "fr" or "en"

    Returns:
        Dictionary with:
        {
            "opening": str,
            "paragraphs": List[str],  # 4 paragraphs
            "closing": str
        }

    Raises:
        ValueError: If generation fails or doesn't meet constraints
    """
    try:
        # Load NEW JSON-based generation prompt
        system_prompt = load_prompt("generate_cover_letter_json.txt")

        # Prepare inputs for LLM
        inputs = {
            "CV_DATA": cv_data,
            "JOB_REQUIREMENTS": job_requirements,
            "MATCHED_ACHIEVEMENTS": matched_data["matched_achievements"],
            "MATCHED_SKILLS": matched_data["matched_skills"],
            "CULTURAL_FIT_SIGNALS": matched_data["cultural_fit_signals"],
            "ADDITIONAL_NOTES": additional_notes or "None provided",
            "LANGUAGE": language
        }

        # Build user message
        user_message = f"""Generate a cover letter with these inputs:

LANGUAGE: {language.upper()}

CV DATA:
{json.dumps(cv_data, ensure_ascii=False, indent=2)}

JOB REQUIREMENTS:
{json.dumps(job_requirements, ensure_ascii=False, indent=2)}

MATCHED ACHIEVEMENTS (use for paragraphs[1] and paragraphs[2]):
{json.dumps(matched_data["matched_achievements"], ensure_ascii=False, indent=2)}

MATCHED SKILLS:
{json.dumps(matched_data["matched_skills"], ensure_ascii=False, indent=2)}

CULTURAL FIT SIGNALS:
{json.dumps(matched_data["cultural_fit_signals"], ensure_ascii=False, indent=2)}

ADDITIONAL NOTES FROM CANDIDATE:
{additional_notes or "None"}

Return ONLY the JSON object following the exact structure in the system prompt.
Target: 260-275 words total, 4 paragraphs in the "paragraphs" array.
"""

        # Call Claude Sonnet 4.5
        response = anthropic_client.messages.create(
            model=MODEL_SONNET,
            max_tokens=2048,
            temperature=0.5,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )

        # Extract text and parse JSON
        response_text = response.content[0].text.strip()

        # Extract JSON from response (might be wrapped in code blocks)
        if "```json" in response_text:
            # Extract from code block
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            # Generic code block
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        # Parse JSON
        try:
            cover_letter_json = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse cover letter JSON: {str(e)}\nResponse: {response_text[:500]}")

        # Validate JSON structure
        required_fields = ["opening", "paragraphs", "closing"]
        for field in required_fields:
            if field not in cover_letter_json:
                raise ValueError(f"Missing required field in JSON: {field}")

        if not isinstance(cover_letter_json["paragraphs"], list):
            raise ValueError("'paragraphs' must be an array")

        if len(cover_letter_json["paragraphs"]) != 4:
            raise ValueError(f"Expected 4 paragraphs, got {len(cover_letter_json['paragraphs'])}")

        # Calculate total word count
        total_text = cover_letter_json["opening"] + " " + " ".join(cover_letter_json["paragraphs"]) + " " + cover_letter_json["closing"]
        word_count = len(total_text.split())

        logger.info(f"      Word count: {word_count} words")

        if word_count > 350:
            logger.warning(f"      [WARN] Word count high ({word_count} words), may risk overflow")
        elif word_count < 240:
            raise ValueError(f"Cover letter too short: {word_count} words (minimum 240)")

        return cover_letter_json

    except Exception as e:
        raise ValueError(f"Cover letter generation failed: {str(e)}")


def translate_cover_letter(
    cover_letter: str,
    source_lang: str,
    target_lang: str
) -> str:
    """
    Translate cover letter using Claude Haiku 3.

    Args:
        cover_letter: Cover letter text to translate
        source_lang: Source language ("fr" or "en")
        target_lang: Target language ("fr" or "en")

    Returns:
        Translated cover letter text (same length ±10%)

    Raises:
        ValueError: If translation fails
    """
    try:
        # Load translation prompt
        system_prompt_template = load_prompt("translate_cover_letter.txt")
        system_prompt = system_prompt_template.replace("{source_lang}", source_lang.upper())
        system_prompt = system_prompt.replace("{target_lang}", target_lang.upper())

        # Call Claude Haiku 3
        response = anthropic_client.messages.create(
            model=MODEL_HAIKU,
            max_tokens=2048,
            temperature=0.3,  # Low temp for accurate translation
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Translate this cover letter from {source_lang.upper()} to {target_lang.upper()}:\n\n{cover_letter}"
                }
            ]
        )

        # Extract translated text
        translated = response.content[0].text.strip()

        # Validate length (should be similar ±20%)
        orig_words = len(cover_letter.split())
        trans_words = len(translated.split())
        length_diff = abs(trans_words - orig_words) / orig_words

        if length_diff > 0.25:  # Allow 25% variation (FR<->EN can differ)
            logger.warning(f"⚠️ Warning: Translation length differs by {length_diff*100:.1f}% ({orig_words} → {trans_words} words)")

        return translated

    except Exception as e:
        raise ValueError(f"Translation failed: {str(e)}")


def generate_cover_letter(
    cv_data: Dict,
    job_offer: str,
    additional_notes: Optional[str] = None,
    language: str = "fr",
    generate_both_languages: bool = False
) -> Dict:
    """
    Generate complete cover letter (orchestrator).

    Pipeline:
    1. Extract job requirements (Haiku 3)
    2. Match CV to job (internal logic)
    3. Generate cover letter (Sonnet 4.5)
    4. Translate if needed (Haiku 3)
    5. Return structured result

    Args:
        cv_data: Structured CV data from Postulae
        job_offer: Raw job offer text
        additional_notes: Optional user notes
        language: Primary language ("fr" or "en")
        generate_both_languages: If True, generate FR + EN

    Returns:
        Dictionary with:
        {
            "job_requirements": Dict,
            "matched_data": Dict,
            "cover_letter_fr": str | None,
            "cover_letter_en": str | None,
            "word_count_fr": int | None,
            "word_count_en": int | None,
            "generation_time": float,
            "cost_estimate": float
        }

    Raises:
        ValueError: If generation fails
    """
    start_time = time.time()
    result = {
        "job_requirements": None,
        "matched_data": None,
        "cover_letter_fr": None,
        "cover_letter_en": None,
        "word_count_fr": None,
        "word_count_en": None,
        "generation_time": 0.0,
        "cost_estimate": 0.0
    }

    # Cost tracking
    cost = 0.0

    # Step 1: Extract job requirements
    logger.info("[1/4] Extracting job requirements...")
    job_requirements = extract_job_requirements(job_offer)
    result["job_requirements"] = job_requirements
    cost += 0.0002  # Haiku extraction cost

    logger.info(f"   Company: {job_requirements.get('company_name', 'Unknown')}")
    logger.info(f"   Position: {job_requirements.get('position', 'Unknown')}")
    logger.info(f"   Skills: {len(job_requirements.get('required_skills', []))} required")

    # Step 2: Match CV to job
    logger.info("[2/4] Matching CV achievements to job...")
    matched_data = match_cv_to_job(cv_data, job_requirements)
    result["matched_data"] = matched_data

    logger.info(f"   Matched achievements: {len(matched_data['matched_achievements'])}")
    logger.info(f"   Matched skills: {len(matched_data['matched_skills'])}")

    # Step 3: Generate cover letter in primary language
    logger.info(f"[3/4] Generating cover letter in {language.upper()}...")
    cover_letter_json_primary = generate_cover_letter_content(
        cv_data,
        job_requirements,
        matched_data,
        additional_notes,
        language
    )
    cost += 0.0145  # Sonnet generation cost

    # Convert JSON to full text for word count
    full_text_primary = _json_to_text(cover_letter_json_primary)

    if language == "fr":
        result["cover_letter_fr_json"] = cover_letter_json_primary
        result["cover_letter_fr"] = full_text_primary
        result["word_count_fr"] = len(full_text_primary.split())
        logger.info(f"   [OK] FR: {result['word_count_fr']} words")
    else:
        result["cover_letter_en_json"] = cover_letter_json_primary
        result["cover_letter_en"] = full_text_primary
        result["word_count_en"] = len(full_text_primary.split())
        logger.info(f"   [OK] EN: {result['word_count_en']} words")

    # Step 4: Translate if needed
    if generate_both_languages:
        target_lang = "en" if language == "fr" else "fr"
        logger.info(f"[4/4] Translating to {target_lang.upper()}...")

        # Translate the full text (for now, keep translate_cover_letter as-is)
        cover_letter_translated_text = translate_cover_letter(
            full_text_primary,
            language,
            target_lang
        )
        cost += 0.0003  # Haiku translation cost

        # For translated version, we don't have JSON (translation returns text)
        # Store the text and use parse logic only for translations
        if target_lang == "fr":
            result["cover_letter_fr"] = cover_letter_translated_text
            result["word_count_fr"] = len(cover_letter_translated_text.split())
            logger.info(f"   [OK] FR: {result['word_count_fr']} words")
        else:
            result["cover_letter_en"] = cover_letter_translated_text
            result["word_count_en"] = len(cover_letter_translated_text.split())
            logger.info(f"   [OK] EN: {result['word_count_en']} words")

    # Finalize
    result["generation_time"] = time.time() - start_time
    result["cost_estimate"] = cost

    logger.info(f"\n[OK] Generation complete!")
    logger.info(f"   Time: {result['generation_time']:.2f}s")
    logger.info(f"   Cost: ${result['cost_estimate']:.4f}")

    return result


if __name__ == "__main__":
    # Test with mock data
    logger.info("Testing cover letter generation...\n")

    mock_cv = {
        "contact_information": [
            {"type": "name", "value": "Fayed HANAFI"},
            {"type": "email", "value": "fayed.hanafi@example.com"},
            {"type": "phone", "value": "+33 6 12 34 56 78"}
        ],
        "education": [
            {
                "institution": "HEC Paris",
                "degree": "Master in Finance",
                "location": "Paris, France",
                "date": "2020 - 2022"
            }
        ],
        "work_experience": [
            {
                "company": "Rothschild & Co",
                "role": "Investment Banking Intern",
                "location": "Paris, France",
                "date": "Jun. 2021 - Dec. 2021",
                "duration": "6 months",
                "responsibilities": [
                    "Supported execution of €450M pharmaceutical M&A, conducting DCF and LBO modeling across 8 European markets",
                    "Streamlined comparables analysis process, reducing preparation time by 30%",
                    "Prepared client presentations and pitch books for senior bankers"
                ]
            }
        ],
        "it_skills": [
            {"name": "Financial Modeling", "level": "Advanced"},
            {"name": "Python", "level": "Intermediate"},
            {"name": "Bloomberg Terminal", "level": "Advanced"}
        ],
        "language_skills": [
            {"language": "French", "level": "Native"},
            {"language": "English", "level": "Fluent"},
            {"language": "Arabic", "level": "Fluent"}
        ]
    }

    mock_job_offer = """
    Goldman Sachs - Investment Banking Analyst (M&A)
    Paris, France

    Goldman Sachs seeks an Investment Banking Analyst for our M&A team in Paris.

    Requirements:
    - 0-2 years of experience in finance or related field
    - Strong financial modeling skills (DCF, LBO, comps)
    - Excellent analytical and communication abilities
    - Fluency in English and French

    Responsibilities:
    - Conduct financial analysis and valuation
    - Support M&A deal execution
    - Prepare client presentations and pitch materials
    - Collaborate with senior bankers on live transactions

    We value meritocracy, intellectual rigor, and client-first mindset.
    """

    result = generate_cover_letter(
        cv_data=mock_cv,
        job_offer=mock_job_offer,
        additional_notes="Passionate about cross-border M&A, admire Goldman's meritocratic culture",
        language="fr",
        generate_both_languages=True
    )

    print("\n" + "="*60)
    logger.info("COVER LETTER (FR):")
    print("="*60)
    print(result["cover_letter_fr"])

    print("\n" + "="*60)
    logger.info("COVER LETTER (EN):")
    print("="*60)
    print(result["cover_letter_en"])

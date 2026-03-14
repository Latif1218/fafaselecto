"""
LLM Client for Postulae CV Generator.
Handles all interactions with OpenAI GPT models.
Stateless, no file operations.
"""
import json
import os
import re
from typing import Dict, Optional
from pathlib import Path
from apps.config import OPENAI_API_KEY
import openai
# from dotenv import load_dotenv

# Import bullet trimmer
from .bullet_trimmer import trim_cv_bullets, validate_bullet_lengths

# load_dotenv()
openai.api_key = OPENAI_API_KEY

# Load prompts from files
PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(filename: str) -> str:
    """Load prompt template from file."""
    prompt_path = PROMPTS_DIR / filename
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def extract_text_from_pdf_bytes(pdf_bytes: bytes, filename: str = "resume.pdf") -> str:
    """
    Extract text from PDF bytes using GPT-4 Vision.

    Args:
        pdf_bytes: PDF file as bytes
        filename: Original filename for context

    Returns:
        Extracted text from PDF

    Raises:
        ValueError: If extraction fails
    """
    try:
        # Create file object in memory for OpenAI API
        file_obj = openai.files.create(
            file=(filename, pdf_bytes),
            purpose="user_data",
        )

        prompt = _load_prompt("extract_from_pdf.txt")

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "file",
                            "file": {"file_id": file_obj.id},
                        },
                    ],
                }
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        content = json.loads(response.choices[0].message.content)
        return content.get("raw_text", "")

    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


def generate_cv_content(
    input_data: Dict,
    domain: str = "finance",
    language: str = "en",
    enrichment_mode: bool = False,
    current_metrics: Optional[Dict] = None,
    enrichment_instructions: Optional[str] = None,
) -> Dict:
    """
    Generate CV content from input data using GPT.

    Args:
        input_data: Input data (raw_text from PDF or structured data)
        domain: Target domain (finance, consulting, startup, government)
        language: Output language (en, fr)
        enrichment_mode: If True, generate comprehensive content for low PFR
        current_metrics: Current page fill metrics for enrichment context

    Returns:
        Structured CV content as dictionary

    Raises:
        ValueError: If generation fails
    """
    try:
        # Load base system prompt
        system_prompt = _load_prompt("base_system.txt")

        # Add language specification
        if language == "fr":
            system_prompt += "\n\nOutput must be in French."
        else:
            system_prompt += "\n\nOutput must be in English."

        # Add adaptive enrichment instructions (NEW SYSTEM)
        if enrichment_instructions:
            system_prompt += "\n\n" + enrichment_instructions

        # Add enrichment instructions if in enrichment mode (LEGACY - for backwards compatibility)
        elif enrichment_mode and current_metrics:
            enrich_prompt = _load_prompt("enrich_content.txt")
            enrich_prompt = enrich_prompt.format(
                fill_percentage=current_metrics.get("fill_percentage", 0),
                char_count=current_metrics.get("char_count", 0),
            )
            system_prompt += "\n\n" + enrich_prompt

        # Prepare user content
        if "raw_text" in input_data:
            user_content = f"Resume data: {input_data['raw_text']}"
        else:
            user_content = f"Resume data: {json.dumps(input_data, ensure_ascii=False)}"

        # Call GPT
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = json.loads(response.choices[0].message.content)

        # TRIMMING DISABLED: PDF reference has LONG bullets (140-210 chars), not short ones!
        # The JSON with short bullets was created by truncating, not by LLM generation.
        print("\n[BULLET TRIMMING] DISABLED - Elite PDFs use long bullets (140-210 chars)")
        # content = trim_cv_bullets(content)

        # Validate bullet lengths after trimming
        stats = validate_bullet_lengths(content)
        if stats["total_bullets"] > 0:
            print(f"\n[BULLET STATS AFTER TRIMMING]")
            print(f"   Total bullets: {stats['total_bullets']}")
            print(f"   Average length: {stats['avg_length']:.1f} chars")
            print(f"   Range: {stats['min_length']}-{stats['max_length']} chars")
            print(f"   Optimal (110-155): {stats['optimal']}/{stats['total_bullets']} ({stats['optimal']/stats['total_bullets']*100:.1f}%)")
            if stats["too_long"] > 0:
                print(f"   WARNING:  Still too long (>155): {stats['too_long']} bullets")
            if stats["too_short"] > 0:
                print(f"   WARNING:  Too short (<110): {stats['too_short']} bullets")

        # SAFETY CHECK: Prevent empty work_experience when source contains experiences
        if (
            "raw_text" in input_data
            and isinstance(content.get("work_experience"), list)
            and len(content.get("work_experience", [])) == 0
        ):
            # Check if raw text contains work experience signals
            raw_text_lower = input_data["raw_text"].lower()
            experience_signals = [
                "experience", "expérience", "work", "job", "position",
                "consultant", "analyst", "manager", "intern", "stage",
                "company", "entreprise", "société"
            ]

            has_experience_signals = any(signal in raw_text_lower for signal in experience_signals)

            # Also check for date patterns (YYYY, Mon YYYY, etc.)
            has_dates = bool(re.search(r'\b(19|20)\d{2}\b', input_data["raw_text"]))

            if has_experience_signals and has_dates:
                # FALLBACK: One-shot targeted extraction
                fallback_prompt = """CRITICAL: The previous extraction returned ZERO work experiences, but the source clearly contains work history.

TASK: Extract ALL work experiences from the source. Look for:
- Company/organization names
- Job titles or roles
- Date ranges (any format)
- Responsibilities or achievements

You MUST extract AT LEAST ONE work experience if ANY exists in the source.

Return ONLY work experiences in this exact format:
{
    "work_experience": [{
        "date": "Mon YYYY-Mon YYYY",
        "company": "COMPANY NAME",
        "location": "City, Country",
        "position": "Job Title",
        "duration": "X months",
        "bullets": ["Achievement 1", "Achievement 2", "Achievement 3"]
    }]
}"""

                fallback_response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": fallback_prompt},
                        {"role": "user", "content": f"Source text:\n\n{input_data['raw_text']}"}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )

                fallback_content = json.loads(fallback_response.choices[0].message.content)

                # Merge fallback work_experience into content
                if fallback_content.get("work_experience") and len(fallback_content["work_experience"]) > 0:
                    content["work_experience"] = fallback_content["work_experience"]

        # QUALITY VALIDATION: Check bullet length (elite CV standard: 120-145 chars, avg ~127)
        if "work_experience" in content:
            for idx, exp in enumerate(content["work_experience"]):
                if "bullets" in exp:
                    for bullet_idx, bullet in enumerate(exp["bullets"]):
                        bullet_len = len(bullet)
                        if bullet_len < 100:
                            print(f"WARNING:  WARNING: Work experience bullet too short (elite standard: 120-145 chars)")
                            print(f"    Experience #{idx+1} ({exp.get('company', 'Unknown')}), Bullet #{bullet_idx+1}: {bullet_len} chars")
                            print(f"    Text: {bullet[:80]}...")
                            print(f"    → This will reduce PFR below elite standards (90%+ requires 120-145 chars)")
                        elif bullet_len < 110:
                            print(f"WARNING:  INFO: Bullet below optimal length")
                            print(f"    Experience #{idx+1} ({exp.get('company', 'Unknown')}), Bullet #{bullet_idx+1}: {bullet_len} chars (optimal: 120-145)")
                        elif bullet_len > 150:
                            print(f"WARNING:  INFO: Bullet above optimal length (may reduce space for other sections)")
                            print(f"    Experience #{idx+1} ({exp.get('company', 'Unknown')}), Bullet #{bullet_idx+1}: {bullet_len} chars (optimal: 120-145)")

        # QUALITY VALIDATION: Check coursework count (elite standard: 5-7 items, NEVER empty for university/prépa)
        if "education" in content:
            for idx, edu in enumerate(content["education"]):
                institution = edu.get('institution', 'Unknown').lower()
                degree = edu.get('degree', '').lower()
                coursework_count = len(edu.get("coursework", []))

                # Detect if university/master or classe préparatoire
                is_university = any(keyword in institution or keyword in degree for keyword in ['university', 'université', 'master', 'hec', 'business school', 'grande école'])
                is_prepa = any(keyword in institution or keyword in degree for keyword in ['préparatoire', 'preparatoire', 'prepa', 'lycée saint-louis', 'lycée louis'])

                if (is_university or is_prepa) and coursework_count == 0:
                    print(f"WARNING:  CRITICAL: Coursework empty for university/prépa (MUST have 4-7 items)")
                    print(f"    Education #{idx+1} ({edu.get('institution', 'Unknown')}): {coursework_count} items")
                    print(f"    → This is a CRITICAL ERROR - infer coursework from specialty/degree if not in source")
                elif (is_university or is_prepa) and coursework_count < 4:
                    print(f"WARNING:  WARNING: Coursework too short for university/prépa")
                    print(f"    Education #{idx+1} ({edu.get('institution', 'Unknown')}): {coursework_count} items (need 5-7)")
                elif is_university and coursework_count >= 5:
                    # Good
                    pass
                elif not is_university and not is_prepa and coursework_count < 5 and coursework_count > 0:
                    print(f"WARNING:  INFO: High school coursework present but limited")
                    print(f"    Education #{idx+1} ({edu.get('institution', 'Unknown')}): {coursework_count} items (acceptable for high school)")

        # QUALITY VALIDATION: Check for empty work_experience when it shouldn't be
        if "raw_text" in input_data and len(content.get("work_experience", [])) == 0:
            print(f"WARNING:  CRITICAL: work_experience is empty but source may contain work history")
            print(f"    This will result in PFR < 65% and generation will be blocked")

        return content

    except Exception as e:
        raise ValueError(f"Failed to generate CV content: {str(e)}")


def enhance_specific_section(
    section_data: Dict,
    section_type: str,
    language: str = "en",
) -> Dict:
    """
    Enhance a specific section with more detail (for targeted enrichment).

    Args:
        section_data: Section data to enhance
        section_type: Type of section (experience, education, etc.)
        language: Output language

    Returns:
        Enhanced section data
    """
    system_prompt = f"""You are enhancing the {section_type} section of a professional CV.
Add more detail, metrics, and context WITHOUT inventing facts.
Only expand on information that can be reasonably inferred.
Maintain professional tone for finance/consulting roles.
Output in {"French" if language == "fr" else "English"}.
Return the enhanced data in the same JSON structure."""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(section_data, ensure_ascii=False)},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        raise ValueError(f"Failed to enhance section: {str(e)}")




async def generate_completion(
    messages: list,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 1000,
    top_p: float = 1.0,
) -> str:
    """
    Generic LLM completion helper.
    Used for cover letter, custom prompts, etc.
    Returns raw text response.
    """
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )

        return response.choices[0].message.content

    except Exception as e:
        raise ValueError(f"LLM completion failed: {str(e)}")
    



def extract_structured_cv_data(pdf_bytes: bytes) -> Dict:
    """
    Generate structured data form PDF using LLM(grader- exact keys)
    """
    try:
        file_obj = openai.files.create(
            file=("resume.pdf", pdf_bytes),
            purpose="user_data",
        )

        prompt = _load_prompt("extract_structured.txt")  

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "file", "file": {"file_id": file_obj.id}}
                    ]
                }
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print(f"Structured extraction failed: {e}")
        return {}
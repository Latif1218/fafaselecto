
from .logger import get_logger
logger = get_logger(__name__)

"""
Cover Letter Layout Engine for Postulae.

Generates PDF and DOCX from cover letter content using:
- Jinja2 templating (HTML/CSS)
- Playwright (PDF generation via Chromium)
- pdf2docx (DOCX conversion)

CONSTRAINTS:
- 1 page A4 exactly
- Marges: 20mm top/bottom, 25mm left/right
- Times New Roman, 11pt
- Professional spacing (line-height: 1.5)
"""
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright
from pdf2docx import Converter
from PyPDF2 import PdfReader

# Paths
TEMPLATES_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


def parse_cover_letter_text(cover_letter: str, language: str) -> Dict:
    """
    DEPRECATED: Parse cover letter text into structured components.

    This function is only used for LEGACY translations (translate_cover_letter returns text).
    For NEW generations, use JSON-structured output from generate_cover_letter_content().

    The JSON approach eliminates:
    - Fragile text parsing
    - Name/signature duplication bugs
    - "Je suis disponible" appearing twice
    - Complex deduplication logic

    Extracts:
    - Opening formula (Madame, Monsieur / Dear Hiring Manager)
    - Body paragraphs (main content)
    - Closing formula (Salutations distinguées / Sincerely)

    Args:
        cover_letter: Raw cover letter text from LLM
        language: "fr" or "en"

    Returns:
        Dictionary with:
        {
            "opening": str,
            "body_paragraphs": List[str],
            "closing": str
        }
    """
    # Split into lines and paragraphs
    lines = cover_letter.strip().split("\n")
    paragraphs = []
    current_para = []

    for line in lines:
        line = line.strip()
        if not line:
            if current_para:
                paragraphs.append(" ".join(current_para))
                current_para = []
        else:
            current_para.append(line)

    if current_para:
        paragraphs.append(" ".join(current_para))

    # Detect opening formula
    opening = ""
    if language == "fr":
        opening_patterns = ["Madame, Monsieur", "Chère Madame", "Cher Monsieur"]
    else:
        opening_patterns = ["Dear Hiring Manager", "Dear Mr.", "Dear Ms.", "Dear"]

    for i, para in enumerate(paragraphs):
        if any(pattern in para for pattern in opening_patterns):
            opening = para
            paragraphs = paragraphs[i+1:]
            break

    # If no explicit opening found, use default
    if not opening:
        opening = "Madame, Monsieur," if language == "fr" else "Dear Hiring Manager,"

    # Detect closing formula (CRITICAL: Remove duplicates and signature names)
    closing = ""
    if language == "fr":
        closing_patterns = [
            "Je vous prie d'agréer",
            "Cordialement",
            "Bien cordialement",
            "Salutations distinguées"
        ]
    else:
        closing_patterns = ["Sincerely", "Best regards", "Kind regards", "Thank you"]

    # Find last paragraph with closing formula
    for i in range(len(paragraphs) - 1, -1, -1):
        para = paragraphs[i]
        if any(pattern in para for pattern in closing_patterns):
            closing = para
            paragraphs = paragraphs[:i]
            break

    # Clean closing: Remove any standalone name lines (will be in signature)
    if closing:
        closing_lines = closing.split("\n")
        cleaned_lines = []
        for line in closing_lines:
            line = line.strip()
            # Skip empty lines
            if not line:
                continue
            # Skip lines that are just names (≤3 words, no punctuation)
            if len(line.split()) <= 3 and not any(char in line for char in [".", ",", ";", "é"]):
                continue  # Skip signature name
            # Keep lines with closing formulas
            if any(pattern in line for pattern in closing_patterns):
                cleaned_lines.append(line)

        closing = "\n\n".join(cleaned_lines) if cleaned_lines else ""

    # Fallback if no closing detected
    if not closing:
        closing = "Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées." if language == "fr" else "Sincerely,"

    # CRITICAL FIX: Remove any body paragraph that is identical to (or contained in) the closing
    # This prevents duplication when LLM generates the closing paragraph twice
    if closing:
        closing_lower = closing.lower().strip()
        filtered_paragraphs = []

        for para in paragraphs:
            para_lower = para.lower().strip()

            # Skip if paragraph is identical to closing
            if para_lower == closing_lower:
                logger.warning(f"      [WARN LAYOUT] Skipping body paragraph identical to closing")
                continue

            # Skip if closing starts with this paragraph (para is subset of closing)
            if closing_lower.startswith(para_lower) and len(para_lower) > 50:
                logger.warning(f"      [WARN LAYOUT] Skipping body paragraph that's start of closing: {para[:60]}...")
                continue

            # Skip if paragraph starts with closing starters and is very similar to closing
            closing_starters = ["je suis disponible", "i am available", "i would be", "je me tiens"]
            if any(para_lower.startswith(starter) for starter in closing_starters):
                # If both contain the same starter, likely duplicate
                if any(closing_lower.startswith(starter) for starter in closing_starters):
                    logger.warning(f"      [WARN LAYOUT] Skipping duplicate closing paragraph in body: {para[:60]}...")
                    continue

            filtered_paragraphs.append(para)

        paragraphs = filtered_paragraphs

    result = {
        "opening": opening,
        "body_paragraphs": paragraphs,
        "closing": closing
    }

    return result


def extract_contact_from_cv(cv_data: Dict) -> List[str]:
    """
    Extract contact information from CV data (NOT USED - no header in cover letter).

    Args:
        cv_data: Structured CV data

    Returns:
        Empty list (header removed from template)
    """
    # Header removed from cover letter template
    # Cover letter starts with date/location only
    return []


def extract_name_from_cv(cv_data: Dict) -> str:
    """
    Extract candidate name from CV data.

    Args:
        cv_data: Structured CV data

    Returns:
        Full name (e.g., "Fayed HANAFI")
    """
    contact_info = cv_data.get("contact_information", [])

    # Look for name field
    for item in contact_info:
        if item.get("type", "").lower() in ["name", "full_name"]:
            return item.get("value", "Candidate Name")

    # Fallback: combine first_name + last_name
    first_name = ""
    last_name = ""
    for item in contact_info:
        if item.get("type", "").lower() == "first_name":
            first_name = item.get("value", "")
        elif item.get("type", "").lower() == "last_name":
            last_name = item.get("value", "")

    if first_name or last_name:
        return f"{first_name} {last_name}".strip()

    return "Candidate Name"


def generate_cover_letter_pdf(
    cover_letter,  # Can be str OR Dict
    cv_data: Dict,
    job_requirements: Dict,
    output_path: str,
    language: str = "fr"
) -> Dict:
    """
    Generate cover letter PDF from text OR JSON using Playwright.

    Args:
        cover_letter: Cover letter text (str) OR JSON (Dict with opening/paragraphs/closing)
        cv_data: Structured CV data
        job_requirements: Job requirements (for company name, etc.)
        output_path: Output PDF path
        language: "fr" or "en"

    Returns:
        Dictionary with:
        {
            "pdf_path": str,
            "page_count": int,
            "word_count": int,
            "warnings": List[str]
        }
    """
    warnings = []

    # Parse cover letter (JSON or text)
    if isinstance(cover_letter, dict):
        # Already structured JSON, no parsing needed
        parsed = {
            "opening": cover_letter["opening"],
            "body_paragraphs": cover_letter["paragraphs"],
            "closing": cover_letter["closing"]
        }
    else:
        # Legacy text format (used by translate_cover_letter)
        parsed = parse_cover_letter_text(cover_letter, language)

    # Extract CV data
    name = extract_name_from_cv(cv_data)
    contact = extract_contact_from_cv(cv_data)

    # Date and location
    today = datetime.now()
    if language == "fr":
        # Format: "Paris, le 31 mars 2026"
        months_fr = [
            "janvier", "février", "mars", "avril", "mai", "juin",
            "juillet", "août", "septembre", "octobre", "novembre", "décembre"
        ]
        date_str = f"{today.day} {months_fr[today.month - 1]} {today.year}"
    else:
        # Format: "March 31, 2026"
        date_str = today.strftime("%B %d, %Y")

    # Location (try to extract from CV, fallback to company location)
    location = "Paris"  # Default
    for item in cv_data.get("contact_information", []):
        if item.get("type", "").lower() in ["location", "city"]:
            location = item.get("value", "Paris")
            break

    # Recipient info (from job requirements)
    recipient_company = job_requirements.get("company_name", "")
    recipient_name = None  # Could be extracted if provided
    recipient_address = None

    # Subject (optional, often not used in elite finance/consulting)
    subject = ""
    if language == "fr":
        position = job_requirements.get("position", "")
        if position:
            subject = f"Objet : Candidature au poste de {position}"
    else:
        position = job_requirements.get("position", "")
        if position:
            subject = f"Re: Application for {position} position"

    # Prepare template data
    template_data = {
        "language": language,
        "name": name,
        "contact": contact,
        "location": location,
        "date": date_str,
        "recipient_name": recipient_name,
        "recipient_company": recipient_company,
        "recipient_address": recipient_address,
        "subject": subject,
        "opening": parsed["opening"],
        "body_paragraphs": parsed["body_paragraphs"],
        "closing": parsed["closing"]
    }

    # Load and render template
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("cover_letter_template.html")
    html_content = template.render(**template_data)

    # Generate PDF using Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Set content
        page.set_content(html_content)

        # Generate PDF
        page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={
                "top": "20mm",
                "bottom": "20mm",
                "left": "25mm",
                "right": "25mm"
            }
        )

        browser.close()

    # Validate page count with PyPDF2 (actual page count, not assumed)
    try:
        reader = PdfReader(output_path)
        page_count = len(reader.pages)
    except Exception as e:
        # Fallback if PyPDF2 fails
        page_count = 1
        warnings.append(f"Could not validate page count: {str(e)}")

    # Word count (from JSON or text)
    if isinstance(cover_letter, dict):
        # Count from all JSON fields
        all_text = cover_letter["opening"] + " " + " ".join(cover_letter["paragraphs"]) + " " + cover_letter["closing"]
        word_count = len(all_text.split())
    else:
        word_count = len(cover_letter.split())

    # Warnings
    if page_count > 1:
        warnings.append(f"CRITICAL: Cover letter overflows to {page_count} pages (MUST be 1 page)")
    if word_count > 350:
        warnings.append(f"Cover letter long ({word_count} words), may overflow 1 page")
    if word_count < 250:
        warnings.append(f"Cover letter short ({word_count} words), may look sparse")

    return {
        "pdf_path": output_path,
        "page_count": page_count,
        "word_count": word_count,
        "warnings": warnings
    }


def convert_pdf_to_docx(pdf_path: str, docx_path: str):
    """
    Convert PDF to DOCX using pdf2docx.

    Args:
        pdf_path: Input PDF path
        docx_path: Output DOCX path
    """
    cv = Converter(pdf_path)
    cv.convert(docx_path, start=0, end=None)
    cv.close()


def generate_cover_letter_files(
    cover_letter: str,
    cv_data: Dict,
    job_requirements: Dict,
    output_dir: str,
    filename_base: str,
    language: str = "fr",
    generate_docx: bool = True
) -> Dict:
    """
    Generate cover letter PDF and optionally DOCX.

    Args:
        cover_letter: Cover letter text
        cv_data: Structured CV data
        job_requirements: Job requirements
        output_dir: Output directory
        filename_base: Base filename (e.g., "cover_letter_fayed_goldman")
        language: "fr" or "en"
        generate_docx: If True, also generate DOCX

    Returns:
        Dictionary with paths and metadata
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Generate PDF
    pdf_filename = f"{filename_base}_{language}.pdf"
    pdf_path = os.path.join(output_dir, pdf_filename)

    result = generate_cover_letter_pdf(
        cover_letter,
        cv_data,
        job_requirements,
        pdf_path,
        language
    )

    # Generate DOCX if requested
    if generate_docx:
        docx_filename = f"{filename_base}_{language}.docx"
        docx_path = os.path.join(output_dir, docx_filename)
        convert_pdf_to_docx(pdf_path, docx_path)
        result["docx_path"] = docx_path

    return result


if __name__ == "__main__":
    # Test
    logger.info("Testing cover letter layout...")

    mock_cv = {
        "contact_information": [
            {"type": "name", "value": "Fayed HANAFI"},
            {"type": "email", "value": "fayed.hanafi@example.com"},
            {"type": "phone", "value": "+33 6 12 34 56 78"},
            {"type": "location", "value": "Paris, France"}
        ]
    }

    mock_job = {
        "company_name": "Goldman Sachs",
        "position": "Investment Banking Analyst"
    }

    mock_letter = """Madame, Monsieur,

Diplômé de HEC Paris avec une expérience concrète en M&A, je souhaite rejoindre Goldman Sachs en tant qu'Analyste Investment Banking. Ayant analysé 15+ transactions cross-border lors de mon stage chez Rothschild, je suis attiré par le leadership de Goldman dans les opérations complexes et son exigence d'excellence analytique.

Lors de mon stage chez Rothschild & Co, j'ai contribué à l'exécution d'une opération M&A pharmaceutique de 450M€, en réalisant des modélisations financières (DCF, LBO) et des due diligences sur 8 marchés européens. J'ai optimisé le processus d'analyse de comparables, réduisant le temps de préparation de 30%.

Goldman Sachs' unparalleled training program and meritocratic culture align with my commitment to continuous learning and excellence. I am particularly impressed by Goldman's recent advisory role on major transactions.

Je suis disponible pour un entretien à votre convenance et serais ravi de discuter de la manière dont mon expérience peut contribuer au succès de Goldman Sachs.

Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.

Fayed HANAFI"""

    result = generate_cover_letter_files(
        cover_letter=mock_letter,
        cv_data=mock_cv,
        job_requirements=mock_job,
        output_dir="output/test_cover_letter",
        filename_base="test_cover_letter",
        language="fr",
        generate_docx=True
    )

    logger.info(f"✅ Generated: {result['pdf_path']}")
    logger.info(f"   Page count: {result['page_count']}")
    logger.info(f"   Word count: {result['word_count']}")
    if result.get("warnings"):
        logger.warning(f"   Warnings: {result['warnings']}")
    if "docx_path" in result:
        logger.info(f"✅ Generated: {result['docx_path']}")

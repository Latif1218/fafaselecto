
from .logger import get_logger
logger = get_logger(__name__)

"""
Cover Letter Page Fill Rate (PFR) calculation and validation.

Similar to CV density.py but adapted for cover letter constraints:
- Target: 85-98% PFR (1 page A4)
- Block if <60% (too short)
- Block if >98% (overflow risk)
- Marges: 20mm top/bottom, 25mm left/right (more aerated than CV)
"""
from typing import Dict


# PFR Thresholds (adjusted for cover letter)
BLOCK_MINIMUM = 0.60  # Block if <60% (too short, unprofessional)
OPTIMAL_MIN = 0.85    # Target minimum 85%
OPTIMAL_MAX = 0.98    # Target maximum 98%
HARD_MAX = 0.99       # Hard limit (>99% = overflow risk)

# Character estimates for 1 page A4 cover letter
# Based on:
# - Marges: 20mm top/bottom, 25mm left/right
# - Font: Times New Roman 11pt
# - Line-height: 1.5 (aéré)
# - Effective area: 160mm × 252mm (A4 210×297 minus marges)
# - ~50 chars/line × ~42 lines = ~2100 chars effective
# - Header (~150 chars) + Date (~50) + Recipient (~100) + Opening (~20) + Closing (~100) = ~420 chars overhead
# - Body available: ~1680 chars for 85% PFR
# - Body max: ~1950 chars for 98% PFR

CHAR_TARGET_85PCT = 1680  # Target minimum characters (body only, no header/closing)
CHAR_TARGET_98PCT = 1950  # Target maximum characters
CHAR_ABSOLUTE_MAX = 2100  # Absolute max before overflow (will trim)


def estimate_cover_letter_chars(cover_letter_text: str) -> int:
    """
    Estimate character count for body content only.

    Excludes:
    - Opening formula (Madame, Monsieur / Dear Hiring Manager)
    - Closing formula (Salutations distinguées / Sincerely)
    - Signature (name)

    Args:
        cover_letter_text: Full cover letter text

    Returns:
        Character count of body paragraphs only
    """
    # Split into paragraphs
    paragraphs = [p.strip() for p in cover_letter_text.split("\n\n") if p.strip()]

    # Exclude first paragraph if it's opening formula
    opening_keywords = ["Madame, Monsieur", "Dear Hiring Manager", "Dear Mr.", "Dear Ms.", "Chère Madame", "Cher Monsieur"]
    if paragraphs and any(kw in paragraphs[0] for kw in opening_keywords):
        paragraphs = paragraphs[1:]

    # Exclude last 1-2 paragraphs if they're closing/signature
    closing_keywords = ["salutations distinguées", "Sincerely", "Best regards", "Cordialement"]
    while paragraphs:
        last_para = paragraphs[-1]
        # Check if last paragraph is closing or just signature (name only)
        if any(kw in last_para for kw in closing_keywords) or len(last_para.split()) <= 3:
            paragraphs = paragraphs[:-1]
        else:
            break

    # Count characters in remaining body paragraphs
    body_chars = sum(len(p) for p in paragraphs)

    return body_chars


def calculate_pfr(cover_letter_text: str) -> float:
    """
    Calculate Page Fill Rate for cover letter.

    PFR = (body_chars / CHAR_TARGET_98PCT) * 100

    Args:
        cover_letter_text: Full cover letter text

    Returns:
        PFR percentage (0.0-1.0+)
    """
    body_chars = estimate_cover_letter_chars(cover_letter_text)
    pfr = body_chars / CHAR_TARGET_98PCT
    return pfr


def validate_cover_letter_density(cover_letter_text: str, language: str) -> Dict:
    """
    Validate cover letter page fill rate.

    Returns status and recommended action.

    Args:
        cover_letter_text: Full cover letter text
        language: "fr" or "en"

    Returns:
        {
            "pfr": float,
            "body_chars": int,
            "status": "optimal" | "short" | "long" | "critical_short" | "critical_long",
            "action": "accept" | "trim" | "expand" | "block",
            "message": str
        }
    """
    body_chars = estimate_cover_letter_chars(cover_letter_text)
    pfr = calculate_pfr(cover_letter_text)

    result = {
        "pfr": pfr,
        "body_chars": body_chars,
        "status": "unknown",
        "action": "accept",
        "message": ""
    }

    # Critical short (<60% = ~1008 chars)
    if pfr < BLOCK_MINIMUM:
        result["status"] = "critical_short"
        result["action"] = "block"
        result["message"] = f"Cover letter too short ({pfr*100:.1f}% PFR, {body_chars} chars). Minimum 60% required."
        return result

    # Short but acceptable (60-85%)
    if pfr < OPTIMAL_MIN:
        result["status"] = "short"
        result["action"] = "expand"
        result["message"] = f"Cover letter slightly short ({pfr*100:.1f}% PFR, {body_chars} chars). Target 85-98%."
        return result

    # Optimal (85-98%)
    if OPTIMAL_MIN <= pfr <= OPTIMAL_MAX:
        result["status"] = "optimal"
        result["action"] = "accept"
        result["message"] = f"Cover letter optimal ({pfr*100:.1f}% PFR, {body_chars} chars)."
        return result

    # Too long (98-99%)
    if OPTIMAL_MAX < pfr <= HARD_MAX:
        result["status"] = "long"
        result["action"] = "trim"
        result["message"] = f"Cover letter too long ({pfr*100:.1f}% PFR, {body_chars} chars). Trim to 85-98%."
        return result

    # Critical overflow (>99%)
    result["status"] = "critical_long"
    result["action"] = "block"
    result["message"] = f"Cover letter overflows page ({pfr*100:.1f}% PFR, {body_chars} chars). MUST trim below 98%."
    return result


def trim_cover_letter_to_target(cover_letter_text: str, target_pfr: float = 0.92) -> str:
    """
    Trim cover letter to target PFR by shortening body paragraphs.

    Strategy:
    - Keep opening and closing intact
    - Trim longest body paragraphs first
    - Remove least important sentences (typically last sentence of paragraphs)

    Args:
        cover_letter_text: Original cover letter
        target_pfr: Target PFR (default 92%)

    Returns:
        Trimmed cover letter text
    """
    target_chars = int(CHAR_TARGET_98PCT * target_pfr)
    current_chars = estimate_cover_letter_chars(cover_letter_text)

    if current_chars <= target_chars:
        return cover_letter_text  # Already within target

    chars_to_remove = current_chars - target_chars

    # Parse cover letter
    paragraphs = [p.strip() for p in cover_letter_text.split("\n\n") if p.strip()]

    # Identify opening, body, closing
    opening_idx = None
    closing_idx = None

    opening_keywords = ["Madame, Monsieur", "Dear Hiring Manager", "Dear Mr.", "Dear Ms."]
    closing_keywords = ["salutations distinguées", "Sincerely", "Best regards"]

    for i, p in enumerate(paragraphs):
        if any(kw in p for kw in opening_keywords):
            opening_idx = i
        if any(kw in p for kw in closing_keywords):
            closing_idx = i
            break

    # Extract body paragraphs (exclude opening and closing)
    if opening_idx is not None:
        body_start = opening_idx + 1
    else:
        body_start = 0

    if closing_idx is not None:
        body_end = closing_idx
    else:
        body_end = len(paragraphs)

    body_paragraphs = paragraphs[body_start:body_end]

    # Trim body paragraphs (remove last sentence from longest paragraphs first)
    chars_removed = 0
    trimmed_body = body_paragraphs.copy()

    while chars_removed < chars_to_remove and trimmed_body:
        # Find longest paragraph
        longest_idx = max(range(len(trimmed_body)), key=lambda i: len(trimmed_body[i]))
        longest_para = trimmed_body[longest_idx]

        # Split into sentences
        sentences = [s.strip() for s in longest_para.split(". ") if s.strip()]

        if len(sentences) <= 1:
            # Can't trim further without removing entire paragraph
            break

        # Remove last sentence
        removed_sentence = sentences[-1]
        trimmed_para = ". ".join(sentences[:-1]) + "."

        chars_removed += len(removed_sentence) + 2  # +2 for ". "
        trimmed_body[longest_idx] = trimmed_para

    # Reconstruct cover letter
    trimmed_paragraphs = []
    if opening_idx is not None:
        trimmed_paragraphs.extend(paragraphs[:opening_idx+1])

    trimmed_paragraphs.extend(trimmed_body)

    if closing_idx is not None:
        trimmed_paragraphs.extend(paragraphs[closing_idx:])

    return "\n\n".join(trimmed_paragraphs)


if __name__ == "__main__":
    # Test with sample cover letter
    sample_fr = """Madame, Monsieur,

Diplômé de HEC Paris avec une expérience concrète en M&A, je souhaite rejoindre Goldman Sachs en tant qu'Analyste Investment Banking. Ayant analysé 15+ transactions cross-border lors de mon stage chez Rothschild, je suis attiré par le leadership de Goldman dans les opérations complexes et son exigence d'excellence analytique.

Lors de mon stage chez Rothschild & Co, j'ai contribué à l'exécution d'une opération M&A pharmaceutique de 450M€, en réalisant des modélisations financières (DCF, LBO) et des due diligences sur 8 marchés européens. J'ai optimisé le processus d'analyse de comparables, réduisant le temps de préparation de 30%, ce qui a permis aux banquiers seniors d'accélérer les présentations clients.

Goldman Sachs' unparalleled training program and meritocratic culture align with my commitment to continuous learning and excellence. I am particularly impressed by Goldman's recent advisory role on major transactions.

Je suis disponible pour un entretien à votre convenance et serais ravi de discuter de la manière dont mon expérience peut contribuer au succès de Goldman Sachs.

Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.

Fayed HANAFI"""

    validation = validate_cover_letter_density(sample_fr, "fr")
    logger.info(f"PFR: {validation['pfr']*100:.1f}%")
    logger.info(f"Body chars: {validation['body_chars']}")
    logger.info(f"Status: {validation['status']}")
    logger.info(f"Action: {validation['action']}")
    logger.info(f"Message: {validation['message']}")

    if validation['action'] == 'trim':
        logger.info("\nTrimming to 92% PFR...")
        trimmed = trim_cover_letter_to_target(sample_fr, target_pfr=0.92)
        validation_trimmed = validate_cover_letter_density(trimmed, "fr")
        logger.info(f"After trim PFR: {validation_trimmed['pfr']*100:.1f}%")
        logger.info(f"After trim chars: {validation_trimmed['body_chars']}")

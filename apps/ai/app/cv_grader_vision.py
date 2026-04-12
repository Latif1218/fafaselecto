
from .logger import get_logger
logger = get_logger(__name__)

"""
CV Grader avec Vision API - Option Hybrid Smart
Analyse visuelle précise (couleurs, layout, graphiques) + scoring contenu
"""

import os
import base64
from typing import Optional, Dict
from openai import OpenAI
from apps.config import OPENAI_API_KEY
from app.cv_grader import grade_cv, GradingResult


# =============================================================================
# VISION API - ANALYSE VISUELLE PRECISE
# =============================================================================

def analyze_cv_visual_with_vision(pdf_bytes: bytes, openai_api_key: Optional[str] = None) -> Dict:
    """
    Analyse visuelle d'un CV PDF avec GPT-4o Vision
    Détecte VRAIMENT les couleurs, graphiques, colonnes, photos

    Args:
        pdf_bytes: PDF en bytes
        openai_api_key: Clé API OpenAI (ou utilise env OPENAI_API_KEY)

    Returns:
        Dict avec analysis_visual:
        {
            "has_colors": bool,
            "has_charts": bool,
            "has_photo": bool,
            "has_column_format": bool,
            "page_count": int,
            "layout_quality": "poor" | "basic" | "professional" | "elite"
        }

    Coût: $0.0025 par appel
    """
    api_key = openai_api_key or os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY manquante (env ou paramètre)")

    client = OpenAI(api_key=api_key)

    # Encode PDF en base64 pour Vision API
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

    # Prompt Vision pour analyse visuelle stricte
    prompt = """Analyse ce CV PDF et réponds UNIQUEMENT avec un JSON strict (aucun texte avant/après):

{
  "has_colors": true/false,  // Vrai si COULEURS utilisées (fond, texte, graphiques) - SAUF noir/blanc/gris
  "has_charts": true/false,  // Vrai si GRAPHIQUES/BARRES/DIAGRAMMES visuels présents
  "has_photo": true/false,   // Vrai si PHOTO de profil visible
  "has_column_format": true/false,  // Vrai si COLONNES structurées (dates | contenu | lieu)
  "page_count": 1,           // Nombre de pages VISUELLES (compte toutes les pages)
  "layout_quality": "poor" | "basic" | "professional" | "elite"  // Qualité visuelle globale
}

CRITÈRES STRICT:
- has_colors: TRUE si utilise bleu/rouge/vert/orange/jaune (PAS JUSTE noir/blanc/gris)
- has_charts: TRUE si graphiques de compétences (barres, cercles, étoiles) VISUELS
- has_column_format: TRUE si structure claire 3 colonnes (dates, contenu, lieu) avec alignement
- layout_quality:
  * "poor": Design amateur, couleurs vives, graphiques fantaisie (Canva coloré)
  * "basic": Sobre mais pas optimisé, alignements approximatifs
  * "professional": Colonnes claires, sobre, aligné, Times New Roman/Georgia
  * "elite": Template finance/conseil (grille stricte, spacing parfait, typo classique)

Retourne UNIQUEMENT le JSON, rien d'autre."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{pdf_base64}",
                                "detail": "high"  # Analyse haute résolution
                            }
                        }
                    ]
                }
            ],
            max_tokens=300,
            temperature=0.1  # Déterministe
        )

        result_text = response.choices[0].message.content.strip()

        # Parse JSON (enlever markdown si présent)
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]

        import json
        analysis_visual = json.loads(result_text)

        # Validation résultat
        required_keys = ["has_colors", "has_charts", "has_photo", "has_column_format", "page_count", "layout_quality"]
        for key in required_keys:
            if key not in analysis_visual:
                raise ValueError(f"Clé manquante dans réponse Vision: {key}")

        return analysis_visual

    except Exception as e:
        # Fallback heuristique si Vision échoue
        logger.error(f"Vision API error: {e}")
        return {
            "has_colors": False,  # Conservative: assume pas de couleurs
            "has_charts": False,
            "has_photo": False,
            "has_column_format": False,
            "page_count": 1,
            "layout_quality": "basic"
        }


# =============================================================================
# GRADING HYBRID SMART (VISION + CONTENU)
# =============================================================================

def grade_cv_hybrid_smart(
    cv_data: Dict,
    pdf_bytes: Optional[bytes] = None,
    analysis_content: Optional[Dict] = None,
    openai_api_key: Optional[str] = None
) -> GradingResult:
    """
    Grading Option Hybrid Smart (RECOMMANDÉ)

    Pipeline:
    1. Si pdf_bytes fourni → Vision API analyse visuelle ($0.0025)
    2. Sinon → Utilise analysis_content fournie (heuristiques)
    3. Merge analysis_visual + analysis_content
    4. Scoring via grade_cv() standard

    Args:
        cv_data: JSON structuré du CV
        pdf_bytes: PDF bytes pour Vision (optionnel mais recommandé)
        analysis_content: Métadonnées pré-calculées (optionnel)
        openai_api_key: Clé API OpenAI

    Returns:
        GradingResult avec score précis

    Coût:
        - Avec Vision: $0.0033 ($0.0025 Vision + $0.0008 scoring)
        - Sans Vision: $0.0008 (heuristiques)
    """
    analysis = analysis_content or {}

    # 1. Analyse visuelle avec Vision si PDF fourni
    if pdf_bytes:
        try:
            analysis_visual = analyze_cv_visual_with_vision(pdf_bytes, openai_api_key)

            # Merge avec analysis_content existante
            analysis.update(analysis_visual)

        except Exception as e:
            logger.error(f"Vision analysis failed, using heuristics: {e}")
            # Continue avec heuristiques si Vision échoue

    # 2. Calcul PFR réel si manquant (utilise formule calibrée)
    if "pfr" not in analysis:
        # Estimer PFR depuis cv_data
        total_chars = sum(
            len(str(exp.get("bullets", [])))
            for exp in cv_data.get("work_experience", [])
        )
        total_chars += sum(
            len(str(edu.get("coursework", [])))
            for edu in cv_data.get("education", [])
        )

        # Formule calibrée (même que cv_grader.py)
        estimated_bullets = max(1, total_chars // 150)
        pfr_estimate = min(98, max(40, (total_chars * 0.027) + (estimated_bullets * 1.5) + 35))
        analysis["pfr"] = round(pfr_estimate, 1)

    # 3. Scoring via grader standard
    result = grade_cv(cv_data, analysis)

    return result


# =============================================================================
# EXEMPLE D'UTILISATION
# =============================================================================

if __name__ == "__main__":
    # Exemple: Grading avec Vision (précis)
    with open("input/CV_exemple.pdf", "rb") as f:
        pdf_bytes = f.read()

    cv_data = {
        "work_experience": [
            {
                "company": "Goldman Sachs",
                "position": "Investment Banking Analyst",
                "bullets": [
                    "Réalisation de 5 due diligences (secteur tech, finance) avec modélisation financière avancée, analyse de marché, coordination équipes pluridisciplinaires (150 chars)",
                    "Optimisation processus M&A pour 3 deals ($200M+) permettant réduction délais de 30% et amélioration précision valorisations (140 chars)"
                ]
            }
        ],
        "education": [
            {
                "institution": "HEC Paris",
                "degree": "Master Finance",
                "coursework": ["Corporate Finance", "Financial Modeling", "M&A Strategy"]
            }
        ],
        "contact_information": [{"email": "exemple@email.com"}]
    }

    # Grading Hybrid Smart (Vision + Contenu)
    result = grade_cv_hybrid_smart(
        cv_data=cv_data,
        pdf_bytes=pdf_bytes,
        openai_api_key="sk-..."  # Ou utilise env OPENAI_API_KEY
    )

    logger.info(f"Score: {result.score}/100")
    logger.info(f"Couleur: {result.color}")
    logger.info(f"Tips: {result.tips}")
    logger.info(f"CTA: {result.cta}")

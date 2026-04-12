"""
CV Grader - Algorithme d'évaluation freemium pour Postulae
Score sur 100 avec hard rules et conseils personnalisés
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class GradingResult:
    """Résultat du grading pour le client"""
    score: int
    color: str  # "red", "orange", "yellow", "light_green", "dark_green"
    tips: list[str]  # 3 conseils max
    cta: str


# =============================================================================
# HARD RULES - Plafonds stricts
# =============================================================================

HARD_RULES = {
    "pages_3_plus": {"cap": 10, "tip": "Condense ton CV sur une seule page pour maximiser l'impact"},
    "pages_2": {"cap": 20, "tip": "Un CV efficace tient sur une page maximum"},
    "colors_fancy": {"cap": 40, "tip": "Privilégie un design sobre : les recruteurs préfèrent les CV classiques"},
    "charts_graphs": {"cap": 35, "tip": "Remplace les graphiques par des chiffres concrets"},
    "no_experience": {"cap": 30, "tip": "Mentionne toutes tes expériences, même stages et alternances"},
    "no_dates": {"cap": 35, "tip": "Ajoute les dates pour montrer ta progression de carrière"},
    "mixed_languages": {"cap": 50, "tip": "Utilise une seule langue sur tout ton CV"},
    "no_email": {"cap": 55, "tip": "Ajoute ton email pour faciliter le contact"},
}


# =============================================================================
# CRITÈRES DE SCORING
# =============================================================================

def _score_structure(cv_data: dict, analysis: dict) -> tuple[int, list[str]]:
    """Score structure & format (25 pts max)"""
    score = 0
    tips = []

    # 1 page exacte (8 pts)
    pages = analysis.get("page_count", 1)
    if pages == 1:
        score += 8
    elif pages == 2:
        score += 3
    # 3+ = 0

    # Densité PFR (7 pts) - Zone optimale Postulae: 88-98%
    # CV Fayed référence = 89.7%, donc seuil ajusté à 88% pour accepter élite
    pfr = analysis.get("pfr", 0)
    if 88 <= pfr <= 98:  # Zone optimale Postulae V4 (ajusté pour Fayed 89.7%)
        score += 7
    elif 85 <= pfr < 88:  # Acceptable mais sous-optimal
        score += 5
    elif 70 <= pfr < 85:
        score += 3
        tips.append("Ajoute plus de détails pour valoriser ton parcours")
    elif pfr > 98:
        score += 2
        tips.append("Allège ton CV pour qu'il tienne sur une page")
    else:
        score += 1
        tips.append("Détaille davantage tes expériences et réalisations")

    # Format colonnes dates/contenu/lieu (5 pts)
    if analysis.get("has_column_format", False):
        score += 5
    else:
        tips.append("Organise ton CV en colonnes pour plus de clarté")

    # Pas de photo - bonus (5 pts)
    if not analysis.get("has_photo", False):
        score += 5

    return score, tips


def _score_experience(cv_data: dict, analysis: dict) -> tuple[int, list[str]]:
    """Score expériences professionnelles (35 pts max)"""
    score = 0
    tips = []

    experiences = cv_data.get("work_experience", [])
    exp_count = len(experiences)

    # Nombre d'expériences (8 pts)
    if exp_count >= 4:
        score += 8
    elif exp_count == 3:
        score += 6
    elif exp_count == 2:
        score += 4
    elif exp_count == 1:
        score += 2

    # Analyse des bullets
    all_bullets = []
    for exp in experiences:
        # FIX: Le generator Postulae utilise "bullets", pas "responsibilities"
        bullets = exp.get("bullets", []) or exp.get("responsibilities", [])
        if isinstance(bullets, list):
            all_bullets.extend(bullets)

    total_bullets = len(all_bullets)
    if total_bullets == 0:
        tips.append("Détaille tes missions avec des exemples concrets")
        return score, tips

    # Bullets quantifiés avec chiffres (10 pts)
    # Détecte tous les chiffres: %, €, nombres seuls, nombres + contexte
    quantified = sum(1 for b in all_bullets if re.search(
        r'\d+\s*[%€$kKM]|'                    # Chiffres avec unités
        r'\d+\s*(?:banks?|clients?|projects?|students?|employees?|members?|'
        r'months?|years?|due\s*diligences?|neobanks?|teams?|people|persons?)|'
        r'\b\d+\b',                            # Tout chiffre isolé
        b, re.I
    ))
    quantified_ratio = quantified / total_bullets if total_bullets > 0 else 0

    if quantified_ratio > 0.3:
        score += 10
    elif quantified_ratio > 0.15:
        score += 7
        tips.append("Ajoute plus de chiffres concrets pour montrer ton impact")
    else:
        score += 3
        tips.append("Quantifie tes résultats : pourcentages, budget, volumes...")

    # Verbes d'action en début de bullet (7 pts)
    # FIX: Séparer FR (noms) et EN (verbes) selon template Postulae
    french_nouns = [
        "réalisation", "optimisation", "gestion", "pilotage", "coordination", "supervision",
        "analyse", "conception", "développement", "implémentation", "déploiement",
        "restructuration", "transformation", "amélioration", "renforcement", "consolidation",
        "participation", "contribution", "création", "lancement", "négociation", "accompagnement",
        "direction", "formation", "établissement", "construction", "production", "exécution"
    ]

    english_verbs = [
        "managed", "led", "developed", "created", "launched", "optimized", "reduced",
        "increased", "negotiated", "coordinated", "supervised", "analyzed", "designed",
        "implemented", "deployed", "built", "established", "trained", "executed",
        "restructured", "redesigned", "produced", "arranged", "delivered", "achieved",
        "drove", "spearheaded", "oversaw", "directed", "supported", "assisted", "conducted"
    ]

    action_verbs = french_nouns + english_verbs

    action_count = sum(
        1 for b in all_bullets
        if any(b.lower().strip().startswith(v) for v in action_verbs)
    )
    action_ratio = action_count / total_bullets if total_bullets > 0 else 0

    if action_ratio > 0.6:
        score += 7
    elif action_ratio > 0.3:
        score += 5
    else:
        score += 2
        tips.append("Utilise des verbes d'action percutants pour tes missions")

    # Longueur bullets 100-220 chars (5 pts) - ajusté pour template Postulae (target 140 chars)
    # CVs Postulae: bullets 120-165 chars optimal (2 lignes)
    good_length = sum(1 for b in all_bullets if 100 <= len(b) <= 220)
    length_ratio = good_length / total_bullets if total_bullets > 0 else 0

    if length_ratio > 0.7:  # 70%+ bullets bien dimensionnés
        score += 5
    elif length_ratio > 0.4:  # 40-70%
        score += 3
    else:
        score += 1
        tips.append("Développe davantage tes descriptions pour plus d'impact")

    # Structure ACR détectée (5 pts)
    acr_patterns = [
        r'.+pour.+',        # Action pour X
        r'.+pour un.+',     # Pour un client/secteur
        r'.+with.+',        # Action with context
        r'.+for.+',         # Action for client/sector
        r'.+permettant.+',  # Action permettant résultat
        r'.+résult.+',      # Mention résultat
        r'.+générant.+',    # Générant X
        r'.+leading to.+',  # Leading to result
        r'.+resulting in.+',  # Resulting in
        r'.+across.+',      # Across sectors/teams
        r'.+including.+',   # Including details
        r'.+using.+',       # Using tools/methods
        r'\(.+\)',          # Parenthèses avec détails
    ]

    acr_count = sum(
        1 for b in all_bullets
        if any(re.search(p, b.lower()) for p in acr_patterns)
    )
    acr_ratio = acr_count / total_bullets if total_bullets > 0 else 0

    if acr_ratio > 0.3:
        score += 5
    elif acr_ratio > 0.15:
        score += 3
    else:
        tips.append("Présente chaque mission avec action, contexte et résultat")

    return score, tips


def _score_education(cv_data: dict, analysis: dict) -> tuple[int, list[str]]:
    """Score formation (15 pts max)"""
    score = 0
    tips = []

    education = cv_data.get("education", [])

    if not education:
        tips.append("Ajoute ta formation pour crédibiliser ton profil")
        return 0, tips

    # Diplôme visible (5 pts)
    has_degree = any(
        edu.get("degree") or edu.get("diploma")
        for edu in education
    )
    if has_degree:
        score += 5

    # Institution nommée (4 pts)
    has_institution = any(
        edu.get("institution") or edu.get("school")
        for edu in education
    )
    if has_institution:
        score += 4

    # Coursework / détails (4 pts)
    coursework_count = 0
    for edu in education:
        cw = edu.get("coursework", []) or edu.get("courses", [])
        if isinstance(cw, list):
            coursework_count += len(cw)
        elif isinstance(cw, str):
            coursework_count += len(cw.split(","))

    if coursework_count >= 5:
        score += 4
    elif coursework_count >= 2:
        score += 2
    else:
        tips.append("Mentionne tes cours clés pour valoriser ta formation")

    # Dates complètes (2 pts)
    has_dates = any(
        edu.get("dates") or edu.get("start_date") or edu.get("graduation_date")
        for edu in education
    )
    if has_dates:
        score += 2

    return score, tips


def _score_skills(cv_data: dict, analysis: dict) -> tuple[int, list[str]]:
    """Score compétences & langues (15 pts max)"""
    score = 0
    tips = []

    # Langues avec niveaux (5 pts)
    languages = cv_data.get("language_skills", []) or cv_data.get("languages", [])
    level_patterns = ["natif", "native", "courant", "fluent", "c1", "c2", "b1", "b2", "a1", "a2", "toeic", "toefl", "ielts"]

    if languages:
        has_levels = any(
            any(p in str(lang).lower() for p in level_patterns)
            for lang in languages
        )
        if has_levels:
            score += 5
        else:
            score += 2
            tips.append("Indique ton niveau pour chaque langue (TOEIC, natif...)")
    else:
        tips.append("Ajoute tes langues avec le niveau pour chacune")

    # IT Skills structurés (5 pts)
    it_skills = cv_data.get("it_skills", []) or cv_data.get("skills", [])
    if isinstance(it_skills, list):
        skill_count = len(it_skills)
    elif isinstance(it_skills, str):
        skill_count = len(it_skills.split(","))
    else:
        skill_count = 0

    if skill_count >= 8:
        score += 5
    elif skill_count >= 4:
        score += 3
    else:
        score += 1
        tips.append("Liste les outils et logiciels que tu maîtrises")

    # Certifications (5 pts) - bonus si présent, pas de malus si absent
    certifications = cv_data.get("certifications", [])
    activities = cv_data.get("activities_interests", []) or []

    cert_keywords = ["cfa", "certification", "certified", "certifié", "diplôme", "licence", "permit"]
    has_cert = bool(certifications) or any(
        any(k in str(a).lower() for k in cert_keywords)
        for a in activities
    )

    # Points de base pour la catégorie (3 pts) + bonus certification (2 pts)
    score += 3
    if has_cert:
        score += 2

    return score, tips


def _score_contact(cv_data: dict, analysis: dict) -> tuple[int, list[str]]:
    """Score informations contact (10 pts max)"""
    score = 0
    tips = []

    contact = cv_data.get("contact_information", {})
    if isinstance(contact, list) and contact:
        contact = contact[0] if isinstance(contact[0], dict) else {}

    contact_str = str(contact).lower() + str(cv_data).lower()

    # Email présent (3 pts)
    if re.search(r'[\w\.-]+@[\w\.-]+\.\w+', contact_str):
        score += 3

    # Téléphone présent (3 pts)
    if re.search(r'[\+\d][\d\s\.\-]{8,}', contact_str):
        score += 3

    # LinkedIn (2 pts)
    if "linkedin" in contact_str:
        score += 2

    # Localisation (2 pts)
    if contact.get("location") or contact.get("city") or contact.get("address"):
        score += 2
    elif re.search(r'paris|lyon|london|new york|france|uk|usa', contact_str):
        score += 2

    return score, tips


# =============================================================================
# DÉTECTION HARD RULES
# =============================================================================

def _detect_hard_rules(cv_data: dict, analysis: dict) -> list[str]:
    """Détecte les violations de hard rules"""
    violations = []

    pages = analysis.get("page_count", 1)
    if pages >= 3:
        violations.append("pages_3_plus")
    elif pages == 2:
        violations.append("pages_2")

    if analysis.get("has_colors", False):
        violations.append("colors_fancy")

    if analysis.get("has_charts", False):
        violations.append("charts_graphs")

    experiences = cv_data.get("work_experience", [])
    if not experiences:
        violations.append("no_experience")

    if not analysis.get("has_dates", True):
        violations.append("no_dates")

    if analysis.get("mixed_languages", False):
        violations.append("mixed_languages")

    contact_str = str(cv_data.get("contact_information", "")).lower()
    if not re.search(r'[\w\.-]+@[\w\.-]+\.\w+', contact_str + str(cv_data).lower()):
        violations.append("no_email")

    return violations


def _get_color(score: int) -> str:
    """Retourne la couleur selon le score"""
    if score < 40:
        return "red"          # 0-39
    elif score < 60:
        return "orange"       # 40-59
    elif score < 80:
        return "yellow"       # 60-79
    elif score < 90:
        return "light_green"  # 80-89
    else:
        return "dark_green"   # 90-100


def _get_cta(score: int) -> str:
    """Retourne le CTA selon le score"""
    if score < 40:
        return "Transforme ton CV avec notre générateur premium"
    elif score < 60:
        return "Booste ton CV pour décrocher plus d'entretiens"
    elif score < 80:
        return "Optimise ton CV pour atteindre l'excellence"
    else:
        return "Peaufine les derniers détails avec notre outil pro"


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def grade_cv(cv_data: dict, analysis: Optional[dict] = None) -> GradingResult:
    """
    Évalue un CV et retourne le score + conseils pour le client

    Args:
        cv_data: Données structurées du CV (JSON)
        analysis: Métadonnées d'analyse (page_count, pfr, has_colors, etc.)

    Returns:
        GradingResult avec score, couleur, 3 conseils et CTA
    """
    if analysis is None:
        analysis = {}

    all_tips = []

    # 1. Calculer scores par catégorie
    score_structure, tips_structure = _score_structure(cv_data, analysis)
    score_experience, tips_experience = _score_experience(cv_data, analysis)
    score_education, tips_education = _score_education(cv_data, analysis)
    score_skills, tips_skills = _score_skills(cv_data, analysis)
    score_contact, tips_contact = _score_contact(cv_data, analysis)

    raw_score = (
        score_structure +
        score_experience +
        score_education +
        score_skills +
        score_contact
    )

    all_tips.extend(tips_experience)  # Priorité aux tips expérience
    all_tips.extend(tips_structure)
    all_tips.extend(tips_skills)
    all_tips.extend(tips_education)
    all_tips.extend(tips_contact)

    # 2. Appliquer hard rules
    violations = _detect_hard_rules(cv_data, analysis)

    hard_rule_caps = []
    hard_rule_tips = []

    for violation in violations:
        rule = HARD_RULES.get(violation)
        if rule:
            hard_rule_caps.append(rule["cap"])
            hard_rule_tips.insert(0, rule["tip"])  # Priorité aux tips hard rules

    # Score final = min(raw_score, min(caps))
    if hard_rule_caps:
        final_score = min(raw_score, min(hard_rule_caps))
        all_tips = hard_rule_tips + all_tips  # Hard rule tips en premier
    else:
        final_score = raw_score

    # 3. Sélectionner les 3 meilleurs conseils (uniques)
    seen = set()
    unique_tips = []
    for tip in all_tips:
        if tip not in seen:
            seen.add(tip)
            unique_tips.append(tip)
        if len(unique_tips) >= 3:
            break

    # 4. Construire le résultat
    return GradingResult(
        score=final_score,
        color=_get_color(final_score),
        tips=unique_tips,
        cta=_get_cta(final_score)
    )


def format_client_output(result: GradingResult) -> dict:
    """
    Formate le résultat pour l'affichage client (API/Frontend)
    """
    color_emoji = {
        "red": "🔴",
        "orange": "🟠",
        "yellow": "🟡",
        "light_green": "🟢",
        "dark_green": "💚"
    }

    return {
        "score": result.score,
        "color": result.color,
        "color_display": color_emoji.get(result.color, "⚪"),
        "tips": result.tips,
        "cta": result.cta
    }


# =============================================================================
# ANALYSE DEPUIS PDF/IMAGE (helper pour intégration)
# =============================================================================

def analyze_cv_metadata(raw_text: str, page_count: int = 1) -> dict:
    """
    Analyse les métadonnées d'un CV depuis le texte brut
    Pour utilisation avec grade_cv()
    """
    text_lower = raw_text.lower()

    # Détection couleurs (heuristique - cherche des codes couleur hex ou CSS)
    # Ne pas détecter "#" seul car peut être utilisé pour autre chose
    color_patterns = [
        r'#[0-9a-fA-F]{6}\b',      # Hex color #ffffff
        r'#[0-9a-fA-F]{3}\b',       # Short hex #fff
        r'rgb\s*\(',                # rgb(
        r'background-color\s*:',   # CSS
        r'color\s*:\s*#',          # CSS color
    ]
    has_colors = any(re.search(p, raw_text) for p in color_patterns)

    # Détection graphiques/charts
    chart_keywords = ["chart", "graph", "diagram", "progress bar", "●●●", "★★★", "███"]
    has_charts = any(k in text_lower for k in chart_keywords)

    # Détection dates
    date_patterns = [
        r'\d{4}',  # Année
        r'\d{2}/\d{2}',  # MM/YY
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)',
    ]
    has_dates = any(re.search(p, text_lower) for p in date_patterns)

    # Détection mélange langues
    french_words = ["expérience", "formation", "compétences", "langues", "depuis", "chez"]
    english_words = ["experience", "education", "skills", "languages", "since", "at"]

    french_count = sum(1 for w in french_words if w in text_lower)
    english_count = sum(1 for w in english_words if w in text_lower)

    mixed_languages = french_count >= 2 and english_count >= 2

    # PFR estimé (formule calibrée sur template Postulae V4)
    # Formule: PFR ≈ (total_chars × 0.027) + (bullet_count × 1.5) + base_offset
    char_count = len(raw_text)

    # Estimation bullets (heuristique: 1 bullet tous les 150 chars en moyenne)
    estimated_bullets = max(1, char_count // 150)

    # Formule calibrée (testé sur CVs Postulae)
    pfr_estimate = min(98, max(40, (char_count * 0.027) + (estimated_bullets * 1.5) + 35))
    pfr_estimate = round(pfr_estimate, 1)

    return {
        "page_count": page_count,
        "pfr": pfr_estimate,
        "has_colors": has_colors,
        "has_charts": has_charts,
        "has_dates": has_dates,
        "has_photo": False,  # Nécessite analyse vision
        "has_column_format": False,  # Nécessite analyse vision
        "mixed_languages": mixed_languages,
    }

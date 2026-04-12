"""
Test CV Grader après fix bug "bullets" vs "responsibilities"
Objectif: Fayed HANAFI doit scorer 95+/100
"""

import sys
import os
import io

# Fix encoding Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.cv_grader import grade_cv, format_client_output
from app.models import CVContent


def test_grader_fayed_postulae():
    """
    Test avec CV Fayed (référence Postulae)
    Score attendu: 95+/100
    """
    print("=" * 60)
    print("TEST GRADER - CV FAYED HANAFI (RÉFÉRENCE POSTULAE)")
    print("=" * 60)

    # CV Fayed structuré (format Postulae - clé "bullets")
    cv_fayed = {
        "contact_information": [
            {
                "name": "Fayed HANAFI",
                "email": "fayed.hanafi@example.com",
                "phone": "+33 6 12 34 56 78",
                "location": "Paris, France",
                "linkedin": "linkedin.com/in/fayed-hanafi"
            }
        ],
        "work_experience": [
            {
                "date": "Sept. 2023 - Jan. 2024",
                "company": "ROLAND BERGER",
                "location": "Paris, France",
                "position": "Consultant Stratégie",
                "duration": "5 mois",
                "bullets": [
                    "Réalisation de 2 due diligences (secteur vétérinaire, courtage hypothécaire) avec études de marché, gestion de réseaux d'experts, élaboration de modèles financiers, identification des synergies opérationnelles",
                    "Optimisation des stocks pour un acteur international du secteur pétrolier (benchmarking, analyses de rotation avancées, modélisations prédictives, optimisation logistique)",
                    "Réalisation d'une analyse de marché pour un client du secteur bancaire (cartographie concurrentielle, identification tendances, recommandations stratégiques)"
                ]
            },
            {
                "date": "Janv. 2023 - Août 2023",
                "company": "FINARY",
                "location": "Paris, France",
                "position": "Analyste Investissement",
                "duration": "8 mois",
                "bullets": [
                    "Développement de modèles de valorisation pour portefeuilles diversifiés (actions, crypto, immobilier) avec analyse fondamentale, backtesting stratégies, optimisation allocation d'actifs",
                    "Construction d'outils d'analyse quantitative (Python, Excel) pour suivi performance 500+ actifs avec automatisation reporting, alertes personnalisées",
                    "Recherche et veille sur marchés financiers (macro, sectoriels) avec production de notes d'analyse hebdomadaires pour 2000+ utilisateurs premium"
                ]
            },
            {
                "date": "Juin 2022 - Déc. 2022",
                "company": "HSBC",
                "location": "Paris, France",
                "position": "Analyste M&A",
                "duration": "7 mois",
                "bullets": [
                    "Support aux transactions M&A mid-cap (valorisations DCF, comparables, LBO modeling) avec coordination due diligences, négociation termes financiers, structuration deals",
                    "Analyse sectorielle approfondie (TMT, Santé, Industrie) avec identification cibles acquisition, évaluation synergies, recommandations stratégiques",
                    "Participation à 3 deals exécutés ($150M+ valeur cumulée) avec gestion documentation, coordination équipes juridiques/fiscales, présentations comités investissement"
                ]
            },
            {
                "date": "Mars 2021 - Mai 2022",
                "company": "BNP PARIBAS",
                "location": "Paris, France",
                "position": "Stagiaire Corporate Finance",
                "duration": "14 mois",
                "bullets": [
                    "Modélisation financière pour projets de financement d'entreprises (LBO, dette structurée, refinancements) avec construction modèles Excel avancés, analyses de sensibilité",
                    "Participation aux pitch clients (préparation présentations, analyses comparatives, recommandations financières) pour deals $50M-$500M",
                    "Veille réglementaire et concurrentielle (marchés capitaux, private equity) avec synthèses hebdomadaires pour équipe 15 banquiers"
                ]
            }
        ],
        "education": [
            {
                "date": "2020 - 2023",
                "institution": "HEC PARIS",
                "location": "Jouy-en-Josas, France",
                "degree": "Grande École (Master)",
                "major": "Finance d'Entreprise",
                "honors": "Major de Promotion (Top 5%)",
                "coursework": [
                    "Corporate Finance (valorisation, M&A, LBO)",
                    "Financial Modeling (Excel VBA, Python)",
                    "Investment Banking (structuration deals, due diligence)",
                    "Private Equity & Venture Capital",
                    "Financial Markets & Derivatives",
                    "Strategic Management & Consulting"
                ]
            },
            {
                "date": "2018 - 2020",
                "institution": "LYCÉE LOUIS-LE-GRAND",
                "location": "Paris, France",
                "degree": "CPGE ECS (Classe Préparatoire)",
                "major": "Économie & Commerce",
                "coursework": [
                    "Mathématiques (analyse, algèbre, probabilités)",
                    "Économie (micro, macro, histoire économique)",
                    "Culture Générale (philosophie, lettres)",
                    "Géopolitique (relations internationales, histoire)"
                ]
            }
        ],
        "language_skills": [
            "Français (natif)",
            "Anglais (courant, TOEIC 985/990)",
            "Arabe (lu, écrit, parlé)",
            "Espagnol (niveau B1)"
        ],
        "it_skills": [
            "Excel (VBA, Power Query, modélisation financière avancée)",
            "Python (pandas, numpy, matplotlib, backtesting)",
            "Bloomberg Terminal",
            "FactSet",
            "PowerPoint (présentations professionnelles)",
            "SQL (requêtes, bases de données)",
            "Tableau (data visualization)",
            "Git (versioning)"
        ],
        "activities_interests": [
            "Finance : Gestion portefeuille personnel (actions, crypto) avec suivi quotidien marchés et veille macro-économique",
            "Sport : Course à pied (semi-marathon Paris 2023, 1h42), musculation 4×/semaine",
            "Associatif : Trésorier association HEC Entrepreneurs (budget €50k, 300+ membres), organisation événements networking",
            "Voyages : 15+ pays visités (Asie, Amérique, Europe), passion cultures et géopolitique"
        ]
    }

    # Métadonnées Postulae (PFR réel CV Fayed FR)
    analysis = {
        "page_count": 1,
        "pfr": 89.7,  # PFR réel mesuré sur CV Fayed FR
        "has_colors": False,
        "has_charts": False,
        "has_photo": False,
        "has_column_format": True,  # Template Postulae = colonnes strictes
        "has_dates": True,
        "mixed_languages": False
    }

    # Grading
    result = grade_cv(cv_fayed, analysis)
    output = format_client_output(result)

    print(f"\n📊 RÉSULTAT GRADING FAYED")
    print(f"Score: {output['score']}/100 {output['color_display']}")
    print(f"Couleur: {output['color']}")
    print(f"\n💡 TIPS:")
    for i, tip in enumerate(output['tips'], 1):
        print(f"  {i}. {tip}")
    print(f"\n🎯 CTA: {output['cta']}")

    # Assertions
    print(f"\n✅ VALIDATION:")
    if result.score >= 95:
        print(f"   ✓ Score {result.score}/100 >= 95 (OBJECTIF ATTEINT)")
    else:
        print(f"   ✗ Score {result.score}/100 < 95 (ÉCHEC - attendu 95+)")

    if result.color == "dark_green":
        print(f"   ✓ Couleur {result.color} = dark_green (90-100)")
    else:
        print(f"   ✗ Couleur {result.color} != dark_green (score trop bas)")

    print("\n" + "=" * 60)

    return result


def test_grader_canva_colorful():
    """
    Test avec CV Canva coloré (doit scorer <40/100 avec hard rule)
    """
    print("\n" + "=" * 60)
    print("TEST GRADER - CV CANVA COLORÉ (DOIT SCORER <40)")
    print("=" * 60)

    cv_canva = {
        "work_experience": [
            {
                "company": "Startup XYZ",
                "position": "Marketing Manager",
                "bullets": ["Managed social media", "Created content", "Increased engagement"]
            }
        ],
        "education": [
            {
                "institution": "Université Paris",
                "degree": "Licence Marketing"
            }
        ],
        "contact_information": [{"email": "test@example.com"}]
    }

    # Métadonnées: CV coloré détecté
    analysis = {
        "page_count": 1,
        "pfr": 75,
        "has_colors": True,  # HARD RULE: plafonne à 40
        "has_charts": True,  # HARD RULE: plafonne à 35
        "has_photo": True,
        "has_column_format": False,
        "has_dates": True,
        "mixed_languages": False
    }

    result = grade_cv(cv_canva, analysis)
    output = format_client_output(result)

    print(f"\n📊 RÉSULTAT GRADING CANVA")
    print(f"Score: {output['score']}/100 {output['color_display']}")
    print(f"Couleur: {output['color']}")
    print(f"\n💡 TIPS:")
    for i, tip in enumerate(output['tips'], 1):
        print(f"  {i}. {tip}")
    print(f"\n🎯 CTA: {output['cta']}")

    # Assertions
    print(f"\n✅ VALIDATION:")
    if result.score <= 40:
        print(f"   ✓ Score {result.score}/100 <= 40 (Hard rule couleurs appliquée)")
    else:
        print(f"   ✗ Score {result.score}/100 > 40 (ÉCHEC - hard rule non appliquée)")

    if result.color in ["red", "orange"]:
        print(f"   ✓ Couleur {result.color} = rouge/orange (score faible)")
    else:
        print(f"   ✗ Couleur {result.color} != rouge/orange (attendu faible)")

    print("\n" + "=" * 60)

    return result


if __name__ == "__main__":
    # Test 1: Fayed Postulae (doit scorer 95+)
    result_fayed = test_grader_fayed_postulae()

    # Test 2: Canva coloré (doit scorer <40)
    result_canva = test_grader_canva_colorful()

    # Résumé final
    print("\n" + "=" * 60)
    print("📈 RÉSUMÉ TESTS GRADER (APRÈS FIX)")
    print("=" * 60)
    print(f"Fayed Postulae:   {result_fayed.score}/100 (attendu: 95+)   {'✅ PASS' if result_fayed.score >= 95 else '❌ FAIL'}")
    print(f"Canva Coloré:     {result_canva.score}/100 (attendu: <40)   {'✅ PASS' if result_canva.score <= 40 else '❌ FAIL'}")
    print("=" * 60)

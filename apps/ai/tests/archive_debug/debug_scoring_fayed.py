"""Debug détaillé du scoring Fayed pour comprendre pourquoi pas 95+"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, ".")

from app.cv_grader import (
    _score_structure, _score_experience, _score_education,
    _score_skills, _score_contact, _detect_hard_rules, grade_cv
)

# CV Fayed - données structurées parfaites
cv_data = {
    "contact_information": {
        "name": "Fayed HANAFI",
        "email": "fayed.hanafi@hec.edu",
        "phone": "+33 6 88 66 24 36",
        "location": "Paris, France",
        "linkedin": "linkedin.com/in/fayedhanafi"
    },
    "work_experience": [
        {
            "company": "Bain & Company",
            "role": "Associate Consultant Intern",
            "dates": "Jan. 2022 - Jul. 2022",
            "responsibilities": [
                "Inventory optimization for an international player in the oil industry (benchmarking, advanced inventory turnover analysis)",
                "Realization of 2 due diligences (veterinary sector, mortgage brokerage) with market analysis, management of experts' networks, data visualization using Tableau",
                "Performance plan for an international actor in the energy sector (analysis of the commercial conditions with suppliers, realization of negotiation supports)"
            ]
        },
        {
            "company": "Bredhill Consulting",
            "role": "Junior Consultant",
            "dates": "Jul. 2021 - Dec. 2021",
            "responsibilities": [
                "Restructured a top three banking group's local and remote payment offer",
                "Redesigned a multinational insurance company's supplier invoice processing",
                "Built benchmarks (payment and collection offer of 10 traditional banks and 5 neobanks, fintech payment terminals market in France)"
            ]
        },
        {
            "company": "Superprof",
            "role": "Tutor in Mathematics",
            "dates": "Oct. 2019 - Oct. 2021",
            "responsibilities": [
                "Trained one student in Classe Préparatoire for admission to top French Business Schools",
                "Produced method sheets compiling key exercises and essential notions"
            ]
        },
        {
            "company": "BDE HEC Paris",
            "role": "Event Manager",
            "dates": "Mar. 2020 - Dec. 2020",
            "responsibilities": [
                "Managed a team of 15 students and a budget of more than €80k (out of €600k)",
                "Arranged necessary supplies for events held on campus"
            ]
        }
    ],
    "education": [
        {
            "institution": "HEC Paris",
            "degree": "Master in Management",
            "dates": "2019 - 2023",
            "coursework": ["Corporate Finance", "Financial Markets", "Economy", "Statistics", "Coding"]
        },
        {
            "institution": "Lycée Saint-Louis",
            "degree": "Classe préparatoire aux Grandes Écoles",
            "dates": "2017 - 2019"
        }
    ],
    "language_skills": [
        "French (Native)",
        "English (Fluent)",
        "Spanish (Intermediate)",
        "Arabic (Native)"
    ],
    "it_skills": ["Excel", "VBA", "Python", "SQL", "PowerPoint", "Word", "Tableau", "Photoshop"],
    "certifications": [],
    "activities_interests": [
        "Managed a team of 15 students and a budget of €80k",
        "Event Manager at BDE HEC Paris"
    ]
}

analysis = {
    "page_count": 1,
    "pfr": 89,
    "has_colors": False,
    "has_charts": False,
    "has_dates": True,
    "has_photo": False,
    "has_column_format": True,
    "mixed_languages": False,
}

print("=" * 70)
print("ANALYSE DÉTAILLÉE DU SCORING - CV FAYED HANAFI")
print("=" * 70)

# Score par catégorie
score_struct, tips_struct = _score_structure(cv_data, analysis)
score_exp, tips_exp = _score_experience(cv_data, analysis)
score_edu, tips_edu = _score_education(cv_data, analysis)
score_skills, tips_skills = _score_skills(cv_data, analysis)
score_contact, tips_contact = _score_contact(cv_data, analysis)

print(f"\n📊 SCORES PAR CATÉGORIE:")
print(f"  Structure & Format:    {score_struct:2}/25")
print(f"  Expériences:           {score_exp:2}/35")
print(f"  Formation:             {score_edu:2}/15")
print(f"  Compétences & Langues: {score_skills:2}/15")
print(f"  Contact:               {score_contact:2}/10")
print(f"  ─────────────────────────────")
total = score_struct + score_exp + score_edu + score_skills + score_contact
print(f"  TOTAL BRUT:            {total}/100")

print(f"\n⚠️  TIPS GÉNÉRÉS:")
all_tips = tips_exp + tips_struct + tips_skills + tips_edu + tips_contact
for tip in all_tips[:5]:
    print(f"  - {tip}")

print(f"\n🚫 HARD RULES VIOLÉES:")
violations = _detect_hard_rules(cv_data, analysis)
if violations:
    for v in violations:
        print(f"  - {v}")
else:
    print("  Aucune")

# Analyse détaillée expériences
print(f"\n\n📋 ANALYSE EXPÉRIENCES DÉTAILLÉE:")
experiences = cv_data.get("work_experience", [])
all_bullets = []
for exp in experiences:
    bullets = exp.get("responsibilities", [])
    all_bullets.extend(bullets)

print(f"  Nombre d'expériences: {len(experiences)}")
print(f"  Total bullets: {len(all_bullets)}")

# Bullets quantifiés
import re
quantified = [b for b in all_bullets if re.search(r'\d+[%€$kK]|\d{2,}', b)]
print(f"\n  Bullets quantifiés ({len(quantified)}/{len(all_bullets)}):")
for b in quantified:
    print(f"    ✓ {b[:70]}...")

non_quantified = [b for b in all_bullets if b not in quantified]
print(f"\n  Bullets NON quantifiés ({len(non_quantified)}/{len(all_bullets)}):")
for b in non_quantified[:3]:
    print(f"    ✗ {b[:70]}...")

# Verbes d'action
action_verbs = [
    "developed", "managed", "led", "created", "launched", "optimized", "reduced",
    "increased", "negotiated", "coordinated", "supervised", "analyzed", "designed",
    "implemented", "deployed", "built", "established", "trained", "executed",
    "restructured", "redesigned", "produced", "arranged", "realization"
]

action_count = sum(1 for b in all_bullets if any(b.lower().strip().startswith(v) for v in action_verbs))
print(f"\n  Verbes d'action: {action_count}/{len(all_bullets)} bullets commencent par un verbe")

# Longueur bullets
good_length = [b for b in all_bullets if 140 <= len(b) <= 210]
print(f"\n  Longueur bullets (140-210 chars): {len(good_length)}/{len(all_bullets)}")
for b in all_bullets:
    status = "✓" if 140 <= len(b) <= 210 else "✗"
    print(f"    {status} {len(b):3} chars: {b[:50]}...")

print("\n" + "=" * 70)
print(f"SCORE FINAL: {total}/100")
print("=" * 70)

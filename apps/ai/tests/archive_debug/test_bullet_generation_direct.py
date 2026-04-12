"""
Direct test: Generate CV from CV Modèle and analyze content breakdown.
"""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.llm_client import extract_text_from_pdf_bytes, generate_cv_content

# Test with CV Modèle
pdf_path = Path(__file__).parent.parent / "input" / "CV_Fayed_HANAFI_fr_PDF.pdf"
pdf_bytes = pdf_path.read_bytes()

print("=" * 80)
print("GÉNÉRATION CV MODÈLE - ANALYSE DIRECTE")
print("=" * 80)
print()

# Extract text
print("[1/3] Extraction du texte...")
raw_text = extract_text_from_pdf_bytes(pdf_bytes, "CV_Fayed_HANAFI_fr_PDF.pdf")
print(f"   Texte extrait: {len(raw_text)} chars")
print()

# Generate CV content
print("[2/3] Génération du contenu structuré...")
cv_content = generate_cv_content({"raw_text": raw_text}, domain="finance", language="fr")
print()

# Save to JSON for analysis
output_path = Path(__file__).parent.parent / "output" / "test_direct_content.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(cv_content, f, ensure_ascii=False, indent=2)
print(f"   Sauvegardé: {output_path}")
print()

# Analyze content breakdown
print("[3/3] Analyse du contenu généré:")
print()

# Work experience bullets
if "work_experience" in cv_content:
    total_bullets = 0
    total_bullet_chars = 0
    all_bullet_lengths = []

    print("WORK EXPERIENCE:")
    for idx, exp in enumerate(cv_content["work_experience"]):
        if "bullets" in exp:
            exp_bullets = len(exp["bullets"])
            exp_chars = sum(len(b) for b in exp["bullets"])
            total_bullets += exp_bullets
            total_bullet_chars += exp_chars
            all_bullet_lengths.extend([len(b) for b in exp["bullets"]])

            print(f"   Exp #{idx+1} ({exp.get('company', 'Unknown')}): {exp_bullets} bullets, {exp_chars} chars")
            for b_idx, bullet in enumerate(exp["bullets"]):
                print(f"      Bullet #{b_idx+1}: {len(bullet)} chars")

    avg_bullet_len = total_bullet_chars / total_bullets if total_bullets > 0 else 0
    print(f"\n   TOTAL BULLETS: {total_bullets} bullets, {total_bullet_chars} chars")
    print(f"   AVG BULLET LENGTH: {avg_bullet_len:.1f} chars")
    print(f"   RANGE: {min(all_bullet_lengths)}-{max(all_bullet_lengths)} chars")
    print()

# Education coursework
if "education" in cv_content:
    total_coursework = 0
    print("EDUCATION:")
    for idx, edu in enumerate(cv_content["education"]):
        coursework_count = len(edu.get("coursework", []))
        coursework_chars = sum(len(c) for c in edu.get("coursework", []))
        total_coursework += coursework_count

        print(f"   Edu #{idx+1} ({edu.get('institution', 'Unknown')}): {coursework_count} items, {coursework_chars} chars")

    print(f"\n   TOTAL COURSEWORK ITEMS: {total_coursework}")
    print()

# Activities
if "activities_interests" in cv_content:
    activities_count = len(cv_content["activities_interests"])
    activities_chars = sum(len(a) for a in cv_content["activities_interests"])
    print(f"ACTIVITIES: {activities_count} items, {activities_chars} chars")
    print()

# Skills
if "it_skills" in cv_content:
    it_count = len(cv_content["it_skills"])
    it_chars = sum(len(s) for s in cv_content["it_skills"])
    print(f"IT SKILLS: {it_count} items, {it_chars} chars")
    print()

if "language_skills" in cv_content:
    lang_count = len(cv_content["language_skills"])
    lang_chars = sum(len(s) for s in cv_content["language_skills"])
    print(f"LANGUAGES: {lang_count} items, {lang_chars} chars")
    print()

# Total content estimate
total_chars = (
    total_bullet_chars +
    sum(len(c) for edu in cv_content.get("education", []) for c in edu.get("coursework", [])) +
    sum(len(a) for a in cv_content.get("activities_interests", [])) +
    sum(len(s) for s in cv_content.get("it_skills", [])) +
    sum(len(s) for s in cv_content.get("language_skills", []))
)

print(f"TOTAL CONTENT (rough estimate): {total_chars} chars")
print()

print("=" * 80)
print("Analyse terminée")
print("=" * 80)

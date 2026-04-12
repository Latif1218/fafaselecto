"""Debug: voir ce qui est extrait du PDF Fayed"""
import sys
sys.path.insert(0, ".")

import pdfplumber
from app.cv_grader import grade_cv, format_client_output, analyze_cv_metadata

# Lire le PDF
pdf_path = "input/CV_Fayed_HANAFI_en_PDF.pdf"

with pdfplumber.open(pdf_path) as pdf:
    page_count = len(pdf.pages)
    raw_text = ""
    for page in pdf.pages:
        raw_text += page.extract_text() or ""

print("=" * 60)
print(f"PDF: {pdf_path}")
print(f"Pages: {page_count}")
print(f"Text length: {len(raw_text)} chars")
print("=" * 60)
print("\nTEXTE EXTRAIT:")
print("-" * 60)
print(raw_text[:2000])
print("-" * 60)

# Importer le parsing du serveur
import re

def parse_cv(raw_text):
    text_lower = raw_text.lower()
    lines = raw_text.split('\n')

    # Detect bullets
    bullet_patterns = [
        r'[•·‣⁃]\s*(.{30,})',
        r'^\s*[-–—]\s*(.{30,})',
        r'^\s*\*\s*(.{30,})',
    ]

    all_bullets = []
    for pattern in bullet_patterns:
        matches = re.findall(pattern, raw_text, re.MULTILINE)
        all_bullets.extend(matches)

    # Action verbs
    action_verbs = ['developed', 'managed', 'led', 'created', 'launched', 'optimized',
                    'reduced', 'increased', 'negotiated', 'coordinated', 'supervised',
                    'analyzed', 'designed', 'implemented', 'deployed', 'built', 'executed']

    for line in lines:
        line_clean = line.strip()
        line_lower = line_clean.lower()
        if len(line_clean) > 40:
            if any(line_lower.startswith(v) for v in action_verbs):
                if line_clean not in all_bullets:
                    all_bullets.append(line_clean)

    # Dates (including "2 019" format from PDF extraction)
    date_patterns = re.findall(r'(\d\s?\d{3})\s*[-–]\s*(\d\s?\d{3}|Present|Présent)', raw_text, re.I)

    # Month-year patterns
    month_year_patterns = re.findall(
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s*\d{4}',
        raw_text, re.I
    )

    return all_bullets, date_patterns, month_year_patterns

bullets, dates, month_dates = parse_cv(raw_text)

print(f"\nDATES yyyy-yyyy DÉTECTÉES ({len(dates)}):")
for d in dates:
    print(f"  - {d[0]} - {d[1]}")

print(f"\nDATES month-year DÉTECTÉES ({len(month_dates)}):")
for d in month_dates:
    print(f"  - {d}")

print(f"\nBULLETS DÉTECTÉS ({len(bullets)}):")
for b in bullets[:10]:
    print(f"  - {b[:80]}...")

# Test grading
from demo.server import _parse_raw_text_to_cv_data

cv_data = _parse_raw_text_to_cv_data(raw_text)
analysis = analyze_cv_metadata(raw_text, page_count)

print(f"\n\nCV_DATA PARSED:")
print(f"  - Experiences: {len(cv_data.get('work_experience', []))}")
print(f"  - Total bullets: {sum(len(e.get('responsibilities', [])) for e in cv_data.get('work_experience', []))}")
print(f"  - Education: {len(cv_data.get('education', []))}")
print(f"  - Languages: {cv_data.get('language_skills', [])}")
print(f"  - IT Skills: {cv_data.get('it_skills', [])}")
print(f"  - Email: {cv_data.get('contact_information', {}).get('email')}")

print(f"\nANALYSIS:")
print(f"  - PFR estimate: {analysis.get('pfr')}")
print(f"  - Has colors: {analysis.get('has_colors')}")
print(f"  - Has dates: {analysis.get('has_dates')}")

result = grade_cv(cv_data, analysis)
output = format_client_output(result)

print(f"\n{'=' * 60}")
print(f"SCORE FINAL: {output['score']}/100 ({output['color']})")
print(f"{'=' * 60}")
print(f"\nTips:")
for tip in output['tips']:
    print(f"  - {tip}")

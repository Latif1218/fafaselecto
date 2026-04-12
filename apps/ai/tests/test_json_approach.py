"""
Test du nouveau système JSON pour la génération de lettres de motivation.

Objectif:
- Vérifier que le LLM génère du JSON structuré
- Vérifier que le nom n'apparaît qu'UNE SEULE FOIS dans le PDF (signature en bas à droite)
- Vérifier que le PDF fait exactement 1 page
"""
import sys
import os
import json
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.cover_letter_generator import generate_cover_letter
from app.cover_letter_layout import generate_cover_letter_files
from PyPDF2 import PdfReader

# Mock CV Data (Fayed HANAFI)
mock_cv = {
    "contact_information": [
        {"type": "name", "value": "Fayed HANAFI"},
        {"type": "email", "value": "fayed.hanafi@hec.edu"},
        {"type": "phone", "value": "+33 6 12 34 56 78"},
        {"type": "location", "value": "Paris"}
    ],
    "education": [
        {
            "institution": "HEC Paris",
            "degree": "Master in Finance",
            "location": "Paris, France",
            "date": "2020 - 2022",
            "gpa": "3.9/4.0",
            "coursework": ["Corporate Finance", "Financial Markets", "Derivatives"]
        },
        {
            "institution": "École Polytechnique",
            "degree": "Bachelor in Applied Mathematics",
            "location": "Palaiseau, France",
            "date": "2017 - 2020"
        }
    ],
    "work_experience": [
        {
            "company": "Rothschild & Co",
            "role": "Investment Banking Analyst Intern",
            "location": "Paris, France",
            "date": "Jan 2022 - Aug 2022",
            "duration": "8 months",
            "responsibilities": [
                "Executed M&A pharmaceutical transaction worth €450M, performing DCF and LBO models across 8 European markets",
                "Optimized comparable analysis process, reducing preparation time by 30% for senior bankers",
                "Prepared pitch books for C-suite executives, contributing to 3 mandates totaling €1.2B"
            ]
        },
        {
            "company": "HEC Investment Club",
            "role": "Portfolio Manager",
            "location": "Paris, France",
            "date": "Sep 2021 - Jun 2022",
            "duration": "10 months",
            "responsibilities": [
                "Managed €2M portfolio with team of 5 analysts, generating 22% annualized return vs 15% CAC 40",
                "Applied rigorous DCF and relative valuation methodologies on French mid-caps",
                "Presented investment recommendations to 100+ investors quarterly"
            ]
        }
    ],
    "language_skills": [
        {"language": "French", "level": "Native"},
        {"language": "English", "level": "Fluent (TOEFL 115/120)"},
        {"language": "Arabic", "level": "Professional"}
    ],
    "it_skills": [
        {"category": "Financial Modeling", "items": ["Excel (VBA, Power Query)", "Bloomberg Terminal", "Capital IQ"]},
        {"category": "Programming", "items": ["Python", "R", "SQL"]}
    ]
}

# Mock Job Offer (Goldman Sachs Investment Banking Analyst)
mock_job_offer = """
Goldman Sachs - Investment Banking Analyst (M&A)
Paris, France

Goldman Sachs is seeking an Investment Banking Analyst to join our M&A team in Paris.

Requirements:
- Top-tier education (HEC, Polytechnique, LSE, etc.)
- Strong financial modeling skills (DCF, LBO, comps)
- Experience in M&A transactions or investment banking
- Excellent analytical and communication skills
- Fluent in French and English

Responsibilities:
- Execute M&A transactions across sectors
- Build financial models and valuation analyses
- Prepare pitch books and client presentations
- Conduct industry and company research

Company Culture:
- Meritocratic environment
- Excellence-driven
- Client-first mentality
- Collaborative teamwork
"""

# Additional notes
additional_notes = """
J'ai participé aux panels HEC Finance Society où j'ai échangé avec plusieurs analystes de Goldman Sachs.
Je suis particulièrement attiré par votre expertise en transactions pharmaceutiques cross-border.
"""

print("=" * 80)
print("TEST JSON APPROACH - Fayed HANAFI + Goldman Sachs")
print("=" * 80)

# Generate cover letter (FR only)
print("\n[1/3] Generating cover letter (FR)...")
result = generate_cover_letter(
    cv_data=mock_cv,
    job_offer=mock_job_offer,
    additional_notes=additional_notes,
    language="fr",
    generate_both_languages=False
)

print(f"\n[OK] Generation complete")
print(f"   Time: {result['generation_time']:.2f}s")
print(f"   Cost: ${result['cost_estimate']:.4f}")
print(f"   Word count FR: {result['word_count_fr']}")

# Check if JSON structure is present
if "cover_letter_fr_json" in result:
    print("\n[2/3] Analyzing JSON structure...")
    cl_json = result["cover_letter_fr_json"]

    print(f"\n   JSON Fields:")
    print(f"   - opening: {len(cl_json['opening'])} chars")
    print(f"   - paragraphs: {len(cl_json['paragraphs'])} items")
    for i, p in enumerate(cl_json['paragraphs']):
        print(f"     [{i+1}] {len(p.split())} words, {len(p)} chars")
    print(f"   - closing: {len(cl_json['closing'])} chars, {len(cl_json['closing'].split())} words")

    # Check if name appears in JSON (SHOULD NOT)
    name_in_json = False
    candidate_name = "Fayed HANAFI"

    if candidate_name in cl_json['opening']:
        print(f"\n   [ERROR] Name '{candidate_name}' found in opening!")
        name_in_json = True

    for i, para in enumerate(cl_json['paragraphs']):
        if candidate_name in para:
            print(f"\n   [ERROR] Name '{candidate_name}' found in paragraph {i+1}!")
            name_in_json = True

    if candidate_name in cl_json['closing']:
        print(f"\n   [ERROR] Name '{candidate_name}' found in closing!")
        name_in_json = True

    if not name_in_json:
        print(f"\n   [OK] Name '{candidate_name}' NOT found in JSON content (as expected)")
else:
    print("\n   [WARN] No JSON structure in result (translation or legacy format)")

# Generate PDF from JSON
print("\n[3/4] Generating PDF from JSON...")
if "cover_letter_fr_json" in result:
    pdf_result = generate_cover_letter_files(
        cover_letter=result["cover_letter_fr_json"],  # Pass JSON directly
        cv_data=mock_cv,
        job_requirements=result["job_requirements"],
        output_dir="output/test_json",
        filename_base="fayed_goldman",
        language="fr",
        generate_docx=False
    )
    pdf_path = pdf_result["pdf_path"]
    print(f"   PDF generated: {pdf_path}")
else:
    print("   [WARN] No JSON, using text format")
    pdf_result = generate_cover_letter_files(
        cover_letter=result["cover_letter_fr"],
        cv_data=mock_cv,
        job_requirements=result["job_requirements"],
        output_dir="output/test_json",
        filename_base="fayed_goldman",
        language="fr",
        generate_docx=False
    )
    pdf_path = pdf_result["pdf_path"]

# Check PDF
print("\n[4/4] Analyzing PDF...")
if pdf_path:

    # Check page count
    reader = PdfReader(pdf_path)
    page_count = len(reader.pages)
    print(f"   Page count: {page_count}")

    if page_count == 1:
        print("   [OK] Exactly 1 page")
    else:
        print(f"   [ERROR] {page_count} pages instead of 1!")

    # Extract text and count name occurrences
    pdf_text = ""
    for page in reader.pages:
        pdf_text += page.extract_text()

    name_count = pdf_text.count(candidate_name)
    print(f"\n   Name occurrences in PDF: {name_count}")

    if name_count == 1:
        print(f"   [OK] Name '{candidate_name}' appears EXACTLY ONCE (signature)")
    else:
        print(f"   [ERROR] Name appears {name_count} times instead of 1!")
        print("\n   PDF Text Preview:")
        print("   " + "-" * 76)
        for line in pdf_text.split("\n")[:30]:
            if line.strip():
                print(f"   {line}")
        print("   " + "-" * 76)

    # Check for "Sincerely" or signature formulas
    if "Sincerely," in pdf_text or "Cordialement," in pdf_text:
        print(f"\n   [WARN] Found 'Sincerely,' or 'Cordialement,' in PDF (should not be in closing)")

    print(f"\n   PDF saved: {pdf_path}")
else:
    print("   [ERROR] No PDF generated!")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)

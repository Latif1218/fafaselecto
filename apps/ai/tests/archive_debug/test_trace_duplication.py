"""Trace duplication issue step by step."""

import sys
sys.path.insert(0, '.')

from app.cover_letter_generator import generate_cover_letter
from app.cover_letter_layout import generate_cover_letter_files, parse_cover_letter_text
from tests.test_cover_letter_fayed import FAYED_CV, GOLDMAN_JOB_OFFER
from PyPDF2 import PdfReader

print("="*80)
print("STEP 1: Generate cover letter")
print("="*80)

result = generate_cover_letter(
    cv_data=FAYED_CV,
    job_offer=GOLDMAN_JOB_OFFER,
    additional_notes="Test duplication",
    language="fr",
    generate_both_languages=False
)

cover_letter_text = result['cover_letter_fr']
print(f"\nGenerated text has {cover_letter_text.count('Je suis disponible')} occurrences of 'Je suis disponible'")

print("\n" + "="*80)
print("STEP 2: Parse cover letter")
print("="*80)

parsed = parse_cover_letter_text(cover_letter_text, "fr")

print(f"\nOpening: {parsed['opening']}")
print(f"Body paragraphs: {len(parsed['body_paragraphs'])}")
for i, p in enumerate(parsed['body_paragraphs']):
    has_closing = "Je suis disponible" in p
    print(f"  {i+1}. {p[:60]}... {'[HAS \"Je suis disponible\"]' if has_closing else ''}")

print(f"\nClosing ({len(parsed['closing'])} chars): {parsed['closing']}")
print(f"Closing has {parsed['closing'].count('Je suis disponible')} occurrences of 'Je suis disponible'")

print("\n" + "="*80)
print("STEP 3: Generate PDF")
print("="*80)

pdf_result = generate_cover_letter_files(
    cover_letter=cover_letter_text,
    cv_data=FAYED_CV,
    job_requirements=result['job_requirements'],
    output_dir="output/trace_test",
    filename_base="trace_duplication",
    language="fr",
    generate_docx=False
)

print(f"\nPDF generated: {pdf_result['pdf_path']}")

print("\n" + "="*80)
print("STEP 4: Check PDF content")
print("="*80)

reader = PdfReader(pdf_result['pdf_path'])
pdf_text = reader.pages[0].extract_text()

count = pdf_text.count('Je suis disponible')
print(f"\nPDF has {count} occurrences of 'Je suis disponible'")

if count > 1:
    print("\n[FAIL] DUPLICATION IN PDF!")
    lines = pdf_text.split('\n')
    for i, line in enumerate(lines):
        if 'Je suis disponible' in line:
            print(f"\n  Occurrence at line {i}:")
            print(f"    {line[:100]}")
else:
    print("\n[OK] No duplication in PDF")

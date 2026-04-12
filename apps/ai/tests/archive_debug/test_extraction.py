"""
Test PDF extraction
"""
import os
from app.llm_client import extract_text_from_pdf_bytes, generate_cv_content

# Load test PDF
input_path = "input/CHLOE.pdf"
with open(input_path, "rb") as f:
    pdf_bytes = f.read()

print("="*70)
print("PDF EXTRACTION TEST")
print("="*70)

# Extract
print("\n[1] Extracting text...")
original_text = extract_text_from_pdf_bytes(pdf_bytes, filename="test.pdf")

print(f"\nExtracted {len(original_text)} characters:")
print("-"*70)
print(original_text[:2000])
print("-"*70)

# Generate content
print("\n[2] Generating CV content...")
content = generate_cv_content(
    input_data={"raw_text": original_text},
    domain="finance",
    language="fr",
    enrichment_mode=False,
)

print("\nGenerated content structure:")
print(f"  - name: {content.get('name', 'N/A')}")
print(f"  - email: {content.get('email', 'N/A')}")
print(f"  - experience: {len(content.get('experience', []))} entries")
print(f"  - education: {len(content.get('education', []))} entries")
print(f"  - skills: {len(content.get('it_skills', []))} entries")

if content.get('experience'):
    print("\nExperiences:")
    for exp in content['experience']:
        print(f"  - {exp.get('title', 'N/A')} @ {exp.get('company', 'N/A')}")
        print(f"    Bullets: {len(exp.get('bullets', []))}")
else:
    print("\n[!] NO EXPERIENCES GENERATED - This is the problem!")
